"""RAVEN Streamlit UI matching the requested reference interface."""

from __future__ import annotations

from datetime import datetime
import html
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


PAGES: Dict[str, Dict[str, str]] = {
    "Dashboard": {"title": "Upload Portal", "sub": "Clinical input and processing"},
    "Analysis Workspace": {"title": "Analysis Workspace", "sub": "AI findings and report comparison"},
    "Discrepancy Resolution": {"title": "Discrepancy Resolution", "sub": "Accept, dismiss, or modify AI findings"},
    "Final Export": {"title": "Final Export", "sub": "Finalize and archive verified report"},
    "History & Archive": {"title": "History & Archive", "sub": "Compliance-grade audit retrieval"},
    "Help Center": {"title": "Help Center", "sub": "Tutorials and support channels"},
}


def demo_history() -> List[Dict[str, Any]]:
    return [
        {
            "id": "SCN-9021",
            "scan_type": "Chest PA/Lateral X-Ray",
            "patient_id": "PAT-7728-B",
            "created_at": "Oct 24, 10:45 AM",
            "verification_status": "Verified",
            "risk": "LOW",
        },
        {
            "id": "SCN-8842",
            "scan_type": "Abdominal Ultrasound",
            "patient_id": "PAT-9102-X",
            "created_at": "Oct 24, 09:12 AM",
            "verification_status": "Discrepancy Found",
            "risk": "HIGH",
        },
        {
            "id": "SCN-8811",
            "scan_type": "Lumbar Spine MRI",
            "patient_id": "PAT-1142-D",
            "created_at": "Oct 23, 04:55 PM",
            "verification_status": "Processing",
            "risk": "MEDIUM",
        },
    ]


def mock_verify(file_name: str, report_text: str) -> Dict[str, Any]:
    now = datetime.now().strftime("%b %d, %I:%M %p")
    return {
        "meta": {
            "file_name": file_name,
            "generated_at": now,
            "study": "DOE, JOHN | 45Y | Chest X-Ray (PA View)",
            "study_id": "88291-XA",
            "timestamp": "OCT 24, 2023 09:42 AM",
        },
        "ai_findings": [
            {
                "name": "Cardiomegaly",
                "confidence": 0.98,
                "rationale": "Transverse heart diameter exceeds 50% of thoracic diameter. Likely indicative of underlying CHF.",
                "status": "mismatch",
            },
            {
                "name": "Pleural Effusion",
                "confidence": 0.82,
                "rationale": "Blunting of the right costophrenic angle suggesting mild fluid accumulation.",
                "status": "omission",
            },
            {
                "name": "Pulmonary Nodule",
                "confidence": 0.22,
                "rationale": "Shadow in upper left lobe; likely vessel end-on or artifact.",
                "status": "low_confidence",
            },
        ],
        "report": {
            "raw_text": report_text,
            "highlighted_html": (
                "<p>Lungs are clear bilaterally without focal consolidation. "
                "<span style='background:rgba(223,73,90,0.18);border-bottom:2px solid #DF495A;padding:0 .1rem;' "
                "title='AI detected Cardiomegaly (98% confidence)'>The cardiomediastinal silhouette is within normal limits.</span> "
                "The pulmonary vasculature is not congested.</p>"
                "<p>No evidence of pneumothorax is seen. "
                "<span style='background:rgba(245,158,11,0.22);border-bottom:2px solid #f59e0b;padding:0 .1rem;' "
                "title='Potential Omission: AI detected mild blunting of right costophrenic angle'>Bony structures and soft tissues are unremarkable.</span></p>"
                "<p style='color:#6b7280;font-style:italic;'>IMPRESSION: No acute cardiopulmonary abnormality.</p>"
            ),
        },
        "comparison": {
            "risk_level": "HIGH",
            "agreement_rate": 0.78,
            "discrepancy_counts": {"mismatches": 1, "omissions": 1, "overstatements": 0},
            "comparison_report_text": (
                "The human report indicates a \"normal\" heart size, but Raven Analysis detects a cardiothoracic ratio "
                "of 0.58, which constitutes cardiomegaly."
            ),
        },
    }


