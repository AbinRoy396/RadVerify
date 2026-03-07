"""
Apply relabel decisions from a CSV to a copied dataset directory.

Expected CSV columns:
- split
- file
- gt_label
- suggested_label

Behavior:
- Copies source dataset -> output dataset (if output does not exist)
- Moves files to suggested label folder when suggested_label is a real class
- Ignores rows with suggested_label in ignore list (default: review_needed)
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path


def ensure_dirs(root: Path, splits: list[str], classes: list[str]) -> None:
    for s in splits:
        for c in classes:
            (root / s / c).mkdir(parents=True, exist_ok=True)


def find_file_by_name(split_root: Path, basename: str, classes: list[str]) -> Path | None:
    for c in classes:
        p = split_root / c / basename
        if p.exists():
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dataset", required=True)
    ap.add_argument("--output-dataset", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--labels", default="models/labels.json")
    ap.add_argument("--ignore-suggested", default="review_needed")
    ap.add_argument("--allowed-splits", default="train,validation,test")
    args = ap.parse_args()

    source = Path(args.source_dataset)
    output = Path(args.output_dataset)
    csv_path = Path(args.csv)
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8"))
    valid = set(labels)
    ignore = {x.strip() for x in args.ignore_suggested.split(",") if x.strip()}
    allowed_splits = {x.strip() for x in args.allowed_splits.split(",") if x.strip()}

    if not source.exists():
        raise FileNotFoundError(f"source dataset not found: {source}")
    if not csv_path.exists():
        raise FileNotFoundError(f"csv not found: {csv_path}")

    if not output.exists():
        shutil.copytree(source, output)
    ensure_dirs(output, ["train", "validation", "test"], labels)

    moved = 0
    skipped_ignore = 0
    skipped_invalid = 0
    missing = 0
    unchanged = 0

    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        split = r.get("split", "").strip()
        gt = r.get("gt_label", "").strip()
        suggested = r.get("suggested_label", "").strip()
        file_path = r.get("file", "").strip()
        basename = Path(file_path).name

        if split not in {"train", "validation", "test"}:
            continue
        if split not in allowed_splits:
            continue
        if suggested in ignore:
            skipped_ignore += 1
            continue
        if suggested not in valid:
            skipped_invalid += 1
            continue

        split_root = output / split

        src = None
        if file_path:
            try:
                rel = Path(file_path)
                # Replace source root prefix with output root when possible.
                if source.name in rel.parts:
                    idx = rel.parts.index(source.name)
                    rel_tail = Path(*rel.parts[idx + 1 :])  # starts at split/class/file
                    candidate = output / rel_tail
                    if candidate.exists():
                        src = candidate
            except Exception:
                src = None

        if src is None:
            src = find_file_by_name(split_root, basename, labels)
        if src is None:
            missing += 1
            continue

        dst = split_root / suggested / basename
        if src.resolve() == dst.resolve():
            unchanged += 1
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            # If already exists, remove source duplicate.
            src.unlink()
        else:
            shutil.move(str(src), str(dst))
        moved += 1

    summary = {
        "source_dataset": str(source),
        "output_dataset": str(output),
        "csv": str(csv_path),
        "rows": len(rows),
        "moved": moved,
        "unchanged": unchanged,
        "skipped_ignore": skipped_ignore,
        "skipped_invalid": skipped_invalid,
        "missing": missing,
        "ignore_suggested": sorted(ignore),
        "allowed_splits": sorted(allowed_splits),
    }
    out = output / "relabel_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
