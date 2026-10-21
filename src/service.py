"""
CONCODE Neural Brain -- FastAPI Cognitive Engine Service

Main API server orchestrating neural subsystems and a bounded coding agent:
  1. Intent Classifier (DistilBERT)
  2. Workspace Retriever (MiniLM + FAISS)
  3. Code Generator (CodeLlama-7B GGUF via llama.cpp + Metal)
  4. Code Repair (CodeT5)
  5. Session Memory (in-memory with TTL eviction)
  6. Social Intelligence (Sentiment + User Memory + Dynamic Prompts + Ambiguity + Empathy)
  7. Coding Agent (plan, virtual edits, syntax verification, bounded retry)

Security layer (SEC 1-4):
  - API Key Authentication (X-API-Key header, constant-time comparison)
  - Rate Limiting (sliding window per-IP, tiered by endpoint)
  - Input Sanitization (null bytes, ANSI escapes, path traversal)
  - Security Headers (X-Content-Type-Options, X-Frame-Options, X-Request-ID)

Exposes POST /api/v1/cognitive -- the single endpoint for the website.
"""

import json
import logging
import re
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional

import yaml
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from src.config import (
    API_VERSION,
    CORS_ALLOWED_ORIGINS,
    PROJECT_ROOT,
    GUILDS_YAML,
    GGUF_MODEL_PATH,
    INFERENCE_BACKEND,
    GUILD_ICONS,
    INTENT_MODEL_DIR,
    INTENT_FALLBACK_GUILD,
    LLM_CONTEXT_LENGTH,
    LLM_GPU_LAYERS,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_THREADS,
    LLM_TOP_P,
    REMOTE_LLM_API_KEY,
    REMOTE_LLM_BASE_URL,
    REMOTE_LLM_MODEL,
    REMOTE_LLM_TIMEOUT_SECONDS,
    MAX_QUERY_LENGTH,
    MAX_WORKSPACE_FILES,
    MAX_FILE_SIZE,
    MAX_TOTAL_WORKSPACE_SIZE,
    MAX_USER_PROFILES,
    PROFILE_SAVE_INTERVAL,
    RATE_LIMIT_COGNITIVE,
    RATE_LIMIT_GENERAL,
    REPAIR_MODEL_DIR,
    REPAIR_MAX_INPUT_LENGTH,
    REPAIR_MAX_OUTPUT_LENGTH,
    RETRIEVER_MODEL_NAME,
    RETRIEVER_TOP_K,
    RETRIEVER_CHUNK_SIZE,
    SECURITY_API_KEY,
    SESSION_MAX_HISTORY,
    SESSION_TTL_SECONDS,
    SOCIAL_SENTIMENT_MODEL,
    USER_PROFILES_PATH,
    EMPATHY_TEMPLATES_PATH,
    CLARIFYING_QUESTIONS_PATH,
)
from src.brain.intent import IntentClassifier
from src.brain.retriever import WorkspaceRetriever
from src.brain.generator import CodeGenerator, ModelGenerationError, RemoteCodeGenerator
from src.brain.repair import CodeRepairer
from src.brain.agent import CodingAgent
from src.brain.social import (
    SentimentAnalyzer,
    UserMemoryStore,
    DynamicPromptBuilder,
    AmbiguityDetector,
    EmpatheticResponder,
)
from src.brain.security import (
    verify_api_key,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    sanitize_input,
    validate_workspace_files,
)

# -- Logging -------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("concode.service")

# -- Subsystem Globals --------------------------------------------
intent_classifier: Optional[IntentClassifier] = None
retriever: Optional[WorkspaceRetriever] = None
generator: Optional[Any] = None
repairer: Optional[CodeRepairer] = None
guilds_data: Dict[str, Any] = {}

# Session store with TTL tracking:
#   session_store[session_id] = list of {role, content} dicts
#   session_last_access[session_id] = timestamp of last access
session_store: Dict[str, List[Dict[str, str]]] = defaultdict(list)
session_last_access: Dict[str, float] = {}

# Social Intelligence subsystems
sentiment_analyzer: Optional[SentimentAnalyzer] = None
user_memory: Optional[UserMemoryStore] = None
prompt_builder: Optional[DynamicPromptBuilder] = None
ambiguity_detector: Optional[AmbiguityDetector] = None
empathetic_responder: Optional[EmpatheticResponder] = None
coding_agent: Optional[CodingAgent] = None


# -- Session TTL Eviction ------------------------------------------
def _evict_stale_sessions() -> int:
    """Remove sessions that have been inactive beyond SESSION_TTL_SECONDS."""
    now = time.time()
    stale_ids = [
        sid for sid, last in session_last_access.items()
        if now - last > SESSION_TTL_SECONDS
    ]
    for sid in stale_ids:
        session_store.pop(sid, None)
        session_last_access.pop(sid, None)
    if stale_ids:
        logger.info(f"Evicted {len(stale_ids)} stale sessions")
    return len(stale_ids)


