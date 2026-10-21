#!/usr/bin/env bash
# Download a verified CONCODE GGUF model without contacting any AI API.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DEFAULT_DESTINATION="$PROJECT_DIR/models/codellama-7b-concode.Q4_K_M.gguf"

MODEL_URL="${CONCODE_MODEL_URL:-}"
MODEL_SHA256="${CONCODE_MODEL_SHA256:-}"
DESTINATION="$DEFAULT_DESTINATION"
FORCE=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/download_model.sh --url MODEL_URL --sha256 SHA256 [--destination PATH] [--force]

Required:
  --url URL              HTTPS URL for an authorized GGUF release asset.
  --sha256 SHA256        Expected SHA-256 checksum for that exact file.

Optional:
  --destination PATH     Model path. Defaults to models/codellama-7b-concode.Q4_K_M.gguf.
  --force                Preserve an existing unverified model as a timestamped backup, then replace it.

You can also provide CONCODE_MODEL_URL and CONCODE_MODEL_SHA256 environment variables.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      MODEL_URL="${2:-}"
      shift 2
      ;;
    --sha256)
      MODEL_SHA256="${2:-}"
      shift 2
      ;;
    --destination)
      DESTINATION="${2:-}"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$MODEL_URL" || -z "$MODEL_SHA256" ]]; then
  echo "A model URL and SHA-256 checksum are required." >&2
  usage >&2
  exit 2
fi

if [[ ! "$MODEL_URL" =~ ^https:// ]]; then
  echo "Model URL must use HTTPS." >&2
  exit 2
fi

if [[ ! "$MODEL_SHA256" =~ ^[A-Fa-f0-9]{64}$ ]]; then
  echo "SHA-256 must be exactly 64 hexadecimal characters." >&2
  exit 2
fi

EXPECTED_SHA="$(printf '%s' "$MODEL_SHA256" | tr '[:upper:]' '[:lower:]')"

checksum() {
  shasum -a 256 "$1" | awk '{print tolower($1)}'
}

if [[ -f "$DESTINATION" ]]; then
  EXISTING_SHA="$(checksum "$DESTINATION")"
  if [[ "$EXISTING_SHA" == "$EXPECTED_SHA" ]]; then
    echo "Verified model already exists: $DESTINATION"
    exit 0
  fi
  if [[ "$FORCE" -ne 1 ]]; then
    echo "An existing model has a different checksum. Use --force to preserve it as a backup and replace it." >&2
    exit 1
  fi
  BACKUP_PATH="${DESTINATION}.backup.$(date +%Y%m%d%H%M%S)"
  mv "$DESTINATION" "$BACKUP_PATH"
  echo "Preserved existing model at: $BACKUP_PATH"
fi

mkdir -p "$(dirname "$DESTINATION")"
TEMP_PATH="$(mktemp "${DESTINATION}.download.XXXXXX")"
trap 'rm -f "$TEMP_PATH"' EXIT

echo "Downloading the verified local model..."
curl --fail --location --retry 3 --retry-delay 2 --output "$TEMP_PATH" "$MODEL_URL"

ACTUAL_SHA="$(checksum "$TEMP_PATH")"
if [[ "$ACTUAL_SHA" != "$EXPECTED_SHA" ]]; then
  echo "Checksum mismatch. The downloaded file was discarded." >&2
  exit 1
fi

mv "$TEMP_PATH" "$DESTINATION"
trap - EXIT
echo "Model installed and verified: $DESTINATION"
