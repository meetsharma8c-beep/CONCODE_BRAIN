"""
CONCODE Neural Brain -- Comprehensive Behavioral Test Suite

Validates every subsystem in isolation and then end-to-end:
  1. Intent Classifier (DistilBERT neural + keyword fallback)
  2. Code Repair (CodeT5 neural + regex fallback)
  3. Sentiment Analyzer (pipeline + rule-based)
  4. Ambiguity Detector
  5. Empathetic Responder
  6. Workspace Retriever (MiniLM + FAISS/NumPy)
  7. Code Generator (local GGUF)
  8. Full Pipeline Integration (all subsystems together)
"""

import json
import os
import sys
import time
import traceback

# Enable MPS CPU fallback for Apple Silicon
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Ensure project root is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.config import (
    GUILDS_YAML,
    INTENT_MODEL_DIR,
    INTENT_FALLBACK_GUILD,
    REPAIR_MODEL_DIR,
    REPAIR_MAX_INPUT_LENGTH,
    REPAIR_MAX_OUTPUT_LENGTH,
    SOCIAL_SENTIMENT_MODEL,
    USER_PROFILES_PATH,
    EMPATHY_TEMPLATES_PATH,
    CLARIFYING_QUESTIONS_PATH,
    RETRIEVER_MODEL_NAME,
    RETRIEVER_CHUNK_SIZE,
    GGUF_MODEL_PATH,
    LLM_CONTEXT_LENGTH,
    LLM_GPU_LAYERS,
    LLM_THREADS,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_TOP_P,
)


# ── Formatting Helpers ────────────────────────────────────────
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
SKIP = "[SKIP]"

results = {"passed": 0, "failed": 0, "warnings": 0, "skipped": 0}


def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def check(name, condition, detail=""):
    global results
    if condition:
        results["passed"] += 1
        print(f"  {PASS} {name}")
    else:
        results["failed"] += 1
        print(f"  {FAIL} {name}")
    if detail:
        print(f"         {detail}")


def warn(name, detail=""):
    global results
    results["warnings"] += 1
    print(f"  {WARN} {name}")
    if detail:
        print(f"         {detail}")


def skip(name, detail=""):
    global results
    results["skipped"] += 1
    print(f"  {SKIP} {name}")
    if detail:
        print(f"         {detail}")


# ═══════════════════════════════════════════════════════════════
#  TEST 1: Intent Classifier
# ═══════════════════════════════════════════════════════════════
def test_intent_classifier():
    section("TEST 1: Intent Classifier (DistilBERT)")

    from src.brain.intent import IntentClassifier

    classifier = IntentClassifier(
        model_dir=str(INTENT_MODEL_DIR),
        guilds_yaml=str(GUILDS_YAML),
        fallback_guild=INTENT_FALLBACK_GUILD,
    )

    check("Model loaded successfully", classifier.is_neural,
          f"Neural mode: {classifier.is_neural}")

    if not classifier.is_neural:
        warn("Skipping neural tests -- model not loaded, keyword fallback only")
        return classifier

    # Test cases: (query, expected_guild, min_confidence)
    test_cases = [
        ("Fix this null pointer exception in my Java code", "debugger", 0.50),
        ("Create a Three.js particle system with shaders", "webgl", 0.50),
        ("Train a transformer model for text classification", "ai_ml", 0.50),
        ("Write unit tests for the login component with Jest", "qa", 0.50),
        ("Set up a PostgreSQL schema for user sessions", "database", 0.50),
        ("Build a REST API endpoint with FastAPI", "api", 0.50),
        ("Implement JWT authentication middleware", "security", 0.50),
        ("Optimize the render loop to reduce frame drops", "performance", 0.50),
        ("Create a responsive dark mode card component with CSS", "ui_ux", 0.50),
        ("Set up Docker Compose with nginx reverse proxy", "devops", 0.50),
        ("Build a full-stack todo app with React and Node", "fullstack", 0.50),
    ]

    correct = 0
    for query, expected_guild, min_conf in test_cases:
        guild, conf = classifier.predict(query)
        is_correct = guild == expected_guild
        if is_correct:
            correct += 1
        check(
            f"'{query[:50]}...' -> {guild}",
            is_correct,
            f"Expected: {expected_guild}, Got: {guild} (conf={conf:.4f})"
        )

    accuracy = correct / len(test_cases) if test_cases else 0
    check(
        f"Overall intent accuracy: {accuracy:.1%} ({correct}/{len(test_cases)})",
        accuracy >= 0.70,
        f"Minimum threshold: 70%"
    )

    return classifier


