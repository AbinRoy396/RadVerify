import streamlit as st

st.set_page_config(page_title="VERA", layout="centered")

st.title(" RAVEN ")
st.subheader("Radiology Analysis and Verification ENgine")

st.write(
    "Upload a medical scan and paste the radiology report. "
    "The system will verify consistency between AI findings and the human report."
)

scan = st.file_uploader("Upload Scan Image", type=["jpg", "png"])
report = st.text_area("Paste Doctor's Report")

if st.button("Verify Report"):
    if scan is not None and report.strip() != "":
        st.success("Scan and report received successfully.")
        st.info("AI verification module will analyze the inputs.")
    else:
        st.error("Please upload a scan and paste the report.")
