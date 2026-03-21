"""RAVEN Streamlit UI matching the requested reference interface."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any, Dict, List, Optional

import streamlit as st


PAGES: Dict[str, Dict[str, str]] = {
    "Dashboard": {"title": "Upload Portal", "sub": "Clinical input and processing"},
    "Analysis Workspace": {"title": "Analysis Workspace", "sub": "AI findings and report comparison"},
    "Discrepancy Resolution": {"title": "Discrepancy Resolution", "sub": "Accept, dismiss, or modify AI findings"},
    "Final Export": {"title": "Final Export", "sub": "Finalize and archive verified report"},
    "Protocol Library": {"title": "Diagnostic Protocol Library", "sub": "Configure and deploy clinical AI sensitivity thresholds"},
    "History & Archive": {"title": "History & Archive", "sub": "Compliance-grade audit retrieval"},
    "Help Center": {"title": "Help Center", "sub": "Tutorials and support channels"},
}


def demo_protocols() -> List[Dict[str, Any]]:
    return [
        {
            "id": "PROTO-ER-TRAUMA",
            "name": "Emergency Trauma",
            "department": "Emergency",
            "creator": "System Defaults",
            "tag": "Urgent Care",
            "accent": "#ea580c",
            "metric_a_label": "Fracture Sensitivity",
            "metric_a": 0.98,
            "metric_b_label": "Soft Tissue Specificity",
            "metric_b": 0.72,
            "updated": "Updated 1d ago",
            "description": "Optimized for rapid detection of acute fractures, dislocations, and internal hemorrhaging in ER settings.",
        },
        {
            "id": "PROTO-ROUTINE",
            "name": "Routine Screening",
            "department": "Radiology",
            "creator": "Dr. Aris (Lead)",
            "tag": "Standard",
            "accent": "#1f66ad",
            "metric_a_label": "Pathology Detection",
            "metric_a": 0.85,
            "metric_b_label": "False Positive Rate",
            "metric_b": 0.04,
            "updated": "Updated 2h ago",
            "description": "Balanced sensitivity for early pathology detection. Focus on longitudinal comparison and noise reduction.",
        },
        {
            "id": "PROTO-PEDS-CHEST",
            "name": "Pediatric Chest",
            "department": "Pediatrics",
            "creator": "Dr. Aris (Lead)",
            "tag": "Pediatric",
            "accent": "#2563eb",
            "metric_a_label": "Specificity for Nodules",
            "metric_a": 0.94,
            "metric_b_label": "Noise Filtering",
            "metric_b": 0.90,
            "updated": "Updated 5d ago",
            "description": "High specificity to reduce false positives in pediatric cases. Enhanced bone suppression for clearer lung views.",
        },
        {
            "id": "PROTO-ONC-FU",
            "name": "Oncology Follow-up",
            "department": "Oncology",
            "creator": "Clinic Admin",
            "tag": "Advanced",
            "accent": "#7c3aed",
            "metric_a_label": "RECIST Accuracy",
            "metric_a": 0.99,
            "metric_b_label": "Volumetric Drift",
            "metric_b": 0.20,
            "updated": "Updated 2w ago",
            "description": "Strict specificity for volumetric measurement and RECIST 1.1 compliance in tracking tumor growth.",
        },
        {
            "id": "PROTO-CARDIAC-CT",
            "name": "Cardiac CT",
            "department": "Radiology",
            "creator": "Clinic Admin",
            "tag": "Cardiovascular",
            "accent": "#e11d48",
            "metric_a_label": "Calcium Scoring",
            "metric_a": 0.92,
            "metric_b_label": "Motion De-blur",
            "metric_b": 0.85,
            "updated": "Updated 3w ago",
            "description": "Calcium scoring automation and motion artifact correction for coronary artery assessments.",
        },
    ]


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


def mock_verify(file_name: str, report_text: str, study_date: str) -> Dict[str, Any]:
    now = datetime.now().strftime("%b %d, %I:%M %p")
    enhanced = (
        report_text.strip()
        + "\n\n---\nAI Enhanced Draft (demo):\n"
        + "1) Correlate with clinical presentation and prior imaging if available.\n"
        + "2) Consider follow-up imaging if symptoms persist.\n"
        + "3) Document key negative findings explicitly to reduce ambiguity.\n"
    ).strip()
    return {
        "meta": {
            "file_name": file_name,
            "generated_at": now,
            "study": "DOE, JOHN | 45Y | Chest X-Ray (PA View)",
            "study_id": "88291-XA",
            "timestamp": f"{study_date} · 09:42 AM",
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
            "ai_enhanced_text": enhanced,
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
        "scans": [],
        "active_scan_idx": 0,
        "image_bytes": None,
        "image_name": "",
        "report_text": "",
        "study_date": datetime.now().date(),
        "enhanced_report_text": "",
        "last_result": None,
        "last_error": "",
        "history_cache": demo_history(),
        "protocols": demo_protocols(),
        "active_protocol_id": "PROTO-ROUTINE",
        "resolution": {},
        "export_config": {
            "heatmap": True,
            "summary": True,
            "narrative": True,
            "discrepancy": True,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


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
        .dark-grid { display:grid; grid-template-columns: 1.35fr 0.82fr 1fr; min-height: 580px; }
        .dark-panel { border-right:1px solid #2a2e33; }
        .dark-panel:last-child { border-right:none; }
        .dark-viewer { background: radial-gradient(circle at center, #2c2f33 0%, #17191c 100%); padding: 16px; display:flex; align-items:center; justify-content:center; }
        .dark-findings { background:#1a1c1e; padding: 0; }
        .dark-report { background:#1e2124; padding: 0; }
        .dark-head { padding: 12px 14px; border-bottom:1px solid #2a2e33; display:flex; justify-content:space-between; align-items:center; }
        .dark-title { font-size:0.78rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#9ca3af; }
        .finding-card { margin: 12px 14px; padding: 12px; border-radius:12px; border-left:4px solid rgba(148,163,184,0.4); background: rgba(30,41,59,0.35); border: 1px solid rgba(148,163,184,0.14); }
        .finding-card.active { border-left-color: rgba(20,143,184,1); box-shadow: 0 0 16px rgba(20,143,184,0.2); border-color: rgba(20,143,184,0.22); }
        .finding-top { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; }
        .finding-name { font-weight:800; color:#f8fafc; }
        .finding-conf { font-size:0.68rem; font-weight:800; color: rgba(20,143,184,1); background: rgba(20,143,184,0.15); border:1px solid rgba(20,143,184,0.2); padding: 3px 8px; border-radius: 999px; white-space:nowrap; }
        .finding-text { margin-top: 8px; color:#94a3b8; font-size:0.86rem; line-height:1.4; }
        .report-body { padding: 14px; color:#cbd5e1; font-size:1.06rem; line-height:1.65; }
        .note-box { margin: 14px; padding: 14px; border-radius: 14px; background: rgba(223,73,90,0.08); border:1px solid rgba(223,73,90,0.16); }
        .note-title { font-size:0.74rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; color:#fb7185; }
        .note-text { margin-top: 8px; color:#cbd5e1; }
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
            ("Protocol Library", "Protocol Library"),
            ("History & Archive", "History & Archive"),
            ("Help Center", "Help Center"),
        ]
        for label, page in nav_items:
            is_active = st.session_state.active_page == page
            if st.button(label, width="stretch", key=f"nav_{page}", type="primary" if is_active else "secondary"):
                st.session_state.active_page = page
                st.rerun()

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-card'><div class='api-title'>DEMO MODE</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtle' style='font-size:0.88rem;'>Offline · Mock data</div>", unsafe_allow_html=True)
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
        if st.button("+ New Analysis", type="primary", width="stretch"):
            st.session_state.scans = []
            st.session_state.active_scan_idx = 0
            st.session_state.image_bytes = None
            st.session_state.image_name = ""
            st.session_state.report_text = ""
            st.session_state.enhanced_report_text = ""
            st.session_state.last_result = None
            st.session_state.last_error = ""
            st.rerun()


def render_dashboard() -> None:
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
        files = st.file_uploader(
            "Drag and drop files here. Support for DICOM, JPEG, PNG",
            type=["png", "jpg", "jpeg", "dcm"],
            label_visibility="collapsed",
            accept_multiple_files=True,
        )

        if files:
            scans = [{"name": f.name, "bytes": f.getvalue()} for f in files]
            if scans != st.session_state.scans:
                st.session_state.scans = scans
                st.session_state.active_scan_idx = 0

        if st.session_state.scans:
            names = [s.get("name", "Scan") for s in st.session_state.scans]
            if len(names) > 1:
                st.session_state.active_scan_idx = st.selectbox(
                    "Active scan",
                    list(range(len(names))),
                    format_func=lambda i: names[i],
                    index=min(int(st.session_state.active_scan_idx or 0), len(names) - 1),
                    key="active_scan_select",
                )

            idx = int(st.session_state.active_scan_idx or 0)
            active = st.session_state.scans[idx]
            st.session_state.image_bytes = active.get("bytes")
            st.session_state.image_name = active.get("name", "")

            st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-family:Lexend,sans-serif;font-weight:900;margin-bottom:8px;'>Selected scan</div><div class='subtle' style='margin-bottom:10px;'>{st.session_state.image_name}</div>",
                unsafe_allow_html=True,
            )
            st.image(st.session_state.image_bytes, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("You can upload 4+ scans at once. Select the active scan to analyze.")

    with right:
        st.markdown("### 2. Human-Written Radiology Report")
        st.session_state.study_date = st.date_input(
            "Study date",
            value=st.session_state.study_date,
        )
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
                    date_str = st.session_state.study_date.strftime("%b %d, %Y")
                    result = mock_verify(st.session_state.image_name, st.session_state.report_text.strip(), date_str)
                    st.session_state.last_result = result
                    st.session_state.enhanced_report_text = (result.get("report") or {}).get("ai_enhanced_text") or ""
                    st.session_state.active_page = "Analysis Workspace"

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
              <div class='dark-sub'>STUDY ID: {meta.get('study_id','')} · {meta.get('timestamp','')} · <span style='color:rgba(20,143,184,1)'>STAT</span></div>
            </div>
            <div style='display:flex;gap:8px;flex-wrap:wrap;'>
              <span style='padding:6px 10px;border-radius:999px;background:rgba(223,73,90,0.14);border:1px solid rgba(223,73,90,0.25);color:#fb7185;font-weight:800;font-size:0.75rem;'>Mismatch {int(counts.get('mismatches') or 0)}</span>
              <span style='padding:6px 10px;border-radius:999px;background:rgba(245,158,11,0.14);border:1px solid rgba(245,158,11,0.26);color:#fbbf24;font-weight:800;font-size:0.75rem;'>Omission {int(counts.get('omissions') or 0)}</span>
            </div>
          </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1.35, 0.82, 1], gap="small")

    with col1:
        st.markdown("<div class='dark-panel dark-viewer'>", unsafe_allow_html=True)
        if st.session_state.image_name:
            st.markdown(
                f"<div style='position:absolute;left:0;right:0;margin-top:-2px;padding:10px 12px;color:#cbd5e1;font-weight:800;font-size:0.95rem;'>Uploaded: {st.session_state.image_name}</div>",
                unsafe_allow_html=True,
            )
        if st.session_state.image_bytes:
            st.image(st.session_state.image_bytes, width="stretch")
            if st.session_state.scans and len(st.session_state.scans) > 1:
                st.markdown(
                    f"<div style='margin-top:10px;color:#9ca3af;font-size:0.82rem;'>Active scan {int(st.session_state.active_scan_idx or 0) + 1} of {len(st.session_state.scans)}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.image(
                "https://lh3.googleusercontent.com/aida-public/AB6AXuD57tZCNaKTyMhcARHi_e-_h-n7kbEwkDiu0bPOhG77MnZk9-Grvq1m0lT1ibcLZrbmk84D_B0As5R3nMwHzzNmBNqB40E0o9u_T49Cjw2KN9nPWd2dBribnY_2lgYQsbde1AKX4Y8NnbtkxyGjc997jLmqBRPTBz7TiVNZIuyjmnY2Le6GUrz5UVhDi_a-pN8lc9vGjkcEsJIONcykPB4qNQF1zdKqQ2UVYPH2WRgXlHtrx0lAe9o0sUJ3AcKDswdk7rd-07p_FxI",
                width="stretch",
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
        view = st.radio(
            "Report view",
            ["Doctor Report", "AI Enhanced Report"],
            horizontal=True,
            label_visibility="collapsed",
        )
        if view == "Doctor Report":
            st.markdown(
                "<div class='dark-panel dark-report'><div class='dark-head'><div class='dark-title'>Doctor Report</div><div style='display:flex;gap:6px;'><div style='width:10px;height:10px;border-radius:999px;background:#DF495A;'></div><div style='width:10px;height:10px;border-radius:999px;background:#f59e0b;'></div></div></div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div class='report-body'>", unsafe_allow_html=True)
            st.markdown((result.get("report") or {}).get("highlighted_html") or "", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div class='note-box'>
                  <div class='note-title'>Discrepancy Detail</div>
                  <div class='note-text'>{cmp.get('comparison_report_text','')}</div>
                </div>
                """ + "</div></div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='dark-panel dark-report'><div class='dark-head'><div class='dark-title'>AI Enhanced Report</div><div style='font-size:0.72rem;color:#9ca3af;'>Draft</div></div>",
                unsafe_allow_html=True,
            )
            st.session_state.enhanced_report_text = st.text_area(
                "AI Enhanced Report",
                value=st.session_state.enhanced_report_text,
                label_visibility="collapsed",
                height=430,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns([1.2, 1.2, 1.6])
    with b1:
        if st.button("Open Resolution Workspace", type="secondary", width="stretch"):
            st.session_state.active_page = "Discrepancy Resolution"
            st.rerun()
    with b2:
        if st.button("Proceed to Export", type="secondary", width="stretch"):
            st.session_state.active_page = "Final Export"
            st.rerun()
    with b3:
        st.markdown(
            f"<div class='subtle' style='text-align:right;padding-top:10px;'>Agreement: {int(float(cmp.get('agreement_rate',0)) * 100)}% · Risk: <b>{str(cmp.get('risk_level','-')).upper()}</b></div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_history() -> None:
    st.markdown("## History & Archive")
    history = st.session_state.history_cache
    st.dataframe(history, width="stretch", hide_index=True)


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


def render_protocol_library() -> None:
    st.markdown(
        """
        <div class='panel-label' style='font-size:2.35rem;margin-bottom:.2rem;'>Diagnostic Protocol Library</div>
        <p class='small-kicker'>Configure and deploy clinical AI sensitivity thresholds across the network.</p>
        """,
        unsafe_allow_html=True,
    )

    t1, t2, t3 = st.columns([1.4, 1.4, 1.0])
    with t1:
        q = st.text_input(
            "Search",
            placeholder="Search protocols by clinical indication...",
            label_visibility="collapsed",
            key="proto_search",
        )
    with t2:
        dept = st.selectbox(
            "Department",
            ["All Departments", "Radiology", "Emergency", "Pediatrics", "Oncology"],
            index=0,
            key="proto_dept",
        )
    with t3:
        creator = st.selectbox(
            "Creator",
            ["All Creators", "Dr. Aris (Lead)", "System Defaults", "Clinic Admin"],
            index=0,
            key="proto_creator",
        )

    a1, a2, a3 = st.columns([1.05, 1.05, 1.1])
    with a1:
        export_payload = {
            "active_protocol_id": st.session_state.active_protocol_id,
            "protocols": st.session_state.protocols,
        }
        st.download_button(
            "Export All",
            data=json.dumps(export_payload, indent=2),
            file_name="raven_protocols.json",
            mime="application/json",
            width="stretch",
        )
    with a2:
        create_open = st.button("Create New Protocol", type="primary", width="stretch")
    with a3:
        st.markdown(
            """
            <div class='table-shell' style='margin-top:0;'>
              <div class='metric-label'>Active Preset</div>
              <div class='metric-value' style='font-size:1.35rem;margin-top:6px;'>"""
            + f"{st.session_state.active_protocol_id}"
            + """</div>
              <div class='metric-sub'>Quick Apply updates demo state only</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if create_open:
        st.session_state["proto_create_open"] = True

    if st.session_state.get("proto_create_open"):
        st.markdown("<div class='table-shell'>", unsafe_allow_html=True)
        st.markdown("### Create New Protocol")
        c1, c2 = st.columns([1, 1])
        with c1:
            new_name = st.text_input("Protocol name", value="", key="proto_new_name")
            new_dept = st.selectbox(
                "Department",
                ["Radiology", "Emergency", "Pediatrics", "Oncology"],
                index=0,
                key="proto_new_dept",
            )
        with c2:
            new_creator = st.selectbox(
                "Creator",
                ["Clinic Admin", "Dr. Aris (Lead)", "System Defaults"],
                index=0,
                key="proto_new_creator",
            )
            new_tag = st.selectbox(
                "Tag",
                ["Standard", "Urgent Care", "Advanced", "Pediatric", "Cardiovascular"],
                index=0,
                key="proto_new_tag",
            )
        new_desc = st.text_area("Description", value="", height=110, key="proto_new_desc")
        st.markdown("**Target thresholds (demo)**")
        m1, m2 = st.columns([1, 1])
        with m1:
            a_val = st.slider(
                "Sensitivity",
                min_value=0.50,
                max_value=0.99,
                value=0.86,
                step=0.01,
                key="proto_new_sens",
            )
        with m2:
            b_val = st.slider(
                "Specificity",
                min_value=0.50,
                max_value=0.99,
                value=0.78,
                step=0.01,
                key="proto_new_spec",
            )

        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("Cancel", type="secondary", width="stretch", key="proto_new_cancel"):
                st.session_state["proto_create_open"] = False
                st.rerun()
        with b2:
            if st.button("Save Protocol", type="primary", width="stretch", key="proto_new_save"):
                pid = f"PROTO-{int(datetime.now().timestamp())}"
                st.session_state.protocols = [
                    {
                        "id": pid,
                        "name": (new_name or "Custom Protocol").strip(),
                        "department": new_dept,
                        "creator": new_creator,
                        "tag": new_tag,
                        "accent": "#1f66ad",
                        "metric_a_label": "Sensitivity",
                        "metric_a": float(a_val),
                        "metric_b_label": "Specificity",
                        "metric_b": float(b_val),
                        "updated": "Updated just now",
                        "description": (new_desc or "Custom diagnostic protocol.").strip(),
                    },
                    *st.session_state.protocols,
                ]
                st.session_state.active_protocol_id = pid
                st.session_state["proto_create_open"] = False
                st.success("Protocol created (demo).")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    protocols = st.session_state.protocols
    if q:
        ql = q.lower().strip()
        protocols = [
            p
            for p in protocols
            if ql in str(p.get("name", "")).lower() or ql in str(p.get("description", "")).lower()
        ]
    if dept != "All Departments":
        protocols = [p for p in protocols if p.get("department") == dept]
    if creator != "All Creators":
        protocols = [p for p in protocols if p.get("creator") == creator]

    st.write("")
    if not protocols:
        st.info("No protocols match your filters.")
        return

    cols = st.columns(3, gap="large")
    for i, p in enumerate(protocols):
        with cols[i % 3]:
            is_active = st.session_state.active_protocol_id == p.get("id")
            a = str(p.get("accent") or "#1f66ad")
            tag = str(p.get("tag") or "")
            st.markdown(
                """
                <div class='table-shell' style='position:relative;'>
                  <div style='display:flex;align-items:flex-start;justify-content:space-between;gap:12px;'>
                    <div style='display:flex;gap:10px;align-items:center;'>
                      <div style='width:38px;height:38px;border-radius:12px;background:"""
                + a
                + """;opacity:0.12; border:1px solid rgba(17,24,39,0.08);'></div>
                      <div>
                        <div style='font-family:Lexend,sans-serif;font-weight:900;font-size:1.08rem;'>"""
                + str(p.get("name") or "")
                + """</div>
                        <div class='subtle' style='font-size:0.92rem;'>"""
                + str(p.get("description") or "")
                + """</div>
                      </div>
                    </div>
                    <div class='pill' style='background:rgba(31,102,173,0.10);border:1px solid rgba(31,102,173,0.18);color:#1f66ad;'>"""
                + tag
                + """</div>
                  </div>
                  <div style='margin-top:12px;'>
                    <div class='subtle' style='font-size:0.85rem;font-weight:700;'>"""
                + str(p.get("metric_a_label") or "Metric A")
                + """</div>
                    <div style='display:flex;align-items:center;justify-content:space-between;margin-top:4px;'>
                      <div style='font-family:Lexend,sans-serif;font-weight:900;font-size:1.35rem;'>"""
                + f"{int(float(p.get('metric_a') or 0) * 100)}%"
                + """</div>
                      <div class='subtle' style='font-size:0.85rem;'>"""
                + str(p.get("department") or "")
                + """</div>
                    </div>
                    <div style='height:8px;background:rgba(17,24,39,0.06);border-radius:999px;overflow:hidden;margin-top:8px;'>
                      <div style='height:100%;width:"""
                + f"{int(float(p.get('metric_a') or 0) * 100)}%"
                + """;background:rgba(31,102,173,0.85);'></div>
                    </div>

                    <div style='margin-top:12px;' class='subtle'>"""
                + str(p.get("metric_b_label") or "Metric B")
                + """</div>
                    <div style='display:flex;align-items:center;justify-content:space-between;margin-top:4px;'>
                      <div style='font-family:Lexend,sans-serif;font-weight:900;font-size:1.12rem;'>"""
                + f"{int(float(p.get('metric_b') or 0) * 100)}%"
                + """</div>
                      <div class='subtle' style='font-size:0.85rem;'>"""
                + str(p.get("creator") or "")
                + """</div>
                    </div>
                    <div style='height:8px;background:rgba(17,24,39,0.06);border-radius:999px;overflow:hidden;margin-top:8px;'>
                      <div style='height:100%;width:"""
                + f"{int(float(p.get('metric_b') or 0) * 100)}%"
                + """;background:rgba(100,116,139,0.55);'></div>
                    </div>
                  </div>
                """
                + ("<div style='position:absolute;top:12px;right:12px;' class='pill pill-ok'>Active</div>" if is_active else "")
                + """
                </div>
                """,
                unsafe_allow_html=True,
            )

            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("Edit", type="secondary", width="stretch", key=f"proto_edit_{p.get('id')}"):
                    st.info("Edit flow can be added next (demo).")
            with b2:
                label = "In Use" if is_active else "Quick Apply"
                if st.button(
                    label,
                    type="primary" if not is_active else "secondary",
                    width="stretch",
                    key=f"proto_apply_{p.get('id')}",
                ):
                    if not is_active:
                        st.session_state.active_protocol_id = str(p.get("id"))
                        st.success("Preset applied (demo).")
                        st.rerun()


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
            stored = st.session_state.resolution.get(key) or {}
            current = stored.get("action") or "Accept AI"
            choice = st.selectbox(
                "Resolution",
                ["Accept AI", "Dismiss", "Modify"],
                index=["Accept AI", "Dismiss", "Modify"].index(current),
                key=f"{key}_action",
                label_visibility="collapsed",
            )
            payload = {"action": choice, "finding": item.get("name", ""), "status": item.get("status", "")}
            if choice == "Modify":
                payload["modified_text"] = st.text_input(
                    "Modified text",
                    value=str(stored.get("modified_text") or ""),
                    key=f"{key}_modified",
                    label_visibility="collapsed",
                    placeholder="Type your corrected sentence...",
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
            "study_date": st.session_state.study_date.strftime("%b %d, %Y") if st.session_state.study_date else "",
            "uploaded_file": st.session_state.image_name,
            "original_report": st.session_state.report_text,
            "ai_enhanced_report": st.session_state.enhanced_report_text,
            "export_config": cfg,
            "resolution": st.session_state.resolution,
            "result": result,
        }
        st.download_button(
            "Download JSON Bundle",
            data=json.dumps(payload, indent=2),
            file_name=f"raven_export_{int(datetime.now().timestamp())}.json",
            mime="application/json",
            width="stretch",
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
    elif page == "Protocol Library":
        render_protocol_library()
    elif page == "Help Center":
        render_help_center()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()