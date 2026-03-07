"""
Model Training Script for RadVerify - v5
Best approach: oversampling + focal loss + two-phase fine-tuning.

Strategy:
 1. Balance the dataset by oversampling minority classes with heavy augmentation.
 2. Use focal loss (gamma=2) + label smoothing to handle remaining imbalance.
 3. Two-phase training: head-only, then top-80-layers fine-tune.
 4. Early stopping monitored on val_accuracy with patience=15.
"""

import os
import json
import numpy as np
import shutil
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
import yaml

# ── helpers ──────────────────────────────────────────────────────────────────

try:
    from modules.ai_analyzer import AIAnalyzer
    STRUCTURE_LABELS = [
        f"{cat}/{s}"
        for cat, structs in AIAnalyzer.FETAL_STRUCTURES.items()
        for s in structs
    ]
except Exception:
    STRUCTURE_LABELS = []


def focal_loss(gamma=1.5, smooth=0.02):
    """Focal loss with label smoothing."""
    def loss_fn(y_true, y_pred):
        n_cls = tf.cast(tf.shape(y_true)[-1], tf.float32)
        y_true_s = y_true * (1.0 - smooth) + smooth / n_cls
        y_pred = tf.clip_by_value(y_pred, 1e-8, 1.0 - 1e-8)
        ce = -tf.reduce_sum(y_true_s * tf.math.log(y_pred), axis=-1)
        p_t = tf.reduce_sum(y_true * y_pred, axis=-1)
        w = tf.pow(1.0 - p_t, gamma)
        return tf.reduce_mean(w * ce)
    return loss_fn


