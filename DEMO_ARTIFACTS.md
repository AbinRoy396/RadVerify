# Demo Artifacts

## Backend startup confirmation
- Use terminal output from `.\scripts\run_backend.ps1` showing:
  - `Loading custom trained model from models/best_model.keras...`
  - `OK: Custom model loaded successfully`
  - `Uvicorn running on http://0.0.0.0:8000`

## Health/readiness evidence
- `logs/demo_ready.json`

## End-to-end verify evidence
- `logs/demo_verify.json`
- Key highlights from latest run:
  - `success: true`
  - `case_id: 56`
  - `risk_level: low`
  - `agreement_rate: 1.0`
  - `enhanced_image_path` present

## Runtime metrics evidence
- `logs/demo_metrics.json`

## Production model lock
- `models/PRODUCTION_MODEL.json`
- Locked source archive: `models/archive/20260228_204710`
