@echo off
setlocal

echo ===================================================
echo   docBrain - Offline Dependency Export Tool
echo   Run this on a machine with internet access
echo ===================================================
echo.

:: Ensure we are in the project root
cd /d "%~dp0"

:: =====================================================
:: 1. Sync Python offline wheel packages
:: =====================================================
echo [1/5] Syncing Python offline packages...
echo        (incremental: download missing, remove stale, log changes)

:: Use .venv Python to run the sync script
.venv\Scripts\python.exe backend\scripts\sync_offline_packages.py
if %errorlevel% neq 0 (
    echo [ERROR] Offline package sync failed.
    pause
    exit /b 1
)

echo.

:: =====================================================
:: 2. Download Python Embedded
:: =====================================================
echo [2/5] Preparing Python Embedded 3.10.9...

:: Always rebuild clean Python Embedded to avoid bloat from setup-installed packages
if exist "runtime\python" (
    echo   Cleaning old runtime\python\ ...
    rmdir /s /q "runtime\python"
)
mkdir runtime\python

:: Check if zip already downloaded
if not exist "python-3.10.9-embed-amd64.zip" (
    echo   Downloading Python 3.10.9 Embedded...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.9/python-3.10.9-embed-amd64.zip' -OutFile 'python-3.10.9-embed-amd64.zip'"
    if %errorlevel% neq 0 (
        echo [ERROR] Download failed. Please manually download python-3.10.9-embed-amd64.zip
        pause
        exit /b 1
    )
)

echo   Extracting Python Embedded...
powershell -Command "Expand-Archive -Path 'python-3.10.9-embed-amd64.zip' -DestinationPath 'runtime\python' -Force"

:: Enable site-packages in ._pth file
echo   Configuring Python Embedded for pip and site-packages...
powershell -Command "(Get-Content 'runtime\python\python310._pth') -replace '#import site','import site' | Set-Content 'runtime\python\python310._pth'"

:: Install pip
echo   Installing pip...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\python\get-pip.py'"
runtime\python\python.exe runtime\python\get-pip.py --no-warn-script-location
del runtime\python\get-pip.py 2>nul

:: Cleanup downloaded zip
del python-3.10.9-embed-amd64.zip 2>nul

echo [OK] Python Embedded configured at runtime\python\ (clean state)
echo.

:: =====================================================
:: 3. Download Node.js Portable
:: =====================================================
echo [3/5] Preparing Node.js Portable...

:: Node.js v22 LTS - variables must be defined outside if block
set NODE_VERSION=v22.14.0
set NODE_PKG=node-%NODE_VERSION%-win-x64

if not exist "runtime\node" (
    mkdir runtime\node

    if not exist "%NODE_PKG%.zip" (
        echo   Downloading Node.js %NODE_VERSION%...
        powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/%NODE_VERSION%/%NODE_PKG%.zip' -OutFile '%NODE_PKG%.zip'"
        if %errorlevel% neq 0 (
            echo [ERROR] Download failed. Please manually download %NODE_PKG%.zip
            pause
            exit /b 1
        )
    )

    echo   Extracting Node.js Portable...
    powershell -Command "Expand-Archive -Path '%NODE_PKG%.zip' -DestinationPath 'runtime\node_temp' -Force"
    :: Node.js zip has a nested directory, move contents up
    powershell -Command "Move-Item -Path 'runtime\node_temp\%NODE_PKG%\*' -Destination 'runtime\node\' -Force"
    rmdir /s /q runtime\node_temp 2>nul

    :: Cleanup downloaded zip
    del %NODE_PKG%.zip 2>nul

    echo [OK] Node.js Portable configured at runtime\node\
) else (
    echo [SKIP] runtime\node\ already exists.
)
echo.

:: =====================================================
:: 4. Download Visual C++ Redistributable
:: =====================================================
echo [4/5] Preparing Visual C++ Redistributable...

if not exist "runtime\vc_redist.x64.exe" (
    echo   Downloading VC++ Runtime...
    powershell -Command "Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile 'runtime\vc_redist.x64.exe'"
    if %errorlevel% neq 0 (
        echo [WARNING] Download failed. You may need to manually provide VC++ Runtime.
    ) else (
        echo [OK] VC++ Runtime downloaded to runtime\vc_redist.x64.exe
    )
) else (
    echo [SKIP] runtime\vc_redist.x64.exe already exists.
)
echo.

:: =====================================================
:: 5. Package frontend dependencies as offline zip
:: =====================================================
echo [5/5] Packaging frontend dependencies...

:: Always reinstall and repackage to ensure version consistency
pushd frontend
echo   Installing frontend dependencies (npm install)...
call ..\runtime\node\npm.cmd install
if %errorlevel% neq 0 (
    echo [ERROR] npm install failed.
    popd
    pause
    exit /b 1
)
popd

if not exist "offline_packages\frontend" mkdir "offline_packages\frontend"
:: Delete old zip
if exist "offline_packages\frontend\node_modules.zip" del "offline_packages\frontend\node_modules.zip"
echo   Compressing node_modules to offline_packages\frontend\node_modules.zip ...
powershell -Command "Compress-Archive -Path 'frontend\node_modules' -DestinationPath 'offline_packages\frontend\node_modules.zip' -CompressionLevel Fastest"
if %errorlevel% equ 0 (
    echo [OK] Frontend dependencies packaged.
) else (
    echo [ERROR] Compression failed. Check disk space.
    pause
    exit /b 1
)
echo.

:: =====================================================
:: Done
:: =====================================================
echo ===================================================
echo   Export complete!
echo.
echo   Project now contains:
echo   - runtime\python\               Python 3.10.9 Embedded
echo   - runtime\node\                 Node.js v22 LTS Portable
echo   - runtime\vc_redist.x64.exe     VC++ Runtime installer
echo   - offline_packages\             Python wheels + node_modules.zip
echo   - backend\models\               Embedding model (in Git)
echo.
echo   Next: Copy the entire docbrain folder to intranet,
echo         then run setup_intranet.bat
echo ===================================================
pause
