#!/bin/bash

# docBrain setup wrapper
echo "Starting docBrain setup..."

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Grant execution permission to other scripts if they exist
chmod +x *.sh 2>/dev/null

# Check for python3
if command -v python3 >/dev/null 2>&1; then
    python3 bootstrap.py
elif command -v python >/dev/null 2>&1; then
    python bootstrap.py
else
    echo "Error: Python 3 not found. Please install Python 3.10+ and try again."
    exit 1
fi
