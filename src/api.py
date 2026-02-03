from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
    # Share the same vector store instance to ensure consistency between ingestion and query
    query_engine = QueryEngine(vector_store=engine.vector_store)
    
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
    active_provider: Optional[str] = None
    llm_providers: Optional[Dict[str, Any]] = None

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
def set_config(payload: ConfigPayload, background_tasks: BackgroundTasks, authorized: bool = Depends(verify_token)):
    old_paths = set(config_manager.get("watch_paths", []))
    
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
    
    # Handle LLM configurations
    if payload.active_provider is not None:
        update_data["active_provider"] = payload.active_provider
    if payload.llm_providers is not None:
        update_data["llm_providers"] = payload.llm_providers
        
    # Legacy support (optional, can be removed if we want to force migration)
    if payload.deepseek_api_key is not None:
        update_data["deepseek_api_key"] = payload.deepseek_api_key
        # We don't set env var here anymore, rely on provider config
        
    if update_data:
        config_manager.update(update_data)
        
        # Handle Path Changes
        if "watch_paths" in update_data:
            new_paths = set(update_data["watch_paths"])
            
            # 1. Handle Removed Paths -> Clean up DB
            removed_paths = old_paths - new_paths
            for path in removed_paths:
                print(f"Config: Path removed {path}. Cleaning up documents...")
                engine.remove_documents_by_root(path)
            
            # 2. Handle Added Paths -> Trigger Indexing
            added_paths = new_paths - old_paths
            if added_paths:
                print(f"Config: New paths added {added_paths}. Triggering ingestion...")
                background_tasks.add_task(scheduler.run_ingestion, list(added_paths))

        # Restart Monitor if needed
        if "watch_paths" in update_data or "enable_watchdog" in update_data:
            print("Config updated: Restarting Monitor...")
            global_monitor.start()
            
    return {"status": "success", "message": "Configuration updated.", "config": config_manager.config}

from src.llm_provider import LLMFactory

@app.post("/actions/browse_folder")
def browse_folder(authorized: bool = Depends(verify_token)):
    """
    Open a native directory selection dialog using PowerShell (Windows).
    Running on the server side (Backend).
    """
    try:
        import subprocess
        
        # PowerShell command to open FolderBrowserDialog
        ps_script = """
        Add-Type -AssemblyName System.Windows.Forms
        $f = New-Object System.Windows.Forms.FolderBrowserDialog
        $f.ShowNewFolderButton = $true
        if ($f.ShowDialog() -eq 'OK') {
            return $f.SelectedPath
        }
        """
        
        # Run PowerShell command
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, 
            text=True, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        folder_path = result.stdout.strip()
        
        if folder_path:
            # Normalize path for Windows
            folder_path = os.path.normpath(folder_path)
            return {"status": "success", "path": folder_path}
        else:
            return {"status": "cancelled", "path": None}
            
    except Exception as e:
        print(f"Browse Folder Error: {e}")
        return {"status": "error", "message": str(e)}

class TestLLMPayload(BaseModel):
    provider: str
    api_key: Optional[str] = ""
    base_url: Optional[str] = ""
    model: Optional[str] = ""

@app.post("/actions/test_llm")
async def test_llm_connection(payload: TestLLMPayload, authorized: bool = Depends(verify_token)):
    """
    Test connectivity with a specific LLM provider configuration.
    This creates a temporary provider instance and attempts a simple generation.
    """
    try:
        # Construct a temporary config dictionary
        config = {}
        if payload.api_key:
            config["api_key"] = payload.api_key
        if payload.base_url:
            config["base_url"] = payload.base_url
        if payload.model:
            config["model"] = payload.model
            
        print(f"Testing connection for provider: {payload.provider} with model {payload.model}...")
        
        # Get provider instance
        provider = LLMFactory.get_provider(payload.provider)
        
        # Get LangChain LLM
        llm = provider.get_langchain_llm(config)
        
        # invoke a simple test
        from langchain_core.messages import HumanMessage
        import time
        
        start_time = time.time()
        response = llm.invoke([HumanMessage(content="Hello, reply with just 'OK'.")])
        duration = time.time() - start_time
        
        return {
            "status": "success",
            "message": "Connection successful.",
            "latency_ms": int(duration * 1000),
            "reply": response.content
        }
        
    except Exception as e:
        print(f"LLM Test Failed: {e}")
        return {
            "status": "error", 
            "message": str(e)
        }

@app.post("/actions/index")
async def trigger_indexing(background_tasks: BackgroundTasks, authorized: bool = Depends(verify_token)):
    """Manually trigger immediate indexing of all watched paths."""
    watch_paths = config_manager.get("watch_paths", [])
    background_tasks.add_task(scheduler.run_ingestion, watch_paths)
    return {"status": "success", "message": "Indexing started in background."}

@app.get("/system/status")
def get_system_status(authorized: bool = Depends(verify_token)):
    """
    Get current background service status.
    Useful for frontend to know when indexing is complete.
    """
    # Check monitor's ingestor status
    monitor_jobs = global_monitor.ingestor.busy_jobs if global_monitor and global_monitor.ingestor else 0
    # Also check local API engine (e.g. for webpage ingest)
    api_jobs = engine.busy_jobs if engine else 0
    
    total_jobs = monitor_jobs + api_jobs
    
    return {
        "status": "success",
        "is_indexing": total_jobs > 0,
        "pending_jobs": total_jobs
    }

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
