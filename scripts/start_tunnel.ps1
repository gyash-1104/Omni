# Start Cloudflare quick tunnel -> localhost:8000
# Keep this window open. Copy the https://....trycloudflare.com URL into .env BASE_URL and Twilio webhook.

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$Cloudflared = Join-Path $PSScriptRoot "cloudflared.exe"

if (-not (Test-Path $Cloudflared)) {
    Write-Host "Downloading cloudflared..."
    Invoke-WebRequest `
        -Uri "https://github.com/cloudflare/cloudflared/releases/download/2025.4.0/cloudflared-windows-amd64.exe" `
        -OutFile $Cloudflared -UseBasicParsing
}

Write-Host ""
Write-Host "Starting tunnel to http://localhost:8000 ..."
Write-Host "1. Copy the https://....trycloudflare.com URL from the log below"
Write-Host "2. Set BASE_URL in .env (no trailing slash)"
Write-Host "3. Twilio webhook: BASE_URL/webhook/whatsapp  (POST)"
Write-Host "4. Restart uvicorn after changing BASE_URL"
Write-Host "5. Verify: .\scripts\verify_whatsapp_tunnel.ps1"
Write-Host ""

& $Cloudflared tunnel --url http://127.0.0.1:8000
