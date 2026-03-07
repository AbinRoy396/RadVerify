"""
Strict compare-and-promote gate for RadVerify models.

Promotion rule:
- Candidate is promoted only if BOTH validation and test improve on:
  - accuracy
  - macro_f1
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _load_metrics(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "validation" not in data or "test" not in data:
        raise ValueError(f"Missing validation/test metrics in {path}")
    return data


def _extract(data: dict) -> dict:
    return {
        "validation": {
            "accuracy": float(data["validation"]["accuracy"]),
            "macro_f1": float(data["validation"]["macro_f1"]),
        },
        "test": {
            "accuracy": float(data["test"]["accuracy"]),
            "macro_f1": float(data["test"]["macro_f1"]),
        },
    }


def _improved(candidate: dict, baseline: dict) -> tuple[bool, dict]:
    checks = {
        "validation_accuracy": candidate["validation"]["accuracy"] > baseline["validation"]["accuracy"],
        "validation_macro_f1": candidate["validation"]["macro_f1"] > baseline["validation"]["macro_f1"],
        "test_accuracy": candidate["test"]["accuracy"] > baseline["test"]["accuracy"],
        "test_macro_f1": candidate["test"]["macro_f1"] > baseline["test"]["macro_f1"],
    }
    return all(checks.values()), checks


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser(description="Strict compare-and-promote gate")
    ap.add_argument("--baseline-dir", required=True, help="Existing production experiment dir")
    ap.add_argument("--candidate-dir", required=True, help="New candidate experiment dir")
    ap.add_argument("--models-dir", default="models", help="Top-level models dir")
    ap.add_argument("--apply", action="store_true", help="Apply promotion when gate passes")
    args = ap.parse_args()

    baseline_dir = Path(args.baseline_dir)
    candidate_dir = Path(args.candidate_dir)
    models_dir = Path(args.models_dir)
    baseline_metrics_path = baseline_dir / "validation_metrics.json"
    candidate_metrics_path = candidate_dir / "validation_metrics.json"

    if not baseline_metrics_path.exists():
        raise FileNotFoundError(f"Missing baseline metrics: {baseline_metrics_path}")
    if not candidate_metrics_path.exists():
        raise FileNotFoundError(f"Missing candidate metrics: {candidate_metrics_path}")

    baseline = _extract(_load_metrics(baseline_metrics_path))
    candidate = _extract(_load_metrics(candidate_metrics_path))
    promote, checks = _improved(candidate, baseline)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "baseline": baseline,
        "candidate": candidate,
        "delta": {
            "validation": {
                "accuracy": round(candidate["validation"]["accuracy"] - baseline["validation"]["accuracy"], 6),
                "macro_f1": round(candidate["validation"]["macro_f1"] - baseline["validation"]["macro_f1"], 6),
            },
            "test": {
                "accuracy": round(candidate["test"]["accuracy"] - baseline["test"]["accuracy"], 6),
                "macro_f1": round(candidate["test"]["macro_f1"] - baseline["test"]["macro_f1"], 6),
            },
        },
        "checks": checks,
        "promote": promote,
        "applied": False,
    }

    report_path = candidate_dir / "comparison_vs_current_v1.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.apply and promote:
        production_backup_dir = models_dir / "archive" / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_pre_promotion"
        production_backup_dir.mkdir(parents=True, exist_ok=True)

        for name in ["best_model.keras", "best_model.h5", "labels.json", "validation_metrics.json", "class_thresholds.json", "MODEL_CARD.md"]:
            _copy_if_exists(models_dir / name, production_backup_dir / name)

        for name in ["best_model.keras", "best_model.h5", "labels.json", "validation_metrics.json", "class_thresholds.json", "MODEL_CARD.md"]:
            _copy_if_exists(candidate_dir / name, models_dir / name)

        production = {
            "locked_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_experiment": str(candidate_dir),
            "model_file": "models/best_model.keras",
            "labels_file": "models/labels.json",
            "metrics_file": "models/validation_metrics.json",
            "promotion_reason": "Strict gate passed: validation+test accuracy and macro_f1 all improved",
            "comparison": {
                "baseline": baseline,
                "candidate": candidate,
                "checks": checks,
            },
            "backup_of_previous_production": str(production_backup_dir),
        }
        (models_dir / "PRODUCTION_MODEL.json").write_text(json.dumps(production, indent=2), encoding="utf-8")
        report["applied"] = True
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

