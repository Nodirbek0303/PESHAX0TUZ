$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$DataDir = Join-Path $Root "backend\app\data"

Write-Host "SmartCross AI - ma'lumotlarni nolga tushirish..."

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

@'
{
  "cameras": []
}
'@ | Set-Content -Path (Join-Path $DataDir "camera_registry.json") -Encoding UTF8

@'
{
  "entries": []
}
'@ | Set-Content -Path (Join-Path $DataDir "location_catalog.json") -Encoding UTF8

Write-Host "OK: camera_registry.json va location_catalog.json nolga tushirildi."
Write-Host "Backend ishlayotgan bo'lsa, qayta ishga tushiring yoki admin paneldan POST /admin/system/reset chaqiring."