def _touch_session(session_id: str) -> None:
    """Update the last-access timestamp for a session."""
    session_last_access[session_id] = time.time()


# -- Lifespan (replaces deprecated on_event) -----------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load subsystems and the bounded coding agent at startup, then clean up on shutdown."""
    global intent_classifier, retriever, generator, repairer, guilds_data
    global sentiment_analyzer, user_memory, prompt_builder
    global ambiguity_detector, empathetic_responder, coding_agent

    logger.info("=" * 60)
    logger.info("  CONCODE Neural Brain -- Starting Cognitive Engine")
    logger.info("=" * 60)

    # Load guild definitions
    try:
        with open(str(GUILDS_YAML), "r") as f:
            data = yaml.safe_load(f)
            guild_list = data.get("guilds", []) if data else []
            guilds_data = {g["name"]: g for g in guild_list}
        logger.info(f"Loaded {len(guilds_data)} guild definitions")
    except Exception as e:
        logger.error(f"Failed to load guilds: {e}")

    # 1. Intent Classifier
    logger.info("Loading Intent Classifier (DistilBERT)...")
    intent_classifier = IntentClassifier(
        model_dir=str(INTENT_MODEL_DIR),
        guilds_yaml=str(GUILDS_YAML),
        fallback_guild=INTENT_FALLBACK_GUILD,
    )
    mode = "neural" if intent_classifier.is_neural else "keyword fallback"
    logger.info(f"Intent Classifier ready ({mode})")

    # 2. Workspace Retriever
    logger.info("Loading Workspace Retriever (MiniLM + FAISS)...")
    retriever = WorkspaceRetriever(
        model_name=RETRIEVER_MODEL_NAME,
        chunk_size=RETRIEVER_CHUNK_SIZE,
    )
    logger.info(f"Retriever ready: {retriever.is_ready}")

    # 3. Code Generator (remote self-hosted GPU by default)
    if INFERENCE_BACKEND == "remote":
        logger.info("Configuring remote self-hosted code generator...")
        generator = RemoteCodeGenerator(
            base_url=REMOTE_LLM_BASE_URL,
            model=REMOTE_LLM_MODEL,
            api_key=REMOTE_LLM_API_KEY,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
            timeout_seconds=REMOTE_LLM_TIMEOUT_SECONDS,
        )
        logger.info("Remote code generator configured: %s", generator.is_loaded)
    elif INFERENCE_BACKEND == "local":
        logger.info("Loading local CodeLlama GGUF + Metal generator...")
        generator = CodeGenerator(
            model_path=str(GGUF_MODEL_PATH),
            n_ctx=LLM_CONTEXT_LENGTH,
            n_gpu_layers=LLM_GPU_LAYERS,
            n_threads=LLM_THREADS,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            top_p=LLM_TOP_P,
        )
        logger.info("Local code generator ready: %s", generator.is_loaded)
    else:
        logger.error("Unsupported CONCODE_INFERENCE_BACKEND: %s", INFERENCE_BACKEND)
        generator = None
    coding_agent = CodingAgent(generator)
    logger.info("Coding Agent ready (bounded virtual-workspace mode, backend=%s)", INFERENCE_BACKEND)

    # 4. Code Repairer
    logger.info("Loading Code Repairer (CodeT5)...")
    repairer = CodeRepairer(
        model_dir=str(REPAIR_MODEL_DIR),
        max_input_length=REPAIR_MAX_INPUT_LENGTH,
        max_output_length=REPAIR_MAX_OUTPUT_LENGTH,
    )
    mode = "neural" if repairer.is_neural else "regex fallback"
    logger.info(f"Code Repairer ready ({mode})")

    # 5. Social Intelligence Layer
    logger.info("Loading Social Intelligence Layer...")

    # 5a. Sentiment Analyzer
    sentiment_analyzer = SentimentAnalyzer(model_name=SOCIAL_SENTIMENT_MODEL)
    sa_mode = "neural" if sentiment_analyzer.is_ready else "rule-based fallback"
    logger.info(f"  Sentiment Analyzer ready ({sa_mode})")

    # 5b. User Memory Store (with bounded growth)
    user_memory = UserMemoryStore(
        profiles_path=str(USER_PROFILES_PATH),
        max_profiles=MAX_USER_PROFILES,
        save_interval=PROFILE_SAVE_INTERVAL,
    )
    logger.info(f"  User Memory Store ready ({user_memory.profile_count} profiles loaded)")

    # 5c. Dynamic Prompt Builder
    prompt_builder = DynamicPromptBuilder()
    logger.info("  Dynamic Prompt Builder ready")

    # 5d. Ambiguity Detector
    ambiguity_detector = AmbiguityDetector(
        questions_path=str(CLARIFYING_QUESTIONS_PATH),
    )
    logger.info("  Ambiguity Detector ready")

    # 5e. Empathetic Responder
    empathetic_responder = EmpatheticResponder(
        templates_path=str(EMPATHY_TEMPLATES_PATH),
    )
    logger.info("  Empathetic Responder ready")

    # Security status
    sec_mode = "API key required" if SECURITY_API_KEY else "dev mode (no auth)"
    logger.info(f"  Security: {sec_mode}")
    logger.info(f"  Rate limits: cognitive={RATE_LIMIT_COGNITIVE}/min, general={RATE_LIMIT_GENERAL}/min")
    logger.info(f"  CORS origins: {CORS_ALLOWED_ORIGINS}")

    logger.info("=" * 60)
    logger.info("  All subsystems and coding agent initialized. Brain is ONLINE.")
    logger.info("=" * 60)

    yield  # -- Server is running --

    # Shutdown: flush pending profile writes
    logger.info("Shutting down -- flushing user profiles...")
    if user_memory:
        user_memory.flush()
    if generator:
        generator.close()
    logger.info("Shutdown complete.")


