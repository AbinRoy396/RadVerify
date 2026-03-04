# Backend Runbook

## Required Environment Variables
- `RADVERIFY_API_KEY`: Required API key for all protected endpoints.

## Optional Environment Variables
- `RADVERIFY_MAX_UPLOAD_BYTES`: Max upload size in bytes. Default: `20971520` (20 MB).
- `RADVERIFY_REQUEST_TIMEOUT_SECONDS`: Pipeline timeout seconds. Default: `120`.
- `RADVERIFY_RATE_LIMIT_REQUESTS`: Max requests per window per client+key. Default: `30`.
- `RADVERIFY_RATE_LIMIT_WINDOW_SECONDS`: Rate limit window seconds. Default: `60`.

## Start Server (Windows PowerShell)
```powershell
$env:RADVERIFY_API_KEY = "change_me_to_strong_key"
.\.venv311\Scripts\python.exe -u api_server.py
```

Or use the helper:
```powershell
.\scripts\run_backend.ps1 -ApiKey "change_me_to_strong_key"
```

## Health and Metrics
- `GET /health`: basic liveness.
- `GET /ready`: readiness check (model/enhancer/security gate).
- `GET /health/details`: dependency + enhancement self-check.
- `GET /metrics`: JSON runtime metrics (API-key protected).
- `GET /metrics/prometheus`: Prometheus text format (API-key protected).

Monitoring helper:
```powershell
.\scripts\monitor_backend.ps1 -BaseUrl "http://localhost:8000" -ApiKey "change_me_to_strong_key"
```

## Verify Endpoint
- `POST /verify` expects:
  - `scan` file
  - `report` text
  - `enhance` boolean
- Returns:
  - analysis, comparison, final report blocks
  - `enhanced_image_path` when enhancement output is produced
  - `request_id`

## Troubleshooting
- `security_not_configured`: set `RADVERIFY_API_KEY`.
- `payload_too_large`: reduce image size or raise `RADVERIFY_MAX_UPLOAD_BYTES`.
- `pipeline_timeout`: increase `RADVERIFY_REQUEST_TIMEOUT_SECONDS` or optimize model path.
- If logs show fallback model:
  - ensure `models/best_model.keras` exists and matches `models/labels.json`.

## Model Quality Evaluation (Held-Out Split)
```powershell
.\.venv311\Scripts\python.exe scripts/evaluate_model_quality.py `
  --dataset data/structure_dataset `
  --split test `
  --model models/best_model.keras `
  --output models/eval `
  --write-validation-metrics
```

## Release Lock + Tag
```powershell
.\scripts\release_backend.ps1 -Tag "v1-backend-stable" -Commit -Push
```
