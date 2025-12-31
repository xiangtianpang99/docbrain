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
            docs = self.vector_store.similarity_search(query, k=k)
            return [doc.page_content for doc in docs]
        
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
        top_docs = [r[0] for r in ranked_results[:k]]
        
        return [doc.page_content for doc in top_docs]

    def ask(self, query: str, quality_mode: bool = False) -> str:
        """
        Ask a question to the LLM with retrieved context.
        """
        context_chunks = self.retrieve_context(query, quality_mode=quality_mode)
        if not context_chunks:
            return "No relevant context found in the knowledge base."
        
        context_str = "\n\n---\n\n".join(context_chunks)
        
        system_prompt = """你是一个专业的个人知识管理助手和工作总结专家。
你的任务是基于提供的本地文档片段，进行逻辑严密的归纳、总结和分析。

遵循以下准则：
1. **结构化输出**：按时间顺序、项目维度或逻辑分点进行整理，确保内容易于阅读。
2. **区分事实与观点**：明确区分工作成果（事实）与个人心得或反思（分析）。
3. **多文档关联**：尝试发现不同文档片段之间的内在联系，形成完整的进展视图。
4. **诚实性**：如果提供的上下文不足以回答问题，请如实告知，并基于现有信息给出搜索建议。

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
                        "size": m.get("file_size", "N/A"),
                        "mtime": m.get("mtime", 0),
                        "chunks": 0
                    }
                docs_summary[source]["chunks"] += 1

            # Format the output
            import datetime
            output = []
            output.append(f"{'Source File':<60} | {'Size (KB)':<10} | {'Modified Time':<20} | {'Chunks':<6}")
            output.append("-" * 105)
            
            for source, info in sorted(docs_summary.items()):
                mtime_str = "N/A"
                if info["mtime"]:
                    mtime_str = datetime.datetime.fromtimestamp(info["mtime"]).strftime('%Y-%m-%d %H:%M:%S')
                
                size_str = "N/A"
                if isinstance(info["size"], (int, float)):
                    size_str = f"{info['size'] / 1024:.2f}"
                
                # Truncate long source paths if needed
                display_source = source
                if len(source) > 60:
                    display_source = "..." + source[-57:]
                    
                output.append(f"{display_source:<60} | {size_str:<10} | {mtime_str:<20} | {info['chunks']:<6}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error listing documents: {e}"

if __name__ == "__main__":
    # Test run (requires DB to be populated first)
    engine = QueryEngine()
    response = engine.ask("What is this project about?")
    print("\n--- Response ---\n")
    print(response)
