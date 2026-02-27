import streamlit as st
import numpy as np
import pandas as pd
import io
import time
from pipeline import RadVerifyPipeline
from modules.database import CaseDatabase

# ==========================================
# 📐 CONFIG & ROBUST STYLING
# ==========================================
st.set_page_config(page_title="RAVEN", page_icon="🩺", layout="wide", initial_sidebar_state="collapsed")

if 'results' not in st.session_state: st.session_state.results = None

# STYLES - ZERO INDENTATION TO PREVENT MARKDOWN PARSING ERRORS
CSS = """
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300..900&display=swap');
:root {--bg:#0a0c0f; --sb:#0f1115; --card:#161a1f; --prim:#17bfcf; --text:#e2e8f0; --sub:#64748b; --err:#ff4b4b; --war:#fbbf24; --brd:#2d333a;}
* {font-family:'Inter',sans-serif!important; box-sizing:border-box;}
.stApp {background:var(--bg); color:var(--text);}
[data-testid="stHeader"], [data-testid="stSidebar"], footer {display:none!important;}
.block-container {padding:0!important; max-width:100%!important;}
.raven-shell {display:flex; height:100vh; width:100vw; overflow:hidden;}
.raven-side {width:64px; background:var(--sb); border-right:1px solid var(--brd); display:flex; flex-direction:column; align-items:center; padding-top:1.5rem; flex-shrink:0;}
.side-icon {color:var(--sub); width:44px; height:44px; display:flex; align-items:center; justify-content:center; border-radius:8px; margin-bottom:1.25rem; cursor:pointer;}
.side-icon.active {color:var(--prim); background:rgba(23,191,207,0.15);}
.raven-main {flex-grow:1; display:flex; flex-direction:column; overflow:hidden;}
.raven-head {height:60px; background:var(--sb); border-bottom:1px solid var(--brd); display:flex; align-items:center; justify-content:space-between; padding:0 1.5rem; flex-shrink:0;}
.logo-grp {display:flex; align-items:center; gap:0.75rem;}
.nav-links {display:flex; gap:1.75rem; margin-left:1.5rem;}
.nav-item {color:var(--sub); font-size:0.8rem; font-weight:600; text-decoration:none;}
.nav-item.active {color:var(--prim); border-bottom:2px solid var(--prim);}
.badge-err {background:rgba(255,75,75,0.1); border:1px solid var(--err); color:var(--err); padding:0.35rem 0.75rem; border-radius:4px; font-size:0.65rem; font-weight:800; display:flex; align-items:center; gap:0.4rem;}
.workspace-scroll {flex-grow:1; overflow-y:auto; padding:2rem 2.5rem 80px 2.5rem;}
.viewer-box {width:100%; border:1px solid var(--brd); border-radius:4px; background:#000; position:relative; aspect-ratio:1.2/1; overflow:hidden;}
.float-tool {position:absolute; top:1rem; left:50%; transform:translateX(-50%); background:rgba(15,17,21,0.95); padding:0.4rem; border-radius:6px; border:1px solid rgba(255,255,255,0.1); display:flex; gap:0.4rem; z-index:10;}
.tool-btn {color:#fff; opacity:0.6; padding:0.35rem; cursor:pointer;}
.tool-btn.active {color:var(--prim); opacity:1;}
.ai-finding {background:var(--card); border:1px solid var(--brd); border-radius:6px; padding:1.25rem; margin-bottom:1rem; position:relative; border-left:3px solid transparent;}
.ai-finding.active {border-color:var(--prim); border-left-color:var(--prim);}
.marker-err {background:rgba(255,75,75,0.2); border-bottom:2px solid var(--err);}
.adj-box {background:rgba(255,75,75,0.04); border:1px solid rgba(255,75,75,0.2); border-radius:6px; padding:1.5rem; margin-top:2rem;}
.foot-bar {position:fixed; bottom:0; left:64px; right:0; height:60px; background:var(--sb); border-top:1px solid var(--brd); display:flex; align-items:center; justify-content:flex-end; padding:0 2rem; gap:1rem; z-index:100;}
.btn-s {background:var(--prim); color:#000; border:none; padding:0.6rem 1.4rem; border-radius:4px; font-weight:800; font-size:0.75rem; cursor:pointer;}
.btn-o {background:#1a1f26; color:#fff; border:1px solid var(--brd); padding:0.6rem 1.4rem; border-radius:4px; font-weight:800; font-size:0.75rem; cursor:pointer;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Helper for Header
def get_header_html():
    has_disc = st.session_state.results and st.session_state.results['verification_results']['agreement_rate'] < 1.0
    badge = '<div class="badge-err"><i class="material-icons" style="font-size:16px">warning</i>DISCREPANCY DETECTED</div>' if has_disc else ''
    return f"""
    <div class="raven-head">
        <div style="display:flex; align-items:center;">
            <div class="logo-grp"><i class="material-icons" style="color:var(--prim); font-size:28px;">hub</i><span style="font-weight:900; font-size:1.1rem;">RAVEN</span></div>
            <div class="nav-links">
                <a href="#" class="nav-item">Analysis Workspace</a><a href="#" class="nav-item">Patient List</a>
                <a href="#" class="nav-item active">Verification</a><a href="#" class="nav-item">History</a>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:1.25rem;">
            {badge}
            <i class="material-icons" style="color:var(--sub); cursor:pointer;">notifications_none</i>
            <i class="material-icons" style="color:var(--sub); cursor:pointer;">settings</i>
            <div style="width:28px; height:28px; border-radius:50%; background:url('https://i.pravatar.cc/150?u=doc1'); background-size:cover; border:1px solid var(--brd);"></div>
        </div>
    </div>
    """

# ==========================================
# 🏗️ UI ASSEMBLY
# ==========================================
st.markdown('<div class="raven-shell">', unsafe_allow_html=True)

# Sidebar
st.markdown("""
<div class="raven-side">
    <div class="side-icon"><i class="material-icons">dashboard</i></div>
    <div class="side-icon active"><i class="material-icons">biotech</i></div>
    <div class="side-icon"><i class="material-icons">folder_open</i></div>
    <div class="side-icon"><i class="material-icons">query_stats</i></div>
    <div style="flex-grow:1"></div>
    <div class="side-icon" style="margin-bottom:1.5rem;"><i class="material-icons" style="font-size:20px">help_outline</i></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="raven-main">', unsafe_allow_html=True)
