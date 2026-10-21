"""
CONCODE Neural Brain -- Intent Classifier
DistilBERT fine-tuned on 13 guild classes.
Falls back to keyword matching if model is not available,
or for guilds not present in the neural model's label space.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional, Set

import yaml

logger = logging.getLogger("concode.intent")


class IntentClassifier:
    """Classifies user prompts into one of 13 expert guilds."""

    def __init__(self, model_dir: str, guilds_yaml: str, fallback_guild: str = "fullstack"):
        self.model_dir = Path(model_dir)
        self.fallback_guild = fallback_guild
        self.model = None
        self.tokenizer = None
        self.label_map = {}
        self.id_to_label = {}
        self.guilds = {}
        self._neural_guild_names: Set[str] = set()
        self._load_guilds(guilds_yaml)
        self._load_model()

    def _load_guilds(self, guilds_yaml: str):
        """Load guild definitions with keywords for fallback."""
        path = Path(guilds_yaml)
        if path.exists():
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                guild_list = data.get("guilds", []) if data else []
                self.guilds = {g["name"]: g for g in guild_list}
            logger.info(f"Loaded {len(self.guilds)} guild definitions")
        else:
            logger.warning(f"Guilds YAML not found at {path}")

    def _load_model(self):
        """Load fine-tuned DistilBERT model if available."""
        config_path = self.model_dir / "config.json"
        if not config_path.exists():
            logger.warning(
                f"Intent classifier model not found at {self.model_dir}. "
                "Using keyword-based fallback. Train the model first."
            )
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_dir), local_files_only=True
            )
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_dir), local_files_only=True
            )
            self.model.eval()

            # Build label map from model config
            if hasattr(self.model.config, "id2label"):
                self.id_to_label = {int(k): v for k, v in self.model.config.id2label.items()}
                self.label_map = {v: int(k) for k, v in self.id_to_label.items()}
                self._neural_guild_names = set(self.id_to_label.values())

            # Log guilds that exist in YAML but not in the neural model
            keyword_only = set(self.guilds.keys()) - self._neural_guild_names
            if keyword_only:
                logger.info(
                    f"Guilds routed via keyword-only (not in neural model): "
                    f"{', '.join(sorted(keyword_only))}"
                )

            logger.info(
                f"Intent classifier loaded: {len(self.id_to_label)} neural classes "
                f"from {self.model_dir}"
            )
        except Exception as e:
            logger.error(f"Failed to load intent classifier: {e}")
            self.model = None
            self.tokenizer = None

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Classify text into one of all 13 expert guilds.

        Returns:
            (guild_name, confidence) -- e.g. ("debugger", 0.95)
        """
        # Keyword check first for high-confidence domain keyword matches.
        # For guilds NOT in the neural model's label space (e.g. mobile,
        # blockchain), keyword matching is the only path, so a lower
        # threshold is used to ensure they get routed correctly.
        keyword_guild, keyword_score = self._predict_keyword(text)

        # If keyword match hits a guild the neural model does not know,
        # always prefer the keyword result to avoid misclassification.
        keyword_only_guild = keyword_guild not in self._neural_guild_names

        if keyword_score >= 0.70:
            return keyword_guild, keyword_score

        if keyword_only_guild and keyword_score >= 0.50:
            return keyword_guild, keyword_score

        # Neural prediction
        if self.model is not None and self.tokenizer is not None:
            neural_guild, neural_conf = self._predict_neural(text)
            if neural_conf >= 0.60:
                return neural_guild, neural_conf

        # Fallback
        return keyword_guild if keyword_score > 0.3 else self.fallback_guild, max(keyword_score, 0.5)

    def _predict_neural(self, text: str) -> Tuple[str, float]:
        """Predict using the fine-tuned DistilBERT model."""
        try:
            import torch

            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True,
            )
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)
                confidence, pred_id = torch.max(probs, dim=-1)

            guild_name = self.id_to_label.get(pred_id.item(), self.fallback_guild)
            return guild_name, round(confidence.item(), 4)
        except Exception as e:
            logger.error(f"Neural prediction failed: {e}, falling back to keywords")
            return self._predict_keyword(text)

    def _predict_keyword(self, text: str) -> Tuple[str, float]:
        """Keyword-based fallback classification."""
        import re
        text_lower = text.lower()
        best_guild = self.fallback_guild
        best_score = 0

        for guild_name, guild_info in self.guilds.items():
            keywords = guild_info.get("keywords", [])
            matches = 0
            for kw in keywords:
                kw_clean = kw.lower()
                pattern = rf"\b{re.escape(kw_clean)}\b"
                if re.search(pattern, text_lower):
                    matches += 1
            if matches > best_score:
                best_score = matches
                best_guild = guild_name

        # Confidence based on keyword match density
        confidence = min(0.5 + (best_score * 0.1), 0.85) if best_score > 0 else 0.3
        return best_guild, round(confidence, 4)


    @property
    def is_neural(self) -> bool:
        """Whether the neural model is loaded."""
        return self.model is not None
