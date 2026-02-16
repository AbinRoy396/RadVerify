# RAVEN Streamlit Web App

This Streamlit frontend now provides a full stitch-style app experience with multiple screens and navigation.

## Implemented screens

- Sign In
- Upload Portal
- Analysis Workspace
- History & Archive
- Analytics Dashboard
- Settings & Preferences
- Help Center

## Backend integration

- `POST /verify` for running AI verification
- `GET /history` for recent cases
- `GET /case/{case_id}` for case details
- Sends required header: `X-API-Key: radverify_secret_key`

## Run

1. Start API backend:

```bash
.venv\Scripts\python.exe api_server.py
```

2. Start Streamlit app:

```bash
.venv\Scripts\streamlit run frontend/streamlit_app.py
```

3. Open the Streamlit URL (usually `http://localhost:8501`).

## Notes

- Sign-in is UI-level (demo flow) and does not yet call an auth backend.
- Analysis workspace renders AI findings, discrepancy status, report highlights, and metrics from backend response.