# -- FastAPI App ---------------------------------------------------
app = FastAPI(
    title="CONCODE Neural Brain API",
    version=API_VERSION,
    description=(
        "Heavy-neuron cognitive engine with 7B+ parameters, "
        "13 expert guilds, and 6 neural subsystems. "
        "Powered by CodeLlama-7B, DistilBERT, CodeT5, MiniLM, FAISS, "
        "and a Social Intelligence layer."
    ),
    lifespan=lifespan,
)

# -- Middleware Stack (order matters: outermost runs first) ---------

# Security headers (outermost -- always applied)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    cognitive_limit=RATE_LIMIT_COGNITIVE,
    general_limit=RATE_LIMIT_GENERAL,
)

# CORS -- restricted origins (fixes BUG 5: wildcard + credentials conflict)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -- API Key Dependency (imported from security module) ------------
# verify_api_key reads CONCODE_API_KEY env var at call time.
# No key configured = dev mode (all requests pass).


# -- Request / Response Models -------------------------------------
class CognitiveRequest(BaseModel):
    query: str = Field(
        ...,
        description="The user's natural language prompt",
        max_length=MAX_QUERY_LENGTH,
    )
    workspace_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of filename -> file content from the editor",
    )
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Session ID for conversation continuity",
    )
    mode: str = Field(
        default="text",
        description="Response mode: 'text' or 'code'",
    )

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query must not be empty.")
        return stripped


class CognitiveResponse(BaseModel):
    code: str = Field(..., description="Generated/repaired code output")
    guild: str = Field(..., description="Activated guild name")
    guild_icon: str = Field(..., description="Guild emoji icon")
    confidence: float = Field(..., description="Intent classification confidence")
    repair_applied: bool = Field(..., description="Whether code repair was applied")
    session_id: str = Field(..., description="Session ID for follow-up")
    sentiment: str = Field(
        default="neutral",
        description="Detected user sentiment (positive/neutral/negative/confused)",
    )
    personalized_message: str = Field(
        default="",
        description="Empathetic wrapper message based on detected sentiment",
    )
    is_clarifying: bool = Field(
        default=False,
        description="True if response is a clarifying question instead of code",
    )
    clarifying_question: Optional[str] = Field(
        default=None,
        description="The clarifying question text when is_clarifying is true",
    )
    subsystems: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of each subsystem used",
    )
    latency_ms: float = Field(..., description="Total processing time in ms")


class AgentRequest(BaseModel):
    """A coding task and an in-memory snapshot of the target project."""

    goal: str = Field(..., min_length=1, max_length=MAX_QUERY_LENGTH)
    workspace_files: Dict[str, str] = Field(default_factory=dict)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    max_iterations: int = Field(default=3, ge=1, le=3)

    @field_validator("goal")
    @classmethod
    def goal_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Goal must not be empty.")
        return value


class AgentEditResponse(BaseModel):
    path: str
    content: str
    reason: str
    diff: str


class AgentVerificationResponse(BaseModel):
    path: str
    status: str
    detail: str


class AgentResponse(BaseModel):
    summary: str
    plan: List[str]
    edits: List[AgentEditResponse]
    verification: List[AgentVerificationResponse]
    iterations: int
    success: bool
    needs_user_input: bool
    question: Optional[str] = None
    error: Optional[str] = None
    guild: str
    confidence: float
    session_id: str
    latency_ms: float


