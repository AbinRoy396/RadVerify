$ErrorActionPreference = "Stop"
$repo = "C:\Users\abinr\RadVerify"
$wslRepo = "/mnt/c/Users/abinr/RadVerify"
$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"

$backendCmd = "chmod +x $wslRepo/scripts/start_backend_wsl.sh; $wslRepo/scripts/start_backend_wsl.sh"
$frontendCmd = "chmod +x $wslRepo/scripts/start_frontend_wsl.sh; $wslRepo/scripts/start_frontend_wsl.sh"

Start-Process powershell -ArgumentList "-NoExit","-Command","wsl -e bash -lc '$backendCmd'"
Start-Process powershell -ArgumentList "-NoExit","-Command","wsl -e bash -lc '$frontendCmd'"

if (Test-Path $cloudflared) {
  Start-Process powershell -ArgumentList "-NoExit","-Command","& '$cloudflared' tunnel --url http://localhost:8501"
} else {
  Write-Host "cloudflared not found at $cloudflared. Update the path in scripts/run_all.ps1" -ForegroundColor Yellow
}