def init_state() -> None:
    defaults = {
        "active_page": "Dashboard",
        "image_bytes": None,
        "image_name": "",
        "report_text": "",
        "last_result": None,
        "last_error": "",
        "history_cache": demo_history(),
        "resolution": {},
        "export_config": {
            "heatmap": True,
            "summary": True,
            "narrative": True,
            "discrepancy": True,
        },
        "backend_url": os.getenv("RADVERIFY_BACKEND_URL", "http://localhost:8000"),
        "backend_api_key": os.getenv("RADVERIFY_API_KEY", "radverify_secret_key"),
        "backend_connected": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _backend_headers() -> Dict[str, str]:
    return {"X-API-Key": st.session_state.backend_api_key.strip()}


def _backend_url(path: str) -> str:
    return st.session_state.backend_url.rstrip("/") + path


def backend_health_check() -> tuple[bool, str]:
    try:
        resp = requests.get(_backend_url("/health"), timeout=4)
        if resp.status_code == 200:
            return True, "Connected"
        return False, f"Health failed: {resp.status_code}"
    except Exception as exc:
        return False, f"Backend unreachable: {exc}"


def fetch_history_backend(limit: int = 20) -> List[Dict[str, Any]]:
    resp = requests.get(
        _backend_url("/history"),
        params={"limit": limit},
        headers=_backend_headers(),
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"/history failed: {resp.status_code} {resp.text}")

    raw = resp.json()
    history: List[Dict[str, Any]] = []
    for item in raw:
        vr = item.get("verification_results") or {}
        risk = str(vr.get("risk_level") or "-").upper()
        history.append(
            {
                "id": f"CASE-{item.get('id', '-')}",
                "scan_type": item.get("image_path") or "Uploaded Scan",
                "patient_id": item.get("patient_id", "-"),
                "created_at": str(item.get("created_at", "-")),
                "verification_status": "Verified" if risk == "LOW" else "Discrepancy Found",
                "risk": risk,
            }
        )
    return history


def _flatten_structures(structures: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for category, vals in (structures or {}).items():
        if isinstance(vals, dict):
            for name, data in vals.items():
                if isinstance(data, dict):
                    out.append(
                        {
                            "name": name,
                            "category": category,
                            "present": bool(data.get("present", False)),
                            "confidence": float(data.get("confidence", 0.0)),
                        }
                    )
    return out


def _resolve_enhanced_image_bytes(path_value: Optional[str]) -> Optional[bytes]:
    if not path_value:
        return None

    raw = str(path_value).strip()
    if not raw:
        return None

    candidates = [
        Path(raw),
        Path.cwd() / raw,
        Path.cwd() / raw.replace("\\", "/"),
    ]
    for candidate in candidates:
        try:
            if candidate.exists() and candidate.is_file():
                return candidate.read_bytes()
        except OSError:
            continue
    return None


def _build_discrepancy_summary(api_result: Dict[str, Any]) -> str:
    vr = api_result.get("verification_results") or {}
    risk = str(vr.get("risk_level", "unknown")).upper()
    agreement = float(vr.get("agreement_rate", 0.0)) * 100
    counts = vr.get("discrepancy_counts") or {}
    comp = vr.get("measurement_comparisons") or {}

    lines = [
        f"Risk Level: {risk}",
        f"Agreement: {agreement:.1f}%",
        (
            "Counts: "
            f"matches={int(counts.get('matches', 0))}, "
            f"omissions={int(counts.get('omissions', 0))}, "
            f"mismatches={int(counts.get('mismatches', 0))}, "
            f"overstatements={int(counts.get('overstatements', 0))}"
        ),
    ]

    if comp:
        lines.append("")
        lines.append("Measurement Comparison:")
        for name, row in comp.items():
            status = str(row.get("status", "unknown")).upper()
            ai_v = row.get("ai_value")
            dr_v = row.get("doctor_value")
            if ai_v is not None and dr_v is not None:
                diff = row.get("difference")
                tol = row.get("tolerance")
                lines.append(f"- {name}: {status} (AI={ai_v}, Doctor={dr_v}, diff={diff}, tol={tol})")
            else:
                lines.append(f"- {name}: {status}")

    return "\n".join(lines)


def normalize_backend_result(api_result: Dict[str, Any], file_name: str, report_text: str) -> Dict[str, Any]:
    ai = api_result.get("ai_findings") or {}
    vr = api_result.get("verification_results") or {}
    structures = _flatten_structures(ai.get("structures_detected") or {})
    top = sorted(structures, key=lambda x: x["confidence"], reverse=True)[:6]

    findings: List[Dict[str, Any]] = []
    for row in top:
        status = "mismatch" if row["present"] else "low_confidence"
        findings.append(
            {
                "name": row["name"].replace("_", " ").title(),
                "confidence": row["confidence"],
                "rationale": f"Category: {row['category']}. Present={row['present']}.",
                "status": status,
            }
        )

    if not findings:
        findings.append(
            {
                "name": "No high-confidence structure",
                "confidence": 0.0,
                "rationale": "No structure-level detections available in response.",
                "status": "low_confidence",
            }
        )

    escaped = html.escape(report_text).replace("\n", "<br/>")
    comparison_text_raw = (
        api_result.get("comparison_report_text")
        or (api_result.get("final_results") or {}).get("comparison_report")
        or "Comparison summary unavailable."
    )
    comparison_text_pretty = _build_discrepancy_summary(api_result)
    enhanced_path = api_result.get("enhanced_image_path")

    return {
        "meta": {
            "file_name": file_name,
            "generated_at": datetime.now().strftime("%b %d, %I:%M %p"),
            "study": f"Uploaded Study | {file_name}",
            "study_id": f"CASE-{api_result.get('case_id', '-')}",
            "timestamp": datetime.now().strftime("%b %d, %Y %I:%M %p").upper(),
        },
        "ai_findings": findings,
        "report": {
            "raw_text": report_text,
            "highlighted_html": f"<p>{escaped}</p>",
        },
        "comparison": {
            "risk_level": vr.get("risk_level", "unknown"),
            "agreement_rate": float(vr.get("agreement_rate", 0.0)),
            "discrepancy_counts": vr.get("discrepancy_counts", {}),
            "comparison_report_text": comparison_text_pretty,
            "comparison_report_text_raw": comparison_text_raw,
        },
        "enhanced_image_bytes": _resolve_enhanced_image_bytes(enhanced_path),
        "enhanced_image_path": enhanced_path,
        "raw_api_result": api_result,
    }


def verify_backend(file_name: str, image_bytes: bytes, report_text: str, enhance: bool = True) -> Dict[str, Any]:
    files = {"scan": (file_name, image_bytes, "application/octet-stream")}
    data = {"report": report_text, "enhance": str(enhance).lower()}
    resp = requests.post(
        _backend_url("/verify"),
        headers=_backend_headers(),
        files=files,
        data=data,
        timeout=240,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"/verify failed: {resp.status_code} {detail}")
    return normalize_backend_result(resp.json(), file_name, report_text)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

        :root {
          --bg: #f3f5f8;
          --panel: #ffffff;
          --panel-2: #fcfcfd;
          --text: #111827;
          --muted: #657586;
          --border: #d9e0e8;
          --primary: #1f66ad;
          --primary-2: #245f9d;
          --shadow: 0 18px 40px rgba(17, 24, 39, 0.08);
          --shadow-sm: 0 10px 24px rgba(17, 24, 39, 0.06);
        }

        .stApp { background: var(--bg); color: var(--text); font-family:'Manrope',sans-serif; }
        h1,h2,h3,h4 { font-family:'Lexend',sans-serif; letter-spacing:-0.02em; }
        a { color: inherit; }

        #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }
        header[data-testid="stHeader"] { background:transparent !important; border:none !important; box-shadow:none !important; }
        [data-testid="stAppViewContainer"] { background: var(--bg); }
        [data-testid="stMainBlockContainer"] { padding-top:1.2rem; max-width:1400px; }

        [data-testid="stSidebar"] { background: var(--panel); border-right:1px solid var(--border); min-width:278px; max-width:278px; }
        section[data-testid="stSidebar"] {
          transform: none !important;
          visibility: visible !important;
          margin-left: 0 !important;
        }
        [data-testid="collapsedControl"] { display:none !important; }
        [data-testid="stSidebarContent"] { padding-top:0.8rem; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin-bottom:0; }
        [data-testid="stSidebar"] div[data-testid="stButton"] { margin-bottom:0.22rem; }
        [data-testid="stSidebar"] .stButton > button {
          border-radius:12px !important;
          text-align:left !important;
          justify-content:flex-start !important;
          padding:0.58rem 0.78rem !important;
          font-size:0.9rem !important;
          font-weight:600 !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
          border:1px solid transparent !important;
          background:transparent !important;
          color:#49637f !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
          background:#f3f7fb !important;
          border-color:#e2e9f2 !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
          border:1px solid #d7e3f1 !important;
          background:#e5edf6 !important;
          color:#1f66ad !important;
          box-shadow:none !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
          border:1px solid #cddced !important;
          background:#deebf8 !important;
          color:#1f66ad !important;
        }

        .logo-wrap { display:flex; align-items:center; gap:12px; margin:6px 0 14px 2px; }
        .logo-box { width:40px; height:40px; border-radius:12px; background: var(--primary); color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; box-shadow: 0 10px 24px rgba(31,102,173,0.25); }
        .sidebar-card {
          margin-top:10px;
          border:1px solid #d9e3ee;
          border-radius:14px;
          padding:12px;
          background:#f5f8fc;
        }
        .api-title { font-family:Lexend,sans-serif; font-size:0.96rem; font-weight:800; color:#1f66ad; }
        .profile-wrap { display:flex; align-items:center; gap:10px; margin-top:12px; }
        .avatar {
          width:40px; height:40px; border-radius:999px;
          background:#e2ebf6; color:#2a5d95; font-weight:800;
          display:flex; align-items:center; justify-content:center;
        }

        .top-shell {
          background: rgba(255,255,255,0.90);
          border:1px solid rgba(217,224,232,0.9);
          border-radius:16px;
          padding:12px 18px;
          margin-left:-0.5rem;
          margin-right:-0.5rem;
          box-shadow: var(--shadow-sm);
          backdrop-filter: blur(10px);
        }
        .hero-title { font-size:3.7rem; font-weight:800; line-height:1.06; letter-spacing:-0.03em; margin-top:.15rem; }
        .subtle { color:#657586; }
        .page-wrap { padding:0 0.25rem; }
        .section-title { font-size:2rem; font-weight:800; margin-top:.5rem; }
        .small-kicker { font-size:1rem; color:#6d7f93; }
        .panel-label { font-size:2.8rem; font-weight:800; letter-spacing:-0.02em; margin-bottom:.4rem; }

        .drop-card {
          border:2px dashed #c8d5e5; border-radius:12px; min-height:300px;
          background:#eef3f8;
          display:flex; flex-direction:column; align-items:center; justify-content:center;
        }

        .action-bar {
          border:1px solid rgba(31,102,173,0.20); background:#e9f0f8;
          border-radius:12px; padding:12px 14px;
        }

        .status-ok { color:#15803d; }
        .status-bad { color:#b91c1c; }

        .stButton > button { border-radius:10px !important; font-weight:700 !important; }
        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button[kind="primary"] {
          background: var(--primary) !important;
          border:1px solid var(--primary) !important;
          color:#fff !important;
          box-shadow: 0 12px 24px rgba(31,102,173,0.20);
        }
        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button[kind="primary"]:hover {
          background: var(--primary-2) !important;
          border-color: var(--primary-2) !important;
        }

        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button[kind="secondary"] {
          border-radius: 12px !important;
          border: 1px solid rgba(217,224,232,0.9) !important;
          background: rgba(255,255,255,0.92) !important;
          box-shadow: 0 10px 20px rgba(17,24,39,0.05);
        }

        [data-testid="stTextArea"] textarea {
          min-height:300px !important;
          border-radius:14px !important;
          border:1px solid rgba(217,224,232,0.95) !important;
          box-shadow: 0 10px 20px rgba(17,24,39,0.04) !important;
          background:#fff !important;
          color:#121417 !important;
          font-size:1.05rem !important;
        }

        [data-testid="stFileUploaderDropzone"] {
          border:1px solid rgba(202,216,231,0.95) !important;
          border-radius:14px !important;
          background:#eef3f8 !important;
          min-height:320px;
          box-shadow: 0 14px 30px rgba(17,24,39,0.06);
        }
        [data-testid="stFileUploaderDropzone"] button {
          background:#1f66ad !important;
          color:#fff !important;
          border:1px solid #1f66ad !important;
          border-radius:10px !important;
        }
        .table-shell {
          margin-top:8px;
          border:1px solid rgba(217,224,232,0.9);
          border-radius:16px;
          background:#fff;
          padding:12px;
          box-shadow: var(--shadow-sm);
        }

        .metric-grid { display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 14px; }
        .metric {
          border: 1px solid rgba(217,224,232,0.9);
          border-radius: 16px;
          background: rgba(255,255,255,0.95);
          padding: 14px;
          box-shadow: var(--shadow-sm);
        }
        .metric-label { font-size: 0.82rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #6d7f93; }
        .metric-value { font-family: Lexend,sans-serif; font-size: 2rem; font-weight: 900; margin-top: 6px; }
        .metric-sub { margin-top: 4px; font-size: 0.92rem; color: var(--muted); }

        @media (max-width: 980px) {
          .metric-grid { grid-template-columns: 1fr; }
        }

        .pill { display:inline-flex; align-items:center; padding:6px 10px; border-radius:999px; font-size:11px; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }
        .pill-ok { background:rgba(22,163,74,0.12); color:#15803d; border:1px solid rgba(22,163,74,0.22); }
        .pill-warn { background:rgba(245,158,11,0.14); color:#b45309; border:1px solid rgba(245,158,11,0.26); }
        .pill-bad { background:rgba(223,73,90,0.14); color:#b42318; border:1px solid rgba(223,73,90,0.26); }

        .dark-shell {
          background:#17191c;
          border:1px solid #24272b;
          border-radius:14px;
          overflow:hidden;
          box-shadow: 0 24px 48px rgba(2, 6, 23, 0.35);
        }
        .dark-bar {
          background:#1e2124;
          border-bottom:1px solid #2a2e33;
          padding:12px 14px;
          color:#e5e7eb;
          display:flex;
          justify-content:space-between;
          align-items:flex-start;
          gap:12px;
        }
        .dark-sub { color:#9ca3af; font-size:0.8rem; }
        .dark-grid { display:grid; grid-template-columns: 1.32fr 0.92fr 1.12fr; min-height: 580px; max-height: 74vh; }
        .dark-panel { border-right:1px solid #2a2e33; }
        .dark-panel:last-child { border-right:none; }
        .dark-viewer { background: radial-gradient(circle at center, #2c2f33 0%, #17191c 100%); padding: 16px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
        .dark-viewer img { max-height: 66vh; object-fit: contain; border-radius: 10px; }
        .dark-findings { background:#1a1c1e; padding: 0; overflow-y:auto; }
        .dark-report { background:#1e2124; padding: 0; overflow-y:auto; }
        .dark-head { position: sticky; top: 0; z-index: 4; padding: 12px 14px; border-bottom:1px solid #2a2e33; display:flex; justify-content:space-between; align-items:center; background:#1f2226; }
        .dark-title { font-size:0.78rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#9ca3af; }
        .finding-card { margin: 12px 14px; padding: 12px; border-radius:12px; border-left:4px solid rgba(148,163,184,0.45); background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.22); }
        .finding-card.active { border-left-color: rgba(20,143,184,1); box-shadow: 0 0 16px rgba(20,143,184,0.2); border-color: rgba(20,143,184,0.22); }
        .finding-top { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }
        .finding-name { font-weight:800; color:#f8fafc; }
        .finding-conf { font-size:0.68rem; font-weight:800; color: rgba(20,143,184,1); background: rgba(20,143,184,0.15); border:1px solid rgba(20,143,184,0.2); padding: 3px 8px; border-radius: 999px; white-space:nowrap; }
        .finding-text { margin-top: 8px; color:#cbd5e1; font-size:0.86rem; line-height:1.45; }
        .report-body { padding: 14px; color:#dde6f3; font-size:1.02rem; line-height:1.62; }
        .report-body p { margin: 0 0 0.8rem 0; }
        .note-box { margin: 14px; padding: 14px; border-radius: 14px; background: rgba(77,23,33,0.58); border:1px solid rgba(223,73,90,0.34); }
        .note-title { font-size:0.74rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#fb7185; }
        .note-text { margin-top: 8px; color:#ffe4e8; }
        .note-pre { margin-top: 8px; color:#ffe4e8; font-size:0.92rem; line-height:1.55; white-space:pre-wrap; overflow-wrap:anywhere; font-family:'Manrope',sans-serif; max-height: 36vh; overflow-y:auto; }

        @media (max-width: 1500px) {
          .dark-grid { grid-template-columns: 1fr; max-height:none; }
          .dark-panel { border-right:none; border-bottom:1px solid #2a2e33; min-height: 320px; }
          .dark-panel:last-child { border-bottom:none; }
          .dark-viewer img { max-height: 54vh; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_pill_html(result: Optional[Dict[str, Any]]) -> str:
    if not result:
        return ""
    counts = (result.get("comparison") or {}).get("discrepancy_counts") or {}
    mism = int(counts.get("mismatches") or 0)
    omis = int(counts.get("omissions") or 0) + int(counts.get("overstatements") or 0)
    if mism > 0:
        return "<span class='pill pill-bad'>Discrepancy</span>"
    if omis > 0:
        return "<span class='pill pill-warn'>Review Needed</span>"
    return "<span class='pill pill-ok'>Match</span>"


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="logo-wrap">
                <div class="logo-box">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="3.5" y="3.5" width="17" height="17" rx="3" stroke="white" stroke-width="1.6"/>
                        <path d="M7 9.2H17" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                        <path d="M7 13H11.3" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
                        <circle cx="15.4" cy="14.8" r="2.2" stroke="white" stroke-width="1.4"/>
                    </svg>
                </div>
                <div>
                    <div style="font-family:Lexend,sans-serif;font-weight:800;color:#1f66ad;font-size:1.05rem;">RAVEN AI</div>
                    <div style="font-size:11px;color:#657586;letter-spacing:.04em;">RADIOLOGY VERIFICATION</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_items = [
            ("Dashboard", "Dashboard"),
            ("Analysis Workspace", "Analysis Workspace"),
            ("Discrepancy Resolution", "Discrepancy Resolution"),
            ("Final Export", "Final Export"),
            ("History & Archive", "History & Archive"),
            ("Help Center", "Help Center"),
        ]
        for label, page in nav_items:
            is_active = st.session_state.active_page == page
            if st.button(label, use_container_width=True, key=f"nav_{page}", type="primary" if is_active else "secondary"):
                st.session_state.active_page = page
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.session_state.backend_url = st.text_input("Backend URL", value=st.session_state.backend_url)
        st.session_state.backend_api_key = st.text_input("API Key", value=st.session_state.backend_api_key, type="password")
        connected, status_msg = backend_health_check()
        st.session_state.backend_connected = connected
        mode_title = "BACKEND MODE" if connected else "DEMO FALLBACK"
        mode_sub = status_msg if connected else f"{status_msg} - using mock data"
        st.markdown(f"<div class='sidebar-card'><div class='api-title'>{mode_title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='subtle' style='font-size:0.88rem;'>{mode_sub}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="profile-wrap">
                <div class="avatar">RV</div>
                <div>
                    <div style="font-family:Lexend,sans-serif;font-weight:700;color:#121417;">RAVEN Operator</div>
                    <div style="font-size:0.9rem;color:#657586;">Clinical Reviewer</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def top_header() -> None:
    c1, c2 = st.columns([6, 1.6])
    with c1:
        pill = status_pill_html(st.session_state.last_result)
        page = st.session_state.active_page
        meta = PAGES.get(page, {"title": page, "sub": ""})
        st.markdown(
            f"""
            <div class="top-shell">
                <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
                  <div>
                    <div style="font-size:2.15rem;font-weight:800;line-height:1;">{meta.get('title','')}</div>
                    <div class="small-kicker">{meta.get('sub','')}</div>
                  </div>
                  <div>{pill}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("+ New Analysis", type="primary", use_container_width=True):
            st.session_state.image_bytes = None
            st.session_state.image_name = ""
            st.session_state.report_text = ""
            st.session_state.last_result = None
            st.session_state.last_error = ""
            st.rerun()


def render_dashboard() -> None:
    if st.session_state.backend_connected:
        try:
            st.session_state.history_cache = fetch_history_backend(limit=20)
        except Exception as exc:
            st.session_state.last_error = str(exc)

    st.markdown(
        """
        <div style="max-width: 980px;">
          <div class='panel-label'>Verify New Medical Scans</div>
          <p class='small-kicker'>Pair medical imagery with human-written reports for high-precision cross-validation.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    history = st.session_state.history_cache
    total = len(history)
    high = sum(1 for h in history if str(h.get("risk", "")).upper() == "HIGH")
    low = sum(1 for h in history if str(h.get("risk", "")).upper() == "LOW")
    st.markdown(
        f"""
        <div class='metric-grid'>
          <div class='metric'>
            <div class='metric-label'>Total Scans</div>
            <div class='metric-value'>{total}</div>
            <div class='metric-sub'>Demo audit archive</div>
          </div>
          <div class='metric'>
            <div class='metric-label'>High Risk</div>
            <div class='metric-value' style='color:#b42318;'>{high}</div>
            <div class='metric-sub'>Priority review cases</div>
          </div>
          <div class='metric'>
            <div class='metric-label'>Low Risk</div>
            <div class='metric-value' style='color:#15803d;'>{low}</div>
            <div class='metric-sub'>Low discrepancy probability</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("### 1. Upload Medical Scans")
        file = st.file_uploader(
            "Drag and drop files here. Support for DICOM, JPEG, PNG",
            type=["png", "jpg", "jpeg", "dcm"],
            label_visibility="collapsed",
        )
        if file is not None:
            st.session_state.image_bytes = file.getvalue()
            st.session_state.image_name = file.name
            st.success(f"Selected: {file.name}")

    with right:
        st.markdown("### 2. Human-Written Radiology Report")
        st.session_state.report_text = st.text_area(
            "Report",
            value=st.session_state.report_text,
            placeholder="Paste the official radiology report text here...",
            label_visibility="collapsed",
        )

    st.write("")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown("<div class='action-bar'>Ensure all patient identifiers are redacted if required by local policy.</div>", unsafe_allow_html=True)
    with c2:
        can_run = bool(st.session_state.image_bytes) and bool(st.session_state.report_text.strip())
        if st.button("Start AI Analysis", type="primary", use_container_width=True, disabled=not can_run):
            st.session_state.last_error = ""
            with st.spinner("Running AI verification..."):
                try:
                    if st.session_state.backend_connected:
                        result = verify_backend(
                            st.session_state.image_name,
                            st.session_state.image_bytes,
                            st.session_state.report_text.strip(),
                            enhance=True,
                        )
                    else:
                        result = mock_verify(st.session_state.image_name, st.session_state.report_text.strip())
                    st.session_state.last_result = result
                    st.session_state.active_page = "Analysis Workspace"

                    if st.session_state.backend_connected:
                        st.session_state.history_cache = fetch_history_backend(limit=20)
                    else:
                        st.session_state.history_cache = [
                            {
                                "id": result.get("meta", {}).get("study_id", "CASE") + "-DEMO",
                                "scan_type": st.session_state.image_name or "Uploaded Scan",
                                "patient_id": "PAT-DEMO",
                                "created_at": datetime.now().strftime("%b %d, %I:%M %p"),
                                "verification_status": "Discrepancy Found",
                                "risk": str((result.get("comparison") or {}).get("risk_level") or "-").upper(),
                            },
                            *st.session_state.history_cache,
                        ]

                    st.rerun()
                except Exception as exc:
                    st.session_state.last_error = str(exc)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    st.write("")
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Recent Activity")
    with h2:
        st.markdown("<div style='text-align:right;color:#1f66ad;font-weight:700;margin-top:8px;'>View Full History</div>", unsafe_allow_html=True)
    history = st.session_state.history_cache
    rows = []
    for item in history:
        rows.append(
            {
                "Scan ID / Type": f"#{item.get('id', '-') } - {item.get('scan_type','-')}",
                "Patient Ref": item.get("patient_id", "-"),
                "Timestamp": item.get("created_at", "-"),
                "Verification Status": item.get("verification_status", "-"),
            }
        )
    st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_analysis() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return

    meta = result.get("meta") or {}
    cmp = result.get("comparison") or {}
    counts = cmp.get("discrepancy_counts") or {}

    st.markdown(
        f"""
        <div class='dark-shell'>
          <div class='dark-bar'>
            <div>
              <div style='font-weight:800;font-size:1.05rem;'>{meta.get('study','')}</div>
              <div class='dark-sub'>STUDY ID: {meta.get('study_id','')} - {meta.get('timestamp','')} - <span style='color:rgba(20,143,184,1)'>STAT</span></div>
            </div>
            <div style='display:flex;gap:8px;flex-wrap:wrap;'>
              <span style='padding:6px 10px;border-radius:999px;background:rgba(223,73,90,0.14);border:1px solid rgba(223,73,90,0.25);color:#fb7185;font-weight:800;font-size:0.75rem;'>Mismatch {int(counts.get('mismatches') or 0)}</span>
              <span style='padding:6px 10px;border-radius:999px;background:rgba(245,158,11,0.14);border:1px solid rgba(245,158,11,0.25);color:#fbbf24;font-weight:800;font-size:0.75rem;'>Omission {int(counts.get('omissions') or 0)}</span>
            </div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.35, 0.82, 1], gap="small")

    with col1:
        st.markdown("<div class='dark-panel dark-viewer'>", unsafe_allow_html=True)
        enhanced_bytes = result.get("enhanced_image_bytes")
        if enhanced_bytes:
            st.image(enhanced_bytes, use_container_width=True, caption="Enhanced scan")
        elif st.session_state.image_bytes:
            st.image(st.session_state.image_bytes, use_container_width=True, caption="Original scan")
        else:
            st.image(
                "https://lh3.googleusercontent.com/aida-public/AB6AXuD57tZCNaKTyMhcARHi_e-_h-n7kbEwkDiu0bPOhG77MnZk9-Grvq1m0lT1ibcLZrbmk84D_B0As5R3nMwHzzNmBNqB40E0o9u_T49Cjw2KN9nPWd2dBribnY_2lgYQsbde1AKX4Y8NnbtkxyGjc997jLmqBRPTBz7TiVNZIuyjmnY2Le6GUrz5UVhDi_a-pN8lc9vGjkcEsJIONcykPB4qNQF1zdKqQ2UVYPH2WRgXlHtrx0lAe9o0sUJ3AcKDswdk7rd-07p_FxI",
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            "<div class='dark-panel dark-findings'><div class='dark-head'><div class='dark-title'>AI Findings</div><div style='font-size:0.72rem;color:#9ca3af;background:rgba(148,163,184,0.12);border:1px solid rgba(148,163,184,0.15);padding:2px 8px;border-radius:999px;'>v2.4.1</div></div>",
            unsafe_allow_html=True,
        )

        cards_html = ""
        for idx, f in enumerate(result.get("ai_findings") or []):
            active = "active" if idx == 0 else ""
            cards_html += (
                f"<div class='finding-card {active}'>"
                f"<div class='finding-top'><div class='finding-name'>{f.get('name','')}</div><div class='finding-conf'>{int(float(f.get('confidence',0)) * 100)}% CONF.</div></div>"
                f"<div class='finding-text'>{f.get('rationale','')}</div>"
                "</div>"
            )
        st.markdown(cards_html + "</div>", unsafe_allow_html=True)

    with col3:
        report_html = (result.get("report") or {}).get("highlighted_html") or ""
        if not report_html:
            report_html = f"<p>{html.escape((result.get('report') or {}).get('raw_text', ''))}</p>"
        cmp_text = cmp.get("comparison_report_text", "")
        cmp_html = f"<pre class='note-pre'>{html.escape(str(cmp_text))}</pre>"
        st.markdown(
            "<div class='dark-panel dark-report'><div class='dark-head'><div class='dark-title'>Human Authored Report</div><div style='display:flex;gap:6px;'><div style='width:10px;height:10px;border-radius:999px;background:#DF495A;'></div><div style='width:10px;height:10px;border-radius:999px;background:#f59e0b;'></div></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='report-body'>", unsafe_allow_html=True)
        st.markdown(report_html, unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='note-box'>
              <div class='note-title'>Discrepancy Detail</div>
              <div class='note-text'>Clean comparison summary:</div>
              {cmp_html}
            </div>
            """ + "</div></div>",
            unsafe_allow_html=True,
        )
        raw_cmp = cmp.get("comparison_report_text_raw")
        if raw_cmp and raw_cmp != cmp_text:
            with st.expander("Show raw backend comparison text"):
                st.code(str(raw_cmp))

    b1, b2, b3 = st.columns([1.2, 1.2, 1.6])
    with b1:
        if st.button("Open Resolution Workspace", type="secondary", use_container_width=True):
            st.session_state.active_page = "Discrepancy Resolution"
            st.rerun()
    with b2:
        if st.button("Proceed to Export", type="secondary", use_container_width=True):
            st.session_state.active_page = "Final Export"
            st.rerun()
    with b3:
        st.markdown(
            f"<div class='subtle' style='text-align:right;padding-top:10px;'>Agreement: {int(float(cmp.get('agreement_rate',0)) * 100)}% - Risk: <b>{str(cmp.get('risk_level','-')).upper()}</b></div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_history() -> None:
    st.markdown("## History & Archive")
    if st.session_state.backend_connected:
        try:
            st.session_state.history_cache = fetch_history_backend(limit=50)
        except Exception as exc:
            st.error(str(exc))
    history = st.session_state.history_cache
    st.dataframe(history, use_container_width=True, hide_index=True)


def render_help_center() -> None:
    st.markdown(
        """
        <div style="text-align:center; padding: 30px; border-radius: 18px; background: radial-gradient(1200px 420px at 20% 0%, rgba(255,255,255,0.24), rgba(255,255,255,0) 60%), linear-gradient(135deg, rgba(31,102,173,1), rgba(26,67,110,1)); color: white; box-shadow: 0 20px 50px rgba(13, 42, 70, 0.25);">
          <h1 style="margin:0; font-family:Lexend,sans-serif; font-weight:900; font-size:2.2rem; letter-spacing:-0.02em;">How can we help you today?</h1>
          <div style="opacity:0.92; margin-top: 10px; font-size:1.02rem;">Search documentation, workflows, and common actions.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    q = st.text_input("Search docs", placeholder="Search docs...", label_visibility="collapsed")

    cards = [
        ("Getting Started", "Upload scan + report, run analysis, resolve discrepancies, export bundle."),
        ("Analysis Workspace", "Understand confidence, overlays, and the discrepancy summary."),
        ("Resolution Workflow", "Accept AI, dismiss false positives, or modify findings before export."),
        ("Export & Audit", "Download compliance bundle and trace changes across sessions."),
    ]

    if q:
        ql = q.lower()
        cards = [c for c in cards if ql in c[0].lower() or ql in c[1].lower()]

    cols = st.columns(2, gap="large")
    for i, (title, desc) in enumerate(cards):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class='table-shell'>
                  <div style='display:flex;align-items:center;justify-content:space-between;gap:10px;'>
                    <div style='font-family:Lexend,sans-serif;font-weight:900;font-size:1.12rem;margin-bottom:6px;'>{title}</div>
                    <div style='width:10px;height:10px;border-radius:999px;background:rgba(31,102,173,0.35);'></div>
                  </div>
                  <div class='subtle' style='font-size:0.98rem;line-height:1.5;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_discrepancy_resolution() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return

    st.markdown("## Discrepancy Resolution")
    st.markdown("<p class='subtle'>Resolve each discrepancy before final export.</p>", unsafe_allow_html=True)

    items = [f for f in (result.get("ai_findings") or []) if f.get("status") in {"mismatch", "omission"}]
    if not items:
        st.success("No active discrepancies.")
        return

    st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
    for idx, item in enumerate(items):
        c1, c2, c3, c4 = st.columns([2.2, 1.2, 1.1, 1.8])
        with c1:
            st.markdown(f"<b>{item.get('name','')}</b>", unsafe_allow_html=True)
        with c2:
            st.markdown("<span class='subtle'>Category</span>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<span class='subtle'>{str(item.get('status','')).upper()}</span>", unsafe_allow_html=True)
        with c4:
            key = f"res_{idx}_{item.get('name','')}"
            current = st.session_state.resolution.get(key, "Accept AI")
            choice = st.selectbox(
                "Resolution",
                ["Accept AI", "Dismiss", "Modify"],
                index=["Accept AI", "Dismiss", "Modify"].index(current),
                key=key,
                label_visibility="collapsed",
            )
            st.session_state.resolution[key] = choice
        st.divider()
    st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("Back to Analysis", type="secondary", use_container_width=True):
            st.session_state.active_page = "Analysis Workspace"
            st.rerun()
    with b2:
        if st.button("Save & Continue Export", type="primary", use_container_width=True):
            st.session_state.active_page = "Final Export"
            st.rerun()


def render_final_export() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return

    st.markdown("## Final Export")
    st.markdown("<p class='subtle'>Generated document preview for archive and compliance (demo).</p>", unsafe_allow_html=True)

    cfg = st.session_state.export_config
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.markdown("### Export Options")
        cfg["heatmap"] = st.checkbox("Include heatmap overlay", value=bool(cfg.get("heatmap")))
        cfg["summary"] = st.checkbox("Include AI summary", value=bool(cfg.get("summary")))
        cfg["narrative"] = st.checkbox("Include narrative", value=bool(cfg.get("narrative")))
        cfg["discrepancy"] = st.checkbox("Include discrepancy log", value=bool(cfg.get("discrepancy")))
        st.session_state.export_config = cfg

    with c2:
        st.markdown("### Export")
        payload = {
            "export_config": cfg,
            "resolution": st.session_state.resolution,
            "result": result,
        }
        st.download_button(
            "Download JSON Bundle",
            data=json.dumps(payload, indent=2),
            file_name=f"raven_export_{int(datetime.now().timestamp())}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
    st.json(payload)
    st.markdown("</div>", unsafe_allow_html=True)


def render_simple(title: str) -> None:
    st.markdown(f"## {title}")
    st.info("This section is available. Next I can wire full interactions screen-by-screen.")


def main() -> None:
    st.set_page_config(page_title="RAVEN Web App", page_icon="R", layout="wide", initial_sidebar_state="expanded")
    init_state()
    inject_css()
    render_sidebar()
    top_header()
    st.write("")

    page = st.session_state.active_page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Analysis Workspace":
        render_analysis()
    elif page == "History & Archive":
        render_history()
    elif page == "Discrepancy Resolution":
        render_discrepancy_resolution()
    elif page == "Final Export":
        render_final_export()
    elif page == "Help Center":
        render_help_center()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