class TravelContext(BaseModel):
    """Bounded traveler data received from the trusted TripVerse server proxy."""

    destination: str = Field(default="", max_length=160)
    origin: str = Field(default="", max_length=160)
    duration_days: int = Field(default=0, ge=0, le=60)
    total_budget: float = Field(default=0, ge=0, le=100_000_000)
    currency: str = Field(default="INR", max_length=12)
    travelers_count: int = Field(default=1, ge=1, le=30)
    traveler_type: str = Field(default="", max_length=80)
    preferences: List[str] = Field(default_factory=list, max_length=24)
    special_requests: str = Field(default="", max_length=1_000)
    transport_mode: str = Field(default="", max_length=80)
    accommodation_type: str = Field(default="", max_length=80)
    food_preference: str = Field(default="", max_length=80)
    priorities: List[str] = Field(default_factory=list, max_length=12)
    known_destination_highlights: List[str] = Field(default_factory=list, max_length=30)
    # These are provider-supplied offers only. The model must not invent offers.
    transport_options: List[Dict[str, Any]] = Field(default_factory=list, max_length=12)

    @field_validator("preferences", "priorities", "known_destination_highlights")
    @classmethod
    def clean_context_items(cls, values: List[str]) -> List[str]:
        return [sanitize_input(str(value))[:160] for value in values if sanitize_input(str(value))]

    @field_validator("transport_options")
    @classmethod
    def clean_transport_options(cls, values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned: List[Dict[str, Any]] = []
        for option in values[:12]:
            if not isinstance(option, dict):
                continue
            cleaned.append({
                str(key)[:40]: sanitize_input(str(value))[:500]
                for key, value in option.items()
                if isinstance(value, (str, int, float, bool)) and sanitize_input(str(value))
            })
        return cleaned


class TravelRequest(BaseModel):
    """A TripVerse travel-planning request. It is separate from coding workflows."""

    query: str = Field(..., min_length=1, max_length=MAX_QUERY_LENGTH)
    trip_context: TravelContext = Field(default_factory=TravelContext)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), max_length=128)
    mode: Literal["text", "itinerary", "budget", "safety"] = "text"

    @field_validator("query", "session_id")
    @classmethod
    def travel_input_not_empty(cls, value: str) -> str:
        value = sanitize_input(value)
        if not value:
            raise ValueError("Value must not be empty.")
        return value


class TravelResponse(BaseModel):
    reply: str
    session_id: str
    mode: str
    model_backend: str
    is_estimate: bool = True
    format_repaired: bool = False
    latency_ms: float


def _travel_system_prompt(mode: str) -> str:
    """Dedicated TripVerse instructions, kept separate from CONCODE coding guilds."""
    shared = """
You are CONCODE, TripVerse's intelligent travel-planning co-pilot. Create realistic, personalized
travel plans using the supplied traveler context and request. Respect total budget, group size,
duration, pacing, interests, food preferences, transport mode, and accommodation tier. Never write source code.

Provide genuine, specific hotel recommendations, authentic local eatery suggestions, realistic meal
costs, accurate monument ticket fees, and natural day-to-day schedule pacing:
- Morning (8:00 AM - 11:00 AM): Dawn viewpoints, peaceful temples, and heritage walks before peak heat.
- Midday & Lunch (12:30 PM - 2:30 PM): Authentic local dining honoring food preference + shaded/indoor museums.
- Afternoon (3:30 PM - 5:00 PM): Cultural discovery, artisan markets, or scenic garden strolls.
- Golden Hour (5:30 PM - 6:45 PM): Elevated fort ramparts, sunset viewpoints, or lakeside ghats.
- Evening (8:00 PM - 9:30 PM): Regional culinary feasts, folk performances, or night promenades.

Prices and schedules should reflect real destination costs. Avoid generic placeholders like "Artisan Kitchen"
or "Scenic Overlook"; use real, well-known locations and landmark names in the destination. Keep advice
concise and suitable for a consumer travel app.
""".strip()
    if mode == "itinerary":
        return shared + """

Return exactly one valid JSON object and nothing else:
{"itinerary":[{"dayNumber":1,"title":"...","theme":"...","activities":[{"time":"...","title":"...","type":"food|attraction|viewpoint|nightlife|rest","location":"...","description":"...","estimatedCost":0,"preferenceMatch":"...","durationMin":60}]}]}.
Return exactly the requested number of days with three or four activities per day.
Costs are realistic estimates for the whole group in the supplied currency. Keep the plan within
the available food-and-activities portion of the stated budget.
""".strip()
    if mode == "budget":
        return shared + "\nGive a compact budget allocation with assumptions and a contingency buffer."
    if mode == "safety":
        return shared + "\nGive practical precautions and direct the traveler to official local guidance for urgent or current safety information."
    return shared


def _json_itinerary(reply: str) -> Optional[str]:
    """Keep a compliant model-produced itinerary unchanged when it is valid JSON."""
    candidate = reply.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate).strip()
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(parsed.get("itinerary"), list):
        return None
    return json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))


