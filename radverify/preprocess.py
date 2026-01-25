"""Image preprocessing utilities for RadVerify."""

from __future__ import annotations

from typing import List, Tuple

import cv2
import numpy as np

from .models import InputPayload, PreprocessedImage

MAX_DIMENSION = 1024
NORMALIZED_GRID = 64


def _compute_resize_dims(width: int, height: int) -> Tuple[int, int]:
    """Resize while preserving aspect ratio and keeping the longest edge <= MAX_DIMENSION."""

    longest_edge = max(width, height)
    if longest_edge <= MAX_DIMENSION:
        return width, height

    scale = MAX_DIMENSION / float(longest_edge)
    return int(width * scale), int(height * scale)


def preprocess_image(payload: InputPayload) -> Tuple[PreprocessedImage, List[str]]:
    """Normalizes the uploaded scan into a lightweight representation."""

    notes: List[str] = []
    image_bgr = payload.raw_image
    height, width = image_bgr.shape[:2]
    notes.append(f"Raw image shape (HxW): {height}x{width}.")

    target_w, target_h = _compute_resize_dims(width, height)
    if (target_w, target_h) != (width, height):
        image_bgr = cv2.resize(image_bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)
        notes.append(f"Resized image to {target_h}x{target_w}.")
        height, width = target_h, target_w

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    notes.append("Converted to grayscale (OpenCV).")

    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    notes.append("Applied Gaussian blur for mild denoising.")

    normalized_grid = cv2.resize(denoised, (NORMALIZED_GRID, NORMALIZED_GRID), interpolation=cv2.INTER_AREA)
    normalized_array = normalized_grid.astype(np.float32) / 255.0
    mean_intensity = float(normalized_array.mean())
    notes.append(f"Computed mean intensity: {mean_intensity:.3f}.")

    preprocessed = PreprocessedImage(
        metadata=payload.metadata,
        width=width,
        height=height,
        mode="L",
        mean_intensity=mean_intensity,
        normalized_pixels=normalized_array.tolist(),
    )

    return preprocessed, notes
