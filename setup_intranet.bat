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

:: --- 检查路径长度 ---
:: 用 PowerShell 计算路径长度，避免 batch 延迟扩展问题
for /f %%L in ('powershell -Command "('%~dp0').Length"') do set PATH_LEN=%%L
if %PATH_LEN% GTR 80 (
    echo [WARNING] 项目路径较长 ^(%PATH_LEN% 字符^)
    echo          建议将项目放在较短路径下 ^(如 C:\docbrain\^)
    echo          路径过长可能导致部分文件操作失败。
    echo.
)

:: --- 检查 runtime 目录 ---
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

if not exist "frontend\node_modules\vite" (
    echo [WARNING] 前端依赖 frontend\node_modules 不完整或缺失。
    echo          请确保开发机已运行 export_deps.bat 完成前端依赖安装。
)

if not exist "backend\models\all-MiniLM-L6-v2\model.safetensors" (
    echo [WARNING] Embedding 模型未找到，向量化功能将不可用。
    echo          请确保 backend\models\all-MiniLM-L6-v2\ 目录完整。
)

:: =====================================================
:: 1. 检测并安装 Visual C++ Redistributable
:: =====================================================
echo [1/5] 检测 Visual C++ Runtime...

:: 通过注册表检测是否已安装 VC++ 2015-2022 x64
reg query "HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64" /v Version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Visual C++ Runtime 已安装。
    goto :vcpp_done
)

:: 未安装，尝试自动安装
if not exist "runtime\vc_redist.x64.exe" (
    echo [WARNING] 未检测到 Visual C++ Runtime，且未找到安装包。
    echo          如遇到 DLL 缺失错误，请手动安装 VC++ 2015-2022 Redistributable。
    goto :vcpp_done
)

echo [INFO] 未检测到 Visual C++ Runtime，正在静默安装...
runtime\vc_redist.x64.exe /install /quiet /norestart
if %errorlevel% equ 0 echo [OK] Visual C++ Runtime 安装成功。
if %errorlevel% equ 1638 echo [OK] 已安装更新版本的 VC++ Runtime。

:vcpp_done
echo.

:: =====================================================
:: 2. 安装 Python 依赖
:: =====================================================
echo [2/5] 安装 Python 依赖到 runtime\python\ ...
echo       (从离线包安装，无需网络)
echo.

:: --upgrade 确保版本更新时会升级已安装的旧版本
:: --no-index 不联网  --find-links 从本地 wheel 安装
runtime\python\python.exe -m pip install --no-index --find-links=offline_packages --upgrade -r backend\requirements.txt --no-warn-script-location
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
:: 3. 清理多余旧包
:: =====================================================
echo [3/5] 清理多余旧包...
runtime\python\python.exe backend\scripts\cleanup_packages.py
echo.

:: =====================================================
:: 4. 解压前端依赖
:: =====================================================
echo [4/5] 安装前端依赖...

if exist "offline_packages\frontend\node_modules.zip" (
    :: 清理旧的 node_modules
    if exist "frontend\node_modules" (
        echo   正在清理旧的 node_modules...
        rmdir /s /q "frontend\node_modules" 2>nul
    )

    echo   正在从 node_modules.zip 解压前端依赖...
    powershell -Command "Expand-Archive -Path 'offline_packages\frontend\node_modules.zip' -DestinationPath 'frontend' -Force"
    if %errorlevel% equ 0 (
        echo [OK] 前端依赖解压完成。
    ) else (
        echo [ERROR] 解压失败，请检查 node_modules.zip 是否完整。
    )
) else (
    echo [WARNING] 未找到 offline_packages\frontend\node_modules.zip，前端将无法启动。
    echo          请确保开发机已运行 export_deps.bat 完成前端依赖打包。
)
echo.

:: =====================================================
:: 5. 配置环境 + 验证
:: =====================================================
echo [5/5] 配置环境并验证...

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
echo   Python: 
runtime\python\python.exe --version

echo   Node.js: 
runtime\node\node.exe --version

echo   测试核心依赖...
runtime\python\python.exe -c "import fastapi; import chromadb; import sentence_transformers; print('  [OK] 核心依赖验证通过')"
if %errorlevel% neq 0 (
    echo [WARNING] 部分核心依赖验证失败，请检查安装日志。
)

echo.
echo   模型:
if exist "backend\models\all-MiniLM-L6-v2\model.safetensors" (
    echo   [OK] Embedding 模型已就绪
) else (
    echo   [WARNING] Embedding 模型缺失
)

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
