@echo off
SET SCRIPT_DIR=%~dp0
SET VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe

IF NOT EXIST "%VENV_PYTHON%" (
    echo Error: Virtual environment not found.
    exit /b 1
)

SET PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%

echo Starting docBrain API Server...
"%VENV_PYTHON%" "%SCRIPT_DIR%src\api.py"
