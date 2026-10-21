"""
CONCODE Neural Brain -- Social Intelligence Subsystem

Components:
1. SentimentAnalyzer: Analyzes prompt sentiment (positive, neutral, negative, confused).
2. UserMemoryStore: Maintains long-term user profile preferences and interaction history.
3. DynamicPromptBuilder: Composes context-aware system prompts based on sentiment, profile, and history.
4. AmbiguityDetector: Detects vague/ambiguous queries and suggests clarifying questions.
5. EmpatheticResponder: Wraps code output with empathetic preambles/postambles.
"""

import json
import logging
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

logger = logging.getLogger("concode.brain.social")


class SentimentAnalyzer:
    """Analyzes text sentiment with neural model or rule-based fallback."""

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        self.model_name = model_name
        self.classifier = None
        self.is_ready = False

        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
            # Do not contact a model host during server startup. The social
            # layer is optional and falls back to its local rules if uncached.
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                local_files_only=True,
            )
            self.classifier = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=-1,  # CPU for lightweight sentiment inference
            )
            self.is_ready = True
            logger.info("Neural sentiment analyzer loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load neural sentiment analyzer ({e}); using rule-based fallback")
            self.is_ready = False

    # Imperative verbs that signal neutral task requests.
    # Checked before the neural model to avoid SST-2 binary misclassification
    # (SST-2 has no neutral class, so "Write a function..." maps to NEGATIVE).
    _IMPERATIVE_VERBS_RE = re.compile(
        r"^\s*(write|create|build|make|implement|add|generate|set up|setup|design|refactor|convert|update|deploy|configure|initialize|define|extend|compose|develop|render|show|list|fetch|get|return|calculate|compute|parse|format|sort|filter|merge|split|map|reduce|find|search|validate|serialize|deserialize|transform|handle|process|call|run|execute|install|connect|disconnect|mount|unmount|register|unregister|encode|decode|hash|verify|check|test|print|log|debug|trace|profile|benchmark|optimize|cache|index|query|insert|delete|select|join|group|aggregate|migrate|seed|scaffold|scaffold|clone|fork|push|pull|commit|tag|release|publish|package)\b",
        re.IGNORECASE,
    )
    _EMOTIONAL_WORDS_RE = re.compile(
        r"\b(frustrated|annoyed|broken|hate|horrible|terrible|stuck|failing|impossible|confused|angry|furious|love|amazing|awesome|great|perfect|excellent|wonderful|beautiful|happy|excited|worried|anxious|scared|afraid|help|error|bug|wrong|fail|crash|issue|problem|sucks|stupid|useless|worst|best|thank|thanks|please|sorry|damn|crap|shit|hell|wtf)\b",
        re.IGNORECASE,
    )

    def analyze(self, text: str) -> Dict[str, Union[str, float]]:
        """Analyze sentiment of query text returning label and confidence."""
        text_lower = text.lower()

        # Check explicit frustration / confusion regex overrides
        if re.search(r"\b(frustrated|annoyed|broken|hate|horrible|terrible|stuck|failing|impossible)\b", text_lower):
            return {"label": "negative", "confidence": 0.95}
        if re.search(r"\b(confused|dont understand|don't understand|what does|how come|why is|explain)\b", text_lower):
            return {"label": "confused", "confidence": 0.90}

        # Neutral imperative detection: task-oriented queries with no emotional
        # words are inherently neutral.  This prevents the SST-2 binary model
        # from misclassifying "Write a function to sort an array" as negative.
        if self._IMPERATIVE_VERBS_RE.match(text) and not self._EMOTIONAL_WORDS_RE.search(text_lower):
            return {"label": "neutral", "confidence": 0.85}

        if self.is_ready and self.classifier:
            try:
                res = self.classifier(text[:512])[0]
                label = res["label"].upper()
                score = float(res["score"])

                if label == "POSITIVE":
                    if score >= 0.85:
                        return {"label": "positive", "confidence": score}
                    else:
                        return {"label": "neutral", "confidence": score}
                else:  # NEGATIVE
                    if score >= 0.70:
                        return {"label": "negative", "confidence": score}
                    else:
                        return {"label": "confused", "confidence": score}
            except Exception as e:
                logger.error(f"Error during neural sentiment prediction: {e}")

        # Rule-based fallback
        pos_words = {"thanks", "thank", "great", "awesome", "perfect", "good", "love", "excellent", "work"}
        neg_words = {"error", "bug", "wrong", "fail", "failed", "bad", "issue", "crash", "help"}

        words = set(re.findall(r"\w+", text_lower))
        pos_count = len(words.intersection(pos_words))
        neg_count = len(words.intersection(neg_words))

        if pos_count > neg_count:
            return {"label": "positive", "confidence": 0.75}
        elif neg_count > pos_count:
            return {"label": "negative", "confidence": 0.75}
        else:
            return {"label": "neutral", "confidence": 0.50}


