import argparse
import sys
import os

# Ensure src is in path if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ingest import IngestionEngine
from src.query import QueryEngine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="docBrain: Local Knowledge Base CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Load default watch dir from environment
    default_dir = os.getenv("WATCH_DIR", "./data")

    # Command: index
    index_parser = subparsers.add_parser("index", help="Index documents from a directory")
    index_parser.add_argument("directory", type=str, nargs='?', default=default_dir, help="Path to the directory containing documents")

    # Command: ask
    ask_parser = subparsers.add_parser("ask", help="Ask a question based on indexed documents")
    ask_parser.add_argument("query", type=str, help="The question or prompt")

    # Command: watch
    watch_parser = subparsers.add_parser("watch", help="Monitor a directory for changes")
    watch_parser.add_argument("directory", type=str, nargs='?', default=default_dir, help="Path to the directory to monitor")

    # Command: list
    subparsers.add_parser("list", help="List all indexed documents and their stats")

    args = parser.parse_args()

    if args.command == "index":
        if not os.path.exists(args.directory):
            print(f"Error: Directory '{args.directory}' does not exist.")
            return
        
        engine = IngestionEngine()
        engine.ingest_directory(args.directory)

    elif args.command == "watch":
        from src.monitor import start_watching
        start_watching(args.directory)

    elif args.command == "list":
        engine = QueryEngine()
        print(engine.list_documents())

    elif args.command == "ask":
        engine = QueryEngine()
        response = engine.ask(args.query)
        print("\n" + "="*50)
        print("Answer:")
        print("="*50)
        print(response)
        print("="*50 + "\n")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
