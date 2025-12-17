import os
import glob
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

class IngestionEngine:
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the Ingestion Engine.
        Args:
            persist_directory: Directory to store the ChromaDB.
            model_name: Name of the SentenceTransformer model to use.
        """
        self.persist_directory = persist_directory
        print(f"Loading embedding model: {model_name}...")
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        self.vector_store = None

    def load_documents(self, source_dir: str) -> List[Document]:
        """
        Load .txt and .md files from the source directory.
        """
        documents = []
        types = ["**/*.txt", "**/*.md"]
        for file_type in types:
            files = glob.glob(os.path.join(source_dir, file_type), recursive=True)
            for file_path in files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    if content.strip():
                        # Store metadata for retrieval later
                        metadata = {"source": file_path}
                        doc = Document(page_content=content, metadata=metadata)
                        documents.append(doc)
                        print(f"Loaded: {file_path}")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(documents)
        print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        return chunks

    def ingest(self, source_dir: str):
        """
        Main method to ingest documents from a directory.
        """
        print(f"Scanning directory: {source_dir}")
        documents = self.load_documents(source_dir)
        if not documents:
            print("No documents found.")
            return

        chunks = self.split_documents(documents)
        
        print("Creating/Updating Vector Store...")
        if self.vector_store is None:
             self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embedding_model,
                persist_directory=self.persist_directory
            )
        else:
            self.vector_store.add_documents(chunks)
        
        # In newer versions of Chroma/LangChain, persist is often automatic, 
        # but calling it explicitly if available is safer for some versions.
        if hasattr(self.vector_store, 'persist'):
             self.vector_store.persist()
        
        print(f"Ingestion complete. Database persisted at {self.persist_directory}")

if __name__ == "__main__":
    # Test run
    ingestor = IngestionEngine()
    ingestor.ingest("./")
