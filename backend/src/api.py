from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
from dotenv import load_dotenv
from dotenv import load_dotenv
from markdownify import markdownify as md
import logging

# 定义日志过滤器，屏蔽 /system/status 的日志
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/system/status") == -1

# 将过滤器应用到 uvicorn 的访问日志
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingest import IngestionEngine
from src.query import QueryEngine
from src.config_manager import config_manager
from src.scheduler import scheduler
from src.monitor import global_monitor, start_watching

load_dotenv()

# 全局引擎 (在 lifespan 中初始化)
engine = None
query_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时加载引擎
    print("正在加载 AI 引擎...")
    global engine, query_engine
    engine = IngestionEngine()
    # 共享向量存储实例以确保一致性
    query_engine = QueryEngine(vector_store=engine.vector_store)
    
    # 根据配置初始化后台服务
    print("正在初始化后台服务...")
    global_monitor.start() # 启动监控
    await scheduler.start() # 启动调度器
    
    print("AI 引擎及服务加载成功。")
    yield
    # 清理
    await scheduler.stop()
    global_monitor.stop()

app = FastAPI(title="docBrain API", description="浏览器扩展集成 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全: 简单的 API Key
# 优先使用配置中的，回退到环境变量或默认值
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
    
    # 处理 LLM 配置
    if payload.active_provider is not None:
        update_data["active_provider"] = payload.active_provider
    if payload.llm_providers is not None:
        update_data["llm_providers"] = payload.llm_providers
        
    # 兼容旧版本 (可选)
    if payload.deepseek_api_key is not None:
        update_data["deepseek_api_key"] = payload.deepseek_api_key
        # 不再设置环境变量，依赖 provider 配置
        
    if update_data:
        config_manager.update(update_data)
        
        # 处理路径变更
        if "watch_paths" in update_data:
            new_paths = set(update_data["watch_paths"])
            
            # 1. 处理移除的路径 -> 清理 DB
            removed_paths = old_paths - new_paths
            for path in removed_paths:
                print(f"配置: 路径已移除 {path}. 清理文档中...")
                engine.remove_documents_by_root(path)
            
            # 2. 处理新增的路径 -> 触发索引
            added_paths = new_paths - old_paths
            if added_paths:
                print(f"配置: 新增路径 {added_paths}. 触发索引...")
                background_tasks.add_task(scheduler.run_ingestion, list(added_paths))

        # 如果需要重启监控器
        if "watch_paths" in update_data or "enable_watchdog" in update_data:
            print("配置已更新: 重启监控器...")
            global_monitor.start()
            
    return {"status": "success", "message": "Configuration updated.", "config": config_manager.config}

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
    """手动触发所有监控路径的立即索引。"""
    watch_paths = config_manager.get("watch_paths", [])
    background_tasks.add_task(scheduler.run_ingestion, watch_paths)
    return {"status": "success", "message": "已在后台开始索引。"}

@app.get("/system/status")
def get_system_status(authorized: bool = Depends(verify_token)):
    """
    获取当前后台服务状态。
    前端用于判断索引是否完成。
    """
    # 检查监控器的索引器状态
    monitor_jobs = global_monitor.ingestor.busy_jobs if global_monitor and global_monitor.ingestor else 0
    monitor_update = global_monitor.ingestor.last_update_time if global_monitor and global_monitor.ingestor else 0
    
    # 同时检查本地 API 引擎 (如网页索引)
    api_jobs = engine.busy_jobs if engine else 0
    api_update = engine.last_update_time if engine else 0
    
    total_jobs = monitor_jobs + api_jobs
    last_update = max(monitor_update, api_update)
    
    return {
        "status": "success",
        "is_indexing": total_jobs > 0,
        "pending_jobs": total_jobs,
        "last_update": last_update 
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

from src.history_manager import history_manager

# --- History / Session APIs ---

@app.get("/sessions")
def list_sessions(authorized: bool = Depends(verify_token)):
    return {"status": "success", "sessions": history_manager.get_sessions()}

@app.post("/sessions")
def create_session(authorized: bool = Depends(verify_token)):
    session_id = history_manager.create_session("New Chat")
    return {"status": "success", "session_id": session_id, "title": "New Chat"}

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, authorized: bool = Depends(verify_token)):
    history_manager.delete_session(session_id)
    return {"status": "success", "message": "Session deleted"}

@app.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, authorized: bool = Depends(verify_token)):
    msgs = history_manager.get_messages(session_id)
    return {"status": "success", "messages": msgs}


@app.post("/query")
async def query_kb(payload: QueryPayload, session_id: Optional[str] = Query(None), authorized: bool = Depends(verify_token)):
    try:
        # 1. 记录用户提问
        if session_id:
            history_manager.add_message(session_id, "user", payload.query)

        response = query_engine.ask(
            payload.query, 
            quality_mode=payload.quality_mode, 
            force_crew=payload.force_crew
        )
        
        if hasattr(response, 'raw'):
            response = response.raw
        elif not isinstance(response, str):
            response = str(response)

        # 2. 记录 AI 回复
        if session_id:
             history_manager.add_message(session_id, "assistant", response)

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
        # api.py is in backend/src, so dirname(dirname(abspath)) is backend/
        backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Default data dir is backend/data
        project_data_dir = os.path.join(backend_root, "data")
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
