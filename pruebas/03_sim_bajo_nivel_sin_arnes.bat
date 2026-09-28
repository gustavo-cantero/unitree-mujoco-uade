@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 3: rutina completa por rt/lowcmd, sin arnés

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)
set "PY=.venv-robot\Scripts\python.exe"

echo ==============================================================
echo  Prueba 3: rutina completa por rt/lowcmd, sin arnés
echo ==============================================================
echo Igual que la prueba 2 pero sin sostener el robot. Resultado
echo esperado: SE CAE, porque con rigideces realistas hace falta un
echo controlador de equilibrio. El programa lo detecta y se detiene.
echo.
echo Abriendo el simulador en otra ventana (se cierra solo en 20 s)...
rem Si ya hay un simulador abierto, esta ventana muestra el error y espera.
start "Simulador G1" cmd /c .\unitree.bat simulador  --duracion 20
rem Espera a que el simulador cargue el modelo y empiece a publicar.
ping -n 5 127.0.0.1 >nul

"%PY%" -m uade_mujoco.unitree bajo-nivel

echo.
pause
