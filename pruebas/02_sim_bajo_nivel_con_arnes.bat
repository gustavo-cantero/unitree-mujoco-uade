@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 2: rutina completa por rt/lowcmd, robot colgado

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)
set "PY=.venv-robot\Scripts\python.exe"

echo ==============================================================
echo  Prueba 2: rutina completa por rt/lowcmd, robot colgado
echo ==============================================================
echo Envía la rutina motor por motor con las rigideces del ejemplo
echo oficial de Unitree. El arnés virtual sostiene el torso, como el
echo soporte que se usa con el robot real. Resultado esperado: completa
echo la rutina.
echo.
echo Abriendo el simulador en otra ventana (se cierra solo en 30 s)...
rem Si ya hay un simulador abierto, esta ventana muestra el error y espera.
start "Simulador G1" cmd /c .\unitree.bat simulador --arnes --duracion 30
rem Espera a que el simulador cargue el modelo y empiece a publicar.
ping -n 5 127.0.0.1 >nul

"%PY%" -m uade_mujoco.unitree bajo-nivel

echo.
pause
