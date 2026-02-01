@echo off
setlocal
echo Starting docBrain setup for Windows...

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found. Please install Python 3.10+ and ensure it's in your PATH.
    pause
    exit /b 1
)

:: Run the bootstrap script
python bootstrap.py

if %errorlevel% neq 0 (
    echo Setup failed.
    pause
    exit /b 1
)

echo.
echo Setup complete! 
echo To start, run:
echo   .venv\Scripts\activate
echo   python src\main.py ask "Hello"
echo.
pause
