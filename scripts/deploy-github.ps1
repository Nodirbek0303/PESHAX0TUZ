# PESHAX0TUZ — GitHub ga push
$ErrorActionPreference = "Stop"
$env:Path = "C:\Program Files\Git\bin;C:\Program Files\GitHub CLI;" + $env:Path
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== GitHub Deploy: PESHAX0TUZ ===" -ForegroundColor Cyan

$auth = & "C:\Program Files\GitHub CLI\gh.exe" auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "GitHub ga kiring (brauzer ochiladi):" -ForegroundColor Yellow
    & "C:\Program Files\GitHub CLI\gh.exe" auth login --hostname github.com --git-protocol https --web
}

& "C:\Program Files\GitHub CLI\gh.exe" repo view Nodirbek0303/PESHAX0TUZ 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Repo yaratilmoqda: PESHAX0TUZ..." -ForegroundColor Yellow
    & "C:\Program Files\GitHub CLI\gh.exe" repo create PESHAX0TUZ --public --description "SmartCross AI — O'zbekiston peshaxot monitoring" --source=. --remote=origin --push
} else {
    git remote remove origin 2>$null
    git remote add origin https://github.com/Nodirbek0303/PESHAX0TUZ.git
    git branch -M main
    git push -u origin main
}

Write-Host "TAYYOR: https://github.com/Nodirbek0303/PESHAX0TUZ" -ForegroundColor Green
