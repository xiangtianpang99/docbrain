from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys
from dotenv import load_dotenv
from markdownify import markdownify as md

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import IngestionEngine
from src.query import QueryEngine

load_dotenv()

# Global Engines (Initialized in lifespan)
engine = None
query_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load engines on startup
    print("Loading AI Engines...")
    global engine, query_engine
    engine = IngestionEngine()
    query_engine = QueryEngine()
    print("AI Engines Loaded successfully.")
    yield
    # Clean up (if needed)

app = FastAPI(title="docBrain API", description="API for browser extension integration", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security: Simple API Key
API_KEY = os.getenv("API_KEY", "docbrain_default_key")

class WebpagePayload(BaseModel):
    url: str
    title: str
    content: str  # Can be HTML or raw text
    duration: Optional[int] = 0
    is_html: Optional[bool] = True

class ConfigPayload(BaseModel):
    watch_dir: Optional[str] = None
    api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    priority_keywords: Optional[str] = None

class QueryPayload(BaseModel):
    query: str
    quality_mode: Optional[bool] = False
    force_crew: Optional[bool] = False

def verify_token(authorization: Optional[str] = Header(None)):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return True

# Initialize Engines
# engine = IngestionEngine()
# query_engine = QueryEngine()

def update_env(key: str, value: str):
    """Update .env file and current environment"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
    
    found = False
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith(f"{key}="):
                f.write(f"{key}={value}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"{key}={value}\n")
    
    os.environ[key] = value

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/config")
def get_config(authorized: bool = Depends(verify_token)):
    return {
        "WATCH_DIR": os.getenv("WATCH_DIR", "./data"),
        "API_KEY": os.getenv("API_KEY", "docbrain_default_key"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
        "PRIORITY_KEYWORDS": os.getenv("PRIORITY_KEYWORDS", "")
    }

@app.post("/config")
def set_config(payload: ConfigPayload, authorized: bool = Depends(verify_token)):
    if payload.watch_dir is not None:
        update_env("WATCH_DIR", payload.watch_dir)
    if payload.api_key is not None:
        # Note: Changing API_KEY will require the client to use the new key immediately
        update_env("API_KEY", payload.api_key)
        global API_KEY
        API_KEY = payload.api_key
    if payload.deepseek_api_key is not None:
        update_env("DEEPSEEK_API_KEY", payload.deepseek_api_key)
    if payload.priority_keywords is not None:
        update_env("PRIORITY_KEYWORDS", payload.priority_keywords)
    
    return {"status": "success", "message": "Configuration updated and persisted."}

@app.post("/ingest/webpage")
async def ingest_webpage(payload: WebpagePayload, authorized: bool = Depends(verify_token)):
    try:
        content = payload.content
        if payload.is_html:
            content = md(payload.content, heading_style="ATX")
        
        chunks_count = engine.ingest_webpage(
            url=payload.url,
            title=payload.title,
            content=content,
            additional_duration=payload.duration
        )
        
        return {
            "status": "success",
            "message": f"Webpage indexed with {chunks_count} chunks.",
            "url": payload.url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def query_kb(payload: QueryPayload, authorized: bool = Depends(verify_token)):
    try:
        response = query_engine.ask(
            payload.query, 
            quality_mode=payload.quality_mode, 
            force_crew=payload.force_crew
        )
        
        # CrewAI returns a CrewOutput object. We need to extract the raw string.
        if hasattr(response, 'raw'):
            response = response.raw
        elif not isinstance(response, str):
            response = str(response)

        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
def list_documents(authorized: bool = Depends(verify_token)):
    try:
        docs = query_engine.get_documents_data()
        return {"status": "success", "documents": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
def get_file(path: str = Query(..., description="Absolute path to the file"), authorized: bool = Depends(verify_token)):
    """
    Securely serve files for preview. 
    Only allows access to files within the currently configured WATCH_DIR or default data directory.
    """
    try:
        # Normalize paths
        target_path = os.path.abspath(path)
        
        # Dynamic allowed paths
        allowed_roots = []
        
        # 1. The main configured WATCH_DIR
        watch_dir = os.getenv("WATCH_DIR")
        if watch_dir:
            allowed_roots.append(os.path.abspath(watch_dir))
            
        # 2. Always allow the default project 'data' folder as a fallback/base
        project_data_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
        allowed_roots.append(project_data_dir)
        
        # Check permissions
        is_allowed = False
        for root in allowed_roots:
            # We use commonpath to ensure target_path is truly a subpath of root
            try:
                if os.path.commonpath([root, target_path]) == root:
                    is_allowed = True
                    break
            except ValueError:
                continue # Paths on different drives
        
        if not is_allowed:
            # Helpful error for debugging
            print(f"Access Denied: '{target_path}' is not in allowed roots: {allowed_roots}")
            raise HTTPException(status_code=403, detail="Access denied: File is not in a configured source directory.")
        
        if not os.path.exists(target_path):
             raise HTTPException(status_code=404, detail="File not found.")
             
        # Determine media type for inline display where possible
        media_type = None
        ext = os.path.splitext(target_path)[1].lower()
        if ext == ".pdf":
            media_type = "application/pdf"
        elif ext in [".jpg", ".jpeg"]:
            media_type = "image/jpeg"
        elif ext == ".png":
            media_type = "image/png"
        elif ext == ".md":
            media_type = "text/markdown"
        elif ext in [".txt", ".log"]:
            media_type = "text/plain"
            
        return FileResponse(target_path, media_type=media_type)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents")
def delete_document(source: str, authorized: bool = Depends(verify_token)):
    try:
        engine.remove_document(source)
        return {"status": "success", "message": f"Document {source} removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/db")
def debug_db(authorized: bool = Depends(verify_token)):
    try:
        count = query_engine.vector_store._collection.count()
        cwd = os.getcwd()
        abs_path = os.path.abspath("./chroma_db")
        db_files = os.listdir("./chroma_db") if os.path.exists("./chroma_db") else "DIR_NOT_FOUND"
        return {
            "cwd": cwd,
            "db_path_resolved": abs_path,
            "doc_count": count,
            "db_files": db_files
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
