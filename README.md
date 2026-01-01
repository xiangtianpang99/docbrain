# docBrain

## 简介
**docBrain** 是一个深度的本地知识全量索引与增量更新系统。它不仅能静默扫描您的整个磁盘（如 D 盘），还能通过浏览器插件实时抓取您的阅读内容，利用大语言模型（LLM）化身为您的“数字大脑”，协助您进行工作总结、进展归纳和知识检索。

详见：[愿景与价值分析](VISION.md)

## 核心功能
*   **全盘静默向量化**：支持后台静默运行，全自动索引整个磁盘（如 D 盘），无需改变任何文件组织习惯。
*   **浏览器实时联动**：提供 Web API 接口，配合浏览器插件，一键将阅读中的网页转化为本地知识。
*   **高质量检索模式 (Quality Mode)**：针对海量数据设计，通过**路径关键词加权**和**文档时效性算法**，优先定位核心工作文档。
*   **多格式深度解析**：支持 Text, Markdown, PDF, Word, Excel, PowerPoint。
*   **全平台静默运行**：在 Windows 上提供 VBScript 脚本，实现真正的“无感”后台监控。
*   **结构化知识视图**：内置 `list` 命令，清晰展示本地文件与网页内容的混合知识大盘。

## 架构组成
1.  **静默摄入引擎 (Silent Ingest)**：自动排除系统垃圾文件（node_modules, .git 等），只处理有价值的文档。
2.  **Web 接收层 (API Layer)**：基于 FastAPI 打造，接收来自外部（如浏览器、移动端）的知识输入。
3.  **智能查询引擎 (Query Engine)**：结合 ChromaDB 语义搜索与 LLM 归纳，支持多维度的权重重排。

## 快速开始

### 1. 安装环境
```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate | Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置数字仓库
复制 `.env.example` 到 `.env`：
*   `DEEPSEEK_API_KEY`: 您的模型 API Key。
*   `WATCH_DIR`: 您想要默认监控的路径（如 `D:\`）。
*   `PRIORITY_KEYWORDS`: 您重点工作的关键路径词（如 `work,project`）。

### 3. 命令指南

| 场景 | 命令 / 脚本 | 说明 |
| :--- | :--- | :--- |
| **全盘后台静默监控** | `run_silent.vbs` (双击) | 无窗口，静默扫盘并监听变化 |
| **启动浏览器接收端** | `./run_api.sh` 或 `run_api.bat` | 开启 8000 端口接收插件数据 |
| **高质量总结提问** | `./run.sh ask "总结本周工作" --quality` | 启用提权算法进行核心总结 |
| **查看知识大盘** | `./run.sh list` | 按时间倒序列出已索引的内容 |
| **手动指定目录索引** | `./run.sh index /path/to/docs` | 针对特定目录进行一次性扫描 |

## 开发者与集成
*   **API 接口**: `POST http://127.0.0.1:8000/ingest/webpage`
*   **鉴权方式**: Header 中添加 `Authorization: Bearer <Your_API_KEY>`
*   **Payload**: `{"url": "...", "title": "...", "content": "..."}`

---
*docBrain - 让您的每一份文档和每一次阅读都有迹可循。*