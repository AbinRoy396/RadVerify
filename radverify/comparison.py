"""Comparison engine aligning AI findings with report interpretation."""

from __future__ import annotations

from typing import Tuple

from .models import AIFinding, ComparisonOutcome, ReportFindings


def compare_findings(ai_finding: AIFinding, report_findings: ReportFindings) -> Tuple[ComparisonOutcome, list[str]]:
    """Implements the decision matrix described in the spec."""

    notes: list[str] = []

    status = "match"
    explanation = "Feature presence aligns across AI and report."

    ai_present = ai_finding.detected
    report_mentions = report_findings.mentioned
    report_negated = report_findings.negated

    notes.append(f"AI detected: {ai_present}. Report mentioned: {report_mentions}. Negated: {report_negated}.")

    if ai_present and report_mentions and not report_negated:
        status = "match"
        explanation = "Both AI and report describe the feature as present."
    elif ai_present and not report_mentions:
        status = "omission"
        explanation = "AI detected the feature, but it was not mentioned in the report."
    elif ai_present and report_negated:
        status = "contradiction"
        explanation = "AI detected the feature, yet the report explicitly negated its presence."
    elif not ai_present and report_mentions and not report_negated:
        status = "overstatement"
        explanation = "Report mentions the feature even though AI did not detect it."
    elif not ai_present and report_negated:
        status = "match_absent"
        explanation = "Both AI and report indicate the feature is absent."
    else:
        status = "match"
        explanation = "No inconsistencies detected for the monitored feature."

    outcome = ComparisonOutcome(status=status, explanation=explanation)
    return outcome, notes
