"""
Create a focused relabel-review pack for weak class: brain_skull.

Inputs:
- logs/hard_examples_core6/train_predictions.csv
- logs/hard_examples_core6/validation_predictions.csv

Outputs:
- logs/brain_skull_review/relabel_candidates.csv
- logs/brain_skull_review/images/... (copied files grouped by reason)
"""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path


def read_rows(csv_path: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["top_conf"] = float(r["top_conf"])
            r["p_brain_skull"] = float(r["p_brain_skull"])
            rows.append(r)
    return rows


def pick_candidates(rows, top_n_each: int):
    out = []

    # 1) GT skull but model strongly predicts another class.
    a = [
        r for r in rows
        if r["gt_label"] == "brain_skull" and r["pred_label"] != "brain_skull"
    ]
    a.sort(key=lambda x: (x["top_conf"], x["p_brain_skull"]), reverse=True)
    for r in a[:top_n_each]:
        out.append({
            **r,
            "reason": "gt_skull_pred_other_high_conf",
            "suggested_label": r["pred_label"],
        })

    # 2) Non-skull but model assigns high skull probability (possible missed skull labels).
    b = [
        r for r in rows
        if r["gt_label"] != "brain_skull" and r["p_brain_skull"] >= 0.30
    ]
    b.sort(key=lambda x: x["p_brain_skull"], reverse=True)
    for r in b[:top_n_each]:
        out.append({
            **r,
            "reason": "non_skull_high_p_skull",
            "suggested_label": "brain_skull",
        })

    # 3) Brain subclasses confusion around skull neighborhood.
    c = [
        r for r in rows
        if r["gt_label"] in {"brain_cerebellum", "brain_ventricles"}
        and r["pred_label"] in {"brain_cerebellum", "brain_ventricles"}
        and r["p_brain_skull"] >= 0.22
    ]
    c.sort(key=lambda x: x["p_brain_skull"], reverse=True)
    for r in c[:top_n_each]:
        out.append({
            **r,
            "reason": "brain_subclass_with_skull_signal",
            "suggested_label": "review_needed",
        })

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/structure_dataset_core6_v1")
    ap.add_argument("--input-dir", default="logs/hard_examples_core6")
    ap.add_argument("--output-dir", default="logs/brain_skull_review")
    ap.add_argument("--top-n-each", type=int, default=150)
    args = ap.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_img = out_dir / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_img.mkdir(parents=True, exist_ok=True)

    all_candidates = []
    for split in ["train", "validation"]:
        csv_path = in_dir / f"{split}_predictions.csv"
        if not csv_path.exists():
            continue
        rows = read_rows(csv_path)
        candidates = pick_candidates(rows, args.top_n_each)
        for c in candidates:
            c["split"] = split
            all_candidates.append(c)

    # Deduplicate by exact file path keeping highest priority reason ordering.
    priority = {
        "gt_skull_pred_other_high_conf": 0,
        "non_skull_high_p_skull": 1,
        "brain_subclass_with_skull_signal": 2,
    }
    best = {}
    for c in all_candidates:
        key = c["file"]
        if key not in best or priority[c["reason"]] < priority[best[key]["reason"]]:
            best[key] = c
    final = list(best.values())
    final.sort(key=lambda x: (x["reason"], -x["top_conf"], -x["p_brain_skull"]))

    # Write manifest and copy files.
    manifest = out_dir / "relabel_candidates.csv"
    fields = [
        "split", "file", "basename", "gt_label", "pred_label",
        "top_conf", "p_brain_skull", "reason", "suggested_label",
    ]
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(final)

    copied = 0
    for c in final:
        src = Path(c["file"])
        if not src.exists():
            continue
        dst_dir = out_img / c["reason"] / c["split"] / c["gt_label"]
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
            copied += 1

    summary = out_dir / "summary.txt"
    by_reason = {}
    for c in final:
        by_reason[c["reason"]] = by_reason.get(c["reason"], 0) + 1
    summary.write_text(
        "\n".join(
            [
                f"total_candidates={len(final)}",
                *(f"{k}={v}" for k, v in sorted(by_reason.items())),
                f"copied_images={copied}",
                f"manifest={manifest}",
                f"images_dir={out_img}",
            ]
        ),
        encoding="utf-8",
    )
    print(summary.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
