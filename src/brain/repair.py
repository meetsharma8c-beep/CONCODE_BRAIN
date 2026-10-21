"""
CONCODE Neural Brain — Code Repair
CodeT5-small (or CodeT5-base) fine-tuned for syntax error repair.
Falls back to regex-based repair if model is not available.
"""

import logging
import re
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("concode.repair")


class CodeRepairer:
    """
    Repairs broken code (missing brackets, typos, syntax errors)
    using a fine-tuned CodeT5 seq2seq model.
    """

    def __init__(self, model_dir: str, max_input_length: int = 512, max_output_length: int = 512):
        self.model_dir = Path(model_dir)
        self.max_input_length = max_input_length
        self.max_output_length = max_output_length
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load fine-tuned CodeT5 model if available."""
        config_path = self.model_dir / "config.json"
        if not config_path.exists():
            logger.warning(
                f"Code repair model not found at {self.model_dir}. "
                "Using regex-based fallback. Train the model first."
            )
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            import torch

            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_dir), local_files_only=True
            )
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                str(self.model_dir), local_files_only=True
            )
            self.model.eval()
            logger.info(f"Code repair model loaded from {self.model_dir}")
        except Exception as e:
            logger.error(f"Failed to load code repair model: {e}")
            self.model = None
            self.tokenizer = None

    def repair(self, code: str) -> Tuple[str, bool]:
        """
        Attempt to repair broken code.

        Args:
            code: Potentially broken code string

        Returns:
            (repaired_code, was_repaired) — the fixed code and whether changes were made
        """
        # Neural repair
        if self.model is not None and self.tokenizer is not None:
            return self._repair_neural(code)

        # Regex fallback
        return self._repair_regex(code)

    def _repair_neural(self, code: str) -> Tuple[str, bool]:
        """Repair using the fine-tuned CodeT5 model."""
        try:
            import torch

            input_text = f"fix: {code}"
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=self.max_input_length,
                truncation=True,
                padding=True,
            )

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.max_output_length,
                    num_beams=4,
                    early_stopping=True,
                )

            repaired = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Only return repaired if it's substantially different
            was_repaired = repaired.strip() != code.strip()
            return repaired if was_repaired else code, was_repaired
        except Exception as e:
            logger.error(f"Neural repair failed: {e}, falling back to regex")
            return self._repair_regex(code)

    def _repair_regex(self, code: str) -> Tuple[str, bool]:
        """
        Rule-based fallback repair for common syntax errors.
        Handles typos, missing brackets, and common JS/Python mistakes.
        """
        original = code
        fixed = code

        # ── Common Typo Fixes ──
        typo_map = {
            "functoin": "function",
            "fucntion": "function",
            "funciton": "function",
            "funtion": "function",
            "retun": "return",
            "retrun": "return",
            "reutrn": "return",
            "cosnt": "const",
            "conts": "const",
            "lat ": "let ",
            "vra ": "var ",
            "ipmort": "import",
            "exoprt": "export",
            "exprot": "export",
            "asyc ": "async ",
            "awiat ": "await ",
            "consol.log": "console.log",
            "consoel.log": "console.log",
            "docuemnt": "document",
            "widnow": "window",
            "elemnent": "element",
            "lenght": "length",
            "udnefined": "undefined",
        }
        for typo, fix in typo_map.items():
            fixed = fixed.replace(typo, fix)

        # ── Bracket Balancing ──
        fixed = self._balance_brackets(fixed)

        was_repaired = fixed != original
        return fixed, was_repaired

    def _balance_brackets(self, code: str) -> str:
        """Attempt to balance unmatched brackets."""
        pairs = {"(": ")", "[": "]", "{": "}"}
        closers = {v: k for k, v in pairs.items()}

        stack = []
        for char in code:
            if char in pairs:
                stack.append(char)
            elif char in closers:
                if stack and stack[-1] == closers[char]:
                    stack.pop()
                # else: extra closer — hard to fix without AST

        # Append missing closers
        while stack:
            opener = stack.pop()
            code += pairs[opener]

        return code

    @property
    def is_neural(self) -> bool:
        """Whether the neural model is loaded."""
        return self.model is not None
