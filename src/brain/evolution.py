"""
CONCODE Neural Brain -- Continual Learning & Trajectory Harvester

Captures verified problem-solving trajectories and self-healed code repair pairs
into structured JSONL datasets for continual QLoRA and Direct Preference
Optimization (DPO) fine-tuning.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("concode.evolution")


class EvolutionHarvester:
    """
    Harvests verified multi-guild solutions and repair pairs from runtime
    execution into JSONL training datasets.
    """

    def __init__(
        self,
        trajectories_path: Path | str,
        dpo_path: Path | str,
    ):
        self.trajectories_path = Path(trajectories_path)
        self.dpo_path = Path(dpo_path)
        self.trajectory_count = self._count_lines(self.trajectories_path)
        self.dpo_count = self._count_lines(self.dpo_path)

    @staticmethod
    def _count_lines(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return sum(1 for line in handle if line.strip())
        except Exception:
            return 0

    def harvest_trajectory(
        self,
        prompt: str,
        response: str,
        guilds: Sequence[str],
        critic_score: float = 1.0,
        plan_steps: Optional[Sequence[str]] = None,
    ) -> bool:
        """
        Save a high-confidence verified trajectory (`critic_score >= 0.80`)
        for future QLoRA instruction fine-tuning.
        """
        if critic_score < 0.80 or not prompt.strip() or not response.strip():
            return False

        record = {
            "timestamp": round(time.time(), 3),
            "guild": guilds[0] if guilds else "fullstack",
            "active_guilds": list(guilds),
            "instruction": prompt.strip(),
            "plan": list(plan_steps or []),
            "output": response.strip(),
            "critic_score": round(float(critic_score), 3),
        }
        try:
            self.trajectories_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trajectories_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.trajectory_count += 1
            return True
        except Exception as exc:
            logger.warning(f"Failed to harvest trajectory: {exc}")
            return False

    def harvest_dpo_pair(
        self,
        prompt: str,
        chosen_response: str,
        rejected_response: str,
        guild: str = "fullstack",
        reason: str = "syntax_or_critic_repair",
    ) -> bool:
        """
        Save a (prompt, chosen, rejected) preference tuple when self-repair or
        multi-iteration retry corrected an initially flawed output.
        """
        if (
            not prompt.strip()
            or not chosen_response.strip()
            or not rejected_response.strip()
            or chosen_response.strip() == rejected_response.strip()
        ):
            return False

        record = {
            "timestamp": round(time.time(), 3),
            "guild": guild,
            "prompt": prompt.strip(),
            "chosen": chosen_response.strip(),
            "rejected": rejected_response.strip(),
            "reason": reason,
        }
        try:
            self.dpo_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.dpo_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.dpo_count += 1
            return True
        except Exception as exc:
            logger.warning(f"Failed to harvest DPO preference pair: {exc}")
            return False

    def stats(self) -> Dict[str, Any]:
        return {
            "harvested_trajectories": self.trajectory_count,
            "harvested_dpo_pairs": self.dpo_count,
            "trajectories_path": str(self.trajectories_path.name),
            "dpo_path": str(self.dpo_path.name),
        }