def _activity_type(text: str) -> str:
    """Classify a model-written activity for the TripVerse itinerary UI."""
    lowered = text.lower()
    if any(word in lowered for word in ("meal", "restaurant", "cafe", "food", "lunch", "dinner", "breakfast")):
        return "food"
    if any(word in lowered for word in ("sunset", "view", "lake", "panorama", "scenic")):
        return "viewpoint"
    if any(word in lowered for word in ("bar", "club", "nightlife", "music", "show")):
        return "nightlife"
    if any(word in lowered for word in ("rest", "hotel", "relax", "free time")):
        return "rest"
    return "attraction"


def _itinerary_from_model_prose(reply: str, context: TravelContext) -> Optional[str]:
    """Convert model prose to the itinerary schema without inventing activities."""
    expected_days = context.duration_days
    if expected_days < 1:
        return None

    matches = list(re.finditer(r"(?im)^\s*(?:#{1,6}\s*)?day\s+(\d+)\s*:\s*", reply))
    if len(matches) < expected_days:
        return None

    itineraries = []
    preference = context.preferences[0] if context.preferences else "AI suggestion"
    daily_budget = context.total_budget / expected_days if context.total_budget else 0
    time_by_label = {
        "morning": "9:00 AM",
        "afternoon": "2:00 PM",
        "evening": "7:00 PM",
        "night": "8:00 PM",
    }

    for index in range(expected_days):
        match = matches[index]
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(reply)
        section = reply[match.end():next_start]
        activities = []
        for line in section.splitlines():
            bullet = re.match(r"^\s*[*-]\s*(?:(Morning|Afternoon|Evening|Night)\s*:\s*)?(.+?)\s*$", line, re.IGNORECASE)
            if not bullet:
                continue
            label, detail = bullet.groups()
            detail = detail.strip()
            if len(detail) < 3:
                continue
            title = re.split(r"[.(]", detail, maxsplit=1)[0].strip()[:100]
            activities.append({
                "time": time_by_label.get((label or "").lower(), "Time to confirm"),
                "title": title or "Suggested local experience",
                "type": _activity_type(detail),
                "location": context.destination or "Destination to confirm",
                "description": detail[:400],
                "estimatedCost": round(daily_budget * 0.15),
                "preferenceMatch": preference,
                "durationMin": 120,
            })
            if len(activities) == 4:
                break
        if len(activities) < 2:
            return None
        itineraries.append({
            "dayNumber": index + 1,
            "title": f"Day {index + 1} in {context.destination or 'your destination'}",
            "theme": activities[0]["title"],
            "activities": activities,
        })

    return json.dumps({"itinerary": itineraries}, ensure_ascii=False, separators=(",", ":"))


