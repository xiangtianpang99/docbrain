@echo off
SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%..
SET VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe

IF NOT EXIST "%VENV_PYTHON%" (
    echo Error: Virtual environment not found.
    exit /b 1
)

SET PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%

echo Starting docBrain API Server...
"%VENV_PYTHON%" "%PROJECT_ROOT%\src\api.py"
