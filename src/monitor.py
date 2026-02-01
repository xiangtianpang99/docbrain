import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.ingest import IngestionEngine

class DocHandler(FileSystemEventHandler):
    def __init__(self, ingestor: IngestionEngine):
        self.ingestor = ingestor
        # Track last modification time to estimate effort
        # { filepath: last_event_time }
        self.file_activity = {}
        self.session_threshold = 900  # 15 minutes gap starts a new session

    def process(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        # Ignore hidden files or temp files
        filename = os.path.basename(filepath)
        
        # New: Ignore specific system/dev directories in path
        ignore_dirs = {
            "node_modules", ".git", ".venv", ".vscode", "__pycache__", 
            "System Volume Information", "$RECYCLE.BIN", ".idea"
        }
        path_parts = set(filepath.replace("\\", "/").split("/"))
        if not path_parts.isdisjoint(ignore_dirs):
            return

        if filename.startswith('.') or filename.startswith('~'):
            return

        print(f"Event detected: {event.event_type} - {filepath}")
        
        now = time.time()
        additional_duration = 0
        
        if filepath in self.file_activity:
            last_time = self.file_activity[filepath]
            gap = now - last_time
            if gap < self.session_threshold:
                additional_duration = int(gap)
        
        # Update last seen time
        self.file_activity[filepath] = now

        if event.event_type == 'deleted':
             self.ingestor.remove_document(filepath)
             if filepath in self.file_activity:
                 del self.file_activity[filepath]
        elif event.event_type in ['created', 'modified']:
             # Small delay to ensure file write is complete
             time.sleep(1)
             self.ingestor.process_file(filepath, additional_duration=additional_duration)
        elif event.event_type == 'moved':
             # Handle rename: delete old, add new
             self.ingestor.remove_document(event.src_path)
             if not event.dest_path.split("/")[-1].startswith('.'):
                 time.sleep(1)
                 self.ingestor.process_file(event.dest_path)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

    def on_deleted(self, event):
        self.process(event)

    def on_moved(self, event):
        self.process(event)

from typing import List
from src.config_manager import config_manager

class GlobalMonitor:
    def __init__(self):
        self.observer = None
        self.ingestor = IngestionEngine()
        self.handler = DocHandler(self.ingestor)

    def start(self):
        self.stop() # Ensure previous observer is stopped
        
        if not config_manager.get("enable_watchdog", True):
             print("Real-time monitoring is disabled in config.")
             return

        self.observer = Observer()
        watch_paths = config_manager.get("watch_paths", ["./data"])
        
        scheduled_count = 0
        for directory in watch_paths:
            if os.path.exists(directory):
                print(f"Monitor: Scheduling watch on {directory}")
                self.observer.schedule(self.handler, directory, recursive=True)
                scheduled_count += 1
            else:
                print(f"Monitor: Warning - Directory {directory} does not exist.")
        
        if scheduled_count > 0:
            self.observer.start()
            print(f"Monitor: Started watching {scheduled_count} directories.")
        else:
            print("Monitor: No valid directories to watch.")

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("Monitor: Stopped.")

global_monitor = GlobalMonitor()

def start_watching(directory: str = None):
    # Backward compatibility wrapper for CLI
    if directory:
        # If CLI provides a specific directory, override config temporarily or just watch that one
        if not os.path.exists(directory):
            print(f"Directory {directory} does not exist.")
            return

        print(f"Starting file monitor on: {directory}")
        ingestor = IngestionEngine()
        print("Performing initial scan...")
        ingestor.ingest_directory(directory)

        event_handler = DocHandler(ingestor)
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=True)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        # Server mode uses the global monitor instance
        global_monitor.start()
