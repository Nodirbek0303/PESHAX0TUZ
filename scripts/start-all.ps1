# SmartCross AI — Backend + Tunnel (Vercel admin uchun)
# Ikki alohida oyna ochiladi. BU OYNANI YOPMANG!

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

Write-Host "=== SmartCross AI — Backend + Tunnel ===" -ForegroundColor Cyan

# Backend tekshiruvi
$backendOk = $false
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 3 | Out-Null
    $backendOk = $true
    Write-Host "[OK] Backend allaqachon ishlayapti (port 8000)" -ForegroundColor Green
} catch {}

if (-not $backendOk) {
    Write-Host "[START] Backend ishga tushirilmoqda..." -ForegroundColor Yellow
    $cors = '["https://peshax0t.vercel.app","https://peshax0tuz.vercel.app","http://localhost:5173"]'
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; `$env:CORS_ORIGINS='$cors'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    Start-Sleep -Seconds 6
}

# Tunnel tekshiruvi
$tunnelOk = $false
$tunnelUrl = $null
$vercelJson = Join-Path $Root "vercel.json"
if (Test-Path $vercelJson) {
    $json = Get-Content $vercelJson -Raw
    if ($json -match "(https://[\w-]+\.loca\.lt)") {
        $tunnelUrl = $matches[1]
        try {
            Invoke-RestMethod -Uri "$tunnelUrl/api/v1/health" -TimeoutSec 5 | Out-Null
            $tunnelOk = $true
            Write-Host "[OK] Tunnel ishlayapti: $tunnelUrl" -ForegroundColor Green
        } catch {}
    }
}

if (-not $tunnelOk) {
    Write-Host "[START] Yangi tunnel ochilmoqda..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; npx --yes localtunnel --port 8000"
    Write-Host ""
    Write-Host "Tunnel oynasidagi URL ni ko'ring (masalan: https://xxx.loca.lt)" -ForegroundColor Yellow
    Write-Host "Keyin vercel.json va Vercel deploy yangilash kerak:" -ForegroundColor Yellow
    Write-Host "  cd $Root" -ForegroundColor Gray
    Write-Host "  npx vercel deploy --prod --yes" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Admin panel:" -ForegroundColor Cyan
Write-Host "  https://peshax0tuz.vercel.app/admin/login" -ForegroundColor White
Write-Host "  Parol: 404-UZ_TEAM" -ForegroundColor Gray
Write-Host ""
Write-Host "MUHIM: Backend va Tunnel oynalarini YOPMANG!" -ForegroundColor Red
