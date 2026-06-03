# Simulate Twilio WhatsApp webhooks against local backend (port 8000).
# Uses TEST_WHATSAPP_FROM from .env in the project root.
#
# Default: sends only "hi" (Nova menu). YOU choose 1-6 on WhatsApp or run again with -Message.
#
# Examples:
#   .\scripts\test_whatsapp_local.ps1
#   .\scripts\test_whatsapp_local.ps1 -Message "2"
#   .\scripts\test_whatsapp_local.ps1 -Message "hi" -Message "2"   # old demo (both at once)

param(
    [string[]]$Message = @("hi")
)

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$EnvFile = Join-Path $ProjectRoot ".env"
$From = "whatsapp:+918639097638"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*TEST_WHATSAPP_FROM=(.+)\s*$') {
            $From = $matches[1].Trim()
        }
    }
}

$BaseUrl = "http://localhost:8000/webhook/whatsapp"

function Send-WhatsAppTest([string]$Text) {
    $body = @{ From = $From; Body = $Text }
    Write-Host "-> $Text (From: $From)"
    Invoke-WebRequest -Uri $BaseUrl -Method POST -Body $body | Out-Null
}

Write-Host "Sending to $BaseUrl"
foreach ($m in $Message) {
    Send-WhatsAppTest $m
    if ($Message.Count -gt 1) { Start-Sleep -Seconds 1 }
}
Write-Host "Done. Reply with 1-6 on WhatsApp when ready (or run with -Message '3' etc.)."
