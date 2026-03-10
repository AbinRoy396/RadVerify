"""
Build a conflict-cleaned dataset by removing:
1) cross-split duplicate leakage (same image in train/val/test)
2) cross-class label conflicts (same image assigned to multiple classes)

Usage:
  python scripts/clean_dataset_conflicts.py \
    --dataset data/structure_dataset_clean12 \
    --output data/structure_dataset_clean12_v2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from pathlib import Path


CLASS_PRIORITY = {
    "brain_skull": 1,
    "brain_ventricles": 1,
    "brain_cerebellum": 1,
    "biometry_abdomen": 1,
    "biometry_femur": 1,
    "heart_four_chamber_view": 1,
    "face_profile": 2,
    "face_nasal_bone": 2,
    "face_lips": 2,
    "spine_vertebrae": 2,
    "spine_skin_coverage": 2,
    "organs_stomach": 3,
    "organs_kidneys": 3,
    "organs_bladder": 3,
    "limbs_arms": 4,
    "limbs_legs": 4,
    "limbs_hands": 4,
    "limbs_feet": 4,
}

# Keep holdout integrity: prefer test/validation over train for duplicate hashes.
SPLIT_PRIORITY = {"test": 0, "validation": 1, "train": 2}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="data/structure_dataset_clean12")
    p.add_argument("--output", default="data/structure_dataset_clean12_v2")
    p.add_argument("--summary", default="logs/dataset_cleaning_summary.json")
    return p.parse_args()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def choose_split(records: list[tuple[str, str, Path]]) -> str:
    splits = sorted({r[0] for r in records}, key=lambda s: SPLIT_PRIORITY.get(s, 999))
    return splits[0]


def choose_class(classes: set[str]) -> str:
    return sorted(classes, key=lambda c: (CLASS_PRIORITY.get(c, 99), c))[0]


def main() -> int:
    args = parse_args()
    src_root = Path(args.dataset)
    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)
    Path(args.summary).parent.mkdir(parents=True, exist_ok=True)

    if not src_root.exists():
        raise FileNotFoundError(f"Dataset not found: {src_root}")

    hash_map: dict[str, list[tuple[str, str, Path]]] = defaultdict(list)
    input_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for split_dir in sorted(src_root.iterdir()):
        if not split_dir.is_dir():
            continue
        split = split_dir.name
        for cls_dir in sorted(split_dir.iterdir()):
            if not cls_dir.is_dir():
                continue
            cls = cls_dir.name
            for file in cls_dir.iterdir():
                if not file.is_file():
                    continue
                h = md5_file(file)
                hash_map[h].append((split, cls, file))
                input_counts[split][cls] += 1

    kept = 0
    dropped = 0
    cross_split_groups = 0
    cross_class_groups = 0
    output_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for h, records in hash_map.items():
        split_set = {r[0] for r in records}
        if len(split_set) > 1:
            cross_split_groups += 1
        target_split = choose_split(records)
        split_records = [r for r in records if r[0] == target_split]
        class_set = {r[1] for r in split_records}
        if len(class_set) > 1:
            cross_class_groups += 1
        target_class = choose_class(class_set)

        # Keep exactly one source file for this hash in the selected split/class.
        candidates = [r for r in split_records if r[1] == target_class]
        chosen = sorted(candidates, key=lambda r: str(r[2]))[0]

        src_path = chosen[2]
        ext = src_path.suffix.lower() or ".png"
        dst_dir = out_root / target_split / target_class
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst_name = f"{h}{ext}"
        dst_path = dst_dir / dst_name
        shutil.copy2(src_path, dst_path)
        kept += 1
        output_counts[target_split][target_class] += 1

        dropped += max(0, len(records) - 1)

    summary = {
        "source_dataset": str(src_root),
        "output_dataset": str(out_root),
        "unique_hashes_kept": kept,
        "duplicates_dropped": dropped,
        "cross_split_duplicate_groups": cross_split_groups,
        "cross_class_conflict_groups": cross_class_groups,
        "input_counts": {k: dict(v) for k, v in input_counts.items()},
        "output_counts": {k: dict(v) for k, v in output_counts.items()},
    }

    with Path(args.summary).open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"kept={kept}")
    print(f"dropped={dropped}")
    print(f"cross_split_groups={cross_split_groups}")
    print(f"cross_class_groups={cross_class_groups}")
    print(f"summary={args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
