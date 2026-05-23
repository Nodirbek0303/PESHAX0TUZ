$ErrorActionPreference = "Stop"

Write-Host "SmartCross AI — GPU inference o'rnatish" -ForegroundColor Cyan
Set-Location $PSScriptRoot\..

python --version
if ($LASTEXITCODE -ne 0) {
    throw "Python topilmadi. Python 3.11 yoki 3.12 tavsiya etiladi."
}

Write-Host "GPU drayver tekshiruvi..." -ForegroundColor Yellow
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi
} else {
    Write-Host "NVIDIA GPU topilmadi. Tizim CPU inference rejimida ishlaydi." -ForegroundColor Yellow
}

Write-Host "Kutubxonalar o'rnatilmoqda..." -ForegroundColor Green
python -m pip install --upgrade pip
python -m pip install -r requirements-gpu.txt

Write-Host "Inference sinovi..." -ForegroundColor Green
python -c "from app.services.inference import create_inference_engine; e = create_inference_engine('gpu'); s = e.status; print(s)"

Write-Host ""
Write-Host "Tayyor. Serverni ishga tushiring:" -ForegroundColor Cyan
Write-Host "  python -m uvicorn app.main:app --reload --port 8000"
Write-Host "Holat endpoint: http://localhost:8000/api/v1/inference/status"
