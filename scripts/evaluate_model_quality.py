"""
Evaluate trained classifier on a held-out dataset and export quality artifacts.

Usage:
  python scripts/evaluate_model_quality.py \
    --dataset data/structure_dataset \
    --split test \
    --model models/best_model.keras
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import tensorflow as tf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RadVerify model quality")
    parser.add_argument("--dataset", default="data/structure_dataset", help="Dataset root containing train/val/test")
    parser.add_argument("--split", default="test", help="Split directory name under dataset root")
    parser.add_argument("--model", default="models/best_model.keras", help="Path to trained model")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size")
    parser.add_argument("--image-size", type=int, default=224, help="Input image size")
    parser.add_argument("--output", default="models/eval", help="Output directory")
    parser.add_argument(
        "--write-validation-metrics",
        action="store_true",
        help="Also merge evaluation summary into models/validation_metrics.json under evaluation_latest",
    )
    return parser.parse_args()


def _save_confusion_matrix(cm: np.ndarray, class_names: list[str], out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=class_names,
        yticklabels=class_names,
        ylabel="True label",
        xlabel="Predicted label",
        title="Confusion Matrix",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    thresh = cm.max() / 2.0 if cm.size else 0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                format(cm[i, j], "d"),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
            )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    dataset_split = Path(args.dataset) / args.split
    model_path = Path(args.model)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not dataset_split.exists():
        raise FileNotFoundError(f"Split directory not found: {dataset_split}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    # Avoid deserialization failures when model was trained with custom losses/metrics.
    model = tf.keras.models.load_model(model_path, compile=False)
    datagen = ImageDataGenerator(rescale=1.0 / 255.0)
    generator = datagen.flow_from_directory(
        str(dataset_split),
        target_size=(args.image_size, args.image_size),
        batch_size=args.batch_size,
        class_mode="categorical",
        shuffle=False,
    )

    probs = model.predict(generator, verbose=0)
    y_pred = np.argmax(probs, axis=1)
    y_true = generator.classes
    class_names = list(generator.class_indices.keys())

    cm = confusion_matrix(y_true, y_pred, labels=np.arange(len(class_names)))
    report = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        labels=np.arange(len(class_names)),
        output_dict=True,
        zero_division=0,
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_path": str(model_path),
        "dataset_split": str(dataset_split),
        "samples": int(len(y_true)),
        "accuracy": float(report["accuracy"]),
        "macro_precision": float(report["macro avg"]["precision"]),
        "macro_recall": float(report["macro avg"]["recall"]),
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "per_class": {
            k: {
                "precision": float(v["precision"]),
                "recall": float(v["recall"]),
                "f1": float(v["f1-score"]),
                "support": int(v["support"]),
            }
            for k, v in report.items()
            if k in class_names
        },
        "confusion_matrix": cm.tolist(),
    }

    summary_path = output_dir / "quality_report.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    cm_path = output_dir / "confusion_matrix.png"
    _save_confusion_matrix(cm, class_names, cm_path)

    if args.write_validation_metrics:
        vm_path = Path("models") / "validation_metrics.json"
        if vm_path.exists():
            with vm_path.open("r", encoding="utf-8") as f:
                vm_data = json.load(f)
        else:
            vm_data = {}
        vm_data["evaluation_latest"] = summary
        with vm_path.open("w", encoding="utf-8") as f:
            json.dump(vm_data, f, indent=2)

    print(f"Saved quality report: {summary_path}")
    print(f"Saved confusion matrix image: {cm_path}")
    print(
        "Accuracy={:.4f} MacroF1={:.4f} WeightedF1={:.4f}".format(
            summary["accuracy"], summary["macro_f1"], summary["weighted_f1"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
