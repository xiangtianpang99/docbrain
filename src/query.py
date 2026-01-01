import os
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

class QueryEngine:
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Query Engine.
        """
        self.persist_directory = persist_directory
        print(f"Loading embedding model: {model_name}...")
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        
        print(f"Loading Vector Store from {persist_directory}...")
        self.vector_store = Chroma(
            persist_directory=persist_directory, 
            embedding_function=self.embedding_model
        )
        
        # Initialize LLM. Expects DEEPSEEK_API_KEY in environment.
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
        Ask a question to the LLM with retrieved context.
        """
        docs = self.retrieve_context(query, quality_mode=quality_mode)
        if not docs:
            return "No relevant context found in the knowledge base."
        
        # Build context string with metadata and formatted duration
        context_parts = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            duration_sec = doc.metadata.get("duration", 0)
            effort_str = f"{duration_sec // 60}m {duration_sec % 60}s"
            
            part = f"[[Chunk {i+1}]]\nSource: {source}\nEffort Time: {effort_str}\nContent:\n{doc.page_content}"
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
        
        print("Sending request to LLM...")
        try:
            response = self.llm(messages)
            return response.content
        except Exception as e:
            return f"Error communicating with LLM: {e}"

    def list_documents(self):
        """
        List all documents in the vector store with their metadata.
        """
        print("Fetching document list from vector store...")
        try:
            # Fetch all metadata from ChromaDB
            data = self.vector_store.get()
            metadatas = data.get("metadatas", [])
            
            if not metadatas:
                return "The knowledge base is empty."

            # Group by source
            docs_summary = {}
            for m in metadatas:
                source = m.get("source", "Unknown")
                if source not in docs_summary:
                    docs_summary[source] = {
                        "title": m.get("title", os.path.basename(source)),
                        "type": m.get("type", "file"),
                        "duration": m.get("duration", 0),
                        "size": m.get("file_size", "N/A"),
                        "mtime": m.get("mtime", 0),
                        "chunks": 0
                    }
                docs_summary[source]["chunks"] += 1

            # Format the output
            # Format the output
            import datetime
            output = []
            # We'll use a wider format for full paths
            header = f"{'Type':<8} | {'Source (Path/URL)':<70} | {'Effort':<10} | {'MTime':<20}"
            output.append(header)
            output.append("-" * len(header))
            
            for source, info in sorted(docs_summary.items(), key=lambda x: x[1]['mtime'], reverse=True):
                mtime_str = "N/A"
                if info["mtime"]:
                    mtime_str = datetime.datetime.fromtimestamp(info["mtime"]).strftime('%Y-%m-%d %H:%M:%S')
                
                # Format duration
                duration_sec = info.get("duration", 0)
                effort_str = f"{duration_sec // 60}m {duration_sec % 60}s"
                
                # Format display source
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