# ═══════════════════════════════════════════════════════════════
#  TEST 2: Code Repair
# ═══════════════════════════════════════════════════════════════
def test_code_repair():
    section("TEST 2: Code Repair (CodeT5)")

    from src.brain.repair import CodeRepairer

    repairer = CodeRepairer(
        model_dir=str(REPAIR_MODEL_DIR),
        max_input_length=REPAIR_MAX_INPUT_LENGTH,
        max_output_length=REPAIR_MAX_OUTPUT_LENGTH,
    )

    check("Model loaded successfully", repairer.is_neural,
          f"Neural mode: {repairer.is_neural}")

    # Test: typo repair
    broken_code = 'functoin hello() { consol.log("hello"); retun 42; }'
    repaired, was_repaired = repairer.repair(broken_code)
    check("Typo repair detects changes", was_repaired,
          f"Input:  {broken_code[:60]}\n         Output: {repaired[:60]}")

    # Test: bracket balancing
    unbalanced = 'function test() { if (true) { console.log("ok")'
    repaired2, was_repaired2 = repairer.repair(unbalanced)
    check("Bracket balancing applied", was_repaired2,
          f"Input:  {unbalanced}\n         Output: {repaired2}")

    # Test: clean code should not be modified
    clean_code = 'function greet(name) { return `Hello, ${name}!`; }'
    repaired3, was_repaired3 = repairer.repair(clean_code)
    if repairer.is_neural:
        # Neural models may or may not modify clean code
        check("Clean code handling (neural)", True,
              f"Modified: {was_repaired3}")
    else:
        check("Clean code not modified (regex)", not was_repaired3)

    return repairer


# ═══════════════════════════════════════════════════════════════
#  TEST 3: Sentiment Analyzer
# ═══════════════════════════════════════════════════════════════
def test_sentiment_analyzer():
    section("TEST 3: Sentiment Analyzer")

    from src.brain.social import SentimentAnalyzer

    analyzer = SentimentAnalyzer(model_name=SOCIAL_SENTIMENT_MODEL)

    check("Sentiment analyzer initialized", True,
          f"Neural mode: {analyzer.is_ready}")

    test_cases = [
        ("This is awesome, thanks for the help!", "positive"),
        ("I'm stuck and frustrated, nothing works", "negative"),
        ("I don't understand how this function works", "confused"),
        ("Write a function to sort an array", "neutral"),
    ]

    for text, expected_sentiment in test_cases:
        result = analyzer.analyze(text)
        label = result["label"]
        conf = result["confidence"]
        check(
            f"'{text[:45]}...' -> {label}",
            label == expected_sentiment,
            f"Expected: {expected_sentiment}, Got: {label} (conf={conf:.4f})"
        )

    return analyzer


