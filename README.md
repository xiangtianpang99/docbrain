# docBrain

## 简介
**docBrain** 是一个简单的基于 Python 的本地知识库，旨在处理、向量化和查询本地文档。通过集成外部大语言模型（LLM），它协助用户完成基于本地内容的材料总结和文档编写任务。

## 主要功能
- **本地文件摄入**: 扫描指定目录下的文本文件（如 Markdown, Text）。
- **向量化**: 使用本地嵌入模型（如 SentenceTransformers）将文档内容转化为向量嵌入，确保数据隐私并降低成本。
- **语义搜索**: 将向量存储在本地向量数据库（ChromaDB）中，以实现相关上下文的快速语义检索。
- **LLM 集成**: 连接外部 LLM（兼容 OpenAI API 格式），利用检索到的本地上下文生成高质量的总结和内容。

## 需求
- **Python**: 3.8+
- **向量数据库**: ChromaDB (本地运行)
- **嵌入模型**: sentence-transformers (本地运行)
- **LLM**: 深度求索 (DeepSeek) API (或其他兼容 OpenAI 格式的模型)。

## 架构
1.  **摄入服务 (Ingestion Service)**: 遍历目录，读取文件，对文本进行分块，并生成嵌入。
2.  **向量存储 (Vector Store)**: 管理高维向量的存储和检索。
3.  **查询引擎 (Query Engine)**: 接收用户问题，检索相关块，构建提示词，并调用 LLM。
4.  **CLI/接口**: 一个简单的命令行接口，用于触发索引和查询。

## 快速开始 (计划中)
### 安装
```bash
pip install -r requirements.txt
```

### 使用方法
1.  **配置 API Key**:
    复制 `.env.example` 为 `.env`，并填入您的 API Key：
    ```bash
    cp .env.example .env
    # 编辑 .env 文件，设置 DEEPSEEK_API_KEY
    ```
3.  **使用 (推荐)**:
    使用 `run.sh` 脚本自动处理环境依赖：
    ```bash
    # 索引
    ./run.sh index ./my_documents
    
### 功能特性
- **多格式支持**: 支持 Text, Markdown, PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx).
- **自动监听**: 支持监听指定目录，文件变动时自动更新索引。

### 常用命令
使用 `run.sh` 脚本：
```bash
# 1. 建立/更新索引 (一次性)
./run.sh index ./my_documents

# 2. 启动自动监听 (持续更新)
./run.sh watch ./my_documents

# 3. 提问
./run.sh ask "总结一下上周的会议记录"
```