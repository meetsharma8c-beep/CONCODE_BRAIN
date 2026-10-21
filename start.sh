#!/bin/bash
# ============================================================
# CONCODE Neural Brain — Launch Server
# Starts the FastAPI cognitive engine with uvicorn
# ============================================================

set -e

echo "=========================================================="
echo "  CONCODE Neural Brain -- Starting Server"
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# ── Python executable resolution ──────────────────────────────
if [ -x "/Library/Developer/CommandLineTools/usr/bin/python3" ] && [ -d "venv/lib/python3.9/site-packages" ]; then
    PYTHON_BIN="/Library/Developer/CommandLineTools/usr/bin/python3"
    export PYTHONPATH="$SCRIPT_DIR/venv/lib/python3.9/site-packages:$PYTHONPATH"
    echo "  Using Python 3.9 from CommandLineTools with venv site-packages"
elif [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_BIN="python3"
    echo "  Virtual environment activated"
else
    PYTHON_BIN="python3"
    echo "  No venv found. Using system Python."
fi

# ── Check key dependencies ────────────────────────────────────
echo ""
echo "Checking dependencies..."
$PYTHON_BIN -c "import fastapi" 2>/dev/null || {
    echo "  FastAPI not installed. Run: pip install -r requirements.txt"
    exit 1
}
echo "  FastAPI found"

$PYTHON_BIN -c "import uvicorn" 2>/dev/null || {
    echo "  Uvicorn not installed. Run: pip install -r requirements.txt"
    exit 1
}
echo "  Uvicorn found"

# ── Check inference configuration ─────────────────────────────
echo ""
if [ "${CONCODE_INFERENCE_BACKEND:-local}" = "remote" ]; then
    echo "Remote self-hosted inference selected"
    if [ -n "${CONCODE_REMOTE_LLM_BASE_URL:-}" ] && [ -n "${CONCODE_REMOTE_LLM_MODEL:-}" ] && [ -n "${CONCODE_REMOTE_LLM_API_KEY:-}" ]; then
        echo "  Remote endpoint and model are configured"
    else
        echo "  Remote settings are loaded from .env by the application; see .env.example."
    fi
elif [ -f "models/codellama-7b-concode.Q4_K_M.gguf" ]; then
    echo "Local GGUF model found ($(du -h models/codellama-7b-concode.Q4_K_M.gguf | cut -f1))"
else
    echo "  Local GGUF model not found -- install a verified local model with scripts/download_model.sh"
fi

if [ -f "models/intent_classifier/config.json" ]; then
    echo "  Intent classifier found"
else
    echo "  Intent classifier not found -- using keyword fallback"
fi

if [ -f "models/code_repair/config.json" ]; then
    echo "  Code repair model found"
else
    echo "  Code repair model not found -- using regex fallback"
fi

# ── Sync Obsidian Vault Nodes ─────────────────────────────────
echo ""
echo "Syncing Obsidian Vault Knowledge Graph..."
$PYTHON_BIN -m src.obsidian_auto_mapper --sync 2>/dev/null || echo "  Obsidian sync skipped (optional)"

# ── Launch server ─────────────────────────────────────────────
echo ""
echo "=========================================================="
echo "  Starting CONCODE Neural Brain on http://localhost:8000"
echo "  API endpoint: POST http://localhost:8000/api/v1/cognitive"
echo "  Press Ctrl+C to stop"
echo "=========================================================="
echo ""

$PYTHON_BIN -m uvicorn src.service:app --host 0.0.0.0 --port 8000
