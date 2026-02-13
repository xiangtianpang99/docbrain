@echo off
setlocal
chcp 65001 >nul 2>&1

echo ===================================================
echo   Starting docBrain Development Environment
echo ===================================================

:: 确保在项目根目录执行
cd /d "%~dp0"

:: 1. 检查运行时
if not exist "runtime\python\python.exe" (
    echo [ERROR] 未找到 runtime\python\python.exe
    echo 请先运行 setup_intranet.bat 或 export_deps.bat
    pause
    exit /b 1
)
if not exist "runtime\node\node.exe" (
    echo [ERROR] 未找到 runtime\node\node.exe
    echo 请先运行 setup_intranet.bat 或 export_deps.bat
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
