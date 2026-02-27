"""
Model Training Script for RadVerify
Fine-tunes EfficientNet-B0 on fetal ultrasound datasets.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import yaml

try:
    from modules.ai_analyzer import AIAnalyzer
    STRUCTURE_LABELS = [
        f"{category}/{structure}"
        for category, structures in AIAnalyzer.FETAL_STRUCTURES.items()
        for structure in structures
    ]
except Exception:
    STRUCTURE_LABELS = []

class FetalUltrasoundTrainer:
    """Trainer for fine-tuning on medical ultrasound data."""
    
    def __init__(self, config_path="config/config.yaml"):
        """Initialize trainer with configuration."""
        self.config = self._load_config(config_path)
        self.model = None
        self.base_model = None
        self.history = None
        
    def _load_config(self, config_path):
        """Load training configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}
    
    def build_model(self, num_classes=10):
        """
        Build the fine-tuning model.
        
        Args:
            num_classes: Number of fetal structure classes to detect
        """
        print("Building model for fine-tuning...")
        
        # Load pre-trained EfficientNet-B0
        base_model = EfficientNetB0(
            weights='imagenet',
            include_top=False,
            input_shape=(224, 224, 3)
        )
        self.base_model = base_model
        # Phase 1 starts with the full backbone frozen.
        self.base_model.trainable = False
        
        # Add custom classification head
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.3)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.2)(x)
        predictions = Dense(num_classes, activation='softmax')(x)
        
        self.model = Model(inputs=base_model.input, outputs=predictions)
        
        # Compile model
        self.model.compile(
            optimizer=Adam(learning_rate=0.0001),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )
        
        print(f"OK: Model built with {num_classes} output classes")
        return self.model

    def _compile(self, learning_rate: float):
        self.model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss='categorical_crossentropy',
            metrics=['accuracy', 'top_k_categorical_accuracy']
        )

    def _compute_class_weights(self, train_generator):
        counts = np.bincount(train_generator.classes)
        total = counts.sum()
        n_classes = len(counts)
        # Inverse-frequency weighting.
        weights = {
            i: float(total / (n_classes * c)) if c > 0 else 1.0
            for i, c in enumerate(counts)
        }
        return weights

    def _save_per_class_metrics(self, val_generator, output_dir="models"):
        val_generator.reset()
        probs = self.model.predict(val_generator, verbose=0)
        y_pred = np.argmax(probs, axis=1)
        y_true = val_generator.classes
        class_names = list(val_generator.class_indices.keys())
        n_classes = len(class_names)

        cm = np.zeros((n_classes, n_classes), dtype=int)
        for t, p in zip(y_true, y_pred):
            cm[t, p] += 1

        metrics = {}
        for i, name in enumerate(class_names):
            tp = cm[i, i]
            fp = cm[:, i].sum() - tp
            fn = cm[i, :].sum() - tp
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            support = int(cm[i, :].sum())
            metrics[name] = {
                "precision": round(float(precision), 4),
                "recall": round(float(recall), 4),
                "f1": round(float(f1), 4),
                "support": support
            }

        out = {
            "class_names": class_names,
            "confusion_matrix": cm.tolist(),
            "per_class": metrics
        }
        metrics_path = os.path.join(output_dir, "validation_metrics.json")
        with open(metrics_path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"Saved per-class metrics to {metrics_path}")
    
    def prepare_data_generators(self, train_dir, val_dir, batch_size=32):
        """
        Create data generators with augmentation.
        
        Args:
            train_dir: Path to training images (organized in class folders)
            val_dir: Path to validation images
            batch_size: Batch size for training
        """
        # Training data augmentation (V3: Reduced to preserve medical features)
        train_datagen = ImageDataGenerator(
            rescale=1./255,
            horizontal_flip=True,
            fill_mode='nearest'
        )
        
        # Validation data (no augmentation)
        val_datagen = ImageDataGenerator(rescale=1./255)
        
        train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(224, 224),
            batch_size=batch_size,
            class_mode='categorical'
        )
        
        val_generator = val_datagen.flow_from_directory(
            val_dir,
            target_size=(224, 224),
            batch_size=batch_size,
            class_mode='categorical'
        )
        
        return train_generator, val_generator
    
    def train(self, train_generator, val_generator, epochs=50, output_dir="models", labels=None):
        """
        Train the model.
        
        Args:
            train_generator: Training data generator
            val_generator: Validation data generator
            epochs: Number of training epochs
            output_dir: Directory to save model weights
        """
        os.makedirs(output_dir, exist_ok=True)
        
        class_weights = self._compute_class_weights(train_generator)
        print(f"Class weights: {class_weights}")

        head_epochs = max(1, int(epochs * 0.4))
        fine_tune_epochs = max(1, epochs - head_epochs)
        print(f"Training schedule: head={head_epochs} epochs, fine_tune={fine_tune_epochs} epochs")

        # Callbacks
        callbacks = [
            ModelCheckpoint(
                filepath=os.path.join(output_dir, 'best_model.h5'),
                monitor='val_accuracy',
                save_best_only=True,
                verbose=1
            ),
            EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]

        print(f"\nStarting training for {epochs} epochs...")
        print(f"Training samples: {train_generator.samples}")
        print(f"Validation samples: {val_generator.samples}")

        # Phase 1: train only the classification head.
        self.base_model.trainable = False
        self._compile(learning_rate=2e-4) # V3: Higher initial LR
        history_head = self.model.fit(
            train_generator,
            validation_data=val_generator,
            epochs=head_epochs,
            callbacks=callbacks,
            class_weight=class_weights,
            verbose=1
        )

        # Phase 2: unfreeze top backbone layers and fine-tune with lower LR.
        self.base_model.trainable = True
        for layer in self.base_model.layers[:-50]: # V3: Unfreeze more layers
            layer.trainable = False
        self._compile(learning_rate=5e-5) # V3: Higher fine-tuning LR
        history_ft = self.model.fit(
            train_generator,
            validation_data=val_generator,
            epochs=head_epochs + fine_tune_epochs,
            initial_epoch=head_epochs,
            callbacks=callbacks,
            class_weight=class_weights,
            verbose=1
        )

        # Keep concatenated history for inspection.
        self.history = {
            "head": history_head.history,
            "fine_tune": history_ft.history
        }
        
        if labels:
            labels_path = os.path.join(output_dir, "labels.json")
            with open(labels_path, "w", encoding="utf-8") as f:
                json.dump(labels, f, indent=2)
            print(f"Saved labels to {labels_path}")

        self._save_per_class_metrics(val_generator, output_dir=output_dir)

        # Save final model
        final_path = os.path.join(output_dir, 'final_model.h5')
        self.model.save(final_path)
        print(f"\nOK: Training complete! Model saved to {final_path}")
        
        return self.history
    
    def evaluate(self, test_generator):
        """Evaluate model on test set."""
        print("\nEvaluating model...")
        results = self.model.evaluate(test_generator, verbose=1)
        print(f"Test Loss: {results[0]:.4f}")
        print(f"Test Accuracy: {results[1]:.4f}")
        return results


