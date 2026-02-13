@echo off
SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%..
SET PYTHON=%PROJECT_ROOT%\..\runtime\python\python.exe

IF NOT EXIST "%PYTHON%" (
    echo Error: runtime\python\python.exe not found.
    echo Please run setup_intranet.bat first.
    exit /b 1
)

SET PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%

echo Starting docBrain API Server...
"%PYTHON%" "%PROJECT_ROOT%\src\api.py"
