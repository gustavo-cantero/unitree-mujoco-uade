@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 4: rutina completa por rt/lowcmd, rigidez alta

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)
set "PY=.venv-robot\Scripts\python.exe"

echo ==============================================================
echo  Prueba 4: rutina completa por rt/lowcmd, rigidez alta
echo ==============================================================
echo Sin arnés, pero con motores muy rígidos (los de --fisica).
echo Resultado esperado: completa la rutina. Esta rigidez NO se puede
echo usar en el robot real y el programa lo impide.
echo.
echo Abriendo el simulador en otra ventana (se cierra solo en 30 s)...
rem Si ya hay un simulador abierto, esta ventana muestra el error y espera.
start "Simulador G1" cmd /c .\unitree.bat simulador  --duracion 30
rem Espera a que el simulador cargue el modelo y empiece a publicar.
ping -n 5 127.0.0.1 >nul

"%PY%" -m uade_mujoco.unitree bajo-nivel --rigidez alta

echo.
pause
