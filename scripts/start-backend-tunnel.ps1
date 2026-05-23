# SmartCross AI — backend + tunnel + Vercel yangilash
# Admin panel Vercel uchun backend tunnel kerak.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

Write-Host "=== SmartCross AI — Backend + Tunnel ===" -ForegroundColor Cyan

# 1. Backend ishga tushirish (8000-port band bo'lsa o'tkazib yuboriladi)
$health = $null
try { $health = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 3 } catch {}
if (-not $health) {
    Write-Host "[1/4] Backend ishga tushirilmoqda (port 8000)..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    Start-Sleep -Seconds 5
} else {
    Write-Host "[1/4] Backend allaqachon ishlayapti." -ForegroundColor Green
}

# 2. Tunnel URL olish
Write-Host "[2/4] Tunnel ochilmoqda..." -ForegroundColor Yellow
$tunnelLog = Join-Path $env:TEMP "peshax0t-tunnel.log"
$tunnelJob = Start-Job -ScriptBlock {
    param($log)
    npx --yes localtunnel --port 8000 2>&1 | Tee-Object -FilePath $log
} -ArgumentList $tunnelLog

$tunnelUrl = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $tunnelLog) {
        $content = Get-Content $tunnelLog -Raw -ErrorAction SilentlyContinue
        if ($content -match "(https://[\w-]+\.loca\.lt)") {
            $tunnelUrl = $matches[1]
            break
        }
    }
}

if (-not $tunnelUrl) {
    Write-Host "Tunnel URL olinmadi. Qo'lda: npx localtunnel --port 8000" -ForegroundColor Red
    exit 1
}
Write-Host "Tunnel URL: $tunnelUrl" -ForegroundColor Green

# 3. vercel.json yangilash
Write-Host "[3/4] vercel.json yangilanmoqda..." -ForegroundColor Yellow
$vercelJson = Join-Path $Root "vercel.json"
$json = Get-Content $vercelJson -Raw | ConvertFrom-Json
$json.rewrites = @(
    @{ source = "/api/:path*"; destination = "$tunnelUrl/api/:path*" },
    @{ source = "/((?!api/).*)"; destination = "/index.html" }
)
$json | ConvertTo-Json -Depth 10 | Set-Content $vercelJson -Encoding UTF8

# 4. Vercel deploy
Write-Host "[4/4] Vercel ga deploy..." -ForegroundColor Yellow
Set-Location $Root
npx vercel env rm BACKEND_URL production --yes 2>$null | Out-Null
$tunnelUrl | npx vercel env add BACKEND_URL production 2>$null | Out-Null
npx vercel deploy --prod --yes

Write-Host ""
Write-Host "TAYYOR!" -ForegroundColor Green
Write-Host "Admin: https://peshax0t.vercel.app/admin/login" -ForegroundColor Cyan
Write-Host "Tunnel va backend ochiq qolishi shart!" -ForegroundColor Yellow
