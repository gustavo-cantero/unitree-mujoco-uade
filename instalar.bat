@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"

where py >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encontró el lanzador de Python.
    echo Instalá Python 3.10 o superior desde https://www.python.org/
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando el entorno virtual .venv...
    py -3 -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/3] El entorno virtual ya existe.
)

echo [2/3] Instalando el proyecto y sus dependencias...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto :error

echo [3/3] Verificando el modelo G1...
".venv\Scripts\python.exe" -m uade_mujoco --check
if errorlevel 1 goto :error

echo.
echo [OK] Instalación terminada. Ahora ejecutá iniciar_demo.bat
pause
exit /b 0

:error
echo.
echo [ERROR] La instalación no pudo completarse.
pause
exit /b 1
