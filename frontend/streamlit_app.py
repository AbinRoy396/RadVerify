"""RAVEN Streamlit UI matching the requested reference interface."""

from __future__ import annotations

from datetime import datetime
import json
import time
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
        "history_cache": [],
        "settings": {
            "api_base": API_BASE,
            "api_key": API_KEY,
            "timeout": 180,
            "export_defaults": {
                "include_ai": True,
                "include_doc": True,
                "include_images": True,
                "include_table": True,
            },
            "preferences": {
                "theme": "Light",
                "language": "English",
                "enable_notifications": True,
                "show_advanced": True,
            },
            "security": {
                "two_factor": False,
                "retention_days": 365,
            },
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
        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button[kind="secondary"] {
          background:#ffffff !important;
          border:1px solid #d5deea !important;
          color:#1f2937 !important;
          box-shadow:none !important;
        }
        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button[kind="secondary"]:hover {
          background:#f3f7fb !important;
          border-color:#cbd6e3 !important;
          color:#1f2937 !important;
        }
        [data-testid="stVerticalBlock"]:not([data-testid="stSidebar"]) .stButton > button:disabled {
          background:#f1f5f9 !important;
          border:1px solid #e2e8f0 !important;
          color:#94a3b8 !important;
          opacity:1 !important;
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
        [data-testid="stTextArea"] label,
        [data-testid="stSelectbox"] label {
          color:#1f2937 !important;
          font-weight:700 !important;
        }
        [data-testid="stTextArea"] textarea::placeholder {
          color:#94a3b8 !important;
          opacity:1 !important;
        }
        [data-testid="stTextInput"] input {
          border-radius:12px !important;
          border:1px solid #cbd5e1 !important;
          background:#ffffff !important;
          color:#0f172a !important;
          box-shadow:none !important;
          padding:10px 12px !important;
        }
        [data-testid="stTextInput"] input:focus {
          border-color:#1f66ad !important;
          box-shadow:0 0 0 2px rgba(31,102,173,0.18) !important;
        }
        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stCheckbox"] label,
        [data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stToggle"] label,
        [data-testid="stToggle"] [data-testid="stMarkdownContainer"] p {
          color:#1f2937 !important;
          font-weight:700 !important;
          opacity:1 !important;
        }
        [data-testid="stNumberInput"] input {
          border-radius:12px !important;
          border:1px solid #cbd5e1 !important;
          background:#ffffff !important;
          color:#0f172a !important;
          box-shadow:none !important;
        }
        [data-testid="stNumberInput"] input:focus {
          border-color:#1f66ad !important;
          box-shadow:0 0 0 2px rgba(31,102,173,0.18) !important;
        }
        [data-testid="stNumberInput"] button {
          color:#475569 !important;
        }
        [data-testid="stToggle"] [role="switch"] {
          background:#e2e8f0 !important;
          border:1px solid #cbd5e1 !important;
        }
        [data-testid="stToggle"] [role="switch"][aria-checked="true"] {
          background:#1f66ad !important;
          border-color:#1f66ad !important;
        }
        [data-testid="stToggle"] [role="switch"] > div {
          background:#ffffff !important;
        }
        [data-testid="stCheckbox"] svg {
          color:#1f66ad !important;
        }
        [data-testid="stSelectbox"] div[role="combobox"] {
          border-radius:12px !important;
          border:1px solid #cbd5e1 !important;
          background:#ffffff !important;
          color:#0f172a !important;
        }
        [data-testid="stSelectbox"] div[role="combobox"]:focus-within {
          border-color:#1f66ad !important;
          box-shadow:0 0 0 2px rgba(31,102,173,0.18) !important;
        }
        [data-testid="stSelectbox"] div[role="combobox"] * {
          color:#0f172a !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
          background:#ffffff !important;
          color:#0f172a !important;
          border-color:#cbd5e1 !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] span,
        [data-testid="stSelectbox"] [data-baseweb="select"] input {
          color:#0f172a !important;
          -webkit-text-fill-color:#0f172a !important;
        }
        [data-testid="stSelectbox"] [data-baseweb="select"] svg {
          color:#475569 !important;
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
        .settings-hero {
          background: linear-gradient(135deg, #e8f1ff 0%, #ffffff 60%);
          border:1px solid #dbe7f6;
          border-radius:16px;
          padding:18px 20px;
          box-shadow: 0 12px 28px rgba(31, 102, 173, 0.12);
        }
        .settings-hero-title {
          font-size:1.6rem;
          font-weight:800;
          color:#0f2a44;
          margin:0;
        }
        .settings-hero-sub {
          margin-top:6px;
          color:#5b6e82;
          font-size:0.98rem;
        }
        .settings-badges { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
        .settings-badge {
          padding:6px 12px;
          border-radius:999px;
          font-weight:700;
          font-size:0.78rem;
          background:#ffffff;
          border:1px solid #dbe7f6;
          color:#1f66ad;
        }
        .settings-card {
          border:1px solid #e2e8f0;
          border-radius:14px;
          padding:16px;
          background:#ffffff;
          box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
        }
        .settings-card-title {
          font-family:'Lexend',sans-serif;
          font-size:1.05rem;
          font-weight:800;
          color:#1a324b;
          margin-bottom:10px;
        }
        .settings-note {
          margin-top:10px;
          font-size:0.9rem;
          color:#64748b;
        }
        .settings-inline {
          display:flex;
          gap:10px;
          flex-wrap:wrap;
          margin-top:8px;
        }
        .settings-inline .pill {
          padding:6px 10px;
          border-radius:999px;
          font-weight:700;
          font-size:0.78rem;
          background:#f1f5f9;
          border:1px solid #e2e8f0;
          color:#1f2937;
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
          padding: 16px 18px;
          border-radius: 14px;
          background: #0f172a;
          border: 1px solid #233044;
          color: #e2e8f0;
          font-family: "Manrope", sans-serif;
          font-size: 0.96rem;
          line-height: 1.7;
          white-space: pre-wrap;
        }
        .ai-report-card {
          margin: 12px 16px 16px;
          padding: 18px 20px;
          border-radius: 16px;
          background: #0f172a;
          border: 1px solid #243247;
          color: #e2e8f0;
          box-shadow: 0 18px 36px rgba(2, 6, 23, 0.25);
        }
        .ai-report-title {
          font-family: "Lexend", sans-serif;
          font-size: 1.2rem;
          font-weight: 800;
          letter-spacing: .04em;
          text-transform: uppercase;
          color: #e2e8f0;
        }
        .ai-report-meta {
          margin-top: 10px;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 8px 14px;
          font-size: 0.92rem;
          color: #cbd5f5;
        }
        .ai-report-meta strong { color:#93c5fd; font-weight:700; }
        .ai-report-divider {
          margin: 14px 0;
          height: 1px;
          background: linear-gradient(90deg, rgba(148,163,184,0) 0%, rgba(148,163,184,0.45) 50%, rgba(148,163,184,0) 100%);
        }
        .ai-report-section {
          margin-top: 12px;
          font-weight: 800;
          color: #f8fafc;
          letter-spacing: .06em;
          text-transform: uppercase;
          font-size: 0.78rem;
        }
        .ai-report-list { margin: 8px 0 0 18px; padding:0; color:#e2e8f0; }
        .ai-report-list li { margin: 6px 0; }
        .ai-report-text { color:#d1d5db; line-height:1.65; font-size:0.95rem; }

        .export-shell {
          background:#ffffff;
          border:1px solid #dce3ea;
          border-radius:16px;
          padding:20px;
          box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
        }
        .export-header { display:flex; justify-content:space-between; align-items:center; gap:12px; }
        .export-title { font-size:2rem; font-weight:800; }
        .export-sub { color:#6b7b8c; margin-top:4px; }
        .export-badges { display:flex; gap:8px; flex-wrap:wrap; }
        .export-badge {
          padding:6px 12px;
          border-radius:999px;
          font-weight:700;
          font-size:0.75rem;
          letter-spacing:.02em;
        }
        .export-badge.low { background:#e8f7ee; color:#15803d; }
        .export-badge.med { background:#fff7e6; color:#b45309; }
        .export-badge.high { background:#fde8e8; color:#b91c1c; }
        .export-card {
          border:1px solid #e2e8f0;
          border-radius:14px;
          padding:14px 16px;
          background:#f8fafc;
        }
        .export-kv { display:flex; justify-content:space-between; gap:10px; }
        .export-kv span { color:#64748b; }
        .export-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
        .export-card [data-testid="stDownloadButton"] button {
          background:#e8f1ff !important;
          border:1px solid #c7ddff !important;
          color:#1f66ad !important;
          font-weight:700 !important;
          border-radius:12px !important;
        }
        .export-card [data-testid="stDownloadButton"] button:hover {
          background:#dbeafe !important;
          border-color:#bfd6fb !important;
          color:#1f66ad !important;
        }
        [data-testid="stDownloadButton"] button {
          background:#e8f1ff !important;
          border:1px solid #c7ddff !important;
          color:#1f66ad !important;
          font-weight:700 !important;
          border-radius:12px !important;
        }
        [data-testid="stDownloadButton"] button:hover {
          background:#dbeafe !important;
          border-color:#bfd6fb !important;
          color:#1f66ad !important;
        }

        .disc-shell {
          background:#ffffff;
          border:1px solid #dce3ea;
          border-radius:16px;
          padding:20px;
          box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
        }
        .disc-grid { display:grid; grid-template-columns: 1.1fr 1.4fr; gap:16px; }
        .disc-card {
          border:1px solid #e2e8f0;
          border-radius:14px;
          padding:14px 16px;
          background:#f8fafc;
        }
        .disc-pill {
          display:inline-flex; align-items:center; gap:6px;
          padding:6px 12px; border-radius:999px; font-weight:700; font-size:0.78rem;
        }
        .disc-pill.mismatch { background:#fde8e8; color:#b91c1c; }
        .disc-pill.omission { background:#fff7e6; color:#b45309; }
        .disc-pill.match { background:#e8f7ee; color:#15803d; }
        .disc-table { width:100%; border-collapse:collapse; font-size:0.92rem; }
        .disc-table th { text-align:left; padding:10px; background:#f1f5f9; border-bottom:1px solid #e2e8f0; }
        .disc-table td { padding:10px; border-bottom:1px solid #eef2f7; color:#334155; }
        .disc-table tr:hover { background:#f8fafc; }
        .analysis-wrap { margin-top: 8px; }
        .agreement-row { text-align:right; padding:8px 16px 14px; color:#cbd5e1; }
        @media (max-width: 1100px) {
          .dark-grid { grid-template-columns: 1fr; max-height:none; }
          .dark-panel { border-right:none; border-bottom:1px solid #2a2e33; }
          .dark-panel:last-child { border-bottom:none; }
          .dark-viewer img { max-height: 52vh; }
        }

        /* Tabs visibility on dark panels */
        .dark-panel [data-testid="stTabs"] [data-baseweb="tab-list"] {
          background:#f8fafc !important;
          border:1px solid #e2e8f0 !important;
          border-radius:999px !important;
          padding:4px !important;
          gap:4px !important;
        }
        .dark-panel [data-testid="stTabs"] [data-baseweb="tab"],
        .dark-panel [data-testid="stTabs"] button[role="tab"],
        .dark-panel [data-testid="stTabs"] div[role="tab"] {
          background:transparent !important;
          color:#111827 !important;
          font-weight:700 !important;
          border-radius:999px !important;
          padding:6px 14px !important;
          border:none !important;
          opacity:1 !important;
          mix-blend-mode:normal !important;
        }
        .dark-panel [data-testid="stTabs"] [data-baseweb="tab"] *,
        .dark-panel [data-testid="stTabs"] button[role="tab"] *,
        .dark-panel [data-testid="stTabs"] div[role="tab"] * {
          color:#111827 !important;
          opacity:1 !important;
        }
        .dark-panel [data-testid="stTabs"] [role="tab"] {
          color:#111827 !important;
        }
        .dark-panel [data-testid="stTabs"] [role="tab"] * {
          color:#111827 !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] span,
        [data-testid="stTabs"] [data-baseweb="tab"] p,
        [data-testid="stTabs"] [data-baseweb="tab"] div {
          color:#111827 !important;
        }
        .dark-panel [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
          background:#1f66ad !important;
          color:#ffffff !important;
          box-shadow: 0 8px 20px rgba(31, 102, 173, 0.35) !important;
        }
        .dark-panel [data-testid="stTabs"] [data-baseweb="tab"]::after {
          border-bottom:none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_settings() -> Dict[str, Any]:
    return st.session_state.get("settings") or {
        "api_base": API_BASE,
        "api_key": API_KEY,
        "timeout": 180,
    }


def get_api_base() -> str:
    return str(get_settings().get("api_base") or API_BASE)


def get_api_key() -> str:
    return str(get_settings().get("api_key") or API_KEY)


def get_timeout() -> int:
    try:
        return int(get_settings().get("timeout") or 180)
    except Exception:
        return 180


def api_headers() -> Dict[str, str]:
    return {"X-API-Key": get_api_key()}

def _api_request(method: str, path: str, **kwargs: Any) -> requests.Response:
    url = f"{get_api_base()}{path}"
    headers = kwargs.pop("headers", {})
    headers.update(api_headers())
    allow_retry = str(method).upper() not in {"POST", "PUT", "PATCH"}
    retries = 2
    backoff = 0.5
    for attempt in range(retries + 1):
        try:
            resp = requests.request(method, url, headers=headers, timeout=get_timeout(), **kwargs)
            if allow_retry and resp.status_code in {429, 502, 503, 504} and attempt < retries:
                time.sleep(backoff)
                backoff *= 2
                continue
            return resp
        except requests.RequestException:
            if (not allow_retry) or attempt >= retries:
                raise
            time.sleep(backoff)
            backoff *= 2
    return requests.request(method, url, headers=headers, timeout=get_timeout(), **kwargs)


def call_verify(file_name: str, image_bytes: bytes, report_text: str) -> Dict[str, Any]:
    files = {"scan": (file_name, image_bytes, "application/octet-stream")}
    data = {"report": report_text, "enhance": "true"}
    resp = _api_request("POST", "/verify", files=files, data=data)
    resp.raise_for_status()
    return resp.json()


def fetch_history(limit: int = 10) -> List[Dict[str, Any]]:
    resp = _api_request("GET", "/history", params={"limit": limit})
    resp.raise_for_status()
    return resp.json()


def fetch_case(case_id: int) -> Dict[str, Any]:
    resp = _api_request("GET", f"/case/{case_id}")
    resp.raise_for_status()
    return resp.json()


def fetch_metrics() -> Dict[str, Any]:
    resp = _api_request("GET", "/metrics")
    resp.raise_for_status()
    return resp.json()


def fetch_ready() -> Dict[str, Any]:
    resp = _api_request("GET", "/ready")
    resp.raise_for_status()
    return resp.json()


def fetch_settings() -> Dict[str, Any]:
    resp = _api_request("GET", "/settings")
    resp.raise_for_status()
    return resp.json()


def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    resp = _api_request("PUT", "/settings", json=settings)
    resp.raise_for_status()
    return resp.json()


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


def _render_ai_report_html(ai_report: str) -> str:
    if not ai_report:
        return ""
    lines = [ln.strip() for ln in ai_report.splitlines() if ln.strip()]
    title = "AI Generated Ultrasound Report"
    meta_pairs: List[tuple[str, str]] = []
    sections: List[tuple[str, List[str]]] = []
    current_section = ""
    current_items: List[str] = []

    def _flush_section() -> None:
        nonlocal current_section, current_items
        if current_section or current_items:
            sections.append((current_section or "Section", current_items))
        current_section = ""
        current_items = []

    for ln in lines:
        if set(ln) <= {"=", "━", "-", "—", "_"}:
            continue
        if ln.upper().startswith("PREGNANCY ULTRASOUND REPORT"):
            title = ln.replace("(", " (").strip()
            continue
        if ln.endswith(":") and len(ln.split()) <= 4:
            _flush_section()
            current_section = ln.replace(":", "").strip()
            continue
        if ":" in ln and current_section == "":
            key, val = ln.split(":", 1)
            if len(key) <= 24:
                meta_pairs.append((key.strip().title(), val.strip()))
                continue
        if ln.startswith("-"):
            current_items.append(ln.lstrip("-").strip())
        else:
            current_items.append(ln)

    _flush_section()
    meta_html = "".join([f"<div><strong>{k}:</strong> {v}</div>" for k, v in meta_pairs])
    sections_html = ""
    for sec, items in sections:
        sec_title = sec or "Details"
        items_html = "".join([f"<li>{item}</li>" for item in items])
        sections_html += (
            f"<div class='ai-report-section'>{sec_title}</div>"
            f"<ul class='ai-report-list'>{items_html}</ul>"
        )
    return (
        "<div class='ai-report-card'>"
        f"<div class='ai-report-title'>{title}</div>"
        f"<div class='ai-report-meta'>{meta_html}</div>"
        "<div class='ai-report-divider'></div>"
        f"<div class='ai-report-text'>{sections_html}</div>"
        "</div>"
    )


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
            h = requests.get(f"{get_api_base()}/health", timeout=5)
            if h.ok:
                st.markdown("<span class='status-ok'>Online (FastAPI connected)</span>", unsafe_allow_html=True)
                try:
                    ready = fetch_ready()
                    if ready.get("ready"):
                        st.markdown("<span class='status-ok'>Ready for verification</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span class='status-bad'>Degraded: checks failing</span>", unsafe_allow_html=True)
                except Exception:
                    st.markdown("<span class='status-bad'>Ready check unavailable</span>", unsafe_allow_html=True)
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
                    msg = str(exc)
                    if "401" in msg or "403" in msg:
                        st.session_state.last_error = "Unauthorized: check API key in Settings."
                    else:
                        st.session_state.last_error = msg

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
                    st.image(enhanced_bytes, use_container_width=True, caption="Enhanced scan")
                else:
                    st.info("Enhanced image not available.")
            with tabs[1]:
                if original_bytes:
                    st.image(original_bytes, use_container_width=True, caption="Original scan")
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
                st.markdown(_render_ai_report_html(ai_report), unsafe_allow_html=True)
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
        show_metrics = bool((get_settings().get("preferences") or {}).get("show_advanced", True))
        if show_metrics:
            try:
                metrics = fetch_metrics()
                if metrics:
                    st.write("")
                    st.markdown("<div class='settings-card'><div class='settings-card-title'>Live Metrics</div>", unsafe_allow_html=True)
                    m1, m2, m3, m4 = st.columns(4, gap="large")
                    with m1:
                        st.markdown(f"<div class='info-card'><h4>Requests</h4><p style='font-size:1.4rem;font-weight:800;'>{metrics.get('requests_total', 0)}</p></div>", unsafe_allow_html=True)
                    with m2:
                        st.markdown(f"<div class='info-card'><h4>Failures</h4><p style='font-size:1.4rem;font-weight:800;'>{metrics.get('requests_failed', 0)}</p></div>", unsafe_allow_html=True)
                    with m3:
                        err_rate = int(float(metrics.get('error_rate', 0)) * 100)
                        st.markdown(f"<div class='info-card'><h4>Error Rate</h4><p style='font-size:1.4rem;font-weight:800;'>{err_rate}%</p></div>", unsafe_allow_html=True)
                    with m4:
                        st.markdown(f"<div class='info-card'><h4>Avg Latency</h4><p style='font-size:1.4rem;font-weight:800;'>{metrics.get('latency_avg_ms', 0)} ms</p></div>", unsafe_allow_html=True)

                    enh = metrics.get("enhancements_by_method") or {}
                    enh_values = [{"method": k, "count": v} for k, v in enh.items()] or [{"method": "none", "count": 0}]
                    st.write("")
                    st.vega_lite_chart(
                        {
                            "data": {"values": enh_values},
                            "mark": {"type": "bar", "cornerRadiusTopLeft": 5, "cornerRadiusTopRight": 5},
                            "encoding": {
                                "x": {"field": "method", "type": "nominal", "axis": {"labelAngle": 0}},
                                "y": {"field": "count", "type": "quantitative"},
                                "color": {"value": "#1f66ad"},
                                "tooltip": [{"field": "method"}, {"field": "count"}],
                            },
                            "height": 220,
                            "width": "container",
                        }
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
            except Exception:
                pass
    except Exception as exc:
        msg = str(exc)
        if "401" in msg or "403" in msg:
            st.error("Unauthorized: check API key in Settings.")
        else:
            st.warning(f"Could not load history: {exc}")


def render_simple(title: str) -> None:
    st.markdown(f"## {title}")
    st.info("This section is available. Next I can wire full interactions screen-by-screen.")

def render_help_center() -> None:
    st.markdown("<div class='panel-label'>Help Center</div>", unsafe_allow_html=True)
    st.markdown(
        "<p class='small-kicker'>Quick answers for operators and clinicians, plus common workflows.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="settings-hero">
          <div class="settings-hero-title">Find answers fast</div>
          <div class="settings-hero-sub">Search guides, troubleshoot issues, and learn core workflows.</div>
          <div class="settings-badges">
            <span class="settings-badge">Getting Started</span>
            <span class="settings-badge">Troubleshooting</span>
            <span class="settings-badge">Export</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    st.text_input("Search help articles", placeholder="Search topics: uploads, discrepancies, exports...")
    st.write("")

    c1, c2, c3 = st.columns(3, gap="large")
    cards = [
        ("Quick Start", "Upload scans, paste report text, and run verification in one flow."),
        ("Mismatch Review", "Resolve discrepancies, add notes, and finalize disposition."),
        ("Export Guide", "Download JSON and report files for audit-ready archives."),
        ("API Keys", "Rotate keys and configure backend access securely."),
        ("Troubleshooting", "Common errors, performance tips, and recovery steps."),
        ("Data Quality", "Best practices for reports and scan uploads."),
    ]
    for idx, (title, desc) in enumerate(cards):
        col = [c1, c2, c3][idx % 3]
        with col:
            st.markdown(
                "<div class='settings-card'>"
                f"<div class='settings-card-title'>{title}</div>"
                f"<div class='settings-note'>{desc}</div>"
                "</div>",
                unsafe_allow_html=True,
            )

    st.write("")
    st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
    st.markdown("<div class='settings-card-title'>Guided Actions</div>", unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns(4, gap="small")
    with a1:
        if st.button("Go to Upload", type="secondary", use_container_width=True):
            st.session_state.active_page = "Dashboard"
            st.rerun()
    with a2:
        if st.button("Resolve Mismatch", type="secondary", use_container_width=True):
            st.session_state.active_page = "Discrepancy Resolution"
            st.rerun()
    with a3:
        if st.button("Final Export", type="secondary", use_container_width=True):
            st.session_state.active_page = "Final Export"
            st.rerun()
    with a4:
        if st.button("Settings", type="secondary", use_container_width=True):
            st.session_state.active_page = "Settings"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    with st.expander("FAQ: Why is the AI report missing?", expanded=False):
        st.write("The backend did not return `ai_report_text`. Verify model output and backend health.")
    with st.expander("FAQ: Why do I see mismatches?", expanded=False):
        st.write("AI and doctor measurements differ beyond tolerance. Review measurement inputs.")
    with st.expander("FAQ: How do I export results?", expanded=False):
        st.write("Use Final Export to download JSON and report files.")

def render_comparative_analytics() -> None:
    st.markdown("<div class='panel-label'>Comparative Analytics</div>", unsafe_allow_html=True)
    st.markdown(
        "<p class='small-kicker'>Compare AI results with radiologist findings across cases.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="settings-hero">
          <div class="settings-hero-title">Agreement Overview</div>
          <div class="settings-hero-sub">Track mismatch trends, risk tiers, and model performance over time.</div>
          <div class="settings-badges">
            <span class="settings-badge">Trends</span>
            <span class="settings-badge">Mismatch</span>
            <span class="settings-badge">Export</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    def _normalize_risk(value: Any) -> str:
        risk = str(value or "").strip().upper()
        if risk in {"LOW", "MEDIUM", "HIGH"}:
            return risk.title()
        return "Medium"

    def _normalize_date(value: Any) -> str:
        if not value:
            return datetime.now().strftime("%Y-%m-%d")
        text = str(value)
        if "T" in text:
            return text.split("T")[0]
        if len(text) >= 10:
            return text[:10]
        return text

    demo_rows = [
        {"case": "CASE-170", "date": "2026-03-22", "scan": "Ultrasound", "ai": "High", "doctor": "High", "confidence": 0.94},
        {"case": "CASE-169", "date": "2026-03-22", "scan": "Ultrasound", "ai": "Low", "doctor": "High", "confidence": 0.71},
        {"case": "CASE-168", "date": "2026-03-23", "scan": "CT", "ai": "Medium", "doctor": "Medium", "confidence": 0.81},
        {"case": "CASE-167", "date": "2026-03-23", "scan": "CT", "ai": "Low", "doctor": "Low", "confidence": 0.88},
        {"case": "CASE-166", "date": "2026-03-24", "scan": "X-Ray", "ai": "Medium", "doctor": "High", "confidence": 0.67},
        {"case": "CASE-165", "date": "2026-03-24", "scan": "X-Ray", "ai": "High", "doctor": "High", "confidence": 0.92},
        {"case": "CASE-164", "date": "2026-03-25", "scan": "MRI", "ai": "Low", "doctor": "Low", "confidence": 0.89},
        {"case": "CASE-163", "date": "2026-03-25", "scan": "MRI", "ai": "High", "doctor": "Medium", "confidence": 0.78},
    ]

    history_rows: List[Dict[str, Any]] = []
    try:
        history = st.session_state.history_cache or fetch_history(limit=200)
        for item in history or []:
            verification = item.get("verification_results") or {}
            risk = _normalize_risk(verification.get("risk_level"))
            doctor_risk = _normalize_risk(
                item.get("doctor_risk")
                or item.get("radiologist_risk")
                or item.get("doctor_risk_level")
                or risk
            )
            confidence = float(verification.get("agreement_rate") or item.get("agreement_rate") or 0.0)
            history_rows.append(
                {
                    "case": item.get("id") or item.get("case_id") or item.get("case") or "-",
                    "date": _normalize_date(item.get("created_at") or item.get("timestamp")),
                    "scan": item.get("scan_type") or item.get("modality") or item.get("scan") or "Unknown",
                    "ai": risk,
                    "doctor": doctor_risk,
                    "confidence": confidence,
                }
            )
    except Exception:
        history_rows = []

    demo_rows = history_rows or demo_rows
    all_dates = [datetime.strptime(r["date"], "%Y-%m-%d").date() for r in demo_rows]
    default_start = min(all_dates)
    default_end = max(all_dates)

    st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([1.2, 1, 1, 1], gap="large")
    with f1:
        date_start = st.date_input("Start date", value=default_start)
        date_end = st.date_input("End date", value=default_end)
    with f2:
        scan_type = st.selectbox("Scan type", ["All", "Ultrasound", "CT", "X-Ray", "MRI"], index=0)
    with f3:
        risk_level = st.selectbox("Risk tier", ["All", "Low", "Medium", "High"], index=0)
    with f4:
        st.selectbox("Model version", ["All", "v2.4.1", "v2.3.9"], index=0)
    st.markdown("</div>", unsafe_allow_html=True)
    st.write("")

    def _in_range(date_str: str) -> bool:
        return date_start <= datetime.strptime(date_str, "%Y-%m-%d").date() <= date_end

    filtered = [r for r in demo_rows if _in_range(r["date"])]
    if scan_type != "All":
        filtered = [r for r in filtered if r["scan"] == scan_type]
    if risk_level != "All":
        filtered = [r for r in filtered if r["ai"] == risk_level or r["doctor"] == risk_level]

    total = len(filtered)
    matches = sum(1 for r in filtered if r["ai"] == r["doctor"])
    mismatches = total - matches
    agreement_pct = int((matches / total) * 100) if total else 0
    avg_conf = int((sum(r["confidence"] for r in filtered) / total) * 100) if total else 0

    k1, k2, k3, k4 = st.columns(4, gap="large")
    with k1:
        st.markdown(f"<div class='info-card'><h4>Total Cases</h4><p style='font-size:1.4rem;font-weight:800;'>{total}</p></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='info-card'><h4>Agreement Rate</h4><p style='font-size:1.4rem;font-weight:800;'>{agreement_pct}%</p></div>", unsafe_allow_html=True)
    with k3:
        st.markdown(f"<div class='info-card'><h4>Mismatches</h4><p style='font-size:1.4rem;font-weight:800;'>{mismatches}</p></div>", unsafe_allow_html=True)
    with k4:
        st.markdown(f"<div class='info-card'><h4>Avg Confidence</h4><p style='font-size:1.4rem;font-weight:800;'>{avg_conf}%</p></div>", unsafe_allow_html=True)
    st.write("")

    # Charts: risk distribution and agreement trend
    ai_counts = {"Low": 0, "Medium": 0, "High": 0}
    doc_counts = {"Low": 0, "Medium": 0, "High": 0}
    trend_map: Dict[str, Dict[str, int]] = {}
    for row in filtered:
        ai_counts[row["ai"]] = ai_counts.get(row["ai"], 0) + 1
        doc_counts[row["doctor"]] = doc_counts.get(row["doctor"], 0) + 1
        trend = trend_map.setdefault(row["date"], {"total": 0, "match": 0})
        trend["total"] += 1
        if row["ai"] == row["doctor"]:
            trend["match"] += 1

    bars = []
    for level in ["Low", "Medium", "High"]:
        bars.append({"tier": level, "group": "AI", "count": ai_counts.get(level, 0)})
        bars.append({"tier": level, "group": "Radiologist", "count": doc_counts.get(level, 0)})
    trend_points = []
    for day in sorted(trend_map.keys()):
        data = trend_map[day]
        pct = (data["match"] / data["total"] * 100.0) if data["total"] else 0.0
        trend_points.append({"date": day, "agreement": round(pct, 1)})

    c1, c2 = st.columns([1.1, 1], gap="large")
    with c1:
        st.markdown("<div class='info-card'><h4>Risk Tier Distribution</h4><p>AI vs Radiologist</p>", unsafe_allow_html=True)
        st.vega_lite_chart(
            {
                "data": {"values": bars},
                "mark": {"type": "bar", "cornerRadiusTopLeft": 5, "cornerRadiusTopRight": 5},
                "encoding": {
                    "x": {"field": "tier", "type": "nominal", "axis": {"labelAngle": 0}},
                    "y": {"field": "count", "type": "quantitative"},
                    "xOffset": {"field": "group"},
                    "color": {"field": "group", "type": "nominal", "scale": {"range": ["#1f66ad", "#22a4c8"]}},
                    "tooltip": [{"field": "group"}, {"field": "tier"}, {"field": "count"}],
                },
                "height": 240,
                "width": "container",
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='info-card'><h4>Agreement Trend</h4><p>Daily agreement percentage</p>", unsafe_allow_html=True)
        st.vega_lite_chart(
            {
                "data": {"values": trend_points},
                "mark": {"type": "line", "point": {"filled": True, "fill": "#1f66ad"}},
                "encoding": {
                    "x": {"field": "date", "type": "temporal"},
                    "y": {"field": "agreement", "type": "quantitative", "scale": {"domain": [0, 100]}},
                    "color": {"value": "#1f66ad"},
                    "tooltip": [{"field": "date"}, {"field": "agreement"}],
                },
                "height": 240,
                "width": "container",
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='info-card'><h4>Case-Level Comparison</h4>", unsafe_allow_html=True)
    rows_html = "".join(
        [
            f"<tr><td>{r['case']}</td><td>{r['date']}</td><td>{r['scan']}</td><td>{r['ai']}</td><td>{r['doctor']}</td><td>{int(r['confidence']*100)}%</td></tr>"
            for r in filtered
        ]
    ) or "<tr><td colspan='6'>No records match the selected filters.</td></tr>"
    st.markdown(
        f"""
        <div class="history-wrap">
          <table class="history-table">
            <thead><tr><th>Case</th><th>Date</th><th>Scan</th><th>AI</th><th>Doctor</th><th>Confidence</th></tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='settings-card'><h4 style='margin:0 0 10px 0;'>Export</h4>", unsafe_allow_html=True)
    ex1, ex2 = st.columns([1, 1], gap="large")
    export_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {"total": total, "agreement_pct": agreement_pct, "mismatches": mismatches},
        "rows": filtered,
    }
    export_json = json.dumps(export_payload, indent=2)
    csv_lines = ["case,date,scan,ai,doctor,confidence"]
    for r in filtered:
        csv_lines.append(f"{r['case']},{r['date']},{r['scan']},{r['ai']},{r['doctor']},{int(r['confidence']*100)}%")
    csv_data = "\n".join(csv_lines)
    with ex1:
        st.download_button("Download JSON", data=export_json, file_name="comparative_analytics.json", mime="application/json", use_container_width=True)
    with ex2:
        st.download_button("Download CSV", data=csv_data, file_name="comparative_analytics.csv", mime="text/csv", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_export() -> None:
    result = st.session_state.last_result
    if not result:
        try:
            history = st.session_state.history_cache or fetch_history(limit=1)
            if history:
                case_id = history[0].get("id") or history[0].get("case_id")
                if case_id is not None:
                    result = fetch_case(int(case_id))
        except Exception:
            result = None
    if not result:
        st.info("No case data available. Run analysis from Dashboard or load History first.")
        return

    verification = (result or {}).get("verification_results") or {}
    risk = str(verification.get("risk_level") or "unknown").lower()
    risk_class = "low" if risk == "low" else "med" if risk == "medium" else "high" if risk == "high" else "med"
    agreement = verification.get("agreement_rate")
    agreement_pct = int(float(agreement or 0) * 100)
    case_id = (result or {}).get("case_id") or "-"
    created = (result or {}).get("metadata", {}).get("timestamp") or "-"

    st.markdown(
        f"""
        <div class="export-shell">
          <div class="export-header">
            <div>
              <div class="export-title">Final Export</div>
              <div class="export-sub">Package and download the verification results.</div>
            </div>
            <div class="export-badges">
              <span class="export-badge {risk_class}">Risk: {risk.upper()}</span>
              <span class="export-badge" style="background:#e8f1ff;color:#1f66ad;">Agreement: {agreement_pct}%</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    col1, col2 = st.columns([1.1, 1])
    with col1:
        export_defaults = (get_settings().get("export_defaults") or {}) if get_settings() else {}
        include_ai = export_defaults.get("include_ai", True)
        include_doc = export_defaults.get("include_doc", True)
        include_images = export_defaults.get("include_images", True)
        include_table = export_defaults.get("include_table", True)
        st.markdown(
            f"""
            <div class="export-card">
              <div class="export-kv"><span>Case ID</span><b>{case_id}</b></div>
              <div class="export-kv"><span>Generated</span><b>{created}</b></div>
              <div class="export-kv"><span>Model</span><b>{(result or {}).get('ai_findings', {}).get('model_used','-')}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            f"""
            <div class="export-card">
              <div style="font-weight:700;margin-bottom:6px;">Export Checklist</div>
              <ul style="margin:0 0 0 18px; padding:0; color:#475569;">
                <li>{"AI report included" if include_ai else "AI report excluded"}</li>
                <li>{"Doctor report included" if include_doc else "Doctor report excluded"}</li>
                <li>Comparison summary included</li>
                <li>{"Images attached (if available)" if include_images else "Images excluded"}</li>
                <li>{"Discrepancy table attached" if include_table else "Discrepancy table excluded"}</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown("<div class='export-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight:700;margin-bottom:6px;'>Download Files</div>", unsafe_allow_html=True)
        json_payload = result or {}
        st.download_button(
            "Download JSON Report",
            data=json.dumps(json_payload, indent=2),
            file_name="radverify_report.json",
            mime="application/json",
            use_container_width=True,
        )
        ai_report = (result or {}).get("ai_report_text") or ""
        if ai_report:
            st.download_button(
                "Download AI Report (TXT)",
                data=ai_report,
                file_name="ai_report.txt",
                mime="text/plain",
                use_container_width=True,
            )
        doctor_report = ((result or {}).get("doctor_findings") or {}).get("raw_text") or st.session_state.report_text
        if doctor_report:
            st.download_button(
                "Download Doctor Report (TXT)",
                data=doctor_report,
                file_name="doctor_report.txt",
                mime="text/plain",
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_discrepancy() -> None:
    result = st.session_state.last_result
    if not result:
        st.info("Run analysis from Dashboard first.")
        return
    verification = result.get("verification_results") or {}
    counts = verification.get("discrepancy_counts") or {}
    rows = _build_comparison_table(verification)
    mismatch_rows = [r for r in rows if str(r.get("status")).lower() == "mismatch"]
    omission_rows = [r for r in rows if str(r.get("status")).lower() == "omission"]

    st.markdown(
        """
        <div class="disc-shell">
          <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
            <div>
              <div class="export-title">Discrepancy Resolution</div>
              <div class="export-sub">Review mismatches and document resolution decisions.</div>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <span class="disc-pill mismatch">Mismatches: {m}</span>
              <span class="disc-pill omission">Omissions: {o}</span>
              <span class="disc-pill match">Matches: {a}</span>
            </div>
          </div>
        </div>
        """.format(m=counts.get("mismatches", 0), o=counts.get("omissions", 0), a=counts.get("matches", 0)),
        unsafe_allow_html=True,
    )
    st.write("")

    col1, col2 = st.columns([1, 1.35], gap="large")
    with col1:
        st.markdown(
            """
            <div class="disc-card">
              <div style="font-weight:700;margin-bottom:8px;">Resolution Checklist</div>
              <ul style="margin:0 0 0 18px; padding:0; color:#475569;">
                <li>Confirm measurement mismatches</li>
                <li>Validate report omissions</li>
                <li>Attach reviewer notes</li>
                <li>Assign final disposition</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.text_area("Reviewer Notes", placeholder="Add discrepancy review notes...", height=160)
        st.selectbox("Disposition", ["Needs Review", "Resolved", "Escalate to Radiologist"])
        st.button("Save Resolution", type="primary", use_container_width=True)

    with col2:
        risk_level = str(verification.get("risk_level") or "unknown").upper()
        agreement = verification.get("agreement_rate")
        agreement_pct = int(float(agreement or 0) * 100)
        st.markdown(
            f"""
            <div class="disc-card" style="margin-bottom:12px;">
              <div style="font-weight:700;margin-bottom:8px;">Resolution Summary</div>
              <div style="display:flex;gap:10px;flex-wrap:wrap;">
                <span class="disc-pill match">Agreement: {agreement_pct}%</span>
                <span class="disc-pill mismatch">Risk: {risk_level}</span>
                <span class="disc-pill omission">Items: {len(rows)}</span>
              </div>
              <div style="margin-top:10px;color:#64748b;font-size:0.9rem;">
                Focus on high-severity mismatches first. Add notes before saving.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div class='disc-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-weight:700;margin-bottom:8px;'>Mismatch Details</div>", unsafe_allow_html=True)
        if mismatch_rows or omission_rows:
            display_rows = mismatch_rows + omission_rows
            table_rows = "".join(
                [
                    f"<tr><td>{r.get('name')}</td><td>{r.get('status')}</td><td>{r.get('ai_value') or r.get('ai_present')}</td><td>{r.get('doctor_value') or r.get('doctor_mentioned')}</td><td>{r.get('severity')}</td></tr>"
                    for r in display_rows
                ]
            )
            st.markdown(
                f"""
                <table class="disc-table">
                  <thead><tr><th>Item</th><th>Status</th><th>AI</th><th>Doctor</th><th>Severity</th></tr></thead>
                  <tbody>{table_rows}</tbody>
                </table>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No discrepancies detected for this case.")
        st.markdown("</div>", unsafe_allow_html=True)

def render_settings() -> None:
    st.markdown("<div class='panel-label'>Settings</div>", unsafe_allow_html=True)
    st.markdown(
        "<p class='small-kicker'>Manage connectivity, preferences, and export defaults in one place.</p>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="settings-hero">
          <div class="settings-hero-title">Environment & Preferences</div>
          <div class="settings-hero-sub">Keep your connection, security, and export behavior consistent across teams.</div>
          <div class="settings-badges">
            <span class="settings-badge">API</span>
            <span class="settings-badge">Preferences</span>
            <span class="settings-badge">Export</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    settings = get_settings()
    if not st.session_state.get("settings_loaded"):
        try:
            backend_settings = fetch_settings()
            if isinstance(backend_settings, dict) and backend_settings:
                st.session_state.settings = {**settings, **backend_settings}
        except Exception:
            pass
        st.session_state.settings_loaded = True
    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("<div class='settings-card-title'>API & Connectivity</div>", unsafe_allow_html=True)
        api_base = st.text_input("Backend URL", value=str(settings.get("api_base") or API_BASE))
        api_key = st.text_input("API Key", value=str(settings.get("api_key") or API_KEY), type="password")
        timeout_val = st.number_input(
            "Backend timeout (seconds)",
            min_value=30,
            max_value=600,
            value=int(settings.get("timeout") or 180),
            step=10,
        )
        st.markdown(
            "<div class='settings-note'>Use a dedicated service key for production environments.</div>",
            unsafe_allow_html=True,
        )
        test_col, _ = st.columns([1, 2])
        with test_col:
            if st.button("Test Connection", type="secondary", use_container_width=True):
                try:
                    resp = requests.get(f"{api_base}/health", headers={"X-API-Key": api_key}, timeout=3)
                    if resp.ok:
                        st.success("Backend is reachable.")
                    else:
                        st.warning("Backend responded but is not healthy.")
                except Exception as exc:
                    st.warning(f"Could not reach backend: {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("<div class='settings-card-title'>Export Defaults</div>", unsafe_allow_html=True)
        export_defaults = settings.get("export_defaults") or {}
        include_ai = st.checkbox("Include AI report", value=bool(export_defaults.get("include_ai", True)))
        include_doc = st.checkbox("Include doctor report", value=bool(export_defaults.get("include_doc", True)))
        include_images = st.checkbox("Include images (if available)", value=bool(export_defaults.get("include_images", True)))
        include_table = st.checkbox("Attach discrepancy table", value=bool(export_defaults.get("include_table", True)))
        st.markdown(
            "<div class='settings-note'>Exports will follow these defaults unless you override them per case.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("<div class='settings-card-title'>Preferences</div>", unsafe_allow_html=True)
        prefs = settings.get("preferences") or {}
        theme = st.selectbox("Theme", ["Light", "Dark"], index=["Light", "Dark"].index(str(prefs.get("theme") or "Light")))
        language = st.selectbox("Language", ["English", "Hindi", "Spanish"], index=["English", "Hindi", "Spanish"].index(str(prefs.get("language") or "English")))
        enable_notifications = st.toggle("Enable notifications", value=bool(prefs.get("enable_notifications", True)))
        show_advanced = st.toggle("Show advanced metrics", value=bool(prefs.get("show_advanced", True)))
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("<div class='settings-card'>", unsafe_allow_html=True)
        st.markdown("<div class='settings-card-title'>Security</div>", unsafe_allow_html=True)
        sec = settings.get("security") or {}
        two_factor = st.toggle("Two-factor authentication", value=bool(sec.get("two_factor", False)))
        retention_days = st.number_input("Data retention (days)", min_value=30, max_value=3650, value=int(sec.get("retention_days") or 365), step=30)
        st.markdown(
            "<div class='settings-inline'><span class='pill'>SOC2 ready</span><span class='pill'>Audit logs enabled</span></div>",
            unsafe_allow_html=True,
        )
        st.button("Rotate API key", type="secondary", use_container_width=True, disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    a1, a2 = st.columns([1, 1])
    with a1:
        if st.button("Save Settings", type="primary", use_container_width=True):
            st.session_state.settings = {
                "api_base": api_base,
                "api_key": api_key,
                "timeout": int(timeout_val),
                "export_defaults": {
                    "include_ai": bool(include_ai),
                    "include_doc": bool(include_doc),
                    "include_images": bool(include_images),
                    "include_table": bool(include_table),
                },
                "preferences": {
                    "theme": theme,
                    "language": language,
                    "enable_notifications": bool(enable_notifications),
                    "show_advanced": bool(show_advanced),
                },
                "security": {
                    "two_factor": bool(two_factor),
                    "retention_days": int(retention_days),
                },
            }
            try:
                save_settings(st.session_state.settings)
                st.success("Settings saved to backend.")
            except Exception as exc:
                st.warning(f"Saved locally, but backend sync failed: {exc}")
    with a2:
        if st.button("Reset to Defaults", type="secondary", use_container_width=True):
            st.session_state.settings = {
                "api_base": API_BASE,
                "api_key": API_KEY,
                "timeout": 180,
            }
            try:
                save_settings(st.session_state.settings)
                st.success("Settings reset on backend.")
            except Exception as exc:
                st.warning(f"Reset locally, but backend sync failed: {exc}")

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
        render_discrepancy()
    elif page == "Final Export":
        render_export()
    elif page == "Help Center":
        render_help_center()
    elif page == "Comparative Analytics":
        render_comparative_analytics()
    else:
        render_settings()


if __name__ == "__main__":
    main()