class UserMemoryStore:
    """
    Manages persistent user profile store and interaction history.

    Guards against unbounded growth via:
    - Profile count cap with LRU eviction (oldest profiles removed first)
    - Write debouncing (saves to disk every N updates, not every request)
    """

    def __init__(
        self,
        profiles_path: str,
        max_profiles: int = 10_000,
        save_interval: int = 5,
    ):
        self.profiles_path = Path(profiles_path)
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.max_profiles = max_profiles
        self.save_interval = max(save_interval, 1)
        self._pending_saves: int = 0
        self._load_profiles()

    def _load_profiles(self) -> None:
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, "r") as f:
                    self.profiles = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load user profiles: {e}")
                self.profiles = {}
        else:
            self.profiles = {}

    def _save_profiles(self, force: bool = False) -> None:
        """Write profiles to disk, respecting debounce interval."""
        self._pending_saves += 1
        if not force and self._pending_saves < self.save_interval:
            return

        try:
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.profiles_path, "w") as f:
                json.dump(self.profiles, f, indent=2)
            self._pending_saves = 0
        except Exception as e:
            logger.error(f"Failed to save user profiles: {e}")

    def flush(self) -> None:
        """Force-save any pending profile changes to disk."""
        if self._pending_saves > 0:
            self._save_profiles(force=True)

    def _evict_oldest(self) -> None:
        """Remove the oldest profiles when the cap is exceeded."""
        overflow = len(self.profiles) - self.max_profiles
        if overflow <= 0:
            return
        # Profiles without a last_active timestamp sort earliest
        sorted_ids = sorted(
            self.profiles.keys(),
            key=lambda sid: self.profiles[sid].get("last_active", 0),
        )
        for sid in sorted_ids[:overflow]:
            del self.profiles[sid]
        logger.info(f"Evicted {overflow} oldest user profiles (cap={self.max_profiles})")

    @property
    def profile_count(self) -> int:
        return len(self.profiles)

    def get_profile(self, session_id: str) -> Dict[str, Any]:
        """Retrieve profile for session, initializing if absent."""
        if session_id not in self.profiles:
            # Evict before adding if at capacity
            if len(self.profiles) >= self.max_profiles:
                self._evict_oldest()
            self.profiles[session_id] = {
                "session_id": session_id,
                "tone_preference": "balanced",
                "favorite_guilds": {},
                "repair_count": 0,
                "sentiment_history": [],
                "history": [],
                "last_active": time.time(),
            }
        return self.profiles[session_id]

    def get_conversation_history(self, session_id: str, turns: int = 3) -> List[Dict[str, str]]:
        profile = self.get_profile(session_id)
        history = profile.get("history", [])
        return history[-(turns * 2):]

    def update_profile(
        self,
        session_id: str,
        query: str,
        response: str,
        guild: str,
        sentiment: str,
        repair_applied: bool,
    ) -> None:
        profile = self.get_profile(session_id)

        # Track last interaction time for LRU eviction
        profile["last_active"] = time.time()

        # Guild activation tracking
        guilds = profile.setdefault("favorite_guilds", {})
        guilds[guild] = guilds.get(guild, 0) + 1

        # Sentiment history
        sentiments = profile.setdefault("sentiment_history", [])
        sentiments.append(sentiment)
        if len(sentiments) > 20:
            profile["sentiment_history"] = sentiments[-20:]

        if repair_applied:
            profile["repair_count"] = profile.get("repair_count", 0) + 1

        # Conversation history update
        hist = profile.setdefault("history", [])
        hist.append({"role": "user", "content": query})
        hist.append({"role": "assistant", "content": response})
        if len(hist) > 20:
            profile["history"] = hist[-20:]

        self._save_profiles()


