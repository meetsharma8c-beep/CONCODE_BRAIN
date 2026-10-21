#!/bin/bash
# ============================================================
# CONCODE Neural Brain — GGUF Conversion & Quantization
# Converts the merged HuggingFace model to GGUF Q4_K_M format
# for local inference on Apple Silicon (Metal GPU)
# ============================================================

set -e

echo "=========================================================="
echo "  CONCODE Neural Brain — GGUF Conversion & Quantization"
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
MODELS_DIR="$PROJECT_ROOT/models"
LLAMA_CPP_DIR="$PROJECT_ROOT/llama.cpp"

# The merged HF model directory (downloaded from Colab)
HF_MODEL_DIR="${1:-$MODELS_DIR/codellama-7b-concode-merged}"
OUTPUT_F16="$MODELS_DIR/codellama-7b-concode.f16.gguf"
OUTPUT_Q4="$MODELS_DIR/codellama-7b-concode.Q4_K_M.gguf"

echo ""
echo "HF Model Dir:  $HF_MODEL_DIR"
echo "Output F16:    $OUTPUT_F16"
echo "Output Q4_K_M: $OUTPUT_Q4"
echo ""

# ── Step 1: Check if HF model exists ─────────────────────────
if [ ! -d "$HF_MODEL_DIR" ]; then
    echo "[ERROR] HuggingFace model directory not found at:"
    echo "   $HF_MODEL_DIR"
    echo ""
    echo "Please either:"
    echo "  1. Download the merged model from Google Colab"
    echo "  2. Unzip codellama-7b-concode-merged.zip into models/"
    echo "  3. Or specify the path: ./convert_to_gguf.sh /path/to/model"
    exit 1
fi

echo "[OK] Found HF model at $HF_MODEL_DIR"

# ── Step 2: Clone & build llama.cpp (if not present) ─────────
if [ ! -d "$LLAMA_CPP_DIR" ]; then
    echo ""
    echo "Cloning llama.cpp..."
    git clone https://github.com/ggerganov/llama.cpp "$LLAMA_CPP_DIR"
fi

echo "Building llama.cpp with Metal support..."
cd "$LLAMA_CPP_DIR"
make clean 2>/dev/null || true
make GGML_METAL=1 -j$(sysctl -n hw.ncpu)
echo "[OK] llama.cpp built with Metal"

# ── Step 3: Convert HF model → GGUF F16 ─────────────────────
echo ""
echo "Converting HuggingFace model to GGUF F16..."

# Install Python deps for conversion
pip3 install -q sentencepiece protobuf 2>/dev/null || true

python3 "$LLAMA_CPP_DIR/convert_hf_to_gguf.py" \
    "$HF_MODEL_DIR" \
    --outfile "$OUTPUT_F16" \
    --outtype f16

echo "[OK] F16 GGUF created: $OUTPUT_F16"

# ── Step 4: Quantize F16 → Q4_K_M ───────────────────────────
echo ""
echo "Quantizing F16 → Q4_K_M..."

"$LLAMA_CPP_DIR/llama-quantize" "$OUTPUT_F16" "$OUTPUT_Q4" Q4_K_M

echo "[OK] Q4_K_M GGUF created: $OUTPUT_Q4"

# ── Step 5: Cleanup (optional) ───────────────────────────────
echo ""
read -p "Delete the F16 intermediate file to save space? (y/n): " cleanup
if [ "$cleanup" = "y" ]; then
    rm -f "$OUTPUT_F16"
    echo "[OK] Cleaned up F16 file"
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "=========================================================="
echo "  [OK] GGUF conversion complete!"
echo ""
echo "  Model file: $OUTPUT_Q4"
echo "  Size: $(du -h "$OUTPUT_Q4" | cut -f1)"
echo ""
echo "  Start the server with:"
echo "    cd $PROJECT_ROOT && ./start.sh"
echo "=========================================================="
