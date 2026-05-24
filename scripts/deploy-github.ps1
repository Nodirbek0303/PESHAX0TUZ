# PESHAX0TUZ — GitHub ga push
$ErrorActionPreference = "Stop"
$env:Path = "C:\Program Files\Git\bin;C:\Program Files\GitHub CLI;" + $env:Path
$Root = Split-Path -Parent $PSScriptRoot
$Gh = "C:\Program Files\GitHub CLI\gh.exe"
Set-Location $Root

Write-Host "=== GitHub Deploy: PESHAX0TUZ ===" -ForegroundColor Cyan

& $Gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub ga kiring:" -ForegroundColor Yellow
    Write-Host "  1. Quyidagi buyruqni bajaring va brauzerda kodni tasdiqlang" -ForegroundColor Gray
    Write-Host "  2. https://github.com/login/device sahifasiga kiring" -ForegroundColor Gray
    & $Gh auth login --hostname github.com --git-protocol https --web
    if ($LASTEXITCODE -ne 0) {
        Write-Host "GitHub login xato. Qayta urinib ko'ring." -ForegroundColor Red
        exit 1
    }
}

$user = (& $Gh api user -q .login)
$repo = "PESHAX0TUZ"
$full = "$user/$repo"

& $Gh repo view $full 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Repo yaratilmoqda: $repo ..." -ForegroundColor Yellow
    & $Gh repo create $repo --public --description "SmartCross AI pedestrian monitoring" --source=. --remote=origin --push
} else {
    git remote remove origin 2>$null
    git remote add origin "https://github.com/$full.git"
    git branch -M main 2>$null
    git push -u origin main
}

Write-Host ""
Write-Host "TAYYOR: https://github.com/$full" -ForegroundColor Green
