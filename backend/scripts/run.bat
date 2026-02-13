@echo off
SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%..
SET PYTHON=%PROJECT_ROOT%\..\runtime\python\python.exe

IF NOT EXIST "%PYTHON%" (
    echo Error: runtime\python\python.exe not found.
    echo Please run setup_intranet.bat first.
    exit /b 1
)

"%PYTHON%" "%PROJECT_ROOT%\src\main.py" %*
