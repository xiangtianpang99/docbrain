import os
from dotenv import load_dotenv
from src.query import QueryEngine

load_dotenv()

def peek_content(limit=3):
    engine = QueryEngine()
    print("\n--- Peeking into Vector Store Chunks ---\n")
    
    try:
        # Get raw data from Chroma
        data = engine.vector_store.get(include=['documents', 'metadatas'])
        documents = data.get('documents', [])
        metadatas = data.get('metadatas', [])
        
        if not documents:
            print("The vector store is empty.")
            return

        count = len(documents)
        print(f"Total chunks in database: {count}")
        print(f"Showing first {min(limit, count)} chunks:\n")

        for i in range(min(limit, count)):
            source = metadatas[i].get('source', 'Unknown')
            content = documents[i]
            print(f"--- Chunk {i+1} (Source: {source}) ---")
            print(content[:500] + ("..." if len(content) > 500 else ""))
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    peek_content()