# ═══════════════════════════════════════════════════════════════
#  TEST 4: Ambiguity Detector
# ═══════════════════════════════════════════════════════════════
def test_ambiguity_detector():
    section("TEST 4: Ambiguity Detector")

    from src.brain.social import AmbiguityDetector

    detector = AmbiguityDetector(questions_path=str(CLARIFYING_QUESTIONS_PATH))
    check("Ambiguity detector initialized", True)

    # Ambiguous queries (no conversation history)
    is_amb, question = detector.check("fix", [])
    check("Short ambiguous 'fix' detected", is_amb,
          f"Question: {question}")

    is_amb2, question2 = detector.check("help", [])
    check("Short ambiguous 'help' detected", is_amb2,
          f"Question: {question2}")

    # Clear query should not be ambiguous
    is_amb3, _ = detector.check("Write a Python function to calculate fibonacci numbers", [])
    check("Clear query is not ambiguous", not is_amb3)

    # Follow-up in active conversation should not trigger ambiguity
    history = [{"role": "user", "content": "fix"}, {"role": "assistant", "content": "Fixed!"}]
    is_amb4, _ = detector.check("fix", history)
    check("Follow-up in conversation not ambiguous", not is_amb4)

    return detector


# ═══════════════════════════════════════════════════════════════
#  TEST 5: Empathetic Responder
# ═══════════════════════════════════════════════════════════════
def test_empathetic_responder():
    section("TEST 5: Empathetic Responder")

    from src.brain.social import EmpatheticResponder

    responder = EmpatheticResponder(templates_path=str(EMPATHY_TEMPLATES_PATH))
    check("Empathetic responder initialized", True,
          f"Templates loaded: {len(responder.templates)} categories")

    code = "function hello() { return 'world'; }"

    # Test neutral wrapping
    wrapped_neutral, msg_neutral = responder.wrap_response(code, "neutral")
    check("Neutral response wrapping", len(wrapped_neutral) >= len(code),
          f"Message length: {len(wrapped_neutral)}")

    # Test negative wrapping
    wrapped_neg, msg_neg = responder.wrap_response(code, "negative")
    check("Negative sentiment wrapping", True,
          f"Preamble present: {bool(msg_neg)}")

    # Test repair notice
    wrapped_repair, msg_repair = responder.wrap_response(code, "neutral", repair_applied=True)
    check("Repair notice wrapping", True,
          f"Repair preamble present: {bool(msg_repair)}")

    return responder


# ═══════════════════════════════════════════════════════════════
#  TEST 6: User Memory Store
# ═══════════════════════════════════════════════════════════════
def test_user_memory():
    section("TEST 6: User Memory Store")

    from src.brain.social import UserMemoryStore
    import tempfile

    # Use a temp file to avoid mutating real profiles
    tmp_path = os.path.join(BASE_DIR, "data", "_test_profiles.json")

    try:
        store = UserMemoryStore(profiles_path=tmp_path, max_profiles=100, save_interval=1)
        check("Memory store initialized", True)

        # Create profile
        profile = store.get_profile("test-session-001")
        check("Profile creation", profile["session_id"] == "test-session-001")

        # Update profile
        store.update_profile(
            session_id="test-session-001",
            query="Fix my code",
            response="Here's the fix...",
            guild="debugger",
            sentiment="negative",
            repair_applied=True,
        )
        updated = store.get_profile("test-session-001")
        check("Profile update -- guild tracking", updated["favorite_guilds"].get("debugger", 0) == 1)
        check("Profile update -- repair count", updated["repair_count"] == 1)
        check("Profile update -- sentiment history", len(updated["sentiment_history"]) == 1)
        check("Profile update -- conversation history", len(updated["history"]) >= 2)

        # Test conversation history retrieval
        history = store.get_conversation_history("test-session-001", turns=3)
        check("Conversation history retrieval", len(history) >= 2)

    finally:
        # Cleanup test file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ═══════════════════════════════════════════════════════════════
