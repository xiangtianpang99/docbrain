# docBrain

## 简介
**docBrain** 是一个深度集成的本地知识索引与智能问答系统。它不仅能静默索引您的本地文档（PDF, Word, Excel, PPTX等），还能通过浏览器插件连接 API 进行实时配置与内容抓取。

最核心的进化是：**docBrain 现在集成了 CrewAI 多智能体框架**。它能自动评估问题的复杂度，对于简单事实直接回答，而对于跨文档的复杂分析（如：根据战略规划分析财务表现），则会自动派出由“高级研究员”和“技术作家”组成的智能体团队进行深度研判。

详见：[愿景与价值分析](VISION.md)

## 核心功能
*   **🧩 CrewAI 多智能体协同**：[新增] 集成高级研究员与技术作家。自动拆解复杂问题，执行多步搜索与深度综合。
*   **🔌 浏览器插件/API 支持**：[新增] 对外暴露 REST API，支持浏览器插件进行连接、实时摄取网页内容及系统配置。
*   **⚖️ 复杂度自动路由**：系统会自动判断问题难度。简单问题走标准 RAG（快速），复杂问题启动 CrewAI（深度）。
*   **📄 全格式文档支持**：支持 TXT, MD, PDF, Word (.docx/doc), Excel (.xlsx/xls), PPT (.pptx/ppt)。
*   **⏱️ 精准溯源与精力追踪**：自动记录路径并累计计算您在每个知识点上投入的**编辑/浏览时间 (Effort Time)**。
*   **🚀 高质量检索 (Quality Mode)**：支持路径关键词加权，优先从核心项目目录提取信息。
*   **🔍 数据库透视**：内置 `peek_db.py` 工具，可直接查看向量库中的原始分块。

## 架构组成
1.  **智能摄入引擎**：基于 `watchdog` 的实时监听，自动处理多种办公格式文档。
2.  **REST API 接口层**：基于 `FastAPI` 提供配置管理、网页摄取及远程问答功能。
3.  **多智能体核心 (CrewAI)**：由高级研究员智能体进行分级搜索，技术作家智能体进行逻辑汇总。
4.  **向量存储层 (ChromaDB)**：高性能本地向量数据库，确保持久化存储。

## 快速开始

### 1. 快速部署 (推荐)
直接运行一键配置脚本，它会自动为您创建虚拟环境、安装依赖并引导配置 API Key。

*   **Windows**: 双击运行 **`setup.bat`**
*   **macOS / Linux**: 在终端运行 **`./setup.sh`**

### 2. 配置
运行 setup 脚本后，生成的 `.env` 文件包含：
*   `DEEPSEEK_API_KEY`: 您的 LLM API Key (推荐 DeepSeek-V3)。
*   `WATCH_DIR`: 默认监控路径。
*   `API_KEY`: API 访问令牌（默认：`docbrain_default_key`）。

### 3. 运行 API 服务 (集成插件)
启动 API 服务器以连接浏览器插件或第三方工具：
```bash
# macOS / Linux
bash run_api.sh

# Windows
run_api.bat
```
API 默认端口为 `8000`。

## 命令指南 (CLI)

| 场景 | 命令 | 说明 |
| :--- | :--- | :--- |
| **智能问答 (自动路由)** | `python src/main.py ask "您的提问"` | 基本用法，自动选择单/多智能体模式 |
| **强制智能体模式** | `python src/main.py ask "..." --crew` | [测试项] 强制启动 CrewAI 团队 |
| **单智能体模式** | `python src/main.py ask "..." --no-crew` | [对比项] 强制跳过 Agent 流程 |
| **高质量总结** | `python src/main.py ask "..." --quality` | 启用提权算法进行核心总结 |
| **启动监控服务** | `python src/main.py watch [dir]` | 实时监听文件变动并同步索引 |
| **查看知识分布** | `python src/main.py list` | 列出所有已建索引的文件及 Effort 统计 |

## 开放接口 (API)

| 接口 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/health` | `GET` | 健康检查 |
| `/config` | `GET/POST` | 获取或更新系统配置（持久化至 .env） |
| `/query` | `POST` | 远程提问接口 |
| `/documents` | `GET` | 以 JSON 格式获取已索引文档列表 |
| `/ingest/webpage`| `POST` | 摄取网页内容（支持 HTML/Markdown） |

*认证方式：所有受保护接口需并在 Header 中携带 `Authorization: Bearer <API_KEY>`*

---
*docBrain - 让您的每一份文档和每一次阅读都有迹可循。*