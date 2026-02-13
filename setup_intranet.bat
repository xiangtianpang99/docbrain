@echo off
setlocal
chcp 65001 >nul 2>&1

echo ===================================================
echo   docBrain - 内网一键安装
echo   在内网目标机器上运行此脚本
echo ===================================================
echo.

:: 确保在项目根目录执行
cd /d "%~dp0"

:: =====================================================
:: 0. 前置检查
:: =====================================================
if not exist "runtime\python\python.exe" (
    echo [ERROR] 未找到 runtime\python\python.exe
    echo 请先在有网的开发机上运行 export_deps.bat
    pause
    exit /b 1
)

if not exist "runtime\node\node.exe" (
    echo [ERROR] 未找到 runtime\node\node.exe
    echo 请先在有网的开发机上运行 export_deps.bat
    pause
    exit /b 1
)

if not exist "offline_packages" (
    echo [ERROR] 未找到 offline_packages 目录
    echo 请先在有网的开发机上运行 export_deps.bat
    pause
    exit /b 1
)

:: =====================================================
:: 1. 安装 Python 依赖
:: =====================================================
echo [1/3] 安装 Python 依赖到 runtime\python\ ...
echo       (从离线包安装，无需网络)
echo.

runtime\python\python.exe -m pip install --no-index --find-links=offline_packages -r backend\requirements.txt --no-warn-script-location
if %errorlevel% neq 0 (
    echo [ERROR] Python 依赖安装失败。
    echo 请检查 offline_packages 目录是否完整。
    pause
    exit /b 1
)
echo.
echo [OK] Python 依赖安装完成。
echo.

:: =====================================================
:: 2. 配置环境
:: =====================================================
echo [2/3] 配置环境...

:: 创建 .env 如果不存在
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy backend\.env.example backend\.env >nul
        echo [OK] 已从 .env.example 创建 .env，请稍后编辑配置。
    ) else (
        echo [SKIP] 未找到 .env.example，跳过环境配置。
    )
) else (
    echo [SKIP] backend\.env 已存在，跳过。
)
echo.

:: =====================================================
:: 3. 验证安装
:: =====================================================
echo [3/3] 验证安装...

echo   Python: 
runtime\python\python.exe --version

echo   Node.js: 
runtime\node\node.exe --version

echo   测试 Python 核心依赖...
runtime\python\python.exe -c "import fastapi; import chromadb; import sentence_transformers; print('  [OK] 核心依赖验证通过')"
if %errorlevel% neq 0 (
    echo [WARNING] 部分核心依赖验证失败，请检查安装日志。
)
echo.

:: =====================================================
:: 完成
:: =====================================================
echo ===================================================
echo   安装完成！
echo.
echo   启动命令:  dev_start.bat
echo.
echo   如需修改配置 (如 LLM API Key), 请编辑:
echo     backend\docbrain_config.json
echo     backend\.env
echo ===================================================
pause
