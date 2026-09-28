@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar.bat
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m uade_mujoco %*
if errorlevel 1 pause
