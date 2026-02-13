@echo off
setlocal
chcp 65001 >nul 2>&1

echo ===================================================
echo   docBrain - 离线依赖导出工具
echo   在有网络的开发机上运行此脚本
echo ===================================================
echo.

:: 确保在项目根目录执行
cd /d "%~dp0"

:: =====================================================
:: 1. 导出 Python 离线 wheel 包
:: =====================================================
echo [1/3] 智能同步 Python 离线依赖包...
echo        (增量检查: 仅下载缺失包, 清理多余包, 记录变更日志)

:: 使用 .venv 的 Python 运行同步脚本
.venv\Scripts\python.exe backend\scripts\sync_offline_packages.py
if %errorlevel% neq 0 (
    echo [ERROR] 离线包同步失败，请检查错误信息。
    pause
    exit /b 1
)

echo.

:: =====================================================
:: 2. 下载 Python Embedded
:: =====================================================
echo [2/3] 准备 Python Embedded 3.10.9...

if not exist "runtime\python" (
    mkdir runtime\python

    :: 检查是否已有下载的 zip
    if not exist "python-3.10.9-embed-amd64.zip" (
        echo 正在下载 Python 3.10.9 Embedded...
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.9/python-3.10.9-embed-amd64.zip' -OutFile 'python-3.10.9-embed-amd64.zip'"
        if %errorlevel% neq 0 (
            echo [ERROR] 下载失败。请手动下载 python-3.10.9-embed-amd64.zip 放到项目根目录后重试。
            pause
            exit /b 1
        )
    )

    echo 解压 Python Embedded...
    powershell -Command "Expand-Archive -Path 'python-3.10.9-embed-amd64.zip' -DestinationPath 'runtime\python' -Force"

    :: 修改 ._pth 文件以启用 site-packages
    echo 配置 Python Embedded 以支持 pip 和 site-packages...
    powershell -Command "(Get-Content 'runtime\python\python310._pth') -replace '#import site','import site' | Set-Content 'runtime\python\python310._pth'"

    :: 安装 pip 到 embedded Python
    echo 安装 pip...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\python\get-pip.py'"
    runtime\python\python.exe runtime\python\get-pip.py --no-warn-script-location
    del runtime\python\get-pip.py 2>nul

    :: 清理下载的 zip
    del python-3.10.9-embed-amd64.zip 2>nul

    echo [OK] Python Embedded 已配置到 runtime\python\
) else (
    echo [SKIP] runtime\python\ 已存在，跳过。
)
echo.

:: =====================================================
:: 3. 下载 Node.js Portable
:: =====================================================
echo [3/3] 准备 Node.js Portable...

:: Node.js v22 LTS (长期支持版，比 v24 更稳定)
:: 变量必须在 if 块外定义，否则 %VAR% 无法展开
set NODE_VERSION=v22.14.0
set NODE_PKG=node-%NODE_VERSION%-win-x64

if not exist "runtime\node" (
    mkdir runtime\node

    if not exist "%NODE_PKG%.zip" (
        echo 正在下载 Node.js %NODE_VERSION%...
        powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/%NODE_VERSION%/%NODE_PKG%.zip' -OutFile '%NODE_PKG%.zip'"
        if %errorlevel% neq 0 (
            echo [ERROR] 下载失败。请手动下载 %NODE_PKG%.zip 放到项目根目录后重试。
            pause
            exit /b 1
        )
    )

    echo 解压 Node.js Portable...
    powershell -Command "Expand-Archive -Path '%NODE_PKG%.zip' -DestinationPath 'runtime\node_temp' -Force"
    :: Node.js zip 解压后有一层目录，需要移动内容
    powershell -Command "Move-Item -Path 'runtime\node_temp\%NODE_PKG%\*' -Destination 'runtime\node\' -Force"
    rmdir /s /q runtime\node_temp 2>nul

    :: 清理下载的 zip
    del %NODE_PKG%.zip 2>nul

    echo [OK] Node.js Portable 已配置到 runtime\node\
) else (
    echo [SKIP] runtime\node\ 已存在，跳过。
)
echo.

:: =====================================================
:: 完成
:: =====================================================
echo ===================================================
echo   导出完成！
echo.
echo   项目目录现在包含:
echo   - runtime\python\     Python 3.10.9 Embedded
echo   - runtime\node\       Node.js v22 LTS Portable
echo   - offline_packages\   Python 离线 wheel 包
echo   - frontend\node_modules\  前端依赖 (已存在)
echo.
echo   下一步: 将整个 docbrain 文件夹拷贝到内网机器，
echo          然后运行 setup_intranet.bat
echo ===================================================
pause
