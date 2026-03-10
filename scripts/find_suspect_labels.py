"""
Find potentially mislabeled samples using high-confidence model disagreements.

Usage:
  python scripts/find_suspect_labels.py \
    --dataset data/structure_dataset_clean12 \
    --split train \
    --model models/best_model.keras \
    --out logs/suspects_train.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="data/structure_dataset_clean12")
    p.add_argument("--split", default="train", choices=["train", "validation", "test"])
    p.add_argument("--model", default="models/best_model.keras")
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--image-size", type=int, default=224)
    p.add_argument("--min-confidence", type=float, default=0.75)
    p.add_argument("--top-k", type=int, default=500)
    p.add_argument("--out", default="logs/suspects_train.csv")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    split_dir = Path(args.dataset) / args.split
    model_path = Path(args.model)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not split_dir.exists():
        raise FileNotFoundError(f"Split not found: {split_dir}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = tf.keras.models.load_model(model_path, compile=False)
    datagen = ImageDataGenerator(rescale=1.0 / 255.0)
    gen = datagen.flow_from_directory(
        str(split_dir),
        target_size=(args.image_size, args.image_size),
        batch_size=args.batch_size,
        class_mode="categorical",
        shuffle=False,
    )

    probs = model.predict(gen, verbose=1)
    y_true = gen.classes
    y_pred = np.argmax(probs, axis=1)
    class_names = {v: k for k, v in gen.class_indices.items()}
    filenames = gen.filenames

    suspects = []
    for i, (t, p) in enumerate(zip(y_true, y_pred)):
        if t == p:
            continue
        conf = float(probs[i, p])
        if conf < args.min_confidence:
            continue
        true_conf = float(probs[i, t])
        suspects.append(
            {
                "index": i,
                "file": filenames[i],
                "true_label": class_names[int(t)],
                "pred_label": class_names[int(p)],
                "pred_confidence": round(conf, 6),
                "true_confidence": round(true_conf, 6),
                "confidence_gap": round(conf - true_conf, 6),
            }
        )

    suspects.sort(key=lambda x: (x["pred_confidence"], x["confidence_gap"]), reverse=True)
    suspects = suspects[: args.top_k]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "index",
                "file",
                "true_label",
                "pred_label",
                "pred_confidence",
                "true_confidence",
                "confidence_gap",
            ],
        )
        writer.writeheader()
        writer.writerows(suspects)

    print(f"suspects_written={len(suspects)}")
    print(f"output={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
