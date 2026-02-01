from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
from dotenv import load_dotenv
from markdownify import markdownify as md

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import IngestionEngine
from src.query import QueryEngine
from src.config_manager import config_manager
from src.scheduler import scheduler
from src.monitor import global_monitor, start_watching

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
    
    # Initialize background services based on config
    print("Initializing Background Services...")
    global_monitor.start() # Starts watching paths from config
    await scheduler.start() # Starts scheduler loop
    
    print("AI Engines & Services Loaded successfully.")
    yield
    # Clean up
    await scheduler.stop()
    global_monitor.stop()

app = FastAPI(title="docBrain API", description="API for browser extension integration", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security: Simple API Key
# Now we prefer the one from config, fallback to env or default
def get_api_key():
    return config_manager.get("api_key") or os.getenv("API_KEY", "docbrain_default_key")

class WebpagePayload(BaseModel):
    url: str
    title: str
    content: str
    duration: Optional[int] = 0
    is_html: Optional[bool] = True

class ConfigPayload(BaseModel):
    watch_paths: Optional[List[str]] = None
    schedule_interval_minutes: Optional[int] = None
    enable_watchdog: Optional[bool] = None
    enable_scheduler: Optional[bool] = None
    api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

class QueryPayload(BaseModel):
    query: str
    quality_mode: Optional[bool] = False
    force_crew: Optional[bool] = False

def verify_token(authorization: Optional[str] = Header(None)):
    current_key = get_api_key()
    if authorization != f"Bearer {current_key}":
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return True

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/config")
def get_config(authorized: bool = Depends(verify_token)):
    return config_manager.config

@app.post("/config")
def set_config(payload: ConfigPayload, authorized: bool = Depends(verify_token)):
    update_data = {}
    if payload.watch_paths is not None:
        update_data["watch_paths"] = payload.watch_paths
    if payload.schedule_interval_minutes is not None:
        update_data["schedule_interval_minutes"] = payload.schedule_interval_minutes
    if payload.enable_watchdog is not None:
        update_data["enable_watchdog"] = payload.enable_watchdog
    if payload.enable_scheduler is not None:
        update_data["enable_scheduler"] = payload.enable_scheduler
    if payload.api_key is not None:
        update_data["api_key"] = payload.api_key
    if payload.deepseek_api_key is not None:
        update_data["deepseek_api_key"] = payload.deepseek_api_key
        # Also update env for heavy libraries that might depend on os.getenv
        os.environ["DEEPSEEK_API_KEY"] = payload.deepseek_api_key

    if update_data:
        config_manager.update(update_data)
        
        # Apply changes immediately to services
        if "watch_paths" in update_data or "enable_watchdog" in update_data:
            print("Config updated: Restarting Monitor...")
            global_monitor.start()
            
    return {"status": "success", "message": "Configuration updated.", "config": config_manager.config}

@app.post("/actions/index")
async def trigger_indexing(background_tasks: BackgroundTasks, authorized: bool = Depends(verify_token)):
    """Manually trigger immediate indexing of all watched paths."""
    watch_paths = config_manager.get("watch_paths", [])
    background_tasks.add_task(scheduler.run_ingestion, watch_paths)
    return {"status": "success", "message": "Indexing started in background."}

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

@app.get("/files")
def get_file(path: str = Query(..., description="Absolute path to the file"), authorized: bool = Depends(verify_token)):
    """
    Securely serve files for preview. 
    Allows access to files within ANY of the configured watch_paths.
    """
    try:
        target_path = os.path.abspath(path)
        
        # Construct allowed roots from config
        allowed_roots = []
        user_paths = config_manager.get("watch_paths", [])
        for p in user_paths:
             allowed_roots.append(os.path.abspath(p))

        # Always allow default data dir
        project_data_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
        allowed_roots.append(project_data_dir)
        
        # Check permissions
        is_allowed = False
        for root in allowed_roots:
            try:
                if os.path.commonpath([root, target_path]) == root:
                    is_allowed = True
                    break
            except ValueError:
                continue 
        
        if not is_allowed:
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
            "db_files": db_files,
            "config": config_manager.config
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
