param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ApiKey = "radverify_secret_key"
)

$ErrorActionPreference = "Stop"

function Invoke-JsonGet {
    param([string]$Url, [hashtable]$Headers = @{})
    try {
        return Invoke-RestMethod -Method Get -Uri $Url -Headers $Headers -TimeoutSec 5
    } catch {
        return @{ error = $_.Exception.Message }
    }
}

$health = Invoke-JsonGet -Url "$BaseUrl/health"
$ready = Invoke-JsonGet -Url "$BaseUrl/ready"
$metrics = Invoke-JsonGet -Url "$BaseUrl/metrics" -Headers @{ "X-API-Key" = $ApiKey }

Write-Host "Health:"
$health | ConvertTo-Json -Depth 4
Write-Host "`nReady:"
$ready | ConvertTo-Json -Depth 4
Write-Host "`nMetrics:"
$metrics | ConvertTo-Json -Depth 4
