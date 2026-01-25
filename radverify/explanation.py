"""Generates natural-language explanations for verification outcomes."""

from __future__ import annotations

from .models import AIFinding, AIReportSnippet, ComparisonOutcome, ReportFindings


def generate_explanation(
    ai_finding: AIFinding,
    report_findings: ReportFindings,
    comparison: ComparisonOutcome,
    ai_report: AIReportSnippet,
) -> str:
    """Return a concise explanation summarizing the verification result."""

    report_state = _describe_report(report_findings)

    if comparison.status in {"match", "match_absent"}:
        return (
            "The AI-derived snippet and the human report both describe the monitored structure consistently. "
            f"{ai_report.summary}"
        )

    if comparison.status == "omission":
        return (
            "AI cues suggest the structure is visible, but the human report never references it. "
            "Consider amending the report if the AI observation is clinically relevant."
        )

    if comparison.status == "contradiction":
        return (
            "The report explicitly negates the structure while AI detected signals resembling it. "
            "Manual review is recommended to resolve the discrepancy."
        )

    if comparison.status == "overstatement":
        return (
            "The report documents the structure as present, yet AI could not confirm it with sufficient confidence. "
            "Verify whether the textual mention was intentional or a potential oversight."
        )

    fallback = (
        f"AI status: {ai_finding.status}. Report status: {report_state}. "
        "No definitive mismatch identified, but the context warrants a quick look."
    )
    return fallback


def _describe_report(report_findings: ReportFindings) -> str:
    if report_findings.status == "not_mentioned":
        return "not mentioned"
    if report_findings.status == "mentioned_negated":
        return "mentioned as absent"
    if report_findings.status == "mentioned":
        return "mentioned as present"
    return report_findings.status.replace("_", " ")
