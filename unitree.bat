@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)

if "%~1"=="" (
    ".venv-robot\Scripts\python.exe" -m uade_mujoco.unitree --help
    echo.
    echo Ejemplos:
    echo   unitree.bat simulador --arnes
    echo   unitree.bat bajo-nivel
    echo   unitree.bat saludo
    echo   unitree.bat saludo --robot --interfaz "Ethernet 2"
    pause
    exit /b 0
)

".venv-robot\Scripts\python.exe" -m uade_mujoco.unitree %*
if errorlevel 1 pause
