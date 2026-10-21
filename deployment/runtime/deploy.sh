#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -f .env ]]; then
    echo "Missing deployment/runtime/.env. Copy .env.example and set CONCODE_DOMAIN and CONCODE_API_KEY." >&2
    exit 1
fi

while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    if [[ "$line" != *=* ]]; then
        echo "Invalid line in .env; use KEY=value entries." >&2
        exit 1
    fi
    key="${line%%=*}"
    value="${line#*=}"
    case "$key" in
        CONCODE_DOMAIN|CONCODE_API_KEY|CONCODE_MODEL_HOST_DIR|CONCODE_CORS_ORIGINS) ;;
        *)
            echo "Unsupported variable name in .env: $key" >&2
            exit 1
            ;;
    esac
    if [[ "$value" == *"'"* || "$value" == *'"'* || "$value" == *'$'* ]]; then
        echo "$key must be an unquoted literal value in .env." >&2
        exit 1
    fi
    export "$key=$value"
done < .env

if [[ -z "${CONCODE_DOMAIN:-}" || "$CONCODE_DOMAIN" == "brain.example.com" ]]; then
    echo "Set CONCODE_DOMAIN to a real DNS name pointing to this host." >&2
    exit 1
fi
if [[ -z "${CONCODE_API_KEY:-}" || ${#CONCODE_API_KEY} -lt 32 ]]; then
    echo "Set CONCODE_API_KEY to a private random value of at least 32 characters." >&2
    exit 1
fi
if [[ "$CONCODE_API_KEY" == *[!a-zA-Z0-9_-]* ]]; then
    echo "Use only letters, numbers, underscore, or hyphen in CONCODE_API_KEY." >&2
    exit 1
fi

MODEL_DIR="${CONCODE_MODEL_HOST_DIR:-../../models}"
if [[ ! -f "$MODEL_DIR/codellama-7b-concode.Q4_K_M.gguf" ]]; then
    echo "Missing $MODEL_DIR/codellama-7b-concode.Q4_K_M.gguf. Install the authorized GGUF model first." >&2
    exit 1
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "NVIDIA host driver is unavailable; GPU deployment cannot start." >&2
    exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
    echo "Docker Compose v2 is required." >&2
    exit 1
fi

docker compose config --quiet
docker compose up --detach --build
echo "Deployment started. Check readiness with: docker compose ps"
echo "After Caddy obtains its certificate, API base URL: https://$CONCODE_DOMAIN"