st.markdown(get_header_html(), unsafe_allow_html=True)

if st.session_state.results is None:
    # Portal View
    st.markdown('<div class="workspace-scroll">', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; padding:4rem 0;"><p style="color:var(--prim); font-weight:800; font-size:0.7rem; letter-spacing:0.15rem; text-transform:uppercase;">Entry Portal</p><h1 style="font-size:3rem; font-weight:900;">Verify Clinical Findings.</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="padding:0 3rem;">', unsafe_allow_html=True)
        up = st.file_uploader("S", label_visibility="collapsed", key="u")
        if not up: st.markdown('<div class="viewer-box" style="border-style:dashed; opacity:0.3; display:flex; align-items:center; justify-content:center;"><div><i class="material-icons" style="font-size:48px;">upload_file</i><br><b>Drop Scan</b></div></div>', unsafe_allow_html=True)
        else: st.image(up)
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div style="padding:0 3rem;">', unsafe_allow_html=True)
        rt = st.text_area("R", height=300, label_visibility="collapsed", placeholder="Paste Report Here...", key="r")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="display:flex; justify-content:center; margin-top:2rem;">', unsafe_allow_html=True)
    if st.button("🚀 EXECUTE PIPELINE", type="primary"):
        if up and rt:
            p = RadVerifyPipeline()
            st.session_state.results = p.process(image_file=up, doctor_report_text=rt)
            st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)