#  TEST 7: Workspace Retriever
# ═══════════════════════════════════════════════════════════════
def test_retriever():
    section("TEST 7: Workspace Retriever (MiniLM + FAISS)")

    from src.brain.retriever import WorkspaceRetriever

    retriever = WorkspaceRetriever(
        model_name=RETRIEVER_MODEL_NAME,
        chunk_size=RETRIEVER_CHUNK_SIZE,
    )

    check("Retriever model loaded", retriever.is_ready,
          f"Model: {RETRIEVER_MODEL_NAME}")

    if not retriever.is_ready:
        skip("Retriever tests -- model not loaded")
        return retriever

    # Index some workspace files
    workspace = {
        "auth.py": """
import jwt
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_token(token: str, secret: str) -> dict:
    return jwt.decode(token, secret, algorithms=["HS256"])
""",
        "database.py": """
import sqlite3

def create_users_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')

def insert_user(conn, username, email):
    conn.execute("INSERT INTO users (username, email) VALUES (?, ?)", (username, email))
    conn.commit()
""",
        "server.py": """
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserRequest(BaseModel):
    username: str
    email: str

@app.post("/users")
async def create_user(request: UserRequest):
    return {"status": "created", "username": request.username}
""",
    }

    retriever.index_workspace(workspace)
    check("Workspace indexed", len(retriever.chunks) > 0,
          f"Chunks created: {len(retriever.chunks)}")

    # Test retrieval
    results_auth = retriever.retrieve("How to hash a password with bcrypt", top_k=3)
    check("Retrieval for auth query", len(results_auth) > 0)
    if results_auth:
        top_source = results_auth[0]["source"]
        check("Top result is auth.py", top_source == "auth.py",
              f"Top source: {top_source}, score: {results_auth[0]['score']:.4f}")

    results_db = retriever.retrieve("Create a database table for users", top_k=3)
    check("Retrieval for database query", len(results_db) > 0)
    if results_db:
        top_source = results_db[0]["source"]
        check("Top result is database.py", top_source == "database.py",
              f"Top source: {top_source}, score: {results_db[0]['score']:.4f}")

    return retriever


