param(
    [string]$ApiKey = "radverify_secret_key",
    [string]$ListenHost = "0.0.0.0",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

# Prefer .venv311 (stable backend env), then .venv_ml, then .venv
$python = Join-Path $repoRoot ".venv311\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = Join-Path $repoRoot ".venv_ml\Scripts\python.exe"
}
if (-not (Test-Path $python)) {
    $python = Join-Path $repoRoot ".venv\Scripts\python.exe"
}
if (-not (Test-Path $python)) {
    throw "Python not found. Create .venv311, .venv_ml, or .venv first."
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw "ApiKey cannot be empty."
}

$env:RADVERIFY_API_KEY = $ApiKey

Write-Host "Starting RadVerify API on ${ListenHost}:${Port} using $python"
Set-Location $repoRoot
& $python -m uvicorn api_server:app --host $ListenHost --port $Port
