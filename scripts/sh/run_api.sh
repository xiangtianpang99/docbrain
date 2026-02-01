#!/bin/bash

# Port can be configured via environment variable
PORT=${PORT:-8000}

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Project Root directory
ROOT_DIR="$SCRIPT_DIR/../.."

# Ensure venv exists
if [ ! -d "$ROOT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found. Please set up the environment first."
    exit 1
fi

# Set PYTHONPATH to include root
export PYTHONPATH=$ROOT_DIR:$PYTHONPATH

echo "Starting docBrain API Server on port $PORT..."
"$ROOT_DIR/.venv/bin/python" "$ROOT_DIR/src/api.py"
