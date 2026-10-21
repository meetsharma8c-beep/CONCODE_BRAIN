#!/usr/bin/env bash
# Print the checksum to publish alongside an authorized CONCODE model release.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_PATH="${1:-$PROJECT_DIR/models/codellama-7b-concode.Q4_K_M.gguf}"

if [[ ! -f "$MODEL_PATH" ]]; then
  echo "Model not found: $MODEL_PATH" >&2
  exit 1
fi

MODEL_SHA256="$(shasum -a 256 "$MODEL_PATH" | awk '{print tolower($1)}')"
echo "CONCODE_MODEL_SHA256=$MODEL_SHA256"
