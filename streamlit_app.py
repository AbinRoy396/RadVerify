"""RAVEN Streamlit UI matching the requested reference interface."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
import streamlit as st

API_BASE = "http://localhost:8000"
API_KEY = "radverify_secret_key"


def init_state() -> None:
    defaults = {
        "active_page": "Dashboard",
        "image_bytes": None,
        "image_name": "",
        "report_text": "",
        "last_result": None,
        "last_error": "",
        "resolution": {},
        "export_config": {"include_raw": True, "include_resolution": True, "include_tables": True},
        "settings": {
            "api_base": API_BASE,
            "api_key": API_KEY,
            "prefer_backend": True,
            "backend_timeout_sec": 180,
        },
        "history_cache": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;600;700;800&family=Manrope:wght@400;500;600;700&display=swap');

        .stApp { background:#f3f5f8; color:#111827; font-family:'Manrope',sans-serif; }
        h1,h2,h3,h4 { font-family:'Lexend',sans-serif; letter-spacing:-0.02em; }

        #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }
        header[data-testid="stHeader"] { background:transparent !important; border:none !important; box-shadow:none !important; }
        [data-testid="stAppViewContainer"] { background:#f3f5f8; }
        [data-testid="stMainBlockContainer"] { padding-top:1.2rem; max-width:1400px; }

        [data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #d9e0e8; min-width:278px; max-width:278px; }
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
        .logo-box { width:40px; height:40px; border-radius:10px; background:#1f66ad; color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800; }
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
          background:#ffffff;
          border:1px solid #dce3ea;
          border-radius:0;
          padding:10px 18px;
          margin-left:-0.5rem;
          margin-right:-0.5rem;
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
          background:#2b6eb6 !important;
          border:1px solid #2b6eb6 !important;
          color:#fff !important;
        }
        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button[kind="primary"]:hover {
          background:#245f9d !important;
          border-color:#245f9d !important;
        }

        [data-testid="stTextArea"] textarea {
          min-height:300px !important;
          border-radius:12px !important;
          border:1px solid #dce0e5 !important;
          box-shadow:none !important;
          background:#fff !important;
          color:#121417 !important;
          font-size:1.05rem !important;
        }
        [data-testid="stTextInput"] input {
          border-radius:12px !important;
          border:1px solid #cbd5e1 !important;
          background:#f8fafc !important;
          color:#0f172a !important;
          box-shadow:none !important;
          padding:10px 12px !important;
        }
        [data-testid="stSelectbox"] div[role="combobox"] {
          border-radius:12px !important;
          border:1px solid #cbd5e1 !important;
          background:#f8fafc !important;
          color:#0f172a !important;
        }
        [data-testid="stSelectbox"] svg {
          color:#475569 !important;
        }

        [data-testid="stFileUploaderDropzone"] {
          border:1px solid #cad8e7 !important;
          border-radius:12px !important;
          background:#eef3f8 !important;
          min-height:320px;
        }
        [data-testid="stFileUploaderDropzone"] * {
          color:#607086 !important;
        }
        [data-testid="stFileUploaderDropzone"] svg {
          color:#7a8aa0 !important;
        }
        [data-testid="stFileUploaderDropzone"] small,
        [data-testid="stFileUploaderDropzone"] p,
        [data-testid="stFileUploaderDropzone"] span {
          color:#607086 !important;
        }
        [data-testid="stFileUploaderDropzone"] button {
          background:#1f66ad !important;
          color:#fff !important;
          border:1px solid #1f66ad !important;
          border-radius:10px !important;
        }
        [data-testid="stFileUploader"] [data-testid="stUploadedFile"] {
          display:none !important;
        }
        [data-testid="stFileUploader"] ul {
          padding-left:0 !important;
          margin:6px 0 0 0 !important;
          display:inline-flex !important;
          flex-direction:column !important;
          gap:6px !important;
        }
        [data-testid="stFileUploader"] li {
          list-style:none !important;
          width: fit-content !important;
          max-width:100% !important;
        }
        [data-testid="stFileUploader"] li > div {
          width: fit-content !important;
          max-width:100% !important;
          display:inline-flex !important;
        }
        [data-testid="stFileUploader"] [data-testid="stUploadedFile"] div,
        [data-testid="stFileUploader"] [data-testid="stUploadedFile"] span {
          width:auto !important;
          max-width:100% !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"] {
          color:#1f66ad !important;
          font-weight:600 !important;
          font-size:0.95rem !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderFileSize"] {
          display:none !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"] {
          color:#64748b !important;
          border-radius:999px !important;
          padding:2px !important;
        }
        [data-testid="stFileUploader"] [data-testid="stFileUploaderDeleteBtn"]:hover {
          color:#ef4444 !important;
          background:#fee2e2 !important;
        }
        [data-testid="stFileUploader"] svg {
          color:#1f66ad !important;
          width:18px !important;
          height:18px !important;
        }

        .selected-pill {
          margin-top:8px;
          padding:10px 14px;
          border-radius:12px;
          background:#e6f4ff;
          border:1px solid #b9d8f5;
          color:#1f66ad;
          font-weight:700;
        }
        .selected-inline { display:none !important; }
        .table-shell {
          margin-top:8px;
          border:1px solid #dce3ea;
          border-radius:12px;
          background:#fff;
          padding:12px;
        }
        .history-wrap {
          border:1px solid #dce3ea;
          border-radius:12px;
          overflow:hidden;
          background:#fff;
        }
        .history-table {
          width:100%;
          border-collapse:collapse;
          font-size:0.95rem;
        }
        .history-table th {
          text-align:left;
          font-weight:700;
          color:#3a4a5a;
          padding:10px 12px;
          border-bottom:1px solid #e3e8ef;
          background:#f7f9fc;
        }
        .history-table td {
          padding:10px 12px;
          border-bottom:1px solid #eef2f7;
          color:#243043;
        }
        .history-table tbody tr:hover {
          background:#f3f7fb;
        }
        .history-pill {
          display:inline-flex;
          align-items:center;
          gap:6px;
          padding:4px 10px;
          border-radius:999px;
          font-weight:700;
          font-size:0.78rem;
        }
        .pill-low { background:#e8f7ee; color:#15803d; }
        .pill-med { background:#fff7e6; color:#b45309; }
        .pill-high { background:#fde8e8; color:#b91c1c; }
        .pill-unk { background:#eef2f7; color:#475569; }

        .dark-shell {
          background: linear-gradient(135deg, rgba(23,25,28,1) 0%, rgba(18,20,24,1) 100%);
          border:1px solid #24272b;
          border-radius:16px;
          overflow:hidden;
          box-shadow: 0 24px 48px rgba(2, 6, 23, 0.35);
        }
        .dark-bar {
          background: linear-gradient(90deg, rgba(29,33,38,1) 0%, rgba(24,27,31,1) 100%);
          border-bottom:1px solid #2a2e33;
          padding:14px 18px;
          color:#e5e7eb;
          display:flex;
          justify-content:space-between;
          align-items:flex-start;
          gap:12px;
        }
        .dark-sub { color:#9ca3af; font-size:0.8rem; }
        .dark-grid { display:grid; grid-template-columns: 1.32fr 0.92fr 1.12fr; min-height: 600px; max-height: 76vh; }
        .dark-panel { border-right:1px solid #2a2e33; }
        .dark-panel:last-child { border-right:none; }
        .dark-viewer { background: radial-gradient(circle at center, #2c2f33 0%, #17191c 100%); padding: 18px; display:flex; align-items:center; justify-content:center; overflow:hidden; }
        .dark-viewer img { max-height: 66vh; object-fit: contain; border-radius: 10px; }
        .dark-findings { background:#1a1c1e; padding: 0; overflow-y:auto; }
        .dark-report { background:#1e2124; padding: 0; overflow-y:auto; }
        .dark-head { position: sticky; top: 0; z-index: 4; padding: 12px 16px; border-bottom:1px solid #2a2e33; display:flex; justify-content:space-between; align-items:center; background:#1f2226; }
        .dark-title { font-size:0.78rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#9ca3af; }
        .finding-card { margin: 12px 16px; padding: 12px; border-radius:12px; border-left:4px solid rgba(148,163,184,0.45); background: rgba(15,23,42,0.72); border: 1px solid rgba(148,163,184,0.22); }
        .finding-card.active { border-left-color: rgba(20,143,184,1); box-shadow: 0 0 16px rgba(20,143,184,0.2); border-color: rgba(20,143,184,0.22); }
        .finding-top { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }
        .finding-name { font-weight:800; color:#f8fafc; }
        .finding-conf { font-size:0.68rem; font-weight:800; color: rgba(20,143,184,1); background: rgba(20,143,184,0.15); border:1px solid rgba(20,143,184,0.2); padding: 3px 8px; border-radius: 999px; white-space:nowrap; }
        .finding-text { margin-top: 8px; color:#94a3b8; font-size:0.86rem; line-height:1.4; }
        .report-body { padding: 16px; color:#e2e8f0; font-size:1.05rem; line-height:1.7; }
        .note-box { margin: 14px 16px; padding: 14px; border-radius: 14px; background: #8b5a63; border:1px solid #a56a73; }
        .note-title { font-size:0.74rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#ffe4e6; }
        .note-text { margin-top: 8px; color:#f8fafc; }
        .raw-report {
          margin: 12px 16px 16px;
          padding: 14px;
          border-radius: 12px;
          background: #101418;
          border: 1px solid #2a2e33;
          color: #f59e0b;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
          font-size: 0.9rem;
          line-height: 1.55;
          white-space: pre-wrap;
        }
        .analysis-wrap { margin-top: 8px; }
        .agreement-row { text-align:right; padding:8px 16px 14px; color:#cbd5e1; }
        @media (max-width: 1100px) {
          .dark-grid { grid-template-columns: 1fr; max-height:none; }
          .dark-panel { border-right:none; border-bottom:1px solid #2a2e33; }
          .dark-panel:last-child { border-bottom:none; }
          .dark-viewer img { max-height: 52vh; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_headers() -> Dict[str, str]:
    api_key = (st.session_state.get("settings") or {}).get("api_key") or API_KEY
    return {"X-API-Key": str(api_key)}


def call_verify(file_name: str, image_bytes: bytes, report_text: str) -> Dict[str, Any]:
    files = {"scan": (file_name, image_bytes, "application/octet-stream")}
    data = {"report": report_text, "enhance": "true"}
    api_base = (st.session_state.get("settings") or {}).get("api_base") or API_BASE
    timeout_s = int((st.session_state.get("settings") or {}).get("backend_timeout_sec") or 180)
    resp = requests.post(f"{api_base}/verify", files=files, data=data, headers=api_headers(), timeout=timeout_s)
    resp.raise_for_status()
    return resp.json()


def fetch_history(limit: int = 10) -> List[Dict[str, Any]]:
    api_base = (st.session_state.get("settings") or {}).get("api_base") or API_BASE
    resp = requests.get(f"{api_base}/history", headers=api_headers(), params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def mock_verify(file_name: str, report_text: str) -> Dict[str, Any]:
    now = datetime.now()
    base = {
        "metadata": {
            "study": f"Study: {file_name}",
            "study_id": f"DEMO-{int(now.timestamp())}",
            "timestamp": now.strftime("%b %d, %Y %H:%M"),
        },
        "doctor_findings": {"raw_text": report_text},
        "ai_report_text": "AI report (demo):\n" + (report_text.strip() or "No doctor report provided."),
        "enhanced_image_path": None,
        "verification_results": {
            "agreement_rate": 0.82,
            "risk_level": "medium",
            "discrepancy_counts": {"matches": 9, "omissions": 1, "mismatches": 2, "overstatements": 0},
            "measurement_comparisons": {
                "Cardiothoracic Ratio": {
                    "status": "mismatch",
                    "ai_value": 0.58,
                    "doctor_value": "normal",
                    "difference": "+0.08",
                    "tolerance": "0.05",
                    "severity": "moderate",
                }
            },
            "structure_comparisons": {
                "thorax": {
                    "Pleural Effusion": {
                        "status": "omission",
                        "ai_present": True,
                        "ai_confidence": 0.76,
                        "doctor_mentioned": False,
                        "doctor_negated": False,
                        "severity": "low",
                    }
                }
            },
        },
        "ai_findings": {
            "structures_detected": {
                "thorax": {
                    "pleural_effusion": {"present": True, "confidence": 0.76},
                    "cardiomegaly": {"present": True, "confidence": 0.81},
                }
            }
        },
    }
    return base


def safe_verify(file_name: str, image_bytes: bytes, report_text: str) -> Dict[str, Any]:
    prefer_backend = bool((st.session_state.get("settings") or {}).get("prefer_backend", True))
    if prefer_backend:
        try:
            return call_verify(file_name, image_bytes, report_text)
        except Exception as exc:
            st.session_state.last_error = f"Backend unavailable. Using demo results. Details: {exc}"
            return mock_verify(file_name, report_text)
    return mock_verify(file_name, report_text)


def _resolve_image_bytes(path_value: Any) -> bytes | None:
    if not path_value:
        return None
    try:
        path = str(path_value)
        if not path:
            return None
        file_path = Path(path)
        if not file_path.is_absolute():
            repo_root = Path(__file__).resolve().parents[1]
            candidate = repo_root / file_path
            if candidate.exists():
                return candidate.read_bytes()
            normalized = Path(str(path).replace("\\", "/"))
            candidate = repo_root / normalized
            if candidate.exists():
                return candidate.read_bytes()
        if file_path.exists():
            return file_path.read_bytes()
    except Exception:
        return None
    return None


def _flatten_ai_findings(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    structures = (raw.get("ai_findings") or {}).get("structures_detected") or {}
    for group, entries in structures.items():
        if not isinstance(entries, dict):
            continue
        for name, info in entries.items():
            if not isinstance(info, dict):
                continue
            confidence = float(info.get("confidence") or 0.0)
            present = info.get("present")
            findings.append(
                {
                    "name": name.replace("_", " ").title(),
                    "confidence": confidence,
                    "rationale": f"Category: {group}. Present={present}.",
                }
            )
    findings.sort(key=lambda item: item.get("confidence", 0.0), reverse=True)
    return findings


def _build_comparison_table(verification: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    measurements = verification.get("measurement_comparisons") or {}
    for name, info in measurements.items():
        if not isinstance(info, dict):
            continue
        rows.append(
            {
                "type": "measurement",
                "name": name,
                "status": info.get("status"),
                "ai_value": info.get("ai_value"),
                "doctor_value": info.get("doctor_value"),
                "difference": info.get("difference"),
                "tolerance": info.get("tolerance"),
                "severity": info.get("severity"),
            }
        )
    structures = verification.get("structure_comparisons") or {}
    for group, entries in structures.items():
        if not isinstance(entries, dict):
            continue
        for name, info in entries.items():
            if not isinstance(info, dict):
                continue
            rows.append(
                {
                    "type": f"structure:{group}",
                    "name": name,
                    "status": info.get("status"),
                    "ai_present": info.get("ai_present"),
                    "ai_confidence": info.get("ai_confidence"),
                    "doctor_mentioned": info.get("doctor_mentioned"),
                    "doctor_negated": info.get("doctor_negated"),
                    "severity": info.get("severity"),
                }
            )
    return rows


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
            ("Comparative Analytics", "Comparative Analytics"),
            ("Settings", "Settings"),
        ]
        for label, page in nav_items:
            is_active = st.session_state.active_page == page
            if st.button(label, width="stretch", key=f"nav_{page}", type="primary" if is_active else "secondary"):
                st.session_state.active_page = page
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-card'><div class='api-title'>API STATUS</div>", unsafe_allow_html=True)
        try:
            api_base = (st.session_state.get("settings") or {}).get("api_base") or API_BASE
            h = requests.get(f"{api_base}/health", timeout=5)
            if h.ok:
                st.markdown("<span class='status-ok'>Online (FastAPI connected)</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='status-bad'>Unavailable</span>", unsafe_allow_html=True)
        except Exception:
            st.markdown("<span class='status-bad'>Unavailable</span>", unsafe_allow_html=True)
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
        st.markdown(
            f"""
            <div class="top-shell">
                <div style="font-size:2.15rem;font-weight:800;line-height:1;">Upload Portal</div>
                <div class="small-kicker">Clinical input and processing</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("+ New Analysis", type="primary", width="stretch"):
            st.session_state.image_bytes = None
            st.session_state.image_name = ""
            st.session_state.report_text = ""
            st.session_state.last_result = None
            st.session_state.last_error = ""
            st.session_state.resolution = {}
            st.rerun()


