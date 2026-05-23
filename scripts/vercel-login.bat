@echo off
cd /d "%~dp0.."
echo === Vercel Login (brauzer ochiladi) ===
npx vercel login
echo.
echo Login tugagach:
echo   powershell -ExecutionPolicy Bypass -File scripts\deploy-vercel.ps1
pause
