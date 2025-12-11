#!/bin/bash

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "🚀 Starting Ollama server..."
    ollama serve &
    echo "⏳ Waiting 5s for Ollama..."
    sleep 5
else
    echo "✅ Ollama is running."
fi

# Activate Virtual Environment
if [ -d ".venv" ]; then
    echo "🐍 Activating Python environment..."
    source .venv/bin/activate
else
    echo "❌ Error: .venv not found. Run 'python3 -m venv .venv' first."
    exit 1
fi

# Run the App
echo "🎙️ Starting Meeting Summarizer..."
python main.py
