# Operator Guide (1-Page)

## 1) Start backend
```powershell
cd C:\Users\abinr\RadVerify
$env:RADVERIFY_API_KEY="radverify_secret_key"
.\scripts\run_backend.ps1
```

## 2) Check readiness
```powershell
curl.exe "http://localhost:8000/ready"
```
Expected: `"ready": true`

## 3) Run one verify case
```powershell
$scan = "C:\Users\abinr\RadVerify\data\Data\Datasets\benign\100_HC.png"
$report = "Single live intrauterine fetus. BPD 46.5 mm, HC 174.0 mm, AC 152.0 mm, FL 30.0 mm. Four chamber heart appears normal."
curl.exe -X POST "http://localhost:8000/verify" `
  -H "X-API-Key: radverify_secret_key" `
  -F "scan=@$scan" `
  -F "report=$report" `
  -F "enhance=true"
```

## 4) Read metrics
```powershell
curl.exe -H "X-API-Key: radverify_secret_key" "http://localhost:8000/metrics"
```

## 5) Production model in use
- `models/best_model.keras`
- `models/labels.json`
- Lock metadata: `models/PRODUCTION_MODEL.json`

## 6) Troubleshooting
- `security_not_configured`:
  - Set `$env:RADVERIFY_API_KEY` before start.
- Model fallback or wrong classes:
  - Restore locked artifacts from `models/archive/20260228_204710`.
- Port busy:
  - Stop old server process, restart `.\scripts\run_backend.ps1`.
