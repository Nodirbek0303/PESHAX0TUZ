# SmartCross AI — Backend deploy (Render.com)
# Admin panel Vercel uchun backend URL kerak.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== SmartCross AI — Backend Deploy (Render) ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. https://dashboard.render.com ga kiring" -ForegroundColor Yellow
Write-Host "2. New -> Blueprint -> GitHub repo: PESHAX0T" -ForegroundColor Yellow
Write-Host "3. render.yaml avtomatik o'qiladi" -ForegroundColor Yellow
Write-Host "4. ADMIN_PASSWORD = 404-UZ_TEAM (yoki o'zingizniki) kiriting" -ForegroundColor Yellow
Write-Host "5. Deploy tugagach, URL masalan: https://peshax0t-api.onrender.com" -ForegroundColor Yellow
Write-Host ""
Write-Host "6. Vercel Dashboard -> peshax0t -> Settings -> Environment Variables:" -ForegroundColor Yellow
Write-Host "   VITE_API_URL = https://peshax0t-api.onrender.com/api/v1" -ForegroundColor White
Write-Host "   VITE_WS_URL  = wss://peshax0t-api.onrender.com/api/v1" -ForegroundColor White
Write-Host ""
Write-Host "7. Vercel -> Deployments -> Redeploy" -ForegroundColor Yellow
Write-Host ""
Write-Host "Yoki skript orqali Vercel env yangilash:" -ForegroundColor Cyan
Write-Host '  $env:VITE_API_URL="https://SIZNING-API.onrender.com/api/v1"' -ForegroundColor Gray
Write-Host "  .\scripts\deploy-vercel.ps1" -ForegroundColor Gray
