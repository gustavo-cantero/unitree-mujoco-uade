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

echo [1/2] Validando el modelo y la trayectoria...
".venv\Scripts\python.exe" -m uade_mujoco --check
if errorlevel 1 goto :error

echo [2/2] Ejecutando pruebas automáticas...
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto :error

echo.
echo [OK] Todas las verificaciones terminaron correctamente.
pause
exit /b 0

:error
echo.
echo [ERROR] Alguna verificación falló. Revisá el mensaje anterior.
pause
exit /b 1
