import streamlit as st
import random  # For placeholder random results
import time    # For simulating loading
from radverify import run_verification

# Set page configuration for a clean, professional look
st.set_page_config(
    page_title="RadVerify",
    page_icon="🩺",  # Medical icon
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for medical theme (blue/green accents, white background)
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    .stButton>button {
        background-color: #007bff;  /* Blue accent */
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton>button:disabled {
        background-color: #cccccc;
        color: #666666;
    }
    .stTextArea textarea {
        border-radius: 5px;
        border: 1px solid #007bff;
    }
    .stFileUploader {
        border-radius: 5px;
        border: 1px solid #007bff;
    }
    .success {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
    }
    .error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    </style>
    """, unsafe_allow_html=True)

# Header Section
st.title("🩺 RadVerify")
st.subheader("AI-Based Radiology Report Verification System")
st.markdown("Upload a medical scan image and paste the corresponding radiology report to verify for mismatches or omissions.")

# Divider for clean separation
st.divider()

# Input Section
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📤 Upload Medical Scan")
    uploaded_image = st.file_uploader("Select a JPG or PNG image (e.g., X-ray or ultrasound)", type=["jpg", "png"], help="Ensure the image is clear and relevant.")

with col2:
    st.markdown("### 📝 Paste Radiology Report")
    report_text = st.text_area("Enter the human-written radiology report here", height=150, help="Copy and paste the full report text.")

# Check if both inputs are provided
inputs_provided = uploaded_image is not None and report_text.strip() != ""

def _render_processing_notes(notes):
    with st.expander("Processing trace (demo)"):
        for note in notes:
            st.write(f"- {note}")

# Verify Button (disabled if inputs not provided)
if st.button("🔍 Verify Report", disabled=not inputs_provided, help="Both image and report are required."):
    try:
        with st.spinner("Analyzing scan and report... Please wait."):
            bundle, processing_notes = run_verification(uploaded_image, report_text)
    except ValueError as exc:
        st.error(f"Input error: {exc}")
    except Exception as exc:  # pragma: no cover - Streamlit runtime guard
        st.error("Unexpected error while running verification pipeline.")
        st.caption(str(exc))
    else:
        pre = bundle.preprocessed_image
        ai = bundle.ai_finding
        report_struct = bundle.report_findings
        comparison = bundle.comparison

        # Display uploaded image + preprocessing stats
        st.divider()
        st.markdown("### 🖼️ Uploaded Scan & Preprocessing Summary")
        img_col, meta_col = st.columns([1.6, 1])
        img_col.image(uploaded_image, caption="Uploaded Medical Scan", use_column_width=True)
        with meta_col:
            st.write(
                f"**File:** {pre.metadata.filename}\n"
                f"**Format:** {pre.metadata.format} | **Size:** {pre.metadata.size_bytes / 1024:.1f} KB\n"
                f"**Normalized grid:** {len(pre.normalized_pixels)}x{len(pre.normalized_pixels[0])}\n"
                f"**Mean intensity:** {pre.mean_intensity:.3f}"
            )

        # Display AI findings
        st.divider()
        st.markdown("### 🤖 AI Feature Detection")
        ai_cols = st.columns(2)
        ai_cols[0].metric("Feature Detected", "Yes" if ai.detected else "No")
        ai_cols[1].metric("Confidence", f"{ai.confidence:.2f}")
        st.info(f"Rationale: {ai.rationale}")

        # Display report parsing summary
        st.divider()
        st.markdown("### 📝 Report Interpretation")
        st.write(
            f"**Mention status:** {report_struct.status.replace('_', ' ').title()}\n"
            f"**Negated:** {'Yes' if report_struct.negated else 'No'}"
        )
        if report_struct.context_snippet:
            st.caption(f"Snippet: “{report_struct.context_snippet}”")

        # Display verification result with color-coded alert
        st.divider()
        st.markdown("### ✅ Verification Result")
        status = comparison.status
        explanation = comparison.explanation
        if status in {"match", "match_absent"}:
            st.success(f"✅ {explanation}")
        elif status == "omission":
            st.warning(f"⚠️ {explanation}")
        else:
            st.error(f"❌ {explanation}")

        _render_processing_notes(processing_notes)

# Footer or additional info if needed
st.divider()
st.markdown("*This is a demo frontend. Actual AI processing would integrate with a backend model.*")