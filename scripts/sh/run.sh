#!/bin/bash
# Wrapper script to run docBrain with the virtual environment

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"

# Check if venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Execute the python script with the provided arguments
"$VENV_PYTHON" "$PROJECT_ROOT/src/main.py" "$@"
