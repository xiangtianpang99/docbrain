@echo off
SET SCRIPT_DIR=%~dp0
SET VENV_PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe

IF NOT EXIST "%VENV_PYTHON%" (
    echo Error: Virtual environment not found at %SCRIPT_DIR%.venv
    echo Please run: python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
    exit /b 1
)

"%VENV_PYTHON%" "%SCRIPT_DIR%src\main.py" %*
