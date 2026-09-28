@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 1: rutina con gravedad y control PD, sin SDK de Unitree.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar.bat
    pause
    exit /b 1
)

echo ==============================================================
echo  Prueba 1: rutina con gravedad en MuJoCo
echo ==============================================================
echo Cada motor recibe un torque PD y el robot debe sostenerse solo.
echo No usa DDS ni el SDK de Unitree.
echo.
".venv\Scripts\python.exe" -m uade_mujoco --fisica

echo.
pause
