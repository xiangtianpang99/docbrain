import asyncio
import time
import os
from src.config_manager import config_manager
from src.ingest import IngestionEngine

class DocBrainScheduler:
    def __init__(self):
        self.running = False
        self.task = None
        self.ingestion_engine = IngestionEngine()

    async def start(self):
        if self.running:
            return
        
        self.running = True
        print("Scheduler started.")
        self.task = asyncio.create_task(self.run_loop())

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("Scheduler stopped.")

    async def run_loop(self):
        while self.running:
            try:
                # 检查配置中是否启用了调度器
                if not config_manager.get("enable_scheduler", True):
                    await asyncio.sleep(60) # 1分钟后再次检查
                    continue
                
                interval_minutes = config_manager.get("schedule_interval_minutes", 60)
                watch_paths = config_manager.get("watch_paths", ["./data"])
                
                # Resolve relative paths relative to backend root
                backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                resolved_paths = []
                for p in watch_paths:
                    if not os.path.isabs(p):
                        if not os.path.exists(p):
                            potential = os.path.join(backend_root, p)
                            if os.path.exists(potential):
                                p = potential
                    resolved_paths.append(os.path.normpath(p))
                
                print(f"调度器: 开始对 {resolved_paths} 进行计划索引...")
                
                # 在单独的线程中运行索引，以免阻塞事件循环
                await asyncio.to_thread(self.run_ingestion, resolved_paths)
                
                print(f"调度器: 索引完成。下次运行将在 {interval_minutes} 分钟后。")
                
                # Wait for the next interval
                await asyncio.sleep(interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"调度器错误: {e}")
                await asyncio.sleep(60) # 出错后1分钟重试

    def run_ingestion(self, paths):
        for path in paths:
            print(f"Scheduler: Ingesting {path}...")
            self.ingestion_engine.ingest_directory(path)

scheduler = DocBrainScheduler()
