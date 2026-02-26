# docBrain 内网开发指南

本指南将指导您如何在 **内网环境** 下，使用内部镜像源搭建 docBrain 开发环境。

## 前置要求

| 项目 | 要求 |
|:---|:---|
| 操作系统 | Windows 10/11 (64-bit) |
| Python | 3.10.x (内置于 `runtime/python/` 或系统安装) |
| Node.js | v22.x LTS (内置于 `runtime/node/` 或系统安装) |
| 内网 PyPI 镜像 | 例如 `http://pypi.example.com/simple/` |
| 内网 npm 镜像 | 例如 `http://npm.example.com/` |

> **注意**: 如果您已经通过 `setup_intranet.bat` 部署了项目，Python 和 Node.js 已经包含在 `runtime/` 目录中，无需额外安装。

---

## 1. 配置 Python (pip) 镜像源

### 方案 A: 使用内置 Python (`runtime/python/`)

创建文件 `runtime/python/pip.ini`:

```ini
[global]
index-url = http://your-pypi-mirror/simple/
trusted-host = your-pypi-mirror
timeout = 60
```

测试配置:

```batch
runtime\python\python.exe -m pip install --dry-run requests
```

### 方案 B: 使用系统 Python

创建或编辑 `%APPDATA%\pip\pip.ini`:

```ini
[global]
index-url = http://your-pypi-mirror/simple/
trusted-host = your-pypi-mirror
timeout = 60
```

### 安装 Python 依赖

```batch
runtime\python\python.exe -m pip install -r backend\requirements.txt
```

安装新包:

```batch
runtime\python\python.exe -m pip install package-name
```

---

## 2. 配置 Node.js (npm) 镜像源

### 方案 A: 使用内置 Node.js (`runtime/node/`)

```batch
runtime\node\npm.cmd config set registry http://your-npm-mirror/
```

验证配置:

```batch
runtime\node\npm.cmd config get registry
```

### 方案 B: 使用系统 Node.js

```batch
npm config set registry http://your-npm-mirror/
```

### 安装前端依赖

```batch
cd frontend
..\runtime\node\npm.cmd install
```

安装新包:

```batch
cd frontend
..\runtime\node\npm.cmd install package-name
```

---

## 3. 环境配置

### 3.1 后端 `.env`

如果尚未创建，请复制示例文件:

```batch
copy backend\.env.example backend\.env
```

编辑 `backend\.env` 并根据需要配置。

### 3.2 禁用遥测 (内网推荐)

在 `backend\.env` 中添加:

```
ANONYMIZED_TELEMETRY=false
```

这将阻止 ChromaDB 尝试向外部服务器发送统计数据，从而消除日志中的 SSL 连接错误。

### 3.3 LLM 配置

编辑 `backend\docbrain_config.json` 以配置您的 LLM 提供商 (例如内网部署的 LLM API)。

---

## 4. 启动开发服务

```batch
dev_start.bat
```

此脚本将:
1. 在 `http://localhost:8000` 启动 **后端 API**
2. 在 `http://localhost:5173` 启动 **前端开发服务器**
3. 自动打开浏览器

脚本会自动优先使用 `runtime/` 下的内置运行环境。

---

## 5. 添加新依赖

### Python

```batch
:: 安装包
runtime\python\python.exe -m pip install new-package-name

:: 添加到 requirements.txt
echo new-package-name >> backend\requirements.txt
```

### Node.js (前端)

```batch
cd frontend
..\runtime\node\npm.cmd install new-package-name
```

新包会自动添加到 `frontend/package.json`。

---

## 6. 常见问题排查

### SSL / 证书错误

如果您的内网镜像使用自签名证书:

**pip:**
```ini
# 在 pip.ini 中添加
[global]
trusted-host = your-pypi-mirror
```

**npm:**
```batch
runtime\node\npm.cmd config set strict-ssl false
```

### Python/Node 版本不匹配

如果您看到版本报错，请确保您使用的是内置运行环境:

```batch
:: 检查当前使用的版本
runtime\python\python.exe --version
runtime\node\node.exe --version
```

请勿依赖系统安装的 Python 或 Node.js，始终使用 `runtime/` 版本。

### torch DLL 加载失败 (WinError 1114)

这表示 **Visual C++ Redistributable** 未安装。请运行:

```batch
runtime\vc_redist.x64.exe /install /quiet /norestart
```

或者直接双击 `runtime\vc_redist.x64.exe` 手动安装。

### PostHog / 遥测错误

如果您在日志中看到 `us.i.posthog.com` 连接失败的错误，请在 `backend\.env` 中添加:

```
ANONYMIZED_TELEMETRY=false
```

---

## 7. 项目结构参考

```
docbrain/
├── dev_start.bat              # 启动开发环境
├── export_deps.bat            # 导出离线依赖 (仅开发机使用)
├── setup_intranet.bat         # 内网一键安装脚本
├── runtime/
│   ├── python/                # 内置 Python 3.10.9
│   ├── node/                  # 内置 Node.js v22.14.0
│   └── vc_redist.x64.exe      # VC++ Runtime 安装程序
├── offline_packages/          # 离线 Python wheels 包
│   └── frontend/
│       └── node_modules.zip   # 离线前端 node_modules
├── backend/
│   ├── requirements.txt       # Python 依赖列表
│   ├── .env                   # 环境变量配置
│   ├── docbrain_config.json   # LLM 配置文件
│   ├── models/                # Embedding 模型文件
│   └── src/                   # 后端源代码
└── frontend/
    ├── package.json           # Node.js 依赖配置
    ├── node_modules/          # 已安装的前端依赖
    └── src/                   # 前端源代码
```

---

## 8. 工作流总结

```
┌─────────────────────────────────────────────┐
│               首次部署                      │
│                                             │
│  1. 将项目拷贝到内网机器                    │
│  2. 运行 setup_intranet.bat                 │
│  3. 配置 pip/npm 镜像源 (见上文)            │
│  4. 编辑 backend\.env                       │
│  5. 运行 dev_start.bat                      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│               日常开发                      │
│                                             │
│  1. 运行 dev_start.bat                      │
│  2. 修改代码 (前端会自动热重载)             │
│  3. 如需重启后端，关闭窗口重新运行          │
│  4. 按需运行 pip install / npm install      │
└─────────────────────────────────────────────┘
```
