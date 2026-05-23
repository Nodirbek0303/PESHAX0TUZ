# SmartCross AI — Vercel deploy (FAQAT frontend dashboard)
# XAVFSIZLIK: Parolni hech kimga yubormang. Faqat brauzer orqali login qiling.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== SmartCross AI — Vercel Deploy ===" -ForegroundColor Cyan
Write-Host ""

# 1. Vercel login tekshiruvi
Write-Host "[1/4] Vercel login tekshirilmoqda..." -ForegroundColor Yellow
$whoami = npx --yes vercel whoami 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Siz Vercel ga kirmagansiz." -ForegroundColor Red
    Write-Host "Quyidagini bajaring (brauzer ochiladi, parol chatga YUBORILMAYDI):" -ForegroundColor Yellow
    Write-Host "  npx vercel login" -ForegroundColor White
    Write-Host ""
    Write-Host "Login qilgach, bu skriptni qayta ishga tushiring." -ForegroundColor Yellow
    exit 1
}
Write-Host "Kirish OK: $whoami" -ForegroundColor Green

# 2. Root requirements.txt bor-yo'qligini tekshirish (Vercel Python xatosini oldini oladi)
if (Test-Path "$Root\requirements.txt") {
    Write-Host ""
    Write-Host "XATO: Root requirements.txt topildi — Vercel Python build qiladi va yiqiladi!" -ForegroundColor Red
    Write-Host "O'chiring: Remove-Item requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 3. Environment variables (build vaqtida kerak)
Write-Host ""
Write-Host "[2/4] Environment variables..." -ForegroundColor Yellow
$googleKey = $env:VITE_GOOGLE_MAPS_API_KEY
if (-not $googleKey -and (Test-Path "$Root\frontend\.env")) {
    Get-Content "$Root\frontend\.env" | ForEach-Object {
        if ($_ -match '^VITE_GOOGLE_MAPS_API_KEY=(.+)$') { $googleKey = $matches[1].Trim() }
    }
}
if (-not $googleKey) {
    $googleKey = Read-Host "VITE_GOOGLE_MAPS_API_KEY kiriting (Google Maps)"
}

$apiUrl = $env:VITE_API_URL
if (-not $apiUrl) {
    $apiUrl = Read-Host "VITE_API_URL (backend server, masalan: https://api.example.com/api/v1)"
    if (-not $apiUrl) { $apiUrl = "/api/v1" }
}

$wsUrl = $env:VITE_WS_URL
if (-not $wsUrl) {
    $wsUrl = Read-Host "VITE_WS_URL (ixtiyoriy, masalan: wss://api.example.com/api/v1)"
}

Write-Host "[3/4] Vercel ga deploy qilinmoqda..." -ForegroundColor Yellow
Write-Host "  (Birinchi marta savollar chiqsa: Y -> link qiling)" -ForegroundColor Gray

$env:VITE_GOOGLE_MAPS_API_KEY = $googleKey
$env:VITE_API_URL = $apiUrl
if ($wsUrl) { $env:VITE_WS_URL = $wsUrl }

npx --yes vercel deploy --prod `
    --yes `
    --name peshax0t `
    --build-env VITE_GOOGLE_MAPS_API_KEY=$googleKey `
    --build-env VITE_API_URL=$apiUrl `
    $(if ($wsUrl) { @("--build-env", "VITE_WS_URL=$wsUrl") })

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deploy xato. Vercel Dashboard -> Settings -> Build Command tekshiring." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/4] TAYYOR!" -ForegroundColor Green
Write-Host ""
Write-Host "ESLATMA: Backend (FastAPI + AI) alohida serverda ishlashi kerak:" -ForegroundColor Yellow
Write-Host "  docker compose up --build -d" -ForegroundColor White
Write-Host ""
Write-Host "Vercel faqat React dashboard ni ko'rsatadi." -ForegroundColor Cyan
