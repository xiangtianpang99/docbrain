@echo off
setlocal

echo ===================================================
echo   Starting docBrain Development Environment
echo ===================================================

:: Ensure we are in the project root
cd /d "%~dp0"

:: 1. Check runtime
if not exist "runtime\python\python.exe" (
    echo [ERROR] runtime\python\python.exe not found
    echo         Please run setup_intranet.bat or export_deps.bat first.
    pause
    exit /b 1
)
if not exist "runtime\node\node.exe" (
    echo [ERROR] runtime\node\node.exe not found
    echo         Please run setup_intranet.bat or export_deps.bat first.
    pause
    exit /b 1
)

:: 2. Start Backend Server in a new window
echo Starting Backend API (Port 8000)...
start "docBrain Backend" cmd /k "cd /d "%~dp0backend" && ..\runtime\python\python.exe src\api.py"

:: 3. Start Frontend Server in a new window
echo Starting Frontend Server (Port 5173)...
start "docBrain Frontend" cmd /k "cd /d "%~dp0frontend" && ..\runtime\node\npm.cmd run dev"

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
