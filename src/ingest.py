import os
import glob
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# Loaders
import pypdf
import docx
import openpyxl
from pptx import Presentation

class IngestionEngine:
    def __init__(self, persist_directory: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        self.persist_directory = persist_directory
        print(f"Loading embedding model: {model_name}...")
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_model
        )

    def parse_file(self, file_path: str) -> List[Document]:
        """
        Parse a single file based on its extension and return Documents.
        """
        ext = os.path.splitext(file_path)[1].lower()
        content = ""
        try:
            if ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif ext == ".pdf":
                reader = pypdf.PdfReader(file_path)
                text_list = []
                for page in reader.pages:
                    text_list.append(page.extract_text())
                content = "\n".join(text_list)
            elif ext == ".docx":
                doc = docx.Document(file_path)
                content = "\n".join([p.text for p in doc.paragraphs])
            elif ext == ".xlsx":
                wb = openpyxl.load_workbook(file_path, data_only=True)
                text_list = []
                for sheet in wb.sheetnames:
                    ws = wb[sheet]
                    for row in ws.iter_rows(values_only=True):
                        row_text = " ".join([str(cell) for cell in row if cell is not None])
                        if row_text:
                            text_list.append(row_text)
                content = "\n".join(text_list)
            elif ext == ".pptx":
                prs = Presentation(file_path)
                text_list = []
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            text_list.append(shape.text)
                content = "\n".join(text_list)
            else:
                print(f"Unsupported file format: {file_path}")
                return []

            if not content.strip():
                return []
            
            # Get file stats for metadata
            stats = os.stat(file_path)
            metadata = {
                "source": file_path,
                "file_size": stats.st_size,
                "mtime": stats.st_mtime
            }
            
            # Return as a single document (splitter will handle chunking)
            return [Document(page_content=content, metadata=metadata)]

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

    def split_documents(self, documents: List[Document]) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        return text_splitter.split_documents(documents)

    def process_file(self, file_path: str):
        """
        Ingest a single file: Delete old vectors -> Parse -> Split -> Add new vectors.
        """
        abs_path = os.path.abspath(file_path)
        print(f"Processing file: {abs_path}")
        
        # 1. Remove existing vectors for this file to avoid duplicates
        # ChromaDB delete by metadata
        try:
            # Try deleting by absolute path
            self.vector_store._collection.delete(where={"source": abs_path})
            
            # Also try deleting by raw path if it differs (legacy support)
            if file_path != abs_path:
                 self.vector_store._collection.delete(where={"source": file_path})
            
            # Also try deleting relative path from cwd (legacy support)
            rel_path = os.path.relpath(abs_path)
            if rel_path != abs_path and rel_path != file_path:
                 self.vector_store._collection.delete(where={"source": rel_path})
                 
        except Exception as e:
            # Maybe collection is empty or other issue, log minimal
            pass

        # 2. Parse
        documents = self.parse_file(abs_path)
        if not documents:
            print(f"No content found in {file_path} or parse error.")
            return

        # 3. Split
        chunks = self.split_documents(documents)
        
        # 4. Add
        if chunks:
            self.vector_store.add_documents(chunks)
            print(f"Updated {file_path}: {len(chunks)} chunks indexed.")
        
    def remove_document(self, file_path: str):
        """
        Remove vectors associated with a file.
        """
        try:
            file_path = os.path.abspath(file_path)
            print(f"Removing documents for: {file_path}")
            self.vector_store._collection.delete(where={"source": file_path})
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

    def ingest_directory(self, source_dir: str):
        """
        Ingest all supported files in a directory.
        """
        print(f"Scanning directory: {source_dir}")
        patterns = ["**/*.txt", "**/*.md", "**/*.pdf", "**/*.docx", "**/*.xlsx", "**/*.pptx"]
        all_files = []
        for pattern in patterns:
            # Recursive glob might return relative paths
            found = glob.glob(os.path.join(source_dir, pattern), recursive=True)
            all_files.extend(found)
        
        for file_path in all_files:
            # process_file will handle abspath conversion
            self.process_file(file_path)
        
        print("Ingestion complete.")

if __name__ == "__main__":
    ingestor = IngestionEngine()
    ingestor.ingest_directory("./data")