def main():
    """
    Main training pipeline.
    
    USAGE:
    1. Organize your dataset:
       data/
         train/
           class_0_head/
             image1.jpg
             image2.jpg
           class_1_abdomen/
             ...
         val/
           class_0_head/
           class_1_abdomen/
    
    2. Run: python train_model.py
    """
    
    # Configuration for User's Custom Dataset
    # Structure based on screenshot:
    # data/Data/
    #   train/
    #   test/
    #   validation/
    
    # Path to where you extracted the folder
    DATASET_PATH = os.getenv("RADVERIFY_DATASET_PATH", "data/Data")
    
    # Explicit folder paths from your screenshot
    TRAIN_DIR = os.path.join(DATASET_PATH, "train")
    VAL_DIR = os.path.join(DATASET_PATH, "validation")
    TEST_DIR = os.path.join(DATASET_PATH, "test")
    
    labels = []
    # Check if we need to auto-detect classes
    if os.path.exists(TRAIN_DIR):
        # Only keep classes that actually have at least one training image.
        classes = []
        for d in os.listdir(TRAIN_DIR):
            class_dir = os.path.join(TRAIN_DIR, d)
            if not os.path.isdir(class_dir):
                continue
            if any(os.path.isfile(os.path.join(class_dir, f)) for f in os.listdir(class_dir)):
                classes.append(d)
        NUM_CLASSES = len(classes)
        labels = sorted(classes)
        print(f"Detected {NUM_CLASSES} non-empty classes: {labels}")
    else:
        NUM_CLASSES = len(STRUCTURE_LABELS) if STRUCTURE_LABELS else 2
        labels = STRUCTURE_LABELS
        
    EPOCHS = int(os.getenv("RADVERIFY_EPOCHS", "20"))
    BATCH_SIZE = int(os.getenv("RADVERIFY_BATCH_SIZE", "16"))

    # Initialize trainer
    trainer = FetalUltrasoundTrainer()
    
    # Build model
    trainer.build_model(num_classes=NUM_CLASSES)
    
    # Prepare data
    print("\nLoading dataset from:", DATASET_PATH)
    
    # Training Generator (from 'train' folder)
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    train_gen = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(224, 224),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=labels if labels else None
    )
    
    # Validation Generator (from 'validation' folder)
    val_datagen = ImageDataGenerator(rescale=1./255)
    
    val_gen = val_datagen.flow_from_directory(
        VAL_DIR,
        target_size=(224, 224),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=labels if labels else None
    )
    
    # Train
    trainer.train(train_gen, val_gen, epochs=EPOCHS, labels=labels)
    
    print("\n" + "="*50)
    print("NEXT STEPS:")
    print("1. Copy 'models/best_model.h5' to your project")
    print("2. Update ai_analyzer.py to load this model:")
    print("   self.model = tf.keras.models.load_model('models/best_model.h5')")
    print("="*50)


if __name__ == "__main__":
    main()