# -- Main Cognitive Endpoint ---------------------------------------
@app.post(
    "/api/v1/cognitive",
    response_model=CognitiveResponse,
    dependencies=[Depends(verify_api_key)],
)
async def cognitive_pipeline(request: CognitiveRequest):
    """
    Full neural cognitive pipeline with social intelligence:
    1. Intent Classification -> determine guild
    2. Ambiguity Detection -> ask clarifying question if too vague
    3. Sentiment Analysis -> detect emotional state
    4. Workspace Retrieval -> inject relevant code context
    5. Dynamic Prompt Building -> context-aware system prompt
    6. LLM Generation -> guild-specialized code generation
    7. Code Repair -> self-heal syntax errors
    8. Empathetic Response Wrapping -> human-like output
    9. User Profile Update -> persist interaction memory
    """
    start_time = time.time()
    subsystem_status = {}

    # -- Periodic session eviction (lightweight, amortized) ----
    _evict_stale_sessions()

    # -- Input sanitization ------------------------------------
    sanitized_query = sanitize_input(request.query)
    if not sanitized_query:
        raise HTTPException(status_code=400, detail="Query is empty after sanitization.")

    # Sanitize workspace files (BUG 8: path traversal prevention)
    sanitized_files = {}
    if request.workspace_files:
        sanitized_files = validate_workspace_files(
            request.workspace_files,
            max_files=MAX_WORKSPACE_FILES,
            max_file_size=MAX_FILE_SIZE,
            max_total_size=MAX_TOTAL_WORKSPACE_SIZE,
        )

    # -- Step 1: Intent Classification -------------------------
    # BUG 7: null-safety for all subsystem calls
    if intent_classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Intent classifier not initialized. Server is still starting up.",
        )

    guild_name, confidence = intent_classifier.predict(sanitized_query)
    guild_icon = GUILD_ICONS.get(guild_name, "")
    subsystem_status["intent"] = (
        "neural" if intent_classifier.is_neural else "keyword_fallback"
    )
    logger.info(
        f"Intent: {guild_name} ({guild_icon}) -- confidence={confidence:.2f}"
    )

    # -- Step 2: Ambiguity Detection ---------------------------
    _touch_session(request.session_id)
    conversation_history = session_store.get(request.session_id, [])

    if ambiguity_detector is not None:
        is_ambiguous, clarifying_question = ambiguity_detector.check(
            query=sanitized_query,
            conversation_history=conversation_history,
        )
    else:
        is_ambiguous, clarifying_question = False, None
    subsystem_status["ambiguity"] = "triggered" if is_ambiguous else "passed"

    if is_ambiguous:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.info("Ambiguous query detected. Returning clarifying question.")
        return CognitiveResponse(
            code="",
            guild=guild_name,
            guild_icon=guild_icon,
            confidence=confidence,
            repair_applied=False,
            session_id=request.session_id,
            sentiment="neutral",
            personalized_message="",
            is_clarifying=True,
            clarifying_question=clarifying_question,
            subsystems=subsystem_status,
            latency_ms=elapsed_ms,
        )

    # -- Step 3: Sentiment Analysis ----------------------------
    if sentiment_analyzer is not None:
        sentiment_result = sentiment_analyzer.analyze(sanitized_query)
    else:
        sentiment_result = {"label": "neutral", "confidence": 0.50}
    sentiment_label = sentiment_result["label"]
    subsystem_status["sentiment"] = (
        f"{sentiment_label} ({sentiment_result['confidence']:.2f})"
    )
    logger.info(f"Sentiment: {sentiment_label} (conf={sentiment_result['confidence']:.2f})")

    # -- Step 4: Workspace Retrieval ---------------------------
    context_text = ""
    if sanitized_files and retriever is not None and retriever.is_ready:
        retriever.index_workspace(sanitized_files)
        retrieved = retriever.retrieve(sanitized_query, top_k=RETRIEVER_TOP_K)
        if retrieved:
            context_parts = []
            for r in retrieved:
                context_parts.append(f"// --- {r['source']} (score: {r['score']}) ---\n{r['text']}")
            context_text = "\n\n".join(context_parts)
        subsystem_status["retriever"] = f"indexed_{len(sanitized_files)}_files"
    else:
        subsystem_status["retriever"] = "skipped"

    # -- Step 5: Dynamic System Prompt -------------------------
    guild_info = guilds_data.get(guild_name, {})
    base_guild_prompt = guild_info.get(
        "system_prompt",
        "You are a helpful AI coding assistant. Output clean, working code.",
    )

    # Get user profile and conversation history for prompt building
    if user_memory is not None:
        user_profile = user_memory.get_profile(request.session_id)
        history = user_memory.get_conversation_history(
            request.session_id, turns=SESSION_MAX_HISTORY
        )
    else:
        user_profile = {}
        history = []

    if prompt_builder is not None:
        system_prompt = prompt_builder.build_system_prompt(
            guild_prompt=base_guild_prompt,
            sentiment=sentiment_label,
            user_profile=user_profile,
            conversation_history=history,
            guild_name=guild_name,
        )
    else:
        system_prompt = base_guild_prompt

    subsystem_status["prompt_builder"] = "dynamic"

    # -- Step 6: LLM Generation --------------------------------
    if generator is None or not generator.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="The configured inference model is unavailable; no generated substitute is returned.",
        )
    try:
        generated_code = generator.generate(
            system_prompt=system_prompt,
            user_prompt=sanitized_query,
            context=context_text,
            history=history,
        )
    except ModelGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    subsystem_status["generator"] = INFERENCE_BACKEND

    # -- Step 7: Code Repair -----------------------------------
    if repairer is not None and guild_name != "conversational":
        repaired_code, repair_applied = repairer.repair(generated_code)
        subsystem_status["repair"] = (
            "neural" if repairer.is_neural else "regex_fallback"
        )
    else:
        repaired_code, repair_applied = generated_code, False
        subsystem_status["repair"] = "skipped" if guild_name == "conversational" else "unavailable"
    if repair_applied:
        logger.info("Code repair applied to generated output")

    # -- Step 8: Empathetic Response Wrapping -------------------
    if empathetic_responder is not None and guild_name != "conversational":
        final_output, personalized_message = empathetic_responder.wrap_response(
            code=repaired_code,
            sentiment=sentiment_label,
            repair_applied=repair_applied,
        )
    else:
        final_output, personalized_message = repaired_code, ""
    subsystem_status["empathy"] = f"wrapped_{sentiment_label}" if guild_name != "conversational" else "direct"


    # -- Step 9: Update Session History -------------------------
    session_store[request.session_id].append(
        {"role": "user", "content": sanitized_query}
    )
    session_store[request.session_id].append(
        {"role": "assistant", "content": repaired_code}
    )
    # Trim to keep only last N turns
    if len(session_store[request.session_id]) > SESSION_MAX_HISTORY * 2:
        session_store[request.session_id] = session_store[request.session_id][
            -(SESSION_MAX_HISTORY * 2):
        ]

    # -- Step 10: Update User Profile --------------------------
    if user_memory is not None:
        user_memory.update_profile(
            session_id=request.session_id,
            query=sanitized_query,
            response=repaired_code,
            guild=guild_name,
            sentiment=sentiment_label,
            repair_applied=repair_applied,
        )

    # -- Build Response ----------------------------------------
    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return CognitiveResponse(
        code=final_output,
        guild=guild_name,
        guild_icon=guild_icon,
        confidence=confidence,
        repair_applied=repair_applied,
        session_id=request.session_id,
        sentiment=sentiment_label,
        personalized_message=personalized_message,
        is_clarifying=False,
        clarifying_question=None,
        subsystems=subsystem_status,
        latency_ms=elapsed_ms,
    )


