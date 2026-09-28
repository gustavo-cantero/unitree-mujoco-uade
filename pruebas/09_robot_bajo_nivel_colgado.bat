@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 9: rutina completa por rt/lowcmd
rem Uso: doble clic, o desde una terminal: pruebas\09_robot_bajo_nivel_colgado.bat "Ethernet 2"

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)
set "PY=.venv-robot\Scripts\python.exe"

echo ==============================================================
echo  Prueba 9: rutina completa por rt/lowcmd  --  ROBOT REAL
echo ==============================================================
echo PELIGRO: apaga el equilibrio de Unitree.
echo El robot DEBE estar COLGADO de un soporte, como en la prueba 2.
echo Al terminar pasa a modo amortiguado.
echo.

set "INTERFAZ=%~1"
if not "%INTERFAZ%"=="" goto :tengo_interfaz
echo Adaptadores de red conectados:
powershell -NoProfile -Command "Get-NetAdapter | Where-Object Status -eq 'Up' | Format-Table -AutoSize Name, InterfaceDescription" <nul
set /p "INTERFAZ=Nombre del adaptador conectado al robot (por ejemplo Ethernet 2): "
if "%INTERFAZ%"=="" (
    echo [ERROR] Hace falta el nombre del adaptador.
    pause
    exit /b 1
)
:tengo_interfaz

"%PY%" -m uade_mujoco.unitree bajo-nivel --robot --interfaz "%INTERFAZ%"

echo.
pause
