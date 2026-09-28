@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0.."

rem Prueba 6: saludo por rt/arm_sdk
rem Uso: doble clic, o desde una terminal: pruebas\06_robot_saludo.bat "Ethernet 2"

if not exist ".venv-robot\Scripts\python.exe" (
    echo [ERROR] Primero ejecutá instalar_robot.bat
    pause
    exit /b 1
)
set "PY=.venv-robot\Scripts\python.exe"

echo ==============================================================
echo  Prueba 6: saludo por rt/arm_sdk  --  ROBOT REAL
echo ==============================================================
echo El robot debe estar DE PIE con su controlador normal activo.
echo Solo se mueven cintura y brazos; Unitree mantiene el equilibrio.
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

"%PY%" -m uade_mujoco.unitree saludo --robot --interfaz "%INTERFAZ%"

echo.
pause