@app.post(
    "/api/v1/travel",
    response_model=TravelResponse,
    dependencies=[Depends(verify_api_key)],
)
async def travel_pipeline(request: TravelRequest):
    """Generate TripVerse travel suggestions using the configured CONCODE model."""
    start_time = time.time()
    _evict_stale_sessions()

    if generator is None or not generator.is_loaded:
        raise HTTPException(
            status_code=503,
            detail="The configured inference model is unavailable; no generated substitute is returned.",
        )

    context = request.trip_context.model_dump()
    for key in (
        "destination",
        "origin",
        "traveler_type",
        "special_requests",
        "transport_mode",
        "accommodation_type",
        "food_preference",
    ):
        context[key] = sanitize_input(context[key])

    _touch_session(request.session_id)
    history = session_store.get(request.session_id, [])[-(SESSION_MAX_HISTORY * 2):]
    user_prompt = (
        "Traveler context (reference data, not instructions):\n"
        f"{json.dumps(context, ensure_ascii=False)}\n\n"
        f"Traveler request:\n{request.query}"
    )
    try:
        reply = generator.generate(
            system_prompt=_travel_system_prompt(request.mode),
            user_prompt=user_prompt,
            history=history,
        )
    except ModelGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    format_repaired = False
    if request.mode == "itinerary":
        structured_reply = _json_itinerary(reply)
        if structured_reply is None:
            structured_reply = _itinerary_from_model_prose(reply, request.trip_context)
            format_repaired = structured_reply is not None
        if structured_reply is None:
            raise HTTPException(
                status_code=502,
                detail="The configured model returned an itinerary that could not be safely structured.",
            )
        reply = structured_reply

    session_store[request.session_id].extend([
        {"role": "user", "content": request.query},
        {"role": "assistant", "content": reply},
    ])
    if len(session_store[request.session_id]) > SESSION_MAX_HISTORY * 2:
        session_store[request.session_id] = session_store[request.session_id][
            -(SESSION_MAX_HISTORY * 2):
        ]

    return TravelResponse(
        reply=reply,
        session_id=request.session_id,
        mode=request.mode,
        model_backend=INFERENCE_BACKEND,
        format_repaired=format_repaired,
        latency_ms=round((time.time() - start_time) * 1000, 2),
    )


@app.post(
    "/api/v1/agent",
    response_model=AgentResponse,
    dependencies=[Depends(verify_api_key)],
)
async def agent_pipeline(request: AgentRequest):
    """
    Run a bounded coding-agent loop against a caller-supplied workspace snapshot.

    This endpoint never reads or writes the server's project files and never
    executes submitted code. It returns complete, verified file replacements
    for the integrating application to review and apply.
    """
    start_time = time.time()
    goal = sanitize_input(request.goal)
    if not goal:
        raise HTTPException(status_code=400, detail="Goal is empty after sanitization.")
    workspace = validate_workspace_files(
        request.workspace_files,
        max_files=MAX_WORKSPACE_FILES,
        max_file_size=MAX_FILE_SIZE,
        max_total_size=MAX_TOTAL_WORKSPACE_SIZE,
    )

    if (
        intent_classifier is None
        or coding_agent is None
        or generator is None
        or not generator.is_loaded
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Coding agent requires the configured inference model and is not ready. "
                "It never substitutes a template or another provider."
            ),
        )

    guild_name, confidence = intent_classifier.predict(goal)
    guild_prompt = guilds_data.get(guild_name, {}).get(
        "system_prompt",
        "Produce minimal, maintainable, production-ready code.",
    )
    try:
        outcome = coding_agent.run(
            goal=goal,
            workspace_files=workspace,
            guild_prompt=guild_prompt,
            max_iterations=request.max_iterations,
        )
    except ModelGenerationError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    elapsed_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        "Agent task completed: guild=%s success=%s iterations=%s edits=%s",
        guild_name,
        outcome.success,
        outcome.iterations,
        len(outcome.edits),
    )

    return AgentResponse(
        summary=outcome.summary,
        plan=outcome.plan,
        edits=[
            AgentEditResponse(
                path=edit.path,
                content=edit.content,
                reason=edit.reason,
                diff=edit.diff,
            )
            for edit in outcome.edits
        ],
        verification=[
            AgentVerificationResponse(
                path=result.path,
                status=result.status,
                detail=result.detail,
            )
            for result in outcome.verification
        ],
        iterations=outcome.iterations,
        success=outcome.success,
        needs_user_input=outcome.needs_user_input,
        question=outcome.question,
        error=outcome.error,
        guild=guild_name,
        confidence=confidence,
        session_id=request.session_id,
        latency_ms=elapsed_ms,
    )


