"""Placeholder AI image analysis for the demo pipeline."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from .models import AIFinding, PreprocessedImage
from .settings import DetectorConfig, get_detector_config

FEATURE_NAME = "target_structure"


def _compute_texture_score(grid: np.ndarray) -> float:
    gradients = np.gradient(grid)
    grad_mag = np.sqrt(np.square(gradients[0]) + np.square(gradients[1]))
    return float(grad_mag.mean())


def _compute_intensity_variation(grid: np.ndarray) -> float:
    return float(grid.std())


def analyze_image(
    preprocessed: PreprocessedImage,
    config: DetectorConfig | None = None,
) -> Tuple[AIFinding, List[str]]:
    """Simulates a constrained AI model that detects a single feature."""

    notes: List[str] = []
    cfg = config or get_detector_config()
    grid = np.asarray(preprocessed.normalized_pixels, dtype=np.float32)

    texture_score = _compute_texture_score(grid)
    variation = _compute_intensity_variation(grid)
    mean_intensity = preprocessed.mean_intensity

    notes.append(f"Texture score: {texture_score:.3f} (edge density proxy).")
    notes.append(f"Intensity variation: {variation:.3f}.")

    detected = texture_score > cfg.texture_threshold and variation > cfg.variance_threshold
    ambiguous = not detected and variation > cfg.uncertain_variance_threshold

    if detected:
        status = "present"
        confidence = min(0.95, cfg.base_confidence + variation)
        summary = "Feature pattern visible with sufficient delineation."
        rationale = "Combined gradient + variance thresholds exceeded."
    elif ambiguous:
        status = "uncertain"
        confidence = 0.55
        summary = "Feature visibility is borderline; additional review suggested."
        rationale = "Variance moderate but edge density low."
    else:
        status = "absent"
        confidence = 0.35 + mean_intensity * 0.1
        summary = "No convincing evidence of the monitored feature."
        rationale = "Both variance and texture below thresholds."

    finding = AIFinding(
        feature_name=FEATURE_NAME,
        detected=detected,
        confidence=round(confidence, 2),
        rationale=rationale,
        status=status,
        summary=summary,
    )

    return finding, notes
