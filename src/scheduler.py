import asyncio
import time
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
                # Check if scheduler is enabled in config
                if not config_manager.get("enable_scheduler", True):
                    await asyncio.sleep(60) # check again in 1 min
                    continue
                
                interval_minutes = config_manager.get("schedule_interval_minutes", 60)
                watch_paths = config_manager.get("watch_paths", ["./data"])
                
                print(f"Scheduler: Starting scheduled ingestion for {watch_paths}...")
                
                # Run ingestion in a separate thread to not block the event loop
                await asyncio.to_thread(self.run_ingestion, watch_paths)
                
                print(f"Scheduler: Ingestion complete. Next run in {interval_minutes} minutes.")
                
                # Wait for the next interval
                await asyncio.sleep(interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Scheduler Error: {e}")
                await asyncio.sleep(60) # retry in 1 min if error

    def run_ingestion(self, paths):
        for path in paths:
            print(f"Scheduler: Ingesting {path}...")
            self.ingestion_engine.ingest_directory(path)

scheduler = DocBrainScheduler()
