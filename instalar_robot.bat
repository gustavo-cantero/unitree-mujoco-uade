@echo off
setlocal
chcp 65001 >nul
set "PYTHONUTF8=1"
cd /d "%~dp0"

rem El SDK de Unitree necesita cyclonedds 0.10.2, que en Windows solo se
rem instala con Python 3.10. Por eso se usa un entorno aparte: .venv-robot

set "SDK=%~dp0..\unitree_sdk2_python"
if not "%UNITREE_SDK2_PYTHON%"=="" set "SDK=%UNITREE_SDK2_PYTHON%"
if not exist "%SDK%\setup.py" (
    echo [ERROR] No se encontró unitree_sdk2_python en:
    echo         %SDK%
    echo Clonalo junto a esta carpeta o indicá la ruta en la variable
    echo UNITREE_SDK2_PYTHON.
    pause
    exit /b 1
)

if exist ".venv-robot\Scripts\python.exe" (
    echo [1/3] El entorno .venv-robot ya existe.
    goto :instalar
)

echo [1/3] Creando .venv-robot con Python 3.10...
rem El lanzador py puede terminar sin error aunque no tenga 3.10: se
rem comprueba la salida y que el entorno realmente se haya creado.
py -3.10 -c "print('py310-ok')" 2>nul | find "py310-ok" >nul
if errorlevel 1 goto :con_uv
py -3.10 -m venv .venv-robot
if not exist ".venv-robot\Scripts\python.exe" goto :error
goto :instalar

:con_uv
where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Falta Python 3.10. Instalalo desde https://www.python.org/
    echo         o instalá uv, que lo descarga automáticamente.
    pause
    exit /b 1
)
uv venv --python 3.10 --seed .venv-robot
if not exist ".venv-robot\Scripts\python.exe" goto :error

:instalar
echo [2/3] Instalando el proyecto y el SDK de Unitree...
".venv-robot\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 ".venv-robot\Scripts\python.exe" -m ensurepip --upgrade
".venv-robot\Scripts\python.exe" -m pip install -e . -e "%SDK%"
if errorlevel 1 goto :error

echo [3/3] Verificando el SDK...
".venv-robot\Scripts\python.exe" -c "import cyclonedds, unitree_sdk2py; print('[OK] SDK de Unitree disponible')"
if errorlevel 1 goto :error

echo.
echo [OK] Listo. Probá el simulador con: unitree.bat simulador
pause
exit /b 0

:error
echo.
echo [ERROR] La instalación no pudo completarse.
pause
exit /b 1
