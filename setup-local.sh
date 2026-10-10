#!/usr/bin/env bash
set -euo pipefail

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is required. Install it from https://ollama.com/download/linux"
  exit 1
fi

MODEL="${OLLAMA_MODEL:-llama3.2:1b}"
echo "Pulling local model: ${MODEL}"
ollama pull "${MODEL}"

if [ ! -f .env ]; then
  cp .env.example .env
fi

docker compose up -d postgres qdrant

if python3 -m venv .venv >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r backend/requirements.txt
else
  python3 -m pip install --user --break-system-packages -r backend/requirements.txt
fi
npm install

echo "Local environment ready. Start Ollama with: ollama serve"
echo "Then start the API with: python3 -m uvicorn backend.app.main:app --reload --port 8000"
echo "And the frontend with: npm run dev"
