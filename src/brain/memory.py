"""
CONCODE Neural Brain -- Persistent Episodic & Graph Memory Manager

Eliminates cross-session amnesia via:
  1. Persistent Episodic Experience Store (JSONL trajectory memory + similarity recall)
  2. Content-Addressable Incremental Workspace Indexing Cache (SHA-256)
  3. Live Obsidian Vault Episodic Log Synchronization
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("concode.memory")


@dataclass
class EpisodicRecord:
    """A verified problem-solving episode stored in long-term memory."""

    id: str
    timestamp: float
    goal: str
    guilds: List[str]
    plan_steps: List[str]
    solution_summary: str
    files_touched: List[str] = field(default_factory=list)
    critic_score: float = 1.0
    verified: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CognitiveMemoryManager:
    """
    Manages long-term episodic experience replay, incremental workspace
    digest caching, and Obsidian vault knowledge synchronization.
    """

    def __init__(
        self,
        episodic_path: Path | str,
        vault_dir: Optional[Path | str] = None,
        max_episodes: int = 2_000,
    ):
        self.episodic_path = Path(episodic_path)
        self.vault_dir = (
            Path(vault_dir)
            if vault_dir
            else Path(__file__).resolve().parent.parent.parent / "concode-neural-brain"
        )
        self.max_episodes = max_episodes
        self.episodes: List[EpisodicRecord] = []
        self._last_workspace_digest: Optional[str] = None
        self._load_episodes()

    def _load_episodes(self) -> None:
        if not self.episodic_path.exists():
            return
        loaded: List[EpisodicRecord] = []
        try:
            with open(self.episodic_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        loaded.append(
                            EpisodicRecord(
                                id=str(data.get("id") or uuid.uuid4()),
                                timestamp=float(data.get("timestamp") or time.time()),
                                goal=str(data.get("goal") or ""),
                                guilds=list(data.get("guilds") or []),
                                plan_steps=list(data.get("plan_steps") or []),
                                solution_summary=str(data.get("solution_summary") or ""),
                                files_touched=list(data.get("files_touched") or []),
                                critic_score=float(data.get("critic_score", 1.0)),
                                verified=bool(data.get("verified", True)),
                            )
                        )
                    except Exception:
                        continue
            self.episodes = loaded[-self.max_episodes :]
            logger.info(f"Loaded {len(self.episodes)} episodic memory records")
        except Exception as exc:
            logger.warning(f"Failed to load episodic memory: {exc}")

    def record_episode(
        self,
        goal: str,
        guilds: Sequence[str],
        plan_steps: Sequence[str],
        solution_summary: str,
        files_touched: Optional[Sequence[str]] = None,
        critic_score: float = 1.0,
        verified: bool = True,
        sync_vault: bool = False,
    ) -> EpisodicRecord:
        """Persist a completed problem-solving episode to disk and memory."""
        record = EpisodicRecord(
            id=str(uuid.uuid4())[:12],
            timestamp=round(time.time(), 3),
            goal=goal.strip()[:1000],
            guilds=list(guilds),
            plan_steps=list(plan_steps)[:10],
            solution_summary=solution_summary.strip()[:1000],
            files_touched=list(files_touched or [])[:25],
            critic_score=round(float(critic_score), 3),
            verified=bool(verified),
        )
        self.episodes.append(record)
        if len(self.episodes) > self.max_episodes:
            self.episodes = self.episodes[-self.max_episodes :]

        try:
            self.episodic_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.episodic_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning(f"Could not write episodic record: {exc}")

        if sync_vault and verified:
            self.sync_episode_to_vault(record)

        return record

    def recall_similar(
        self, query: str, top_k: int = 3, min_similarity: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant verified episodes for Few-Shot Experience Replay.
        """
        query_tokens = self._tokenize(query)
        if not query_tokens or not self.episodes:
            return []

        scored = []
        for ep in self.episodes:
            if not ep.verified:
                continue
            ep_tokens = self._tokenize(f"{ep.goal} {' '.join(ep.guilds)} {ep.solution_summary}")
            if not ep_tokens:
                continue
            intersection = len(query_tokens & ep_tokens)
            union = len(query_tokens | ep_tokens)
            jaccard = intersection / union if union else 0.0
            score = round(jaccard * (0.7 + 0.3 * ep.critic_score), 4)
            if score >= min_similarity:
                scored.append((score, ep))

        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        for score, ep in scored[: max(1, min(top_k, 10))]:
            item = ep.to_dict()
            item["similarity"] = score
            results.append(item)
        return results

    def format_episodic_context(self, query: str, top_k: int = 2) -> str:
        """Format recalled episodes as concise few-shot guidance for prompt injection."""
        recalled = self.recall_similar(query, top_k=top_k)
        if not recalled:
            return ""
        lines = []
        for item in recalled:
            steps = " -> ".join(item.get("plan_steps", [])[:4])
            lines.append(
                f"- Past Goal ({', '.join(item.get('guilds', []))}, sim={item['similarity']}): "
                f"{item['goal'][:120]} | Plan: {steps} | Outcome: {item['solution_summary'][:140]}"
            )
        return "\n".join(lines)

    def index_workspace_incremental(
        self, retriever: Any, workspace_files: Dict[str, str]
    ) -> bool:
        """
        Index workspace files into the retriever only if the SHA-256 content digest
        has changed since the last indexing operation.

        Returns True if re-indexing was performed, False if cache hit.
        """
        if retriever is None or not getattr(retriever, "is_ready", False) or not workspace_files:
            return False

        hasher = hashlib.sha256()
        for path in sorted(workspace_files.keys()):
            hasher.update(path.encode("utf-8", errors="ignore"))
            hasher.update(b"\x00")
            hasher.update(workspace_files[path].encode("utf-8", errors="ignore"))
            hasher.update(b"\x00")
        digest = hasher.hexdigest()

        if digest == self._last_workspace_digest and getattr(retriever, "chunks", None):
            return False

        retriever.index_workspace(workspace_files)
        self._last_workspace_digest = digest
        return True

    def sync_episode_to_vault(self, record: EpisodicRecord) -> Optional[Path]:
        """Append verified episode summary to the Obsidian vault session logs."""
        if not self.vault_dir.exists():
            return None
        log_dir = self.vault_dir / "05-Session-Logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "Episodic-Memory-Log.md"

        try:
            if not log_file.exists():
                header = (
                    "---\n"
                    "title: Episodic Memory Log\n"
                    "type: session-log\n"
                    "tags:\n"
                    "  - system/memory\n"
                    "  - log/episodic\n"
                    "---\n\n"
                    "# Episodic Memory Log\n\n"
                    "> Automated log of verified problem-solving trajectories recorded by `CognitiveMemoryManager`.\n\n"
                    "- Related Architecture: [[01-Brain-Architecture/10-Universal-Evolution-Plan|10-Universal-Evolution-Plan]]\n"
                    "- Master Dashboard: [[00-Dashboard/Dashboard|Dashboard]]\n\n"
                    "---\n\n"
                )
                log_file.write_text(header, encoding="utf-8")

            entry = (
                f"## Episode `{record.id}`\n"
                f"- **Guilds**: {', '.join(f'`{g}`' for g in record.guilds)}\n"
                f"- **Critic Score**: `{record.critic_score}`\n"
                f"- **Goal**: {record.goal[:200]}\n"
                f"- **Summary**: {record.solution_summary[:240]}\n\n"
            )
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(entry)
            return log_file
        except Exception as exc:
            logger.debug(f"Vault episodic log sync skipped: {exc}")
            return None

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        stop = {
            "the", "and", "for", "with", "that", "this", "from", "into",
            "are", "was", "were", "have", "has", "had", "not", "but", "can",
            "will", "just", "should", "now", "how", "what", "when", "where",
        }
        tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]{2,}", text.lower()))
        return tokens - stop

    @property
    def episode_count(self) -> int:
        return len(self.episodes)
