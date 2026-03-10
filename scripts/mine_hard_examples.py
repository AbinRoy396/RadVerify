"""
Mine hard examples for skull-focused relabel review.

Outputs:
- CSV with prediction details
- Copied review images for top skull confusions
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

import numpy as np
import tensorflow as tf


IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp"}


def load_paths(split_dir: Path, labels: list[str]):
    rows = []
    for gt_idx, cls in enumerate(labels):
        cdir = split_dir / cls
        if not cdir.exists():
            continue
        for p in cdir.iterdir():
            if p.suffix.lower() in IMG_EXTS:
                rows.append((p, gt_idx))
    return rows


def preprocess(paths: list[Path]) -> tf.Tensor:
    xs = []
    for p in paths:
        img = tf.io.decode_image(tf.io.read_file(str(p)), channels=3, expand_animations=False)
        img = tf.image.resize(img, [224, 224])
        xs.append(tf.cast(img, tf.float32) / 255.0)
    return tf.stack(xs, axis=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/structure_dataset_core6_v1")
    ap.add_argument("--model", default="models/best_model.keras")
    ap.add_argument("--labels", default="models/labels.json")
    ap.add_argument("--split", default="train", choices=["train", "validation", "test"])
    ap.add_argument("--out", default="logs/hard_examples_core6")
    ap.add_argument("--top-n", type=int, default=200)
    args = ap.parse_args()

    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    model = tf.keras.models.load_model(args.model, compile=False)
    split_dir = Path(args.dataset) / args.split
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    items = load_paths(split_dir, labels)
    if not items:
        print("No images found.")
        return

    paths = [p for p, _ in items]
    y_true = np.array([y for _, y in items], dtype=np.int32)
    probs = model.predict(preprocess(paths), batch_size=32, verbose=0)
    y_pred = np.argmax(probs, axis=1)

    skull_idx = labels.index("brain_skull") if "brain_skull" in labels else -1
    records = []
    for p, gt, pred, prob in zip(paths, y_true, y_pred, probs):
        top_conf = float(prob[pred])
        p_sk = float(prob[skull_idx]) if skull_idx >= 0 else 0.0
        records.append(
            {
                "file": str(p),
                "basename": p.name,
                "gt_label": labels[gt],
                "pred_label": labels[pred],
                "top_conf": round(top_conf, 6),
                "p_brain_skull": round(p_sk, 6),
                "is_error": int(gt != pred),
            }
        )

    csv_path = out_dir / f"{args.split}_predictions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "basename",
                "gt_label",
                "pred_label",
                "top_conf",
                "p_brain_skull",
                "is_error",
            ],
        )
        w.writeheader()
        w.writerows(records)

    # Skull-focused hard set: GT skull but predicted not skull, highest confidence wrong first.
    hard = [
        r for r in records
        if r["gt_label"] == "brain_skull" and r["pred_label"] != "brain_skull"
    ]
    hard.sort(key=lambda r: r["top_conf"], reverse=True)
    hard = hard[: args.top_n]

    review_root = out_dir / f"{args.split}_skull_hard_top{args.top_n}"
    for r in hard:
        pred_dir = review_root / r["pred_label"]
        pred_dir.mkdir(parents=True, exist_ok=True)
        src = Path(r["file"])
        dst = pred_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)

    summary = {
        "split": args.split,
        "samples": len(records),
        "errors": int(sum(r["is_error"] for r in records)),
        "accuracy": round(float(np.mean(y_true == y_pred)), 4),
        "skull_gt_count": int(sum(1 for r in records if r["gt_label"] == "brain_skull")),
        "skull_gt_recall": round(
            float(
                np.mean(
                    [
                        r["pred_label"] == "brain_skull"
                        for r in records
                        if r["gt_label"] == "brain_skull"
                    ]
                )
            ),
            4,
        ),
        "csv": str(csv_path),
        "review_dir": str(review_root),
        "hard_count": len(hard),
    }
    (out_dir / f"{args.split}_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

