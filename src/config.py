"""
CONCODE Neural Brain -- Centralized Configuration
All paths, model names, hyperparameters, and security settings in one place.
"""

import os
from pathlib import Path

# Runtime inference is local only. These values are set before transformers or
# sentence-transformers are imported, so a missing cache produces a local error
# rather than an implicit model download.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# ── Load .env file if present ─────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass  # python-dotenv is optional; env vars can be set directly

# ── Project Root ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = Path(os.environ.get("CONCODE_MODEL_DIR", PROJECT_ROOT / "models"))
SRC_DIR = PROJECT_ROOT / "src"

# ── Model Paths ───────────────────────────────────────────────
GGUF_MODEL_PATH = MODELS_DIR / "codellama-7b-concode.Q4_K_M.gguf"
INTENT_MODEL_DIR = MODELS_DIR / "intent_classifier"
REPAIR_MODEL_DIR = MODELS_DIR / "code_repair"
EMBEDDER_MODEL_DIR = MODELS_DIR / "embedder"

# ── Guilds Config ─────────────────────────────────────────────
GUILDS_YAML = DATA_DIR / "guilds.yaml"

# ── LLM Inference Settings ────────────────────────────────────
# Inference runs locally by default. Set this to "remote" only when you have
# configured your own remote GPU server.
INFERENCE_BACKEND = os.environ.get("CONCODE_INFERENCE_BACKEND", "local").strip().lower()
REMOTE_LLM_BASE_URL = os.environ.get("CONCODE_REMOTE_LLM_BASE_URL", "").strip()
REMOTE_LLM_MODEL = os.environ.get("CONCODE_REMOTE_LLM_MODEL", "").strip()
REMOTE_LLM_API_KEY = os.environ.get("CONCODE_REMOTE_LLM_API_KEY", "").strip()
REMOTE_LLM_TIMEOUT_SECONDS = int(os.environ.get("CONCODE_REMOTE_LLM_TIMEOUT_SECONDS", "120"))
LLM_CONTEXT_LENGTH = int(os.environ.get("CONCODE_LLM_CTX", "2048"))
LLM_MAX_TOKENS = int(os.environ.get("CONCODE_LLM_MAX_TOKENS", "1200"))
LLM_TEMPERATURE = 0.3
LLM_TOP_P = 0.9
LLM_GPU_LAYERS = int(os.environ.get("CONCODE_LLM_GPU_LAYERS", "32"))
LLM_THREADS = int(os.environ.get("CONCODE_LLM_THREADS", "2"))      # Eco thermal governor: 2 threads prevents CPU overheating
LLM_BATCH_SIZE = int(os.environ.get("CONCODE_LLM_BATCH_SIZE", "128"))  # Lower batch size reduces peak Metal GPU wattage
LLM_LAZY_LOAD = os.environ.get("CONCODE_LLM_LAZY_LOAD", "1").strip() == "1"
LLM_IDLE_UNLOAD_SECONDS = int(os.environ.get("CONCODE_LLM_IDLE_UNLOAD_SECONDS", "300"))

# ── Intent Classifier Settings ────────────────────────────────
INTENT_MAX_LENGTH = 128
INTENT_FALLBACK_GUILD = "fullstack"

# ── Retriever Settings ────────────────────────────────────────
RETRIEVER_MODEL_NAME = "all-MiniLM-L6-v2"
RETRIEVER_TOP_K = 3
RETRIEVER_CHUNK_SIZE = 512  # characters per chunk

# ── Code Repair Settings ──────────────────────────────────────
REPAIR_MAX_INPUT_LENGTH = 512
REPAIR_MAX_OUTPUT_LENGTH = 512

