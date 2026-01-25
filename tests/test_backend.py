"""Unit tests for the RadVerify backend pipeline."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from radverify import run_verification
from radverify.ai_analysis import analyze_image
from radverify.comparison import compare_findings
from radverify.explanation import generate_explanation
from radverify.input_handler import prepare_inputs
from radverify.models import (
    AIFinding,
    AIReportSnippet,
    ComparisonOutcome,
    ImageMetadata,
    PreprocessedImage,
    ReportFindings,
)
from radverify.preprocess import preprocess_image
from radverify.report_parser import parse_report


class DummyUpload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def _encode_image(array: np.ndarray) -> bytes:
    success, buffer = cv2.imencode(".jpg", array)
    assert success, "Failed to encode test image."
    return buffer.tobytes()


def make_upload(name: str = "scan.jpg", patterned: bool = False) -> DummyUpload:
    if patterned:
        array = np.zeros((128, 128, 3), dtype=np.uint8)
        for y in range(128):
            value = 30 if (y // 6) % 2 == 0 else 220
            array[y, :, :] = value
        cv2.circle(array, (64, 64), 25, (255, 255, 255), thickness=2)
    else:
        array = np.full((128, 128, 3), 160, dtype=np.uint8)
    return DummyUpload(name, _encode_image(array))


def build_preprocessed_from_grid(grid: np.ndarray) -> PreprocessedImage:
    metadata = ImageMetadata(filename="test", format="JPG", size_bytes=0)
    return PreprocessedImage(
        metadata=metadata,
        width=grid.shape[1],
        height=grid.shape[0],
        mode="L",
        mean_intensity=float(grid.mean()),
        normalized_pixels=grid.tolist(),
    )


def test_prepare_inputs_valid_image():
    upload = make_upload()
    payload, notes = prepare_inputs(upload, "  Report text with spacing.   ")

    assert payload.cleaned_report == "Report text with spacing."
    assert payload.raw_image.shape[:2] == (128, 128)
    assert any("File extension" in note for note in notes)


def test_prepare_inputs_invalid_extension():
    upload = make_upload(name="scan.gif")
    with pytest.raises(ValueError):
        prepare_inputs(upload, "Report")


def test_preprocess_image_outputs_normalized_grid():
    payload, _ = prepare_inputs(make_upload(patterned=True), "Report")
    preprocessed, notes = preprocess_image(payload)

    assert preprocessed.mode == "L"
    assert len(preprocessed.normalized_pixels) == 64
    assert any("mean intensity" in note.lower() for note in notes)


def test_analyze_image_detects_patterned_grid():
    checkerboard = (np.indices((64, 64)).sum(axis=0) % 2).astype(np.float32)
    preprocessed = build_preprocessed_from_grid(checkerboard)

    finding, notes = analyze_image(preprocessed)

    assert finding.status == "present"
    assert finding.summary
    assert any("texture score" in note.lower() for note in notes)


def test_analyze_image_absent_on_flat_grid():
    flat_grid = np.zeros((64, 64), dtype=np.float32)
    preprocessed = build_preprocessed_from_grid(flat_grid)

    finding, _ = analyze_image(preprocessed)

    assert finding.status == "absent"
    assert finding.detected is False


def test_parse_report_detects_negation_and_confidence():
    text = "No calcifications are seen. Findings are otherwise normal."
    report, notes = parse_report(text)

    assert report.mentioned is True
    assert report.negated is True
    assert "normal" in report.confidence_terms
    assert any("negation" in note.lower() for note in notes)


def test_compare_findings_identifies_omission():
    ai = AIFinding(
        feature_name="target_structure",
        detected=True,
        confidence=0.9,
        rationale="Unit test",
        status="present",
        summary="Structure present",
    )
    report = ReportFindings(
        feature_name="target_structure",
        mentioned=False,
        negated=False,
        context_snippet=None,
        status="not_mentioned",
        confidence_terms=[],
    )

    comparison, _ = compare_findings(ai, report)
    assert comparison.status == "omission"


def test_generate_explanation_handles_contradiction():
    ai = AIFinding(
        feature_name="target_structure",
        detected=True,
        confidence=0.82,
        rationale="",
        status="present",
        summary="",
    )
    report = ReportFindings(
        feature_name="target_structure",
        mentioned=True,
        negated=True,
        context_snippet="no calcifications",
        status="mentioned_negated",
        confidence_terms=[],
    )
    comparison = ComparisonOutcome(status="contradiction", explanation="")
    snippet = AIReportSnippet(summary="", confidence_statement="")

    explanation = generate_explanation(ai, report, comparison, snippet)

    assert "Manual review" in explanation


def test_run_verification_returns_bundle():
    upload = make_upload(patterned=True)
    report_text = "Calcifications are not described in this exam."

    bundle, notes = run_verification(upload, report_text)

    assert bundle.ai_finding.summary
    assert bundle.report_findings.status in {"not_mentioned", "mentioned", "mentioned_negated"}
    assert bundle.explanation
    assert notes, "Processing notes should not be empty."
