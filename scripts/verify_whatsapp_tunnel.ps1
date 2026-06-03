# Quick check: local API + public tunnel + RESTART45 webhook
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$TunnelUrlFile = Join-Path $ProjectRoot ".tunnel-url"

Write-Host "`n=== TatvaOps WhatsApp connectivity ===`n"

try {
    $local = Invoke-RestMethod -Uri "http://127.0.0.1:8000/webhook/whatsapp/health" -TimeoutSec 5
    Write-Host "[OK] Uvicorn local: running (env=$($local.environment))"
} catch {
    Write-Host "[FAIL] Uvicorn not reachable on http://127.0.0.1:8000"
    Write-Host "       Start: python -m uvicorn backend.main:app --reload --port 8000"
}

if (Test-Path $TunnelUrlFile) {
    $base = (Get-Content $TunnelUrlFile -Raw).Trim()
} else {
    $envPath = Join-Path $ProjectRoot ".env"
    $base = (Select-String -Path $envPath -Pattern '^BASE_URL=(.+)$').Matches.Groups[1].Value.Trim()
}

if (-not $base) {
    Write-Host "[FAIL] No BASE_URL — run scripts\start_tunnel.ps1 and copy URL to .env"
    exit 1
}

Write-Host "     BASE_URL: $base"
try {
    $pub = Invoke-RestMethod -Uri "$base/webhook/whatsapp/health" -TimeoutSec 15
    Write-Host "[OK] Tunnel public URL reaches your PC"
} catch {
    Write-Host "[FAIL] Tunnel URL not reachable — restart scripts\start_tunnel.ps1 (keep window open)"
    Write-Host "       Update .env BASE_URL with the NEW https://....trycloudflare.com URL"
    exit 1
}

Write-Host "`nTwilio Sandbox webhook (POST):"
Write-Host "  $base/webhook/whatsapp"
Write-Host "`nAfter changing tunnel URL, restart uvicorn once.`n"
