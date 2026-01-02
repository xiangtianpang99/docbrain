from fastapi import FastAPI, HTTPException, Header, Depends
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

app = FastAPI(title="docBrain API", description="API for browser extension integration")

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
engine = IngestionEngine()
query_engine = QueryEngine()

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

@app.delete("/documents")
def delete_document(source: str, authorized: bool = Depends(verify_token)):
    try:
        engine.remove_document(source)
        return {"status": "success", "message": f"Document {source} removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
