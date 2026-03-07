"""
Build the core-6 dataset from an existing split dataset.

Core-6 classes:
  - brain_skull
  - brain_ventricles
  - brain_cerebellum
  - biometry_abdomen
  - biometry_femur
  - heart_four_chamber_view

Usage:
  python scripts/build_core6_dataset.py \
    --source data/structure_dataset_clean12_v2 \
    --output data/structure_dataset_core6_v1
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


CORE6_CLASSES = [
    "brain_skull",
    "brain_ventricles",
    "brain_cerebellum",
    "biometry_abdomen",
    "biometry_femur",
    "heart_four_chamber_view",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="data/structure_dataset_clean12_v2")
    p.add_argument("--output", default="data/structure_dataset_core6_v1")
    p.add_argument("--summary", default="logs/core6_dataset_summary.json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.source)
    dst = Path(args.output)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(f"Source dataset not found: {src}")

    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)

    counts = {}
    for split in ["train", "validation", "test"]:
        counts[split] = {}
        for cls in CORE6_CLASSES:
            src_dir = src / split / cls
            dst_dir = dst / split / cls
            dst_dir.mkdir(parents=True, exist_ok=True)
            if not src_dir.exists():
                counts[split][cls] = 0
                continue
            n = 0
            for f in src_dir.iterdir():
                if not f.is_file():
                    continue
                shutil.copy2(f, dst_dir / f.name)
                n += 1
            counts[split][cls] = n

    total = {split: sum(c.values()) for split, c in counts.items()}
    out = {
        "source": str(src),
        "output": str(dst),
        "classes": CORE6_CLASSES,
        "counts": counts,
        "totals": total,
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"output={dst}")
    print(f"train={total['train']} validation={total['validation']} test={total['test']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