def render_dashboard() -> None:
    st.markdown("<div class='panel-label'>Verify New Medical Scans</div>", unsafe_allow_html=True)
    st.markdown("<p class='small-kicker'>Pair medical imagery with human-written reports for high-precision cross-validation.</p>", unsafe_allow_html=True)
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
            # no extra pill display

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
        if st.button("Start AI Analysis", type="primary", width="stretch", disabled=not can_run):
            st.session_state.last_error = ""
            with st.spinner("Running AI verification..."):
                try:
                    result = safe_verify(
                        st.session_state.image_name,
                        st.session_state.image_bytes,
                        st.session_state.report_text.strip(),
                    )
                    st.session_state.last_result = result
                    st.session_state.active_page = "Analysis Workspace"
                    st.rerun()
                except Exception as exc:
                    st.session_state.last_error = str(exc)

    if st.session_state.last_error:
        st.error(st.session_state.last_error)

    st.write("")


def render_analysis() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return
    meta = result.get("metadata") or result.get("meta") or {}
    verification = result.get("verification_results") or {}
    counts = verification.get("discrepancy_counts") or {}
    ai_findings = _flatten_ai_findings(result)

    st.markdown("<div class='analysis-wrap'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='dark-shell'>
          <div class='dark-bar'>
            <div>
              <div style='font-weight:800;font-size:1.05rem;'>{meta.get('study','Uploaded Study')}</div>
              <div class='dark-sub'>STUDY ID: {meta.get('study_id','CASE')} · {meta.get('timestamp','')} · <span style='color:rgba(20,143,184,1)'>STAT</span></div>
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
        enhanced_bytes = _resolve_image_bytes(result.get("enhanced_image_path"))
        original_bytes = st.session_state.image_bytes
        if enhanced_bytes or original_bytes:
            tabs = st.tabs(["Enhanced", "Original"])
            with tabs[0]:
                if enhanced_bytes:
                    st.image(enhanced_bytes, width="stretch", caption="Enhanced scan")
                else:
                    st.info("Enhanced image not available.")
            with tabs[1]:
                if original_bytes:
                    st.image(original_bytes, width="stretch", caption="Original scan")
                else:
                    st.info("Original image not available.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            "<div class='dark-panel dark-findings'><div class='dark-head'><div class='dark-title'>AI Findings</div><div style='font-size:0.72rem;color:#9ca3af;background:rgba(148,163,184,0.12);border:1px solid rgba(148,163,184,0.15);padding:2px 8px;border-radius:999px;'>v2.4.1</div></div>",
            unsafe_allow_html=True,
        )
        cards_html = ""
        for idx, f in enumerate(ai_findings):
            active = "active" if idx == 0 else ""
            cards_html += (
                f"<div class='finding-card {active}'>"
                f"<div class='finding-top'><div class='finding-name'>{f.get('name','')}</div><div class='finding-conf'>{int(float(f.get('confidence',0)) * 100)}% CONF.</div></div>"
                f"<div class='finding-text'>{f.get('rationale','')}</div>"
                "</div>"
            )
        st.markdown(cards_html + "</div>", unsafe_allow_html=True)

    with col3:
        st.markdown(
            "<div class='dark-panel dark-report'><div class='dark-head'><div class='dark-title'>Report Views</div><div style='display:flex;gap:6px;'><div style='width:10px;height:10px;border-radius:999px;background:#DF495A;'></div><div style='width:10px;height:10px;border-radius:999px;background:#f59e0b;'></div></div></div>",
            unsafe_allow_html=True,
        )
        tabs = st.tabs(["Doctor Report", "AI Generated Report"])

        with tabs[0]:
            report_text = (result.get("doctor_findings") or {}).get("raw_text") or st.session_state.report_text
            report_html = "<br>".join((report_text or "").splitlines())
            st.markdown("<div class='report-body'>", unsafe_allow_html=True)
            st.markdown(report_html, unsafe_allow_html=True)
            counts = verification.get("discrepancy_counts") or {}
            risk_level = str(verification.get("risk_level") or "-").upper()
            agreement = verification.get("agreement_rate")
            agreement_pct = int(float(agreement or 0) * 100)
            measurement_lines = []
            for name, info in (verification.get("measurement_comparisons") or {}).items():
                if not isinstance(info, dict):
                    continue
                measurement_lines.append(
                    f"{name}: {str(info.get('status','-')).upper()} (AI={info.get('ai_value')}, Doctor={info.get('doctor_value')}, diff={info.get('difference')}, tol={info.get('tolerance')})"
                )
            if not measurement_lines:
                measurement_lines.append("No measurement discrepancies.")
            bullets = "".join([f"<li>{line}</li>" for line in measurement_lines])
            st.markdown(
                f"""
                <div class='note-box'>
                  <div class='note-title'>Discrepancy Detail</div>
                  <div class='note-text'>
                    Clean comparison summary:<br/>
                    Risk Level: <b>{risk_level}</b> &nbsp; Agreement: <b>{agreement_pct}%</b><br/>
                    Counts: matches={counts.get('matches',0)}, omissions={counts.get('omissions',0)}, mismatches={counts.get('mismatches',0)}, overstatements={counts.get('overstatements',0)}<br/>
                    Measurement Comparison:
                    <ul style='margin:8px 0 0 18px; padding:0;'>{bullets}</ul>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with tabs[1]:
            ai_report = result.get("ai_report_text") or ""
            if ai_report:
                parts = [p for p in ai_report.splitlines() if p.strip()]
                preview = "\n".join(parts[:20])
                st.markdown("<div class='raw-report'>", unsafe_allow_html=True)
                st.markdown(preview, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                with st.expander("View full AI report"):
                    st.markdown(
                        f"<div class='raw-report' style='margin:0;'>{ai_report}</div>",
                        unsafe_allow_html=True,
                    )
            else:
                st.info("AI report not available for this case.")

        with st.expander("View full JSON report"):
            st.json(result)

        agreement = verification.get("agreement_rate")
        risk = verification.get("risk_level")
        if agreement is not None or risk:
            st.markdown(
                f"<div class='agreement-row'>Agreement: {int(float(agreement or 0) * 100)}% · Risk: <b>{str(risk or '-').upper()}</b></div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


def render_history() -> None:
    st.markdown("## History & Archive")
    st.markdown("<p class='small-kicker'>Review and export prior verification cases.</p>", unsafe_allow_html=True)
    st.write("")
    try:
        history = fetch_history(limit=50)
        st.session_state.history_cache = history
        rows = []
        for item in history:
            risk = str((item.get("verification_results") or {}).get("risk_level", "-")).upper()
            if risk == "LOW":
                risk_class = "pill-low"
            elif risk == "MEDIUM":
                risk_class = "pill-med"
            elif risk == "HIGH":
                risk_class = "pill-high"
            else:
                risk_class = "pill-unk"
            rows.append(
                {
                    "case_id": item.get("id") or item.get("case_id") or "-",
                    "patient": item.get("patient_id", "-"),
                    "risk": f"<span class='history-pill {risk_class}'>{risk}</span>",
                    "created": item.get("created_at", "-"),
                    "status": item.get("status") or item.get("stage") or "-",
                }
            )
        table_rows = "".join(
            [
                f"<tr><td>{r['case_id']}</td><td>{r['patient']}</td><td>{r['risk']}</td><td>{r['created']}</td><td>{r['status']}</td></tr>"
                for r in rows
            ]
        )
        st.markdown(
            f"""
            <div class='history-wrap'>
              <table class='history-table'>
                <thead>
                  <tr>
                    <th>Case ID</th>
                    <th>Patient Ref</th>
                    <th>Risk</th>
                    <th>Created</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {table_rows}
                </tbody>
              </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.warning(f"Could not load history: {exc}")


def render_discrepancy_resolution() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return

    verification = result.get("verification_results") or {}
    rows = _build_comparison_table(verification)
    items = [r for r in rows if str(r.get("status") or "").lower() in {"mismatch", "omission", "overstatement"}]

    st.markdown("## Discrepancy Resolution")
    st.markdown("<p class='small-kicker'>Accept, dismiss, or modify AI discrepancies before export.</p>", unsafe_allow_html=True)
    if not items:
        st.success("No discrepancies detected for this case.")
        return

    st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
    for idx, item in enumerate(items):
        name = str(item.get("name") or "-")
        status = str(item.get("status") or "-").upper()
        kind = str(item.get("type") or "-")
        key = f"res_{idx}_{kind}_{name}"
        stored = st.session_state.resolution.get(key) or {}
        current = stored.get("action") or "Accept AI"

        c1, c2, c3, c4 = st.columns([2.4, 1.3, 1.0, 1.8])
        with c1:
            st.markdown(f"<div style='font-weight:800;'>{name}</div><div class='subtle' style='font-size:0.88rem;'>{kind}</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='subtle' style='font-size:0.8rem;'>Status</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:800;'>{status}</div>", unsafe_allow_html=True)
        with c3:
            sev = str(item.get("severity") or "-").upper()
            st.markdown("<div class='subtle' style='font-size:0.8rem;'>Severity</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-weight:800;'>{sev}</div>", unsafe_allow_html=True)
        with c4:
            choice = st.selectbox(
                "Resolution",
                ["Accept AI", "Dismiss", "Modify"],
                index=["Accept AI", "Dismiss", "Modify"].index(current),
                key=f"{key}_action",
                label_visibility="collapsed",
            )
            payload: Dict[str, Any] = {
                "action": choice,
                "name": name,
                "type": kind,
                "status": str(item.get("status") or ""),
            }
            if choice == "Modify":
                payload["modified_text"] = st.text_input(
                    "Modified text",
                    value=str(stored.get("modified_text") or ""),
                    key=f"{key}_modified",
                    label_visibility="collapsed",
                    placeholder="Type your corrected statement...",
                )
            st.session_state.resolution[key] = payload

        st.divider()
    st.markdown("</div>", unsafe_allow_html=True)

    b1, b2 = st.columns([1, 1])
    with b1:
        if st.button("Back to Analysis", type="secondary", width="stretch"):
            st.session_state.active_page = "Analysis Workspace"
            st.rerun()
    with b2:
        if st.button("Save & Continue Export", type="primary", width="stretch"):
            st.session_state.active_page = "Final Export"
            st.rerun()


def render_final_export() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return

    st.markdown("## Final Export")
    st.markdown("<p class='small-kicker'>Download a bundle containing the scan metadata, doctor report, AI report, and your resolutions.</p>", unsafe_allow_html=True)

    cfg = st.session_state.export_config or {}
    c1, c2 = st.columns([1.2, 1.0], gap="large")
    with c1:
        st.markdown("### Export Options")
        cfg["include_raw"] = st.checkbox("Include raw backend JSON", value=bool(cfg.get("include_raw", True)))
        cfg["include_tables"] = st.checkbox("Include discrepancy tables", value=bool(cfg.get("include_tables", True)))
        cfg["include_resolution"] = st.checkbox("Include discrepancy resolutions", value=bool(cfg.get("include_resolution", True)))
        st.session_state.export_config = cfg

        verification = result.get("verification_results") or {}
        counts = verification.get("discrepancy_counts") or {}
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Mismatch", int(counts.get("mismatches") or 0))
        with m2:
            st.metric("Omission", int(counts.get("omissions") or 0))
        with m3:
            st.metric("Risk", str(verification.get("risk_level") or "-").upper())

    with c2:
        payload: Dict[str, Any] = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "uploaded_file": st.session_state.image_name,
            "doctor_report": st.session_state.report_text,
            "ai_report": result.get("ai_report_text") or "",
            "export_config": cfg,
        }
        if cfg.get("include_resolution"):
            payload["resolution"] = st.session_state.resolution
        if cfg.get("include_tables"):
            payload["comparison_table"] = _build_comparison_table(result.get("verification_results") or {})
        if cfg.get("include_raw"):
            payload["result"] = result

        st.download_button(
            "Download JSON Bundle",
            data=st.session_state.get("_export_json") or "",
            file_name=f"radverify_export_{int(datetime.now().timestamp())}.json",
            mime="application/json",
            width="stretch",
            disabled=True,
        )
        export_json = ""
        try:
            import json

            export_json = json.dumps(payload, indent=2)
        except Exception:
            export_json = str(payload)
        st.session_state["_export_json"] = export_json
        st.download_button(
            "Download JSON Bundle",
            data=export_json,
            file_name=f"radverify_export_{int(datetime.now().timestamp())}.json",
            mime="application/json",
            width="stretch",
        )

    with st.expander("Preview export"):
        st.json(payload)


def render_help_center() -> None:
    st.markdown("## Help Center")
    st.markdown("<p class='small-kicker'>Quick answers and workflow guidance.</p>", unsafe_allow_html=True)
    q = st.text_input("Search help", placeholder="Try: upload scans, discrepancy resolution, export...")

    articles = [
        {"title": "Uploading scans", "body": "Use Dashboard to upload a scan and paste the doctor report. Then click Start AI Analysis."},
        {"title": "Discrepancy resolution", "body": "Open Discrepancy Resolution to accept, dismiss, or modify mismatches/omissions."},
        {"title": "Final export", "body": "Use Final Export to download a JSON bundle for archiving."},
        {"title": "Backend connection", "body": "If FastAPI is offline, the app will automatically use demo results so you can keep testing the UI."},
        {"title": "Troubleshooting", "body": "If you see errors, check Settings for API base URL and API key, then rerun analysis."},
    ]
    if q:
        qq = q.strip().lower()
        articles = [a for a in articles if qq in a["title"].lower() or qq in a["body"].lower()]

    cols = st.columns(2, gap="large")
    for i, a in enumerate(articles):
        with cols[i % 2]:
            st.markdown(
                f"<div class='table-shell'><div style='font-family:Lexend,sans-serif;font-weight:900;margin-bottom:6px;'>{a['title']}</div><div class='subtle'>{a['body']}</div></div>",
                unsafe_allow_html=True,
            )


def render_comparative_analytics() -> None:
    result = st.session_state.last_result
    st.markdown("## Comparative Analytics")
    st.markdown("<p class='small-kicker'>Summaries and tables based on the most recent analysis.</p>", unsafe_allow_html=True)
    if not result:
        st.info("Run analysis from Dashboard first.")
        return

    verification = result.get("verification_results") or {}
    counts = verification.get("discrepancy_counts") or {}
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Agreement", f"{int(float(verification.get('agreement_rate') or 0) * 100)}%")
    with c2:
        st.metric("Risk", str(verification.get("risk_level") or "-").upper())
    with c3:
        st.metric("Mismatches", int(counts.get("mismatches") or 0))
    with c4:
        st.metric("Omissions", int(counts.get("omissions") or 0))

    st.write("")
    st.markdown("### Comparison Table")
    table = _build_comparison_table(verification)
    if table:
        st.dataframe(table, width="stretch", hide_index=True)
    else:
        st.info("No comparison rows available.")


def render_settings() -> None:
    st.markdown("## Settings")
    st.markdown("<p class='small-kicker'>Configure backend connectivity and app behavior.</p>", unsafe_allow_html=True)
    s = st.session_state.settings or {}
    c1, c2 = st.columns([1.1, 0.9], gap="large")
    with c1:
        s["api_base"] = st.text_input("API base URL", value=str(s.get("api_base") or API_BASE))
        s["api_key"] = st.text_input("API key", value=str(s.get("api_key") or ""), type="password")
        s["prefer_backend"] = st.checkbox("Prefer backend (fallback to demo if unavailable)", value=bool(s.get("prefer_backend", True)))
        s["backend_timeout_sec"] = st.number_input(
            "Backend timeout (seconds)",
            min_value=5,
            max_value=600,
            value=int(s.get("backend_timeout_sec") or 180),
            step=5,
        )
        st.session_state.settings = s

        if st.button("Test Connection", type="secondary", width="stretch"):
            try:
                h = requests.get(f"{s['api_base']}/health", timeout=5)
                if h.ok:
                    st.success("Backend is reachable.")
                else:
                    st.warning("Backend responded but is not healthy.")
            except Exception as exc:
                st.warning(f"Could not reach backend: {exc}")

    with c2:
        st.markdown("### Current Run")
        st.markdown(
            f"<div class='table-shell'><div style='font-weight:900;'>Active page</div><div class='subtle'>{st.session_state.active_page}</div></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='table-shell'><div style='font-weight:900;'>Uploaded scan</div><div class='subtle'>{st.session_state.image_name or '-'}</div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Clear errors", type="secondary", width="stretch"):
            st.session_state.last_error = ""
            st.rerun()


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
    elif page == "Comparative Analytics":
        render_comparative_analytics()
    else:
        render_settings()


if __name__ == "__main__":
    main()
