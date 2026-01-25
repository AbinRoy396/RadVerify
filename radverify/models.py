"""Data models shared across the RadVerify backend pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ImageMetadata:
    """Information about the uploaded scan image."""

    filename: str
    format: str
    size_bytes: int


@dataclass
class PreprocessedImage:
    """Represents a normalized version of the uploaded scan."""

    metadata: ImageMetadata
    width: int
    height: int
    mode: str
    mean_intensity: float
    normalized_pixels: List[List[float]]  # lightweight representation for demo


@dataclass
class AIFinding:
    """Single-feature output from the vision model surrogate."""

    feature_name: str
    detected: bool
    confidence: float
    rationale: str
    status: str
    summary: str


@dataclass
class ReportFindings:
    """Structured interpretation of the human-written report."""

    feature_name: str
    mentioned: bool
    negated: bool
    context_snippet: Optional[str]
    status: str  # e.g., "mentioned", "not_mentioned", "contradicted"
    confidence_terms: List[str] = field(default_factory=list)


@dataclass
class AIReportSnippet:
    """Template-generated snippet that mirrors a radiology report sentence."""

    summary: str
    confidence_statement: str


@dataclass
class InputPayload:
    """Validated and normalized raw inputs ready for downstream modules."""

    metadata: ImageMetadata
    raw_image: Any  # numpy.ndarray
    cleaned_report: str


@dataclass
class ComparisonOutcome:
    """Result of aligning AI and report findings."""

    status: str  # match | omission | overstatement | contradiction
    explanation: str


@dataclass
class VerificationBundle:
    """Container returned to the Streamlit app for rendering."""

    preprocessed_image: PreprocessedImage
    ai_finding: AIFinding
    report_findings: ReportFindings
    comparison: ComparisonOutcome
    ai_report_snippet: AIReportSnippet
    explanation: str
    processing_notes: List[str] = field(default_factory=list)
