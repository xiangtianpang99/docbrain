@echo off
setlocal

echo ===================================================
echo   Starting docBrain Development Environment
echo ===================================================

:: 1. Check if virtual environment exists
if not exist ".venv" (
    echo Error: Virtual environment .venv not found.
    echo Please run scripts\setup.bat first.
    pause
    exit /b 1
)

:: 2. Start Backend Server in a new window
echo Starting Backend API (Port 8000)...
start "docBrain Backend" cmd /k "cd backend && ..\.venv\Scripts\python.exe src\api.py"

:: 3. Start Frontend Server in a new window
echo Starting Frontend Server (Port 5173)...
start "docBrain Frontend" cmd /k "cd frontend && npm run dev"

:: 4. Wait a moment for servers to initialize, then open browser
echo Waiting for servers to launch...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo Development environment started!
echo - Backend logs are in the "docBrain Backend" window.
echo - Frontend logs are in the "docBrain Frontend" window.
echo.
pause
