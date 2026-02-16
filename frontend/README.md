# RadVerify Frontend (RAVEN Analysis Workspace)

This is a static HTML/JS frontend that mirrors the design from the “stitch_analysis_verification_workspace” reference. It talks to the RadVerify FastAPI backend to perform AI‑driven radiology report verification.

## How to run locally

1. Start the backend API (from the repo root):
   ```bash
   .venv\Scripts\python.exe api_server.py
   # or: uvicorn api_server:app --reload
   ```

2. Open `frontend/index.html` in a modern browser (Chrome/Firefox/Edge). No local server is required.

3. Click **Verify Study** → select a JPG/PNG scan → paste the radiology report when prompted → see AI findings, discrepancy/omission highlights, and status banner.

## What it does

- **Image viewer** with simulated AI overlay/heatmap toggle.
- **AI Findings panel** showing feature, confidence, and rationale.
- **Human report panel** with inline discrepancy/omission highlights.
- **Top banner** that switches between Match/Omission/Discrepancy based on backend response.
- **Placeholder actions** (Sync & Approve, Compare Previous, etc.) ready for further wiring.

## Architecture notes

- Pure static HTML + TailwindCSS + vanilla JS.
- Calls `POST /verify` on the FastAPI backend.
- Renders `ai_finding`, `report_findings`, and `comparison` fields from the backend response.
- UI is responsive and supports dark/light mode via Tailwind.

## Next steps (optional)

- Wire the remaining actions (history, compare previous, flag for review).
- Persist patient context or load from a backend list.
- Add real image manipulation (zoom/pan/windowing) via a canvas library.
- Integrate user authentication/role UI if needed.
