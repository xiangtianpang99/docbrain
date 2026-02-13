@echo off
setlocal
chcp 65001 >nul 2>&1

echo Starting docBrain setup for Windows...

:: 确保在 scripts 目录执行，然后切换到项目根目录
cd /d "%~dp0"
cd ..

:: 检查运行时
if exist "..\runtime\python\python.exe" (
    echo 使用项目内嵌 Python 运行时...
    set PYTHON=..\runtime\python\python.exe
) else (
    echo 未找到内嵌 Python，使用系统 Python...
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] 未找到 Python。请安装 Python 3.10+ 或运行 export_deps.bat
        pause
        exit /b 1
    )
    set PYTHON=python
)

:: Run the bootstrap script
%PYTHON% scripts\bootstrap.py

if %errorlevel% neq 0 (
    echo Setup failed.
    pause
    exit /b 1
)

echo.
echo Setup complete!
echo To start, run: dev_start.bat
echo.
pause
