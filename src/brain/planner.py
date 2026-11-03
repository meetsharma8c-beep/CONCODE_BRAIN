"""
CONCODE Neural Brain -- Executive Meta-Planner (System-2 DAG Decomposition)

Decomposes arbitrary goals into a Directed Acyclic Graph (DAG) of verifiable
sub-tasks assigned to specialized expert guilds, tracks execution state, and
supports backtracking when verification fails.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("concode.planner")

TASK_STATES = ("PENDING", "EXECUTING", "VERIFYING", "BACKTRACKING", "COMPLETED", "FAILED")


@dataclass
class PlanTask:
    """A single verifiable node in the Executive Execution Plan DAG."""

    id: str
    title: str
    description: str
    guild: str
    dependencies: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    status: str = "PENDING"
    attempts: int = 0
    result_summary: str = ""
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Directed Acyclic Graph (DAG) representing a decomposed universal goal."""

    goal: str
    tasks: List[PlanTask] = field(default_factory=list)
    complexity_tier: int = 1
    active_guilds: List[str] = field(default_factory=list)
    state: str = "PENDING"

    def validate_dag(self) -> Tuple[bool, Optional[str]]:
        """Verify that task IDs are unique, dependencies exist, and no cycles exist."""
        task_map: Dict[str, PlanTask] = {}
        for task in self.tasks:
            if not task.id:
                return False, "Task ID must not be empty."
            if task.id in task_map:
                return False, f"Duplicate task ID: {task.id}"
            task_map[task.id] = task

        for task in self.tasks:
            for dep in task.dependencies:
                if dep not in task_map:
                    return False, f"Task '{task.id}' depends on unknown task '{dep}'."
                if dep == task.id:
                    return False, f"Task '{task.id}' cannot depend on itself."

        # Kahn's topological sort to detect cycles
        in_degree: Dict[str, int] = {t.id: len(t.dependencies) for t in self.tasks}
        dependents: Dict[str, List[str]] = {t.id: [] for t in self.tasks}
        for task in self.tasks:
            for dep in task.dependencies:
                dependents[dep].append(task.id)

        queue = [tid for tid, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            current = queue.pop(0)
            visited += 1
            for nxt in dependents[current]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        if visited != len(self.tasks):
            return False, "Cycle detected in task dependency graph."
        return True, None

    def ready_tasks(self) -> List[PlanTask]:
        """Return tasks in PENDING or BACKTRACKING state whose dependencies are COMPLETED."""
        completed_ids = {t.id for t in self.tasks if t.status == "COMPLETED"}
        ready = []
        for task in self.tasks:
            if task.status in ("PENDING", "BACKTRACKING"):
                if all(dep in completed_ids for dep in task.dependencies):
                    ready.append(task)
        return ready

    def mark_executing(self, task_id: str) -> None:
        task = self._get(task_id)
        task.status = "EXECUTING"
        task.attempts += 1
        self.state = "EXECUTING"

    def mark_completed(self, task_id: str, summary: str = "") -> None:
        task = self._get(task_id)
        task.status = "COMPLETED"
        task.result_summary = summary
        task.error = None
        if all(t.status == "COMPLETED" for t in self.tasks):
            self.state = "COMPLETED"

    def mark_failed(self, task_id: str, error: str, max_attempts: int = 3) -> bool:
        """
        Record a failure on task_id.

        Returns True if the task can backtrack and retry, False if exhausted.
        """
        task = self._get(task_id)
        task.error = error
        if task.attempts < max_attempts:
            task.status = "BACKTRACKING"
            self.state = "BACKTRACKING"
            return True
        task.status = "FAILED"
        self.state = "FAILED"
        return False

    def _get(self, task_id: str) -> PlanTask:
        for task in self.tasks:
            if task.id == task_id:
                return task
        raise KeyError(f"Unknown task_id: {task_id}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "complexity_tier": self.complexity_tier,
            "active_guilds": list(self.active_guilds),
            "state": self.state,
            "tasks": [asdict(t) for t in self.tasks],
        }


class ExecutivePlanner:
    """
    System-2 Meta-Planner that decomposes arbitrary objectives into a multi-guild
    DAG of verifiable tasks.
    """

    def __init__(self, intent_classifier: Any = None, generator: Any = None):
        self.intent_classifier = intent_classifier
        self.generator = generator

    def decompose(
        self,
        goal: str,
        workspace_files: Optional[Dict[str, str]] = None,
        use_llm: bool = False,
    ) -> ExecutionPlan:
        """
        Decompose a high-level goal into a validated ExecutionPlan DAG.

        Uses multi-guild intent analysis and clause decomposition by default,
        and optionally queries the LLM when use_llm=True.
        """
        workspace_files = workspace_files or {}
        guilds_with_scores = self._detect_guilds(goal)
        active_guilds = [g for g, _ in guilds_with_scores]
        complexity_tier = self._estimate_tier(goal, workspace_files, active_guilds)

        if use_llm and self.generator is not None and getattr(self.generator, "is_loaded", False):
            llm_plan = self._decompose_via_llm(goal, workspace_files, active_guilds, complexity_tier)
            if llm_plan is not None:
                return llm_plan

        return self._decompose_deterministic(goal, workspace_files, active_guilds, complexity_tier)

    def _detect_guilds(self, goal: str) -> List[Tuple[str, float]]:
        if self.intent_classifier is not None:
            if hasattr(self.intent_classifier, "predict_multi"):
                return self.intent_classifier.predict_multi(goal, top_k=4)
            guild, conf = self.intent_classifier.predict(goal)
            return [(guild, conf)]
        return [("fullstack", 0.5)]

    @staticmethod
    def _estimate_tier(
        goal: str, workspace_files: Dict[str, str], active_guilds: Sequence[str]
    ) -> int:
        word_count = len(goal.split())
        file_count = len(workspace_files)
        if word_count > 60 or file_count > 8 or len(active_guilds) >= 3:
            return 3
        if word_count > 20 or file_count > 2 or len(active_guilds) == 2:
            return 2
        return 1

    def _decompose_deterministic(
        self,
        goal: str,
        workspace_files: Dict[str, str],
        active_guilds: List[str],
        complexity_tier: int,
    ) -> ExecutionPlan:
        primary_guild = active_guilds[0] if active_guilds else "fullstack"
        clauses = self._split_clauses(goal)
        tasks: List[PlanTask] = []

        # Step 1: Context & Architecture analysis
        tasks.append(
            PlanTask(
                id="task_1_analyze",
                title="Analyze goal constraints and workspace context",
                description=(
                    f"Inspect the workspace ({len(workspace_files)} files) and establish "
                    f"invariants for goal: {goal[:160]}"
                ),
                guild="system_architect" if complexity_tier >= 3 else primary_guild,
                dependencies=[],
                acceptance_criteria=[
                    "Target files and interfaces identified",
                    "Input constraints validated",
                ],
            )
        )

        # Step 2..N: Domain implementation sub-tasks
        prev_ids = ["task_1_analyze"]
        if len(clauses) > 1:
            for idx, clause in enumerate(clauses[:4], start=2):
                clause_guild = primary_guild
                if self.intent_classifier is not None:
                    clause_guild, _ = self.intent_classifier.predict(clause)
                tid = f"task_{idx}_implement"
                tasks.append(
                    PlanTask(
                        id=tid,
                        title=f"Execute sub-goal: {clause[:70]}",
                        description=clause,
                        guild=clause_guild,
                        dependencies=list(prev_ids),
                        acceptance_criteria=[
                            "Complete implementation generated without placeholders",
                            "Syntax and structural checks pass",
                        ],
                    )
                )
                prev_ids = [tid]
        else:
            tid = "task_2_implement"
            tasks.append(
                PlanTask(
                    id=tid,
                    title="Synthesize primary domain solution",
                    description=goal,
                    guild=primary_guild,
                    dependencies=["task_1_analyze"],
                    acceptance_criteria=[
                        "Target solution produced",
                        "All edited files pass deterministic syntax verification",
                    ],
                )
            )
            prev_ids = [tid]

        # Final Step: Critic & QA Verification Gate
        verify_id = f"task_{len(tasks) + 1}_verify"
        tasks.append(
            PlanTask(
                id=verify_id,
                title="Verify syntax, runtime invariants, and critic audit",
                description="Run static parsers, sandbox checks, and security/QA critic review.",
                guild="critic_verifier" if "critic_verifier" in active_guilds else "qa",
                dependencies=list(prev_ids),
                acceptance_criteria=[
                    "Zero syntax or delimiter errors",
                    "Critic verification gate passes",
                ],
            )
        )

        plan = ExecutionPlan(
            goal=goal,
            tasks=tasks,
            complexity_tier=complexity_tier,
            active_guilds=active_guilds,
            state="PENDING",
        )
        valid, err = plan.validate_dag()
        if not valid:
            logger.warning(f"Generated DAG failed validation ({err}); falling back to single-task plan.")
            plan.tasks = [
                PlanTask(
                    id="task_1",
                    title="Execute goal",
                    description=goal,
                    guild=primary_guild,
                    dependencies=[],
                    acceptance_criteria=["Verified output"],
                )
            ]
        return plan

    def _decompose_via_llm(
        self,
        goal: str,
        workspace_files: Dict[str, str],
        active_guilds: List[str],
        complexity_tier: int,
    ) -> Optional[ExecutionPlan]:
        prompt = (
            "Decompose the following goal into a JSON Directed Acyclic Graph (DAG) of 2 to 5 tasks.\n"
            f"Goal: {goal}\n"
            f"Available Guilds: {', '.join(active_guilds or ['fullstack', 'qa', 'security'])}\n"
            f"Workspace Files: {', '.join(sorted(workspace_files.keys())[:20]) or 'None'}\n"
            "Return ONLY valid JSON with shape:\n"
            "{\"tasks\":[{\"id\":\"t1\",\"title\":\"...\",\"description\":\"...\",\"guild\":\"...\",\"dependencies\":[],\"acceptance_criteria\":[\"...\"]}]}"
        )
        try:
            raw = self.generator.generate(
                system_prompt="You are CONCODE Executive Meta-Planner. Output only valid JSON.",
                user_prompt=prompt,
                context="",
                history=None,
            )
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                return None
            parsed = json.loads(match.group(0))
            raw_tasks = parsed.get("tasks")
            if not isinstance(raw_tasks, list) or not raw_tasks:
                return None
            tasks: List[PlanTask] = []
            for idx, item in enumerate(raw_tasks[:6], start=1):
                if not isinstance(item, dict):
                    continue
                tasks.append(
                    PlanTask(
                        id=str(item.get("id") or f"task_{idx}"),
                        title=str(item.get("title") or f"Step {idx}"),
                        description=str(item.get("description") or goal),
                        guild=str(item.get("guild") or (active_guilds[0] if active_guilds else "fullstack")),
                        dependencies=[str(d) for d in item.get("dependencies", []) if isinstance(d, str)],
                        acceptance_criteria=[
                            str(c) for c in item.get("acceptance_criteria", ["Verified"]) if isinstance(c, str)
                        ],
                    )
                )
            if not tasks:
                return None
            plan = ExecutionPlan(
                goal=goal,
                tasks=tasks,
                complexity_tier=complexity_tier,
                active_guilds=active_guilds,
                state="PENDING",
            )
            valid, _ = plan.validate_dag()
            return plan if valid else None
        except Exception as e:
            logger.debug(f"LLM DAG decomposition fallback triggered: {e}")
            return None

    @staticmethod
    def _split_clauses(goal: str) -> List[str]:
        """Split compound goals into logical sub-clauses when numbered or joined by conjunctions."""
        numbered = re.findall(r"(?:^|\n)\s*(?:\d+[.)]|[-*])\s+([^\n]+)", goal)
        if len(numbered) >= 2:
            return [c.strip() for c in numbered if len(c.strip()) > 5]

        parts = re.split(r"\b(?:and then|after that|additionally|furthermore|finally)\b|;\s+", goal, flags=re.IGNORECASE)
        cleaned = [p.strip(" .,") for p in parts if len(p.strip()) >= 12]
        return cleaned if len(cleaned) >= 2 else [goal.strip()]
