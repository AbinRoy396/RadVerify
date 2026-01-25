"""Handles raw input validation and normalization for RadVerify."""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from .models import ImageMetadata, InputPayload

ALLOWED_FORMATS = {"jpg", "jpeg", "png"}


def _clean_report_text(report_text: str) -> str:
    normalized = report_text.strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def _validate_extension(filename: str) -> str:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in ALLOWED_FORMATS:
        raise ValueError(f"Unsupported image format '{suffix}'. Use JPG or PNG scans only.")
    return suffix


def prepare_inputs(uploaded_file, report_text: str) -> Tuple[InputPayload, List[str]]:
    """Validates raw inputs and returns a structured payload for downstream modules."""

    if uploaded_file is None:
        raise ValueError("An image must be uploaded for verification.")

    cleaned_report = _clean_report_text(report_text or "")
    if not cleaned_report:
        raise ValueError("Radiology report text cannot be empty.")

    notes: List[str] = []
    suffix = _validate_extension(uploaded_file.name or "scan.jpg")
    notes.append(f"File extension validated as {suffix}.")

    raw_bytes = uploaded_file.getvalue()
    if not raw_bytes:
        raise ValueError("Uploaded image contains no data.")

    np_buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image. Ensure the file is a valid JPG or PNG scan.")

    notes.append(f"Image decoded via OpenCV with shape {image.shape}.")

    metadata = ImageMetadata(
        filename=uploaded_file.name or "scan",
        format=suffix.upper(),
        size_bytes=len(raw_bytes),
    )

    payload = InputPayload(
        metadata=metadata,
        raw_image=image,
        cleaned_report=cleaned_report,
    )

    notes.append("Report text cleaned (whitespace collapsed).")

    return payload, notes