class DynamicPromptBuilder:
    """Constructs dynamic system prompts based on guild, sentiment, profile, and history."""

    def build_system_prompt(
        self,
        guild_prompt: str,
        sentiment: str,
        user_profile: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        guild_name: str = "",
    ) -> str:
        prompt_parts = [guild_prompt.strip()]

        if guild_name == "conversational":
            prompt_parts.append(
                "Note: The user is engaging in conversational interaction. Respond concisely in 1 to 3 friendly sentences. Do not wrap text in code blocks."
            )

        # Tone / sentiment instruction tuning
        if sentiment == "negative":
            prompt_parts.append(
                "Note: The user is experiencing difficulty. Provide clear, direct, and empathetic solutions without unnecessary fluff."
            )
        elif sentiment == "confused":
            prompt_parts.append(
                "Note: The user is confused. Include explicit comments and step-by-step explanations alongside code."
            )

        # Conversation history context summary if available
        if conversation_history:
            turns_summary = f"Active conversation context length: {len(conversation_history) // 2} previous turn(s)."
            prompt_parts.append(turns_summary)

        return "\n\n".join(prompt_parts)



class AmbiguityDetector:
    """Detects vague or ambiguous queries that require clarification."""

    def __init__(self, questions_path: str):
        self.questions_path = Path(questions_path)
        self.patterns: List[Dict[str, Any]] = []
        self._load_patterns()

    def _load_patterns(self) -> None:
        if self.questions_path.exists():
            try:
                with open(self.questions_path, "r") as f:
                    data = yaml.safe_load(f)
                    self.patterns = data.get("patterns", []) if data else []
            except Exception as e:
                logger.error(f"Failed to load clarifying questions: {e}")
                self.patterns = []

    def check(
        self, query: str, conversation_history: List[Dict[str, str]]
    ) -> Tuple[bool, Optional[str]]:
        # Do not block follow-up queries in an active conversation session
        if conversation_history and len(conversation_history) > 0:
            return False, None

        q_clean = query.strip().lower()

        # Direct exact match or regex check against ambiguous patterns
        for item in self.patterns:
            keywords = item.get("keywords", [])
            for kw in keywords:
                if q_clean == kw or q_clean.startswith(kw + " "):
                    return True, item.get("question", "Could you provide more context or specifications?")

        # Extremely short ambiguous query check
        if len(q_clean.split()) <= 2 and q_clean in {"fix", "help", "code", "run", "build"}:
            return True, "Could you specify what component or task you would like to work on?"

        return False, None


class EmpatheticResponder:
    """Wraps generated responses with empathetic messaging."""

    def __init__(self, templates_path: str):
        self.templates_path = Path(templates_path)
        self.templates: Dict[str, Any] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        if self.templates_path.exists():
            try:
                with open(self.templates_path, "r") as f:
                    data = yaml.safe_load(f)
                    self.templates = data.get("templates", {}) if data else {}
            except Exception as e:
                logger.error(f"Failed to load empathy templates: {e}")

    def wrap_response(
        self, code: str, sentiment: str, repair_applied: bool = False
    ) -> Tuple[str, str]:
        preamble = ""
        postamble = ""

        cat = sentiment if sentiment in self.templates else "neutral"

        if cat in self.templates:
            preambles = self.templates[cat].get("preambles", [])
            postambles = self.templates[cat].get("postambles", [])
            if preambles:
                preamble = random.choice(preambles)
            if postambles:
                postamble = random.choice(postambles)

        if repair_applied and "repair_notice" in self.templates:
            repair_preambles = self.templates["repair_notice"].get("preambles", [])
            if repair_preambles:
                preamble = random.choice(repair_preambles) + "\n\n" + preamble

        personalized_message = preamble.strip()
        final_output = code

        if preamble:
            final_output = f"{preamble}\n\n{code}"
        if postamble:
            final_output = f"{final_output}\n\n{postamble}"

        return final_output, personalized_message
