"""Configuration helpers for RadVerify backend."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DetectorConfig:
    texture_threshold: float = 0.035
    variance_threshold: float = 0.08
    uncertain_variance_threshold: float = 0.05
    base_confidence: float = 0.65


def get_detector_config() -> DetectorConfig:
    """Return the default detector configuration.

    Later we can source these from env vars or user preferences.
    """

    return DetectorConfig()
