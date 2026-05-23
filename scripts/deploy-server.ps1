$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "SmartCross AI - serverga joylash tayyorgarligi..."

& (Join-Path $PSScriptRoot "reset-data.ps1")

if (-not (Test-Path (Join-Path $Root "backend\.env"))) {
  Copy-Item (Join-Path $Root "backend\.env.example") (Join-Path $Root "backend\.env")
  Write-Host "backend\.env yaratildi (.env.example dan). Parol va API kalitlarni yangilang."
}

if (-not (Test-Path (Join-Path $Root "frontend\.env"))) {
  Copy-Item (Join-Path $Root "frontend\.env.example") (Join-Path $Root "frontend\.env")
  Write-Host "frontend\.env yaratildi."
}

if (-not (Test-Path (Join-Path $Root ".env")) {
  Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
  Write-Host ".env yaratildi (Docker uchun)."
}

Write-Host ""
Write-Host "Keyingi qadamlar:"
Write-Host "1) backend\.env va .env fayllarida ADMIN_PASSWORD va GOOGLE_API_KEY ni sozlang"
Write-Host "2) docker compose up --build -d"
Write-Host "3) Brauzer: http://SERVER-IP/  va  http://SERVER-IP/admin/login"
Write-Host "4) Admin panel -> KAMERALAR orqali kameralarni bosqichma-bosqich o'rnating"