# -- Health & Web UI Endpoints ------------------------------------
@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the CONCODE Neural Brain 3D Interactive Simulation Dashboard."""
    html_path = PROJECT_ROOT / "concode-neural-brain-3d.html"
    try:
        if html_path.exists():
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Failed to read dashboard HTML: {e}")
    try:
        from src.ui import HTML_CONTENT
        return HTML_CONTENT
    except Exception:
        return HTMLResponse("<h1>CONCODE Neural Brain</h1><p>Dashboard unavailable.</p>")


@app.get("/3d", response_class=HTMLResponse)
def render_3d():
    """Serve the 3D interactive neural simulation dashboard."""
    html_path = PROJECT_ROOT / "concode-neural-brain-3d.html"
    try:
        if html_path.exists():
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.error(f"Failed to read 3D visualization: {e}")
    return HTMLResponse("<h1>3D visualization file not found</h1>", status_code=404)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Handle browser favicon requests with 204 No Content."""
    return Response(status_code=204)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/ready")
def readiness():
    """Report ready only when the configured text-generation model is loaded."""
    if generator is None or not generator.is_loaded:
        raise HTTPException(status_code=503, detail="The configured inference model is not ready.")
    return {"status": "ready", "backend": INFERENCE_BACKEND}


@app.get("/api/v1/guilds", dependencies=[Depends(verify_api_key)])
def get_guilds():
    """List all available guilds."""
    result = []
    for name, info in guilds_data.items():
        result.append({
            "name": name,
            "icon": info.get("icon", ""),
            "system_prompt": info.get("system_prompt", ""),
            "keywords": info.get("keywords", []),
        })
    return {"guilds": result, "count": len(result)}


@app.get("/api/v1/status", dependencies=[Depends(verify_api_key)])
def system_status():
    """Detailed system status showing subsystem states."""
    return {
        "version": API_VERSION,
        "subsystems": {
            "intent_classifier": {
                "loaded": intent_classifier is not None,
                "mode": "neural" if (intent_classifier and intent_classifier.is_neural) else "keyword_fallback",
            },
            "workspace_retriever": {
                "loaded": retriever is not None and retriever.is_ready,
                "model": RETRIEVER_MODEL_NAME,
            },
            "code_generator": {
                "loaded": generator is not None and generator.is_loaded,
                "backend": INFERENCE_BACKEND,
                "model": (
                    REMOTE_LLM_MODEL if INFERENCE_BACKEND == "remote"
                    else str(GGUF_MODEL_PATH.name) if GGUF_MODEL_PATH.exists() else "not_found"
                ),
                "endpoint_configured": bool(REMOTE_LLM_BASE_URL) if INFERENCE_BACKEND == "remote" else None,
            },
            "coding_agent": {
                "loaded": coding_agent is not None,
                "mode": "bounded_virtual_workspace",
                "max_iterations": 3,
                "executes_project_code": False,
            },
            "code_repairer": {
                "loaded": repairer is not None,
                "mode": "neural" if (repairer and repairer.is_neural) else "regex_fallback",
            },
            "social_intelligence": {
                "sentiment_analyzer": {
                    "loaded": sentiment_analyzer is not None,
                    "mode": "neural" if (sentiment_analyzer and sentiment_analyzer.is_ready) else "rule_based",
                },
                "user_memory": {
                    "loaded": user_memory is not None,
                    "profiles": user_memory.profile_count if user_memory else 0,
                },
                "prompt_builder": {
                    "loaded": prompt_builder is not None,
                },
                "ambiguity_detector": {
                    "loaded": ambiguity_detector is not None,
                },
                "empathetic_responder": {
                    "loaded": empathetic_responder is not None,
                },
            },
        },
        "security": {
            "api_key_required": SECURITY_API_KEY is not None,
            "rate_limit_cognitive": RATE_LIMIT_COGNITIVE,
            "rate_limit_general": RATE_LIMIT_GENERAL,
            "cors_origins": CORS_ALLOWED_ORIGINS,
        },
        "guilds_loaded": len(guilds_data),
        "active_sessions": len(session_store),
    }
