#!/bin/bash
# ============================================================
# CONCODE Neural Brain — Setup Script
# Sets up the Python environment, installs dependencies,
# and downloads the embedding model.
# ============================================================

set -e

echo "=========================================================="
echo "  CONCODE Neural Brain — Environment Setup"
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# ── Step 1: Check Python ─────────────────────────────────────
echo ""
echo "Step 1: Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
    echo "  [OK] Found: $(python3 --version)"
else
    echo "  [ERROR] Python 3 not found. Install from https://python.org"
    exit 1
fi

# ── Step 2: Create Virtual Environment ───────────────────────
echo ""
echo "Step 2: Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "  [OK] Created venv/"
else
    echo "  [OK] venv/ already exists"
fi

source venv/bin/activate
echo "  [OK] Activated venv"

# ── Step 3: Upgrade pip ──────────────────────────────────────
echo ""
echo "Step 3: Upgrading pip..."
pip install --upgrade pip -q

# ── Step 4: Install llama-cpp-python with Metal ──────────────
echo ""
echo "Step 4: Installing llama-cpp-python with Metal GPU support..."
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python --no-cache-dir -q
echo "  [OK] llama-cpp-python installed with Metal"

# ── Step 5: Install remaining dependencies ───────────────────
echo ""
echo "Step 5: Installing Python dependencies..."
pip install -r requirements.txt -q
echo "  [OK] All dependencies installed"

# ── Step 6: Download MiniLM embedding model ──────────────────
echo ""
echo "Step 6: Pre-downloading MiniLM embedding model..."
$PYTHON -c "
from sentence_transformers import SentenceTransformer
print('  Downloading all-MiniLM-L6-v2...')
model = SentenceTransformer('all-MiniLM-L6-v2')
print('  [OK] MiniLM model cached')
"

# ── Step 7: Create model directories ─────────────────────────
echo ""
echo "Step 7: Ensuring model directories exist..."
mkdir -p models/intent_classifier
mkdir -p models/code_repair
mkdir -p models/embedder
echo "  [OK] Model directories ready"

# ── Step 8: Generate training data ───────────────────────────
echo ""
echo "Step 8: Generating training datasets..."
$PYTHON -m src.generate_data
echo "  [OK] Training data generated"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "=========================================================="
echo "  [OK] Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. Upload data/ files to Google Colab"
echo "    2. Run src/train_colab.ipynb to train models"
echo "    3. Download trained models to models/"
echo "    4. Convert LLM to GGUF: bash src/convert_to_gguf.sh"
echo "    5. Start server: ./start.sh"
echo ""
echo "  Or start in fallback mode (no trained models):"
echo "    ./start.sh"
echo "=========================================================="