def make_tf_dataset(directory, class_names, img_size=224, batch_size=32,
                    augment=False, oversample=False, target_per_class=None,
                    aug_profile="ultrasound", weak_class_names=None,
                    weak_aug_prob=0.75):
    """
    Build a tf.data.Dataset from a directory structured as class sub-folders.
    If oversample=True, minority classes are repeated so every class has
    roughly target_per_class samples before augmentation.
    """
    # Gather file paths + labels
    paths, labels = [], []
    class_to_idx = {c: i for i, c in enumerate(class_names)}
    weak_class_names = weak_class_names or []
    weak_indices = [class_to_idx[c] for c in weak_class_names if c in class_to_idx]
    counts = {c: 0 for c in class_names}

    for cls in class_names:
        cls_dir = os.path.join(directory, cls)
        if not os.path.isdir(cls_dir):
            continue
        files = [os.path.join(cls_dir, f) for f in os.listdir(cls_dir)
                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        counts[cls] = len(files)

        if oversample and target_per_class and len(files) < target_per_class:
            # Repeat the list until we reach target_per_class
            repeats = (target_per_class + len(files) - 1) // len(files)
            files = (files * repeats)[:target_per_class]

        paths.extend(files)
        labels.extend([class_to_idx[cls]] * len(files))

    print(f"  Dataset: {directory}")
    for c, n in counts.items():
        eff = target_per_class if (oversample and target_per_class and n < target_per_class) else n
        print(f"    {c}: {n} raw -> {eff} effective")

    paths_t = tf.constant(paths)
    labels_t = tf.constant(labels, dtype=tf.int32)
    n_classes = len(class_names)

    def load_and_preprocess(path, label):
        img = tf.io.read_file(path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, [img_size, img_size])
        img = tf.cast(img, tf.float32) / 255.0
        return img, tf.one_hot(label, n_classes)

    def _strong_augment(img):
        if aug_profile == "strong":
            img = tf.image.random_flip_left_right(img)
            img = tf.image.random_brightness(img, 0.2)
            img = tf.image.random_contrast(img, 0.8, 1.2)
            img = tf.image.random_saturation(img, 0.8, 1.2)
            img = tf.image.random_crop(
                tf.image.resize_with_crop_or_pad(img, img_size + 20, img_size + 20),
                [img_size, img_size, 3]
            )
        else:
            # Strong policy focused on weak classes only.
            img = tf.image.random_flip_left_right(img)
            img = tf.image.random_brightness(img, 0.14)
            img = tf.image.random_contrast(img, 0.82, 1.18)
            img = tf.image.random_saturation(img, 0.9, 1.1)
            img = tf.image.random_crop(
                tf.image.resize_with_crop_or_pad(img, img_size + 16, img_size + 16),
                [img_size, img_size, 3]
            )
            noise = tf.random.normal(tf.shape(img), mean=0.0, stddev=0.02, dtype=tf.float32)
            img = img + noise
        return tf.clip_by_value(img, 0.0, 1.0)

    def _default_augment(img):
        # Default: conservative augment for fetal ultrasound.
        img = tf.image.random_brightness(img, 0.08)
        img = tf.image.random_contrast(img, 0.9, 1.1)
        img = tf.image.random_crop(
            tf.image.resize_with_crop_or_pad(img, img_size + 8, img_size + 8),
            [img_size, img_size, 3]
        )
        noise = tf.random.normal(tf.shape(img), mean=0.0, stddev=0.01, dtype=tf.float32)
        img = img + noise
        return tf.clip_by_value(img, 0.0, 1.0)

    weak_idx_tensor = tf.constant(weak_indices, dtype=tf.int32) if weak_indices else None

    def augment_fn(img, label):
        if weak_idx_tensor is None:
            return _default_augment(img), label

        label_idx = tf.argmax(label, axis=-1, output_type=tf.int32)
        is_weak = tf.reduce_any(tf.equal(label_idx, weak_idx_tensor))
        apply_strong = tf.logical_and(
            is_weak, tf.less(tf.random.uniform([], 0.0, 1.0), weak_aug_prob)
        )
        img = tf.cond(apply_strong, lambda: _strong_augment(img), lambda: _default_augment(img))
        img = tf.clip_by_value(img, 0.0, 1.0)
        return img, label

    ds = tf.data.Dataset.from_tensor_slices((paths_t, labels_t))
    ds = ds.shuffle(len(paths), reshuffle_each_iteration=True)
    ds = ds.map(load_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    if augment:
        ds = ds.map(augment_fn, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return ds, len(paths), n_classes


# ── Trainer ──────────────────────────────────────────────────────────────────

class FetalUltrasoundTrainer:
    """v5 Trainer: oversampling + focal loss + two-phase fine-tuning."""

    def __init__(self, config_path="config/config.yaml"):
        self.config = self._load_config(config_path)
        self.model = None
        self.base_model = None
        self.history = None

    def _load_config(self, config_path):
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def build_model(self, num_classes=3):
        print(f"Building EfficientNet-B0 for {num_classes} classes (v5)...")
        base = EfficientNetB0(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        self.base_model = base
        self.base_model.trainable = False

        x = base.output
        x = GlobalAveragePooling2D()(x)
        x = BatchNormalization()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.4)(x)
        x = BatchNormalization()(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.3)(x)
        out = Dense(num_classes, activation='softmax')(x)

        self.model = Model(inputs=base.input, outputs=out)
        print(f"  Output shape: {self.model.output_shape}")
        return self.model

    def _compile(self, lr):
        gamma = float(os.getenv("RADVERIFY_FOCAL_GAMMA", "1.5"))
        smooth = float(os.getenv("RADVERIFY_LABEL_SMOOTH", "0.02"))
        self.model.compile(
            optimizer=Adam(learning_rate=lr),
            loss=focal_loss(gamma=gamma, smooth=smooth),
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )

    def _callbacks(self, output_dir, monitor='val_accuracy', patience=15):
        return [
            ModelCheckpoint(
                os.path.join(output_dir, 'best_model.keras'),
                monitor=monitor, save_best_only=True, verbose=1
            ),
            ModelCheckpoint(
                os.path.join(output_dir, 'best_model.h5'),
                monitor=monitor, save_best_only=True, verbose=0
            ),
            EarlyStopping(
                monitor=monitor, patience=patience,
                restore_best_weights=True, verbose=1, min_delta=0.005
            ),
            ReduceLROnPlateau(
                monitor='val_loss', factor=0.5, patience=5,
                min_lr=1e-7, verbose=1
            ),
        ]

    def _evaluate_ds(self, ds, class_names):
        all_true, all_pred = [], []
        for imgs, lbls in ds:
            preds = self.model.predict(imgs, verbose=0)
            all_true.extend(np.argmax(lbls.numpy(), axis=1))
            all_pred.extend(np.argmax(preds, axis=1))

        all_true = np.array(all_true)
        all_pred = np.array(all_pred)
        n = len(class_names)
        cm = np.zeros((n, n), dtype=int)
        for t, p in zip(all_true, all_pred):
            cm[t, p] += 1

        per_class = {}
        for i, name in enumerate(class_names):
            tp = cm[i, i]; fp = cm[:, i].sum() - tp; fn = cm[i, :].sum() - tp
            pr = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rc = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * pr * rc / (pr + rc) if (pr + rc) > 0 else 0.0
            per_class[name] = {
                'precision': round(pr, 4), 'recall': round(rc, 4),
                'f1': round(f1, 4), 'support': int(cm[i].sum())
            }

        acc = float(np.mean(all_true == all_pred))
        macro_f1 = float(np.mean([m['f1'] for m in per_class.values()]))
        return {
            'class_names': class_names,
            'confusion_matrix': cm.tolist(),
            'per_class': per_class,
            'macro_f1': round(macro_f1, 4),
            'accuracy': round(acc, 4),
            'samples': int(len(all_true)),
        }

    def _collect_probs(self, ds):
        """Collect y_true indices and model probabilities for threshold calibration."""
        y_true, y_prob = [], []
        for imgs, lbls in ds:
            preds = self.model.predict(imgs, verbose=0)
            y_true.extend(np.argmax(lbls.numpy(), axis=1))
            y_prob.extend(preds.tolist())
        return np.array(y_true, dtype=np.int32), np.array(y_prob, dtype=np.float32)

    def _calibrate_thresholds(self, y_true, y_prob, class_names):
        """
        One-vs-rest threshold sweep per class.
        Pick threshold that maximizes F1 on validation data.
        """
        out = {}
        if y_true.size == 0 or y_prob.size == 0:
            return out

        grid = np.linspace(0.05, 0.95, 91)
        n_classes = len(class_names)
        for i in range(n_classes):
            pos = (y_true == i).astype(np.int32)
            scores = y_prob[:, i]
            best = {
                'threshold': 0.5,
                'f1': 0.0,
                'precision': 0.0,
                'recall': 0.0,
            }
            for thr in grid:
                pred = (scores >= thr).astype(np.int32)
                tp = int(np.sum((pred == 1) & (pos == 1)))
                fp = int(np.sum((pred == 1) & (pos == 0)))
                fn = int(np.sum((pred == 0) & (pos == 1)))
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

                if f1 > best['f1'] or (
                    abs(f1 - best['f1']) < 1e-9 and precision > best['precision']
                ):
                    best = {
                        'threshold': float(round(thr, 3)),
                        'f1': float(round(f1, 4)),
                        'precision': float(round(precision, 4)),
                        'recall': float(round(recall, 4)),
                    }
            out[class_names[i]] = best
        return out

    def train(self, train_ds, val_ds, test_ds, class_names, steps_per_epoch,
              epochs=50, output_dir="models"):
        os.makedirs(output_dir, exist_ok=True)
        head_ep = max(1, int(epochs * 0.35))
        ft_ep = max(1, epochs - head_ep)
        print(f"Schedule: {head_ep} head epochs + {ft_ep} fine-tune epochs")

        # Phase 1: head only
        self.base_model.trainable = False
        self._compile(lr=5e-4)
        print("\n-- Phase 1: Training head --")
        h1 = self.model.fit(
            train_ds, validation_data=val_ds,
            epochs=head_ep, steps_per_epoch=steps_per_epoch,
            callbacks=self._callbacks(output_dir),
            verbose=1
        )

        # Phase 2: fine-tune top-80 layers
        self.base_model.trainable = True
        for layer in self.base_model.layers[:-80]:
            layer.trainable = False
        self._compile(lr=1e-5)
        print("\n-- Phase 2: Fine-tuning top layers --")
        h2 = self.model.fit(
            train_ds, validation_data=val_ds,
            epochs=head_ep + ft_ep,
            initial_epoch=head_ep,
            steps_per_epoch=steps_per_epoch,
            callbacks=self._callbacks(output_dir),
            verbose=1
        )

        self.history = {'head': h1.history, 'fine_tune': h2.history}

        # Save labels
        labels_path = os.path.join(output_dir, 'labels.json')
        with open(labels_path, 'w') as f:
            json.dump(class_names, f, indent=2)
        print(f"Saved labels to {labels_path}")

        # Evaluate & save metrics
        print("\nEvaluating on validation set...")
        val_metrics = self._evaluate_ds(val_ds, class_names)
        test_metrics = self._evaluate_ds(test_ds, class_names) if test_ds else None
        y_val_true, y_val_prob = self._collect_probs(val_ds)
        calibrated_thresholds = self._calibrate_thresholds(y_val_true, y_val_prob, class_names)

        metrics_bundle = {
            'validation': val_metrics,
            'test': test_metrics,
            'calibrated_thresholds': calibrated_thresholds,
        }
        mpath = os.path.join(output_dir, 'validation_metrics.json')
        with open(mpath, 'w') as f:
            json.dump(metrics_bundle, f, indent=2)
        print(f"Saved metrics to {mpath}")
        tpath = os.path.join(output_dir, 'class_thresholds.json')
        with open(tpath, 'w') as f:
            json.dump(calibrated_thresholds, f, indent=2)
        print(f"Saved class thresholds to {tpath}")

        # Save final model
        self.model.save(os.path.join(output_dir, 'final_model.keras'))
        self.model.save(os.path.join(output_dir, 'final_model.h5'))

        # Archive
        ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        arc_dir = os.path.join(output_dir, 'archive', ts)
        os.makedirs(arc_dir, exist_ok=True)
        for fn in ['best_model.keras', 'best_model.h5', 'labels.json', 'validation_metrics.json', 'class_thresholds.json']:
            src = os.path.join(output_dir, fn)
            if os.path.exists(src):
                shutil.copy2(src, arc_dir)

        with open(os.path.join(output_dir, 'MODEL_CARD.md'), 'w') as f:
            f.write("# RadVerify Model Card\n\n")
            f.write(f"- Version: v5 (oversampling + focal loss)\n")
            f.write(f"- Timestamp: {ts}\n")
            f.write(f"- Classes: {class_names}\n")
            f.write(f"- Val Accuracy: {val_metrics['accuracy']*100:.1f}%\n")
            f.write(f"- Val Macro F1: {val_metrics['macro_f1']:.4f}\n")
            if test_metrics:
                f.write(f"- Test Accuracy: {test_metrics['accuracy']*100:.1f}%\n")

        print(f"\n{'='*50}")
        print(f"OK: Training complete! (v5)")
        print(f"  Val Accuracy: {val_metrics['accuracy']*100:.1f}%")
        print(f"  Val Macro F1: {val_metrics['macro_f1']:.4f}")
        print(f"  Per-class F1:")
        for cls, m in val_metrics['per_class'].items():
            print(f"    {cls}: F1={m['f1']:.3f}  (precision={m['precision']:.2f}, recall={m['recall']:.2f})")
        print(f"{'='*50}\n")
        return self.history


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    DATASET_PATH = os.getenv("RADVERIFY_DATASET_PATH", "data/Data")
    TRAIN_DIR = os.path.join(DATASET_PATH, "train")
    VAL_DIR   = os.path.join(DATASET_PATH, "validation")
    TEST_DIR  = os.path.join(DATASET_PATH, "test")
    OUTPUT_DIR = os.getenv("RADVERIFY_OUTPUT_DIR", "models")

    EPOCHS      = int(os.getenv("RADVERIFY_EPOCHS",      "50"))
    BATCH_SIZE  = int(os.getenv("RADVERIFY_BATCH_SIZE",  "16"))
    AUG_PROFILE = os.getenv("RADVERIFY_AUG_PROFILE", "ultrasound").strip().lower()
    WEAK_CLASSES = [
        x.strip()
        for x in os.getenv("RADVERIFY_WEAK_CLASSES", "").split(",")
        if x.strip()
    ]
    WEAK_AUG_PROB = float(os.getenv("RADVERIFY_WEAK_AUG_PROB", "0.75"))
    REQUIRE_GPU = os.getenv("RADVERIFY_REQUIRE_GPU", "0").strip() == "1"

    gpus = tf.config.list_physical_devices("GPU")
    print(f"Detected GPUs: {len(gpus)}")
    if REQUIRE_GPU and not gpus:
        raise RuntimeError("RADVERIFY_REQUIRE_GPU=1 but no GPU detected. Aborting training.")

    # Auto-detect classes
    class_names = sorted([
        d for d in os.listdir(TRAIN_DIR)
        if os.path.isdir(os.path.join(TRAIN_DIR, d))
        and any(True for f in os.listdir(os.path.join(TRAIN_DIR, d))
                if os.path.isfile(os.path.join(TRAIN_DIR, d, f)))
    ])
    print(f"Detected classes: {class_names}")

    # Count raw samples to determine oversample target
    raw_counts = {}
    for c in class_names:
        raw_counts[c] = len([
            f for f in os.listdir(os.path.join(TRAIN_DIR, c))
            if os.path.isfile(os.path.join(TRAIN_DIR, c, f))
        ])
    max_count = max(raw_counts.values())
    target_per_class = max_count  # oversample minorities to match the majority

    print(f"Raw counts: {raw_counts}")
    print(f"Oversampling minorities to {target_per_class} samples each")
    if WEAK_CLASSES:
        print(f"Weak classes for targeted augmentation: {WEAK_CLASSES}")
        print(f"Weak-class strong augmentation probability: {WEAK_AUG_PROB}")

    # Build datasets
    print("\nBuilding training dataset (with oversampling)...")
    train_ds, n_train, n_classes = make_tf_dataset(
        TRAIN_DIR, class_names,
        img_size=224, batch_size=BATCH_SIZE,
        augment=True, oversample=True, target_per_class=target_per_class,
        aug_profile=AUG_PROFILE,
        weak_class_names=WEAK_CLASSES,
        weak_aug_prob=WEAK_AUG_PROB,
    )

    print("\nBuilding validation dataset...")
    val_ds, n_val, _ = make_tf_dataset(
        VAL_DIR, class_names,
        img_size=224, batch_size=BATCH_SIZE,
        augment=False, oversample=False,
        aug_profile=AUG_PROFILE
    )

    test_ds = None
    if os.path.isdir(TEST_DIR):
        print("\nBuilding test dataset...")
        test_ds, _, _ = make_tf_dataset(
            TEST_DIR, class_names,
            img_size=224, batch_size=BATCH_SIZE,
            augment=False, oversample=False,
            aug_profile=AUG_PROFILE
        )

    steps_per_epoch = (n_train + BATCH_SIZE - 1) // BATCH_SIZE

    # Train
    trainer = FetalUltrasoundTrainer()
    trainer.build_model(num_classes=n_classes)
    trainer.train(
        train_ds, val_ds, test_ds, class_names,
        steps_per_epoch=steps_per_epoch,
        epochs=EPOCHS,
        output_dir=OUTPUT_DIR,
    )


if __name__ == "__main__":
    main()
