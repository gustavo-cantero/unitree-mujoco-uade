@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"

rem Comprueba que haya Python 3.10 o superior. Se prueba primero el
rem lanzador py y, si no está (por ejemplo, Python de la Microsoft Store),
rem el comando python.
set "VERSION_OK=import sys; sys.exit(sys.version_info < (3, 10))"
set "PY="
where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "%VERSION_OK%" >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "%VERSION_OK%" >nul 2>&1
        if not errorlevel 1 set "PY=python"
    )
)
if not defined PY (
    echo [ERROR] No se encontró Python 3.10 o superior.
    echo Instalalo desde https://www.python.org/ y volvé a ejecutar este archivo.
    pause
    exit /b 1
)

rem Un .venv creado antes con un Python viejo no sirve: se vuelve a crear.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "%VERSION_OK%" >nul 2>&1
    if errorlevel 1 (
        echo El entorno .venv usa un Python anterior a 3.10: se va a crear de nuevo.
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creando el entorno virtual .venv...
    %PY% -m venv .venv
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
