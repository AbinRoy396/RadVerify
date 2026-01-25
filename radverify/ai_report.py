"""Transforms AI findings into structured report-like snippets."""

from __future__ import annotations

from .models import AIFinding, AIReportSnippet


def generate_ai_report(finding: AIFinding) -> AIReportSnippet:
    """Maps the AI finding to a human-readable statement."""

    if finding.status == "present":
        summary = "The monitored structure is visualized with expected contours."
        confidence_stmt = f"AI confidence {finding.confidence:.0%} with stable delineation."
    elif finding.status == "uncertain":
        summary = "The structure is partially appreciable; clarity is limited by acquisition."
        confidence_stmt = "Visibility borderline—recommend manual inspection."
    else:
        summary = "No convincing appearance of the monitored structure in this scan."
        confidence_stmt = f"Low-likelihood finding; confidence {finding.confidence:.0%}."

    return AIReportSnippet(summary=summary, confidence_statement=confidence_stmt)
