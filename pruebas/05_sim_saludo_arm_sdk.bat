@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 5: saludo por rt/arm_sdk

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)
set "PY=.venv-robot\Scripts\python.exe"

echo ==============================================================
echo  Prueba 5: saludo por rt/arm_sdk
echo ==============================================================
echo El controlador interno del simulador mantiene al robot de pie,
echo como el de Unitree en el robot real; el programa solo mueve los
echo brazos. Resultado esperado: saluda sin perder el equilibrio.
echo.
echo Abriendo el simulador en otra ventana (se cierra solo en 20 s)...
rem Si ya hay un simulador abierto, esta ventana muestra el error y espera.
start "Simulador G1" cmd /c .\unitree.bat simulador  --duracion 20
rem Espera a que el simulador cargue el modelo y empiece a publicar.
ping -n 5 127.0.0.1 >nul

"%PY%" -m uade_mujoco.unitree saludo

echo.
pause
