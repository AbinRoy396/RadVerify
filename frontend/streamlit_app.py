"""RAVEN Streamlit UI matching the requested reference interface."""

from __future__ import annotations

from datetime import datetime
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

        [data-testid="stFileUploaderDropzone"] {
          border:1px solid #cad8e7 !important;
          border-radius:12px !important;
          background:#eef3f8 !important;
          min-height:320px;
        }
        [data-testid="stFileUploaderDropzone"] button {
          background:#1f66ad !important;
          color:#fff !important;
          border:1px solid #1f66ad !important;
          border-radius:10px !important;
        }
        .table-shell {
          margin-top:8px;
          border:1px solid #dce3ea;
          border-radius:12px;
          background:#fff;
          padding:12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_headers() -> Dict[str, str]:
    return {"X-API-Key": API_KEY}


def call_verify(file_name: str, image_bytes: bytes, report_text: str) -> Dict[str, Any]:
    files = {"scan": (file_name, image_bytes, "application/octet-stream")}
    data = {"report": report_text, "enhance": "true"}
    resp = requests.post(f"{API_BASE}/verify", files=files, data=data, headers=api_headers(), timeout=180)
    resp.raise_for_status()
    return resp.json()


def fetch_history(limit: int = 10) -> List[Dict[str, Any]]:
    resp = requests.get(f"{API_BASE}/history", headers=api_headers(), params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    return resp.json()


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
            if st.button(label, use_container_width=True, key=f"nav_{page}", type="primary" if is_active else "secondary"):
                st.session_state.active_page = page
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-card'><div class='api-title'>API STATUS</div>", unsafe_allow_html=True)
        try:
            h = requests.get(f"{API_BASE}/health", timeout=5)
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
        if st.button("+ New Analysis", type="primary", use_container_width=True):
            st.session_state.image_bytes = None
            st.session_state.image_name = ""
            st.session_state.report_text = ""
            st.session_state.last_result = None
            st.session_state.last_error = ""
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
                    result = call_verify(
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
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown("### Recent Activity")
    with h2:
        st.markdown("<div style='text-align:right;color:#1f66ad;font-weight:700;margin-top:8px;'>View Full History</div>", unsafe_allow_html=True)
    try:
        history = fetch_history(limit=10)
        st.session_state.history_cache = history
        rows = []
        for item in history:
            rows.append(
                {
                    "Case ID": item.get("id") or item.get("case_id"),
                    "Patient Ref": item.get("patient_id", "-"),
                    "Risk": str((item.get("verification_results") or {}).get("risk_level", "-")).upper(),
                    "Created": item.get("created_at", "-"),
                }
            )
        st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as exc:
        st.warning(f"Could not load history: {exc}")


def render_analysis() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return
    st.markdown("## Analysis Workspace")
    st.json(result.get("verification_results", {}))


def render_history() -> None:
    st.markdown("## History & Archive")
    history = st.session_state.history_cache
    if not history:
        try:
            history = fetch_history(limit=50)
        except Exception as exc:
            st.error(str(exc))
            return
    st.dataframe(history, use_container_width=True)


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
        render_simple("Discrepancy Resolution")
    elif page == "Final Export":
        render_simple("Final Export")
    elif page == "Help Center":
        render_simple("Help Center")
    elif page == "Comparative Analytics":
        render_simple("Comparative Analytics")
    else:
        render_simple("Settings")


if __name__ == "__main__":
    main()

