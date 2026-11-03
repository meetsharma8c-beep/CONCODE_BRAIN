"""
CONCODE Neural Brain -- Hybrid Neural Compute Router

Dynamically estimates problem complexity and routes generation across three
compute tiers:
  - TIER_1_REFLEX: Fast local reflex generation for single-step queries
  - TIER_2_DEEP_LOCAL: Deep multi-step local Metal reasoning
  - TIER_3_FRONTIER: High-complexity or remote GPU escalation
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("concode.router")

TIER_1_REFLEX = "TIER_1_REFLEX"
TIER_2_DEEP_LOCAL = "TIER_2_DEEP_LOCAL"
TIER_3_FRONTIER = "TIER_3_FRONTIER"


@dataclass
class RoutingDecision:
    """Computed complexity score and selected neural compute tier."""

    tier: str
    complexity_score: float
    backend_used: str
    escalated: bool = False
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HybridComputeRouter:
    """
    Complexity-aware compute router that selects between local GGUF generation
    and optional remote/frontier generators with automatic escalation on failure.
    """

    def __init__(self, primary_generator: Any, secondary_generator: Any = None):
        self.primary_generator = primary_generator
        self.secondary_generator = secondary_generator

    @property
    def is_loaded(self) -> bool:
        p_ok = self.primary_generator is not None and getattr(self.primary_generator, "is_loaded", True)
        s_ok = self.secondary_generator is not None and getattr(self.secondary_generator, "is_loaded", False)
        return bool(p_ok or s_ok)

    def estimate_complexity(
        self,
        goal: str,
        workspace_files: Optional[Dict[str, str]] = None,
        active_guilds: Optional[Sequence[str]] = None,
    ) -> RoutingDecision:
        """Score task complexity on [0.0, 1.0] and select the optimal compute tier."""
        workspace_files = workspace_files or {}
        active_guilds = active_guilds or []

        words = len(goal.split())
        total_chars = sum(len(c) for c in workspace_files.values())
        file_count = len(workspace_files)
        guild_count = len(active_guilds)

        score = 0.15
        score += min(words / 150.0, 0.30)
        score += min(file_count / 10.0, 0.25)
        score += min(total_chars / 25_000.0, 0.20)
        if guild_count >= 2:
            score += 0.15
        if any(g in active_guilds for g in ("system_architect", "research_scientist", "critic_verifier")):
            score += 0.10

        score = round(min(score, 1.0), 3)

        secondary_ready = (
            self.secondary_generator is not None
            and getattr(self.secondary_generator, "is_loaded", False)
        )

        if score >= 0.75:
            tier = TIER_3_FRONTIER if secondary_ready else TIER_2_DEEP_LOCAL
            backend = "secondary_frontier" if secondary_ready else "primary_local"
            reason = "High multi-file or multi-guild complexity."
        elif score >= 0.40:
            tier = TIER_2_DEEP_LOCAL
            backend = "primary_local"
            reason = "Moderate multi-step engineering complexity."
        else:
            tier = TIER_1_REFLEX
            backend = "primary_local"
            reason = "Focused single-domain task."

        return RoutingDecision(
            tier=tier,
            complexity_score=score,
            backend_used=backend,
            escalated=False,
            reason=reason,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        force_escalate: bool = False,
    ) -> str:
        """
        Compatible generator interface that routes to the active backend and
        automatically escalates to secondary_generator if primary fails.
        """
        secondary_ready = (
            self.secondary_generator is not None
            and getattr(self.secondary_generator, "is_loaded", False)
        )
        primary_ready = (
            self.primary_generator is not None
            and getattr(self.primary_generator, "is_loaded", True)
        )

        if force_escalate and secondary_ready:
            return self.secondary_generator.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context=context,
                history=history,
            )

        if primary_ready:
            try:
                return self.primary_generator.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    context=context,
                    history=history,
                )
            except Exception as primary_err:
                if secondary_ready:
                    logger.warning(
                        f"Primary generator failed ({primary_err}); escalating to secondary generator."
                    )
                    return self.secondary_generator.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        context=context,
                        history=history,
                    )
                raise

        if secondary_ready:
            return self.secondary_generator.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context=context,
                history=history,
            )

        raise RuntimeError("No loaded inference generator is available in HybridComputeRouter.")