else:
    # Diagnostic Workspace
    res = st.session_state.results
    st.markdown('<div class="workspace-scroll">', unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:2rem;"><div><h2 style="font-size:1.4rem; font-weight:900;">PATIENT_{res.get("patient_id", "ANON")} | Chest X-Ray</h2><p style="color:var(--sub); font-size:0.75rem; font-weight:600;">ID: {res.get("patient_id", "88291-XA")} • STAT</p></div><div style="display:flex; gap:0.75rem;"><button class="btn-o">Previous</button><button class="btn-s">Verify</button></div></div>', unsafe_allow_html=True)
    
    g1, g2, g3 = st.columns([1.6, 0.8, 1.2])
    with g1:
        st.markdown('<div class="viewer-box">', unsafe_allow_html=True)
        st.markdown('<div class="float-tool"><div class="tool-btn"><i class="material-icons">search</i></div><div class="tool-btn"><i class="material-icons" style="color:var(--prim)">visibility</i> <span style="font-size:0.5rem; font-weight:900; margin-left:4px;">AI OVERLAY</span></div></div>', unsafe_allow_html=True)
        if res.get('enhanced_image') is not None:
            st.image(res['enhanced_image'], use_container_width=True)
        else:
            st.warning("Enhanced image not available.")
        st.markdown('<div style="position:absolute; top:50%; left:58%; width:120px; height:150px; border:1px dashed var(--prim); background:rgba(23,191,207,0.05);"><div style="background:var(--prim); font-size:0.5rem; font-weight:900; padding:2px 4px; position:absolute; top:-15px;">Cardiomegaly</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with g2:
        st.markdown('<p style="font-size:0.6rem; font-weight:800; color:var(--sub); margin-bottom:1rem;">AI FINDINGS</p>', unsafe_allow_html=True)
        for fn, fd in res['ai_findings']['biometry'].items():
            act = "cardiothoracic" in fn.lower()
            st.markdown(f'<div class="ai-finding {"active" if act else ""}"><span style="position:absolute; top:1rem; right:1rem; font-size:0.6rem; color:var(--prim); font-weight:800;">{int(fd.get("confidence", 0.9)*100)}%</span><p style="font-weight:700; font-size:0.85rem;">{fn.capitalize()}</p><p style="color:var(--sub); font-size:0.7rem;">{fd["value"]} {fd["unit"]} detected.</p></div>', unsafe_allow_html=True)
    with g3:
        st.markdown('<p style="font-size:0.6rem; font-weight:800; color:var(--sub); margin-bottom:1rem;">HUMAN REPORT</p>', unsafe_allow_html=True)
        txt = res.get('doctor_report_text', '')
        if "Normal cardiomediastinal silhouette" in txt:
            txt = txt.replace("Normal cardiomediastinal silhouette", '<span class="marker-err">Normal cardiomediastinal silhouette</span>')
        st.markdown(f'<div style="font-size:0.9rem; line-height:1.6; color:#CBD5E1;">{txt}</div>', unsafe_allow_html=True)
        if res['verification_results']['agreement_rate'] < 1.0:
            st.markdown(f'<div class="adj-box"><p style="color:var(--err); font-weight:800; font-size:0.6rem; margin-bottom:0.5rem;">DISCREPANCY DETECTED</p><p style="font-size:0.75rem; color:var(--sub);">{res.get("medical_narrative", "Conflict detected.")}</p><div style="display:flex; gap:0.5rem; margin-top:1rem;"><button class="btn-s" style="background:var(--err); color:#fff; flex:1; font-size:0.6rem;">OVERRIDE</button><button class="btn-s" style="flex:1; font-size:0.6rem;">REVISE</button></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="foot-bar"><button class="btn-o">Flag</button><button class="btn-s">Sync & Approve</button></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)