# ── Social Intelligence Settings ─────────────────────────────
SOCIAL_SENTIMENT_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
USER_PROFILES_PATH = Path(os.environ.get("CONCODE_USER_PROFILES_PATH", DATA_DIR / "user_profiles.json"))
EMPATHY_TEMPLATES_PATH = DATA_DIR / "empathy_templates.yaml"
CLARIFYING_QUESTIONS_PATH = DATA_DIR / "clarifying_questions.yaml"

# ── Session Settings ──────────────────────────────────────────
SESSION_MAX_HISTORY = 3   # Keep last N turns per session
SESSION_TTL_SECONDS = 3600  # Evict sessions after 1 hour of inactivity

# ── Server Settings ───────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
API_VERSION = "2.1.0"

# ── Security Settings ────────────────────────────────────────
# API Key: set CONCODE_API_KEY env var to enable auth (unset = dev mode)
SECURITY_API_KEY = os.environ.get("CONCODE_API_KEY")
if os.environ.get("CONCODE_REQUIRE_API_KEY", "0").strip() == "1":
    if not SECURITY_API_KEY or len(SECURITY_API_KEY) < 32:
        raise RuntimeError(
            "CONCODE_API_KEY must contain at least 32 characters when CONCODE_REQUIRE_API_KEY=1."
        )

# Rate limiting
RATE_LIMIT_COGNITIVE = 30    # requests per minute for /api/v1/cognitive
RATE_LIMIT_GENERAL = 120     # requests per minute for other API endpoints

# CORS: comma-separated origins, or "*" for dev mode
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CONCODE_CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:5173,http://127.0.0.1:5173"
).split(",")

# Input validation
MAX_QUERY_LENGTH = 8192          # max characters for user prompt
MAX_WORKSPACE_FILES = 50         # max files per request
MAX_FILE_SIZE = 500_000          # max bytes per workspace file
MAX_TOTAL_WORKSPACE_SIZE = 5_000_000  # max total bytes for all files

# Profile management
MAX_USER_PROFILES = 10_000       # evict oldest when exceeded
PROFILE_SAVE_INTERVAL = 5        # save profiles every N updates (debounce)

# ── Guild Icons Lookup ────────────────────────────────────────
GUILD_ICONS = {
    "debugger": "[DEBUG]",
    "webgl": "[WEBGL]",
    "ai_ml": "[AI_ML]",
    "qa": "[QA]",
    "security": "[SEC]",
    "performance": "[PERF]",
    "database": "[DB]",
    "ui_ux": "[UIUX]",
    "devops": "[DEVOPS]",
    "api": "[API]",
    "fullstack": "[FULLSTACK]",
    "mobile": "[MOBILE]",
    "blockchain": "[CHAIN]",
    "conversational": "[CHAT]",
    "system_architect": "[ARCH]",
    "research_scientist": "[SCI]",
    "automation_operator": "[AUTO]",
    "critic_verifier": "[CRITIC]",
}

# ── Universal Brain v3.0 Evolution Settings ───────────────────
EPISODIC_MEMORY_PATH = Path(
    os.environ.get("CONCODE_EPISODIC_MEMORY_PATH", DATA_DIR / "episodic_memory.jsonl")
)
HARVESTED_TRAJECTORIES_PATH = Path(
    os.environ.get("CONCODE_HARVESTED_TRAJECTORIES_PATH", DATA_DIR / "harvested_trajectories.jsonl")
)
HARVESTED_DPO_PATH = Path(
    os.environ.get("CONCODE_HARVESTED_DPO_PATH", DATA_DIR / "harvested_dpo_pairs.jsonl")
)
SANDBOX_TIMEOUT_SECONDS = float(os.environ.get("CONCODE_SANDBOX_TIMEOUT_SECONDS", "5.0"))
SANDBOX_MAX_OUTPUT_BYTES = int(os.environ.get("CONCODE_SANDBOX_MAX_OUTPUT_BYTES", "32768"))
MAX_UNIVERSAL_ITERATIONS = int(os.environ.get("CONCODE_MAX_UNIVERSAL_ITERATIONS", "6"))
