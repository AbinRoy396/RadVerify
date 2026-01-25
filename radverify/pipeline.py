"""Orchestrates the end-to-end verification workflow."""

from __future__ import annotations

from typing import List, Tuple

from .ai_analysis import analyze_image
from .ai_report import generate_ai_report
from .comparison import compare_findings
from .explanation import generate_explanation
from .input_handler import prepare_inputs
from .models import VerificationBundle
from .preprocess import preprocess_image
from .report_parser import parse_report
from .telemetry import get_telemetry_client
from .tracing import TraceRecorder


def run_verification(uploaded_image, report_text: str) -> Tuple[VerificationBundle, List[str]]:
    """Runs the complete pipeline and returns a structured bundle plus notes."""

    tracer = TraceRecorder()
    telemetry = get_telemetry_client()

    context = {"filename": getattr(uploaded_image, "name", "unknown")}
    telemetry.record_event("verification_start", context)

    try:
        payload, input_notes = prepare_inputs(uploaded_image, report_text)
        tracer.extend("Input", input_notes)

        preprocessed, preprocess_notes = preprocess_image(payload)
        tracer.extend("Preprocess", preprocess_notes)

        ai_finding, ai_notes = analyze_image(preprocessed)
        tracer.extend("AI", ai_notes)

        ai_report_snippet = generate_ai_report(ai_finding)
        tracer.add("AI", "Report snippet generated from finding.")

        report_findings, report_notes = parse_report(payload.cleaned_report, feature_name=ai_finding.feature_name)
        tracer.extend("Report", report_notes)

        comparison, comparison_notes = compare_findings(ai_finding, report_findings)
        tracer.extend("Comparison", comparison_notes)

        explanation = generate_explanation(ai_finding, report_findings, comparison, ai_report_snippet)
        tracer.add("Explanation", "Explanation synthesized for frontend display.")

        processing_notes = tracer.as_strings()

        bundle = VerificationBundle(
            preprocessed_image=preprocessed,
            ai_finding=ai_finding,
            report_findings=report_findings,
            comparison=comparison,
            ai_report_snippet=ai_report_snippet,
            explanation=explanation,
            processing_notes=processing_notes,
        )

    except Exception as exc:
        telemetry.record_event(
            "verification_error",
            {**context, "error": str(exc.__class__.__name__), "detail": str(exc)},
        )
        raise
    else:
        telemetry.record_event(
            "verification_success",
            {**context, "status": bundle.comparison.status},
        )
        return bundle, processing_notes
