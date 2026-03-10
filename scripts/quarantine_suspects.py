"""
Move suspect training files into a quarantine folder so they are excluded from training.

Usage:
  python scripts/quarantine_suspects.py \
    --dataset data/structure_dataset_clean12 \
    --split train \
    --suspects-csv logs/suspects_train.csv \
    --quarantine-root data/structure_dataset_quarantine
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="data/structure_dataset_clean12")
    p.add_argument("--split", default="train")
    p.add_argument("--suspects-csv", default="logs/suspects_train.csv")
    p.add_argument("--quarantine-root", default="data/structure_dataset_quarantine")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    dataset = Path(args.dataset)
    split_dir = dataset / args.split
    suspects_csv = Path(args.suspects_csv)
    quarantine_root = Path(args.quarantine_root) / args.split

    if not split_dir.exists():
        raise FileNotFoundError(f"Split not found: {split_dir}")
    if not suspects_csv.exists():
        raise FileNotFoundError(f"Suspects CSV not found: {suspects_csv}")

    moved = 0
    missing = 0
    with suspects_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel = Path(row["file"])
            src = split_dir / rel
            dst = quarantine_root / rel
            if not src.exists():
                missing += 1
                continue
            if args.dry_run:
                moved += 1
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved += 1

    print(f"moved={moved}")
    print(f"missing={missing}")
    print(f"quarantine={quarantine_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
