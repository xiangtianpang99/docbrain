import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.ingest import IngestionEngine

class DocHandler(FileSystemEventHandler):
    def __init__(self, ingestor: IngestionEngine):
        self.ingestor = ingestor

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
        
        if event.event_type == 'deleted':
             self.ingestor.remove_document(filepath)
        elif event.event_type in ['created', 'modified']:
             # Small delay to ensure file write is complete
             time.sleep(1)
             self.ingestor.process_file(filepath)
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

def start_watching(directory: str):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    print(f"Starting file monitor on: {directory}")
    ingestor = IngestionEngine()
    
    # Initial scan
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
