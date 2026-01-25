"""Lightweight NLP utilities to structure radiology reports."""

from __future__ import annotations

import re
from typing import List, Tuple

from .models import ReportFindings

NEGATION_PATTERN = re.compile(r"\b(no|without|absent|denies)\b", re.IGNORECASE)
FEATURE_KEYWORDS = [
    "calcification",
    "calcified focus",
    "calcifications",
]
CONFIDENCE_KEYWORDS = [
    "normal",
    "adequate",
    "clear",
    "intact",
    "stable",
    "unremarkable",
]


def parse_report(report_text: str, feature_name: str = "calcification") -> Tuple[ReportFindings, List[str]]:
    """Extracts a coarse representation of whether the feature is mentioned."""

    notes: List[str] = []
    normalized = report_text.strip()
    if not normalized:
        raise ValueError("Report text is empty.")

    notes.append("Report text normalized and ready for parsing.")
    lowered = normalized.lower()

    mentioned = any(keyword in lowered for keyword in FEATURE_KEYWORDS)
    notes.append(f"Feature mention detected: {mentioned}.")

    negated = False
    snippet = None
    status = "not_mentioned"
    confidence_terms: List[str] = []

    if mentioned:
        matches = [keyword for keyword in FEATURE_KEYWORDS if keyword in lowered]
        snippet = _extract_context_snippet(lowered, matches[0]) if matches else None
        context_section = snippet or normalized[:80]
        negated = bool(NEGATION_PATTERN.search(context_section))
        status = "mentioned_negated" if negated else "mentioned"
        notes.append(f"Negation context around mention: {negated}.")
    else:
        notes.append("Feature not explicitly mentioned by keywords.")

    for term in CONFIDENCE_KEYWORDS:
        if term in lowered:
            confidence_terms.append(term)

    report = ReportFindings(
        feature_name=feature_name,
        mentioned=mentioned,
        negated=negated,
        context_snippet=snippet,
        status=status,
        confidence_terms=confidence_terms,
    )

    return report, notes


def _extract_context_snippet(text: str, keyword: str, window: int = 60) -> str:
    index = text.find(keyword)
    start = max(index - window // 2, 0)
    end = min(index + len(keyword) + window // 2, len(text))
    snippet = text[start:end].strip()
    return snippet
