# docBrain

## 简介
**docBrain** 是一个深度集成的本地知识索引与智能问答系统。它不仅能静默索引您的本地文档（PDF, Word, Excel, PPTX等），还能通过浏览器插件实时抓取阅读内容。

最核心的进化是：**docBrain 现在集成了 CrewAI 多智能体框架**。它能自动评估问题的复杂度，对于简单事实直接回答，而对于跨文档的复杂分析（如：根据战略规划分析财务表现），则会自动派出由“高级研究员”和“技术作家”组成的智能体团队进行深度研判。

详见：[愿景与价值分析](VISION.md)

## 核心功能
*   **🧩 CrewAI 多智能体协同**：[新增] 集成高级研究员与技术作家。自动拆解复杂问题，执行多步搜索与深度综合。
*   **⚖️ 复杂度自动路由**：系统会自动判断问题难度。简单问题走标准 RAG（快速），复杂问题启动 CrewAI（深度）。
*   **📄 全格式文档支持**：支持 TXT, MD, PDF, Word (.docx), Excel (.xlsx), PPT (.pptx)。
*   **⏱️ 精准溯源与精力追踪**：自动记录路径并累计计算您在每个知识点上投入的**编辑/浏览时间 (Effort Time)**。
*   **🚀 高质量检索 (Quality Mode)**：支持路径关键词加权，优先从核心项目目录提取信息。
*   **🔍 数据库透视**：内置 `peek_db.py` 工具，可直接查看向量库中的原始分块。

## 架构组成
1.  **智能摄入引擎**：基于 `watchdog` 的实时监听，自动处理多种办公格式文档。
2.  **多智能体核心 (CrewAI)**：由高级研究员智能体进行分级搜索，技术作家智能体进行逻辑汇总。
3.  **向量存储层 (ChromaDB)**：高性能本地向量数据库，确保持久化存储。

## 快速开始

### 1. 安装环境
要求：Python 3.10 或更高版本。
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置配置
复制 `.env.example` 到 `.env`：
*   `DEEPSEEK_API_KEY`: 您的 API Key (推荐 DeepSeek-V3)。
*   `WATCH_DIR`: 默认监控路径。

### 3. 命令指南

| 场景 | 命令 | 说明 |
| :--- | :--- | :--- |
| **智能问答 (自动路由)** | `python src/main.py ask "您的提问"` | 基本用法，自动选择单/多智能体模式 |
| **强制智能体模式** | `python src/main.py ask "..." --crew` | [测试项] 强制启动 CrewAI 团队 |
| **单智能体模式** | `python src/main.py ask "..." --no-crew` | [对比项] 强制跳过 Agent 流程 |
| **高质量总结** | `python src/main.py ask "..." --quality` | 启用提权算法进行核心总结 |
| **启动监控服务** | `python src/main.py watch [dir]` | 实时监听文件变动并同步索引 |
| **查看知识分布** | `python src/main.py list` | 列出所有已建索引的文件及 Effort 统计 |
| **查看底层数据** | `python peek_db.py` | [工具] 查看向量库中的原始分块内容 |

## 验证与测试
您可以尝试以下指令来感受 CrewAI 的深度：
```bash
# 跨文件、多维度的分析请求
python src/main.py ask "根据战略规划文件中的 ROI 指标，分析本季度的财务报告并给出改进建议"
```

---
*docBrain - 让您的每一份文档和每一次阅读都有迹可循。*