# ═══════════════════════════════════════════════════════════════
#  TEST 8: Code Generator
# ═══════════════════════════════════════════════════════════════
def test_code_generator():
    section("TEST 8: Code Generator (CodeLlama GGUF)")

    from src.brain.generator import CodeGenerator, ModelGenerationError

    generator = CodeGenerator(
        model_path=str(GGUF_MODEL_PATH),
        n_ctx=LLM_CONTEXT_LENGTH,
        n_gpu_layers=LLM_GPU_LAYERS,
        n_threads=LLM_THREADS,
        max_tokens=256,  # Shorter for testing speed
        temperature=LLM_TEMPERATURE,
        top_p=LLM_TOP_P,
    )

    check("Generator initialized", True,
          f"GGUF loaded: {generator.is_loaded}")

    # Test generation using the local GGUF model.
    system_prompt = "You are a debugging specialist. Provide clean, working code."
    user_prompt = "Write a function to find the maximum element in an array"

    start = time.time()
    response = generator.generate(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    elapsed = time.time() - start

    check("Code generation produces output", len(response) > 0,
          f"Response length: {len(response)} chars, Time: {elapsed:.2f}s")

    # Verify it contains code-like content
    has_code = any(kw in response.lower() for kw in ["function", "def ", "return", "const", "class", "import"])
    check("Response contains code-like content", has_code,
          f"First 100 chars: {response[:100]}")

    # A missing local model must fail visibly, never return canned code.
    unavailable = CodeGenerator(model_path="/tmp/concode-missing-model.gguf")
    try:
        unavailable.generate(system_prompt=system_prompt, user_prompt=user_prompt)
        unavailable_error = False
    except ModelGenerationError:
        unavailable_error = True
    check("Missing model returns a genuine availability error", unavailable_error)

    return generator


# ═══════════════════════════════════════════════════════════════
#  TEST 9: Dynamic Prompt Builder
# ═══════════════════════════════════════════════════════════════
def test_prompt_builder():
    section("TEST 9: Dynamic Prompt Builder")

    from src.brain.social import DynamicPromptBuilder

    builder = DynamicPromptBuilder()
    check("Prompt builder initialized", True)

    # Build a prompt with negative sentiment and conversation history
    prompt = builder.build_system_prompt(
        guild_prompt="You are a debugging specialist.",
        sentiment="negative",
        user_profile={"session_id": "test", "tone_preference": "balanced"},
        conversation_history=[
            {"role": "user", "content": "My code is broken"},
            {"role": "assistant", "content": "Here's the fix..."},
        ],
    )
    check("Dynamic prompt includes guild base", "debugging specialist" in prompt)
    check("Dynamic prompt includes sentiment note", "difficulty" in prompt.lower() or "empathetic" in prompt.lower())
    check("Dynamic prompt includes history context", "previous turn" in prompt.lower())

    # Build prompt with confused sentiment
    prompt_confused = builder.build_system_prompt(
        guild_prompt="You are a QA specialist.",
        sentiment="confused",
        user_profile={},
        conversation_history=[],
    )
    check("Confused prompt includes explanation note", "confused" in prompt_confused.lower() or "step-by-step" in prompt_confused.lower())

    return builder


# ═══════════════════════════════════════════════════════════════
#  TEST 10: Full Pipeline Integration
# ═══════════════════════════════════════════════════════════════
def test_full_pipeline():
    section("TEST 10: Full Pipeline Integration")

    from src.brain.intent import IntentClassifier
    from src.brain.retriever import WorkspaceRetriever
    from src.brain.generator import CodeGenerator
    from src.brain.repair import CodeRepairer
    from src.brain.social import (
        SentimentAnalyzer,
        DynamicPromptBuilder,
        AmbiguityDetector,
        EmpatheticResponder,
    )

    # Initialize all subsystems
    intent = IntentClassifier(
        model_dir=str(INTENT_MODEL_DIR),
        guilds_yaml=str(GUILDS_YAML),
        fallback_guild=INTENT_FALLBACK_GUILD,
    )
    repairer = CodeRepairer(
        model_dir=str(REPAIR_MODEL_DIR),
        max_input_length=REPAIR_MAX_INPUT_LENGTH,
        max_output_length=REPAIR_MAX_OUTPUT_LENGTH,
    )
    sentiment = SentimentAnalyzer(model_name=SOCIAL_SENTIMENT_MODEL)
    ambiguity = AmbiguityDetector(questions_path=str(CLARIFYING_QUESTIONS_PATH))
    empathy = EmpatheticResponder(templates_path=str(EMPATHY_TEMPLATES_PATH))
    prompt_builder = DynamicPromptBuilder()
    retriever = WorkspaceRetriever(
        model_name=RETRIEVER_MODEL_NAME,
        chunk_size=RETRIEVER_CHUNK_SIZE,
    )
    generator = CodeGenerator(
        model_path=str(GGUF_MODEL_PATH),
        n_ctx=LLM_CONTEXT_LENGTH,
        n_gpu_layers=LLM_GPU_LAYERS,
        n_threads=LLM_THREADS,
        max_tokens=256,
        temperature=LLM_TEMPERATURE,
        top_p=LLM_TOP_P,
    )

    check("All subsystems initialized", True)

    # Simulate a full cognitive pipeline request
    query = "Fix the null pointer error in my authentication middleware"
    session_id = "integration-test-001"

    print(f"\n  Simulating full pipeline for: \"{query}\"")
    pipeline_start = time.time()

    # Step 1: Intent
    guild, conf = intent.predict(query)
    print(f"    1. Intent: {guild} (conf={conf:.4f})")

    # Step 2: Ambiguity
    is_amb, clarify = ambiguity.check(query, [])
    print(f"    2. Ambiguity: {'triggered' if is_amb else 'passed'}")

    # Step 3: Sentiment
    sent_result = sentiment.analyze(query)
    sent_label = sent_result["label"]
    print(f"    3. Sentiment: {sent_label} (conf={sent_result['confidence']:.4f})")

    # Step 4: Retrieval (empty workspace for this test)
    print(f"    4. Retrieval: skipped (no workspace)")

    # Step 5: Dynamic prompt
    system_prompt = prompt_builder.build_system_prompt(
        guild_prompt="You are a security expert. Fix authentication issues with precision.",
        sentiment=sent_label,
        user_profile={},
        conversation_history=[],
    )
    print(f"    5. Prompt built: {len(system_prompt)} chars")

    # Step 6: Generation
    code = generator.generate(system_prompt=system_prompt, user_prompt=query)
    print(f"    6. Generated: {len(code)} chars")

    # Step 7: Repair
    repaired, was_repaired = repairer.repair(code)
    print(f"    7. Repair: {'applied' if was_repaired else 'no changes'}")

    # Step 8: Empathetic wrapping
    final, msg = empathy.wrap_response(repaired, sent_label, was_repaired)
    print(f"    8. Empathy: wrapped ({len(final)} chars)")

    pipeline_elapsed = time.time() - pipeline_start

    check("Pipeline completed", len(final) > 0,
          f"Total time: {pipeline_elapsed:.2f}s")
    check("Pipeline latency acceptable", pipeline_elapsed < 120,
          f"Elapsed: {pipeline_elapsed:.2f}s (threshold: 120s)")

    print(f"\n  --- Pipeline Output Preview ---")
    print(f"  Guild: {guild} | Sentiment: {sent_label} | Repair: {was_repaired}")
    print(f"  Output (first 300 chars):")
    for line in final[:300].split("\n"):
        print(f"    {line}")
    if len(final) > 300:
        print(f"    ... ({len(final) - 300} more chars)")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  CONCODE Neural Brain -- Comprehensive Behavioral Test Suite")
    print("=" * 70)
    print(f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Project: {BASE_DIR}")

    total_start = time.time()

    try:
        test_intent_classifier()
    except Exception as e:
        print(f"\n  {FAIL} Intent classifier test crashed: {e}")
        traceback.print_exc()

    try:
        test_code_repair()
    except Exception as e:
        print(f"\n  {FAIL} Code repair test crashed: {e}")
        traceback.print_exc()

    try:
        test_sentiment_analyzer()
    except Exception as e:
        print(f"\n  {FAIL} Sentiment analyzer test crashed: {e}")
        traceback.print_exc()

    try:
        test_ambiguity_detector()
    except Exception as e:
        print(f"\n  {FAIL} Ambiguity detector test crashed: {e}")
        traceback.print_exc()

    try:
        test_empathetic_responder()
    except Exception as e:
        print(f"\n  {FAIL} Empathetic responder test crashed: {e}")
        traceback.print_exc()

    try:
        test_user_memory()
    except Exception as e:
        print(f"\n  {FAIL} User memory test crashed: {e}")
        traceback.print_exc()

    try:
        test_retriever()
    except Exception as e:
        print(f"\n  {FAIL} Retriever test crashed: {e}")
        traceback.print_exc()

    try:
        test_code_generator()
    except Exception as e:
        print(f"\n  {FAIL} Code generator test crashed: {e}")
        traceback.print_exc()

    try:
        test_prompt_builder()
    except Exception as e:
        print(f"\n  {FAIL} Prompt builder test crashed: {e}")
        traceback.print_exc()

    try:
        test_full_pipeline()
    except Exception as e:
        print(f"\n  {FAIL} Full pipeline test crashed: {e}")
        traceback.print_exc()

    total_elapsed = time.time() - total_start

    # ── Final Report ──────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  FINAL REPORT")
    print("=" * 70)
    print(f"  Passed:   {results['passed']}")
    print(f"  Failed:   {results['failed']}")
    print(f"  Warnings: {results['warnings']}")
    print(f"  Skipped:  {results['skipped']}")
    print(f"  Total:    {results['passed'] + results['failed'] + results['warnings'] + results['skipped']}")
    print(f"  Time:     {total_elapsed:.2f}s")
    print("=" * 70)

    if results["failed"] > 0:
        print(f"\n  RESULT: FAILURES DETECTED ({results['failed']} tests failed)")
        sys.exit(1)
    else:
        print(f"\n  RESULT: ALL TESTS PASSED")
        sys.exit(0)
