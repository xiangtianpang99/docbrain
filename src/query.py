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

    def retrieve_context(self, query: str, k: int = 4) -> List[str]:
        """
        Retrieve relevant document chunks for a query.
        """
        print(f"Searching for context related to: '{query}'")
        docs = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def ask(self, query: str) -> str:
        """
        Ask a question to the LLM with retrieved context.
        """
        context_chunks = self.retrieve_context(query)
        if not context_chunks:
            return "No relevant context found in the knowledge base."
        
        context_str = "\n\n---\n\n".join(context_chunks)
        
        system_prompt = """You are a helpful assistant for a local knowledge base. 
Use the provided context to answer the user's question or complete their request.
If the answer is not in the context, say so, but you can use your general knowledge to supplement if asked."""

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
