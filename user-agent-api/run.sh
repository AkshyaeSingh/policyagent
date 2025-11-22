#!/bin/bash

# Script to run the user-agent-api with virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -e .
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if .env file exists and has content
if [ ! -f ".env" ] || [ ! -s ".env" ]; then
    echo "Warning: .env file is missing or empty!"
    echo "Please create .env file with: OPENROUTER_API_KEY=your_key_here"
    exit 1
fi

# Check if API key is set
if ! grep -q "OPENROUTER_API_KEY=" .env || grep -q "OPENROUTER_API_KEY=$" .env || grep -q "OPENROUTER_API_KEY=your" .env; then
    echo "Warning: OPENROUTER_API_KEY not properly set in .env file"
    echo "Please add your OpenRouter API key to .env file"
    exit 1
fi

echo "Starting User-Agent API server on http://localhost:8001"
echo "Press Ctrl+C to stop"
echo ""

python main.py

