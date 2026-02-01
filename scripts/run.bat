@echo off
SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%..
SET VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe

IF NOT EXIST "%VENV_PYTHON%" (
    echo Error: Virtual environment not found at %PROJECT_ROOT%\.venv
    echo Please run: scripts\setup.bat
    exit /b 1
)

"%VENV_PYTHON%" "%PROJECT_ROOT%\src\main.py" %*
