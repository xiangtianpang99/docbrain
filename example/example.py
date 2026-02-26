import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"

try:
    import onnxruntime
except ImportError:
    pass

import torch
import requests
from dotenv import load_dotenv
from typing import List, Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
# from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

COMPANY_API_URL = os.getenv("COMPANY_API_URL", "").strip()
COMPANY_API_KEY = os.getenv("COMPANY_API_KEY", "").strip()
DEFAULT_OPEN_ID = os.getenv("COMPANY_OPEN_ID", "").strip()


def call_company_agent(
        input_params: dict,
        open_id: Optional[str] = None,
        session_id: Optional[str] = None,
        response_mode: str = "noStreaming",
        timeout: int = 30,
) -> dict:
    """
    按公司提供的 curl 示例调用内部模型 API。
    返回值是 response.json() 的结果，你需要根据实际返回结构解析文本。
    """
    if not COMPANY_API_URL or not COMPANY_API_KEY:
        raise RuntimeError("COMPANY_API_URL 或 COMPANY_API_KEY 未配置，请在 .env 中设置。")

    headers = {
        "Api-Key": COMPANY_API_KEY,
        "Content-Type": "application/json;charset=utf-8",
    }

    payload = {
        "sessionId": session_id or "",
        "responseMode": response_mode,  # "streaming" 或 "noStreaming"
        "openId": open_id or DEFAULT_OPEN_ID,  # 必填
        "inputParams": input_params,  # 这里的 key 必须和你在 agent 那边配置的变量名对应
    }

    resp = requests.post(COMPANY_API_URL, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()

    if not isinstance(data, dict):
        return str(data)

    if data.get("returnCode") != "SUC0000":
        raise RuntimeError(f"LLM API error: {data.get('returnCode')} - {data.get('errorMsg')}")

    body = data.get("body") or {}
    text = body.get("output") or ""

    return str(text)


class QueryEngine:
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Query Engine.
        """
        self.persist_directory = persist_directory
        print(f"Loading embedding model: {model_name}...")
        model_path = "D:/docBrain-auto/models/all-MiniLM-L6-V2"
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_path)

        settings = Settings(
            anonymized_telemetry=False
        )

        print(f"Loading Vector Store from {persist_directory}...")
        self.vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embedding_model,
            client_settings = settings
        )

        # Initialize LLM. Expects DEEPSEEK_API_KEY in environment.
        """
        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = "https://api.deepseek.com" # DeepSeek API Base URL
        
        if not api_key:
             print("WARNING: DEEPSEEK_API_KEY not found in environment. LLM calls might fail.")

        self.llm = ChatOpenAI(
            model_name="deepseek-chat", 
            temperature=0.7,
            openai_api_key=api_key,
            openai_api_base=base_url
        )
        """

    def retrieve_context(self, query: str, k: int = 8, quality_mode: bool = False) -> List[str]:
        """
        Retrieve relevant document chunks for a query.
        """
        if not quality_mode:
            print(f"Searching for context related to: '{query}'")
            return self.vector_store.similarity_search(query, k=k)

        # Quality Mode Implementation
        print(f"Searching in Quality Mode for: '{query}'")
        priority_keywords = os.getenv("PRIORITY_KEYWORDS", "").lower().split(",")
        priority_keywords = [kw.strip() for kw in priority_keywords if kw.strip()]

        # 1. Fetch a larger pool of candidates
        fetch_k = k * 3
        docs_with_scores = self.vector_store.similarity_search_with_relevance_scores(query, k=fetch_k)

        # 2. Re-rank based on path keywords and recency
        ranked_results = []
        import time
        now = time.time()

        for doc, score in docs_with_scores:
            boost = 1.0
            source_path = doc.metadata.get("source", "").lower()
            mtime = doc.metadata.get("mtime", 0)

            # Boost based on keywords in path
            if any(kw in source_path for kw in priority_keywords):
                boost += 0.5  # 50% boost for priority paths

            # Slight boost for recency (within the last 30 days)
            age_days = (now - mtime) / (24 * 3600)
            if age_days < 30:
                # Up to 20% boost for very recent files
                recency_boost = 0.2 * (1 - (max(0, age_days) / 30))
                boost += recency_boost

            final_score = score * boost
            ranked_results.append((doc, final_score))

        # 3. Sort by final score and take top k
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in ranked_results[:k]]

    def ask(self, query: str, quality_mode: bool = False) -> str:
        """
        Ask a question to the LLM with retrieved context or via CrewAI.
        """
        # 1. Check complexity

        # 2. Standard RAG (Simple Query)
        print(">>> Using Standard RAG (Simple Query) <<<")
        docs = self.retrieve_context(query, quality_mode=quality_mode)
        if not docs:
            return "No relevant context found in the knowledge base."

        # Build context string with metadata and formatted duration
        context_parts = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            duration_sec = doc.metadata.get("duration", 0)
            effort_str = f"{duration_sec // 60}m {duration_sec % 60}s"

            part = f"[[Chunk {i + 1}]]\nSource: {source}\nEffort Time: {effort_str}\nContent:\n{doc.page_content}"
            context_parts.append(part)

        context_str = "\n\n---\n\n".join(context_parts)

        system_prompt = """你是一个专业的个人知识管理助手和工作总结专家。
你的任务是基于提供的本地文档片段，进行逻辑严密的归纳、总结和分析。

遵循以下准则：
1. **结构化输出**：按时间顺序、项目维度或逻辑分点进行整理，确保内容易于阅读。
2. **区分事实与观点**：明确区分工作成果（事实）与个人心得或反思（分析）。
3. **强制来源引用**：在每个关键结论或事实后，必须在括号内注明来源（如：[来源: D:\\docs\\project.md] 或 [来源: https://...]）。
4. **体现投入精力**：如果用户询问工作进展，请结合提供的 "Effort Time" 信息，提及在该任务上花费的估算时间。
5. **诚实性**：如果提供的上下文不足以回答问题，请如实告知。

请使用专业、简洁且富有洞察力的语气回答。"""

        user_prompt = f"""Context from local documents:
{context_str}

User Question/Request: {query}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        print("Sending request to company LLM...")
        try:
            # 把系统提示和用户问题组合成一个输入，
            # 具体放在哪个 key，要和 agent 变量配置一致
            input_params = {
                "instruction": system_prompt,  # 比如一个变量存系统说明
                "question": user_prompt,  # 一个变量存最终用户问题+上下文
            }

            answer = call_company_agent(
                input_params=input_params,
                open_id=DEFAULT_OPEN_ID,
                session_id=None,
                response_mode="noStreaming"
            )

            return answer
        except Exception as e:
            return f"Error communicating with company LLM: {e}"

    def get_documents_data(self):
        """
        Get all documents in the vector store as a list of dictionaries.
        """
        print("Fetching document list from vector store...")
        try:
            data = self.vector_store.get()
            metadatas = data.get("metadatas", [])

            if not metadatas:
                return []

            docs_summary = {}
            for m in metadatas:
                source = m.get("source", "Unknown")
                if source not in docs_summary:
                    docs_summary[source] = {
                        "source": source,
                        "title": m.get("title", os.path.basename(source)),
                        "type": m.get("type", "file"),
                        "duration": m.get("duration", 0),
                        "file_size": m.get("file_size", "N/A"),
                        "mtime": m.get("mtime", 0),
                        "chunks": 0
                    }
                docs_summary[source]["chunks"] += 1

            return list(docs_summary.values())
        except Exception as e:
            print(f"Error fetching document data: {e}")
            return []

    def list_documents(self):
        """
        List all documents in the vector store with their metadata.
        """
        try:
            docs_data = self.get_documents_data()
            if not docs_data:
                return "The knowledge base is empty."

            # Format the output
            # Format the output
            import datetime
            output = []
            # We will use a wider format for full paths
            header = f"{'Type':<8} | {'Source (Path/URL)':<70} | {'Effort':<10} | {'MTime':<20}"
            output.append(header)
            output.append("-" * len(header))

            for info in sorted(docs_data, key=lambda x: x['mtime'], reverse=True):
                mtime_str = "N/A"
                if info["mtime"]:
                    mtime_str = datetime.datetime.fromtimestamp(info["mtime"]).strftime('%Y-%m-%d %H:%M:%S')

                # Format duration
                duration_sec = info.get("duration", 0)
                effort_str = f"{duration_sec // 60}m {duration_sec % 60}s"

                # Format display source
                source = info["source"]
                if info["type"] == "webpage":
                    display_source = f"{info['title']} ({source})"
                else:
                    display_source = source

                if len(display_source) > 70:
                    display_source = "..." + display_source[-67:]

                output.append(f"{info['type']:<8} | {display_source:<70} | {effort_str:<10} | {mtime_str:<20}")

            return "\n".join(output)

        except Exception as e:
            return f"Error listing documents: {e}"


if __name__ == "__main__":
    # Test run (requires DB to be populated first)
    engine = QueryEngine()
    response = engine.ask("What is this project about?")
    print("\n--- Response ---\n")
    print(response)