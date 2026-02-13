@echo off
setlocal

echo ===================================================
echo   docBrain - Intranet Setup
echo   Run this script on the target intranet machine
echo ===================================================
echo.

:: Ensure we are in the project root
cd /d "%~dp0"

:: =====================================================
:: 0. Pre-flight checks
:: =====================================================

:: --- Check path length ---
for /f %%L in ('powershell -Command "('%~dp0').Length"') do set PATH_LEN=%%L
if %PATH_LEN% GTR 80 (
    echo [WARNING] Project path is long ^(%PATH_LEN% chars^)
    echo          Consider a shorter path like C:\docbrain\
    echo.
)

:: --- Check runtime files ---
if not exist "runtime\python\python.exe" goto :err_no_python
if not exist "runtime\node\node.exe" goto :err_no_node
if not exist "offline_packages" goto :err_no_offline
goto :checks_done

:err_no_python
echo [ERROR] runtime\python\python.exe not found
echo         Please run export_deps.bat on a machine with internet first.
pause
exit /b 1

:err_no_node
echo [ERROR] runtime\node\node.exe not found
echo         Please run export_deps.bat on a machine with internet first.
pause
exit /b 1

:err_no_offline
echo [ERROR] offline_packages directory not found
echo         Please run export_deps.bat on a machine with internet first.
pause
exit /b 1

:checks_done

:: =====================================================
:: 1. Visual C++ Redistributable
:: =====================================================
echo [1/5] Checking Visual C++ Runtime...

reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64" /v Version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Visual C++ Runtime is installed.
    goto :vcpp_done
)

if not exist "runtime\vc_redist.x64.exe" (
    echo [WARNING] VC++ Runtime not detected, installer not found.
    goto :vcpp_done
)

echo [INFO] VC++ Runtime not detected, installing silently...
runtime\vc_redist.x64.exe /install /quiet /norestart
if %errorlevel% equ 0 echo [OK] VC++ Runtime installed successfully.
if %errorlevel% equ 1638 echo [OK] A newer version of VC++ Runtime is already installed.

:vcpp_done
echo.

:: =====================================================
:: 2. Install Python dependencies
:: =====================================================
echo [2/5] Installing Python dependencies to runtime\python\ ...
echo       (offline install, no internet required)
echo.

runtime\python\python.exe -m pip install --no-index --find-links=offline_packages --upgrade -r backend\requirements.txt --no-warn-script-location
if %errorlevel% neq 0 (
    echo [ERROR] Python dependency installation failed.
    pause
    exit /b 1
)
echo.
echo [OK] Python dependencies installed.
echo.

:: =====================================================
:: 3. Cleanup stale packages
:: =====================================================
echo [3/5] Cleaning up stale packages...
runtime\python\python.exe backend\scripts\cleanup_packages.py
echo.

:: =====================================================
:: 4. Extract frontend dependencies
:: =====================================================
echo [4/5] Installing frontend dependencies...

if not exist "offline_packages\frontend\node_modules.zip" goto :no_frontend_zip

if exist "frontend\node_modules" (
    echo   Removing old node_modules...
    rmdir /s /q "frontend\node_modules" 2>nul
)

echo   Extracting node_modules from zip...
powershell -Command "Expand-Archive -Path 'offline_packages\frontend\node_modules.zip' -DestinationPath 'frontend' -Force"
if %errorlevel% equ 0 (
    echo [OK] Frontend dependencies extracted.
) else (
    echo [ERROR] Extraction failed.
)
goto :frontend_done

:no_frontend_zip
echo [WARNING] offline_packages\frontend\node_modules.zip not found.
echo          Frontend will not work.

:frontend_done
echo.

:: =====================================================
:: 5. Configure and verify
:: =====================================================
echo [5/5] Configuring environment and verifying...

if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy backend\.env.example backend\.env >nul
        echo [OK] Created .env from .env.example
    )
) else (
    echo [SKIP] backend\.env already exists
)

echo.
echo   Python:
runtime\python\python.exe --version

echo   Node.js:
runtime\node\node.exe --version

echo   Core dependencies:
runtime\python\python.exe -c "import fastapi; import chromadb; import sentence_transformers; print('  [OK] Core dependencies verified')"

echo.
echo   Model:
if exist "backend\models\all-MiniLM-L6-v2\model.safetensors" (
    echo   [OK] Embedding model ready
) else (
    echo   [WARNING] Embedding model missing
)
echo.

:: =====================================================
:: Done
:: =====================================================
echo ===================================================
echo   Setup complete!
echo.
echo   Start command:  dev_start.bat
echo.
echo   Config files:
echo     backend\docbrain_config.json
echo     backend\.env
echo ===================================================
pause
