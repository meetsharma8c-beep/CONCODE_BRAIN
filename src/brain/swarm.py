"""
CONCODE Neural Brain -- Multi-Guild Swarm Orchestrator & Adversarial Critic

Coordinates multiple specialized expert guilds simultaneously, synthesizes
composite system prompts, invokes the Universal Tool Bus, runs the CodingAgent,
and enforces an adversarial Critic audit (Security, Performance, QA, Critic).
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.brain.agent import AgentEdit, CodingAgent, VerificationResult
from src.brain.planner import ExecutionPlan, ExecutivePlanner
from src.brain.sandbox import SandboxResult, SandboxedExecutor
from src.brain.tools import ToolCallResult, UniversalToolBus

logger = logging.getLogger("concode.swarm")


@dataclass
class CriticReport:
    """Adversarial quality, security, and completeness audit report."""

    passed: bool
    score: float
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    auditor_guilds: List[str] = field(
        default_factory=lambda: ["critic_verifier", "security", "performance", "qa"]
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SwarmOutcome:
    """Complete result from a Multi-Guild Swarm execution cycle."""

    goal: str
    summary: str
    success: bool
    plan: Dict[str, Any]
    activated_guilds: List[Dict[str, Any]]
    edits: List[AgentEdit] = field(default_factory=list)
    verification: List[VerificationResult] = field(default_factory=list)
    critic_report: Optional[CriticReport] = None
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    sandbox_results: List[Dict[str, Any]] = field(default_factory=list)
    direct_answer: str = ""
    iterations: int = 0
    needs_user_input: bool = False
    question: Optional[str] = None
    error: Optional[str] = None


class CriticAuditor:
    """
    Deterministic + heuristic adversarial auditor representing the Security,
    Performance, QA, and Critic Verifier guilds.
    """

    _SECRET_RE = re.compile(
        r"(?:api[_-]?key|secret[_-]?key|password|private[_-]?key)\s*=\s*['\"][A-Za-z0-9_\-]{12,}['\"]",
        re.IGNORECASE,
    )
    _SQLI_RE = re.compile(
        r"(?:SELECT|INSERT|UPDATE|DELETE)\s+.*?(?:\+\s*[a-zA-Z_]|f['\"].*?\{)",
        re.IGNORECASE,
    )
    _BARE_EXCEPT_RE = re.compile(r"except\s*:\s*\n\s*pass\b")

    def audit(
        self,
        edits: Sequence[AgentEdit],
        verification: Sequence[VerificationResult],
        sandbox_results: Sequence[SandboxResult],
        direct_answer: str = "",
    ) -> CriticReport:
        issues: List[str] = []
        recommendations: List[str] = []
        penalty = 0.0

        # 1. Check static verification results
        for v in verification:
            if v.status == "failed":
                issues.append(f"[QA/Syntax] {v.path}: {v.detail}")
                penalty += 0.35

        # 2. Check sandbox runtime results
        for sb in sandbox_results:
            if not sb.passed:
                issues.append(f"[Runtime/Sandbox] {sb.target} exited with {sb.exit_code}: {sb.stderr[:160]}")
                penalty += 0.35

        # 3. Inspect edited file contents for security/quality anti-patterns
        for edit in edits:
            code = edit.content
            if self._SECRET_RE.search(code):
                issues.append(f"[Security] Potential hardcoded credential detected in {edit.path}.")
                recommendations.append(f"Load secrets from environment variables in {edit.path}.")
                penalty += 0.25
            if self._SQLI_RE.search(code):
                issues.append(f"[Security] Potential string-interpolated SQL query in {edit.path}.")
                recommendations.append(f"Use parameterized SQL queries in {edit.path}.")
                penalty += 0.25
            if self._BARE_EXCEPT_RE.search(code):
                recommendations.append(
                    f"[Reliability] Avoid silent 'except: pass' blocks in {edit.path}; log or handle specific exceptions."
                )
                penalty += 0.05

        if not edits and not direct_answer.strip():
            issues.append("[Completeness] Neither workspace edits nor a direct solution was produced.")
            penalty += 0.50

        score = round(max(0.0, 1.0 - penalty), 2)
        passed = len(issues) == 0 and score >= 0.70
        return CriticReport(
            passed=passed,
            score=score,
            issues=issues,
            recommendations=recommendations,
        )


class MultiGuildSwarm:
    """
    Orchestrates multi-guild collaboration across the Executive Planner,
    Universal Tool Bus, CodingAgent, SandboxedExecutor, and CriticAuditor.
    """

    def __init__(
        self,
        intent_classifier: Any,
        guilds_data: Dict[str, Any],
        generator: Any,
        coding_agent: Optional[CodingAgent] = None,
        planner: Optional[ExecutivePlanner] = None,
        tool_bus: Optional[UniversalToolBus] = None,
        sandbox_executor: Optional[SandboxedExecutor] = None,
        critic: Optional[CriticAuditor] = None,
    ):
        self.intent_classifier = intent_classifier
        self.guilds_data = guilds_data or {}
        self.generator = generator
        self.coding_agent = coding_agent or CodingAgent(generator)
        self.planner = planner or ExecutivePlanner(intent_classifier, generator)
        self.tool_bus = tool_bus or UniversalToolBus(sandbox_executor=sandbox_executor)
        self.sandbox_executor = sandbox_executor
        self.critic = critic or CriticAuditor()

    def synthesize_guild_prompt(self, guilds: Sequence[Tuple[str, float]]) -> str:
        """Combine system instructions from the lead guild and supporting specialist guilds."""
        if not guilds:
            return "You are CONCODE Universal Engine. Solve the problem rigorously from first principles."

        lead_name, lead_conf = guilds[0]
        lead_prompt = self.guilds_data.get(lead_name, {}).get(
            "system_prompt",
            "You are a principal engineering specialist.",
        ).strip()

        if len(guilds) == 1:
            return lead_prompt

        support_directives = []
        for g_name, g_conf in guilds[1:]:
            g_prompt = self.guilds_data.get(g_name, {}).get("system_prompt", "").strip()
            if g_prompt:
                first_sentence = g_prompt.split(".")[0].strip() + "."
                support_directives.append(f"- [{g_name.upper()} (conf={g_conf:.2f})]: {first_sentence}")

        joined = "\n".join(support_directives)
        return (
            f"{lead_prompt}\n\n"
            f"Multi-Guild Swarm Collaboration Active:\n{joined}\n"
            "Synthesize a unified solution satisfying all active guild constraints."
        )

    def execute(
        self,
        goal: str,
        workspace_files: Optional[Dict[str, str]] = None,
        max_iterations: int = 4,
        enable_sandbox: bool = False,
        episodic_context: str = "",
    ) -> SwarmOutcome:
        """
        Execute a full universal problem-solving cycle:
        1. Multi-guild intent routing
        2. Executive DAG decomposition
        3. Automatic tool bus enrichment (AST inspection, math eval, vault lookup)
        4. Multi-iteration agent execution or direct reasoning synthesis
        5. Optional sandboxed test execution
        6. Adversarial Critic verification gate
        """
        workspace = dict(workspace_files or {})
        max_iterations = max(1, min(max_iterations, 10))

        # 1. Multi-guild activation
        if self.intent_classifier is not None and hasattr(self.intent_classifier, "predict_multi"):
            activated = self.intent_classifier.predict_multi(goal, top_k=3)
        elif self.intent_classifier is not None:
            g, c = self.intent_classifier.predict(goal)
            activated = [(g, c)]
        else:
            activated = [("fullstack", 0.5)]

        activated_dicts = [{"guild": g, "confidence": c} for g, c in activated]
        composite_prompt = self.synthesize_guild_prompt(activated)

        # 2. Executive DAG Plan
        plan: ExecutionPlan = self.planner.decompose(goal=goal, workspace_files=workspace)
        for task in plan.ready_tasks():
            plan.mark_executing(task.id)
            plan.mark_completed(task.id, "Context and constraints analyzed.")

        # 3. Pre-execution Tool Bus enrichment
        tool_results: List[Dict[str, Any]] = []
        enrichment_notes: List[str] = []

        if workspace:
            ast_res: ToolCallResult = self.tool_bus.invoke("ast_inspect", workspace_files=workspace)
            if ast_res.success:
                tool_results.append(ast_res.to_dict())

        math_expr = self._extract_math_expression(goal)
        if math_expr:
            math_res = self.tool_bus.invoke("math_evaluate", expression=math_expr)
            if math_res.success:
                tool_results.append(math_res.to_dict())
                enrichment_notes.append(
                    f"Deterministic Math Tool Result: {math_expr} = {math_res.output.get('result')}"
                )

        if any(w in goal.lower() for w in ("obsidian", "vault", "guild", "concode", "subsystem")):
            vault_res = self.tool_bus.invoke("vault_query", query=goal, top_k=2)
            if vault_res.success and vault_res.output.get("notes"):
                tool_results.append(vault_res.to_dict())
                for n in vault_res.output["notes"]:
                    enrichment_notes.append(f"Vault Note ({n['note']}): {n['excerpt'][:240]}")

        if episodic_context:
            enrichment_notes.append(f"Past Episodic Experience:\n{episodic_context}")

        augmented_goal = goal
        if enrichment_notes:
            augmented_goal = f"{goal}\n\nVerified Tool & Memory Context:\n" + "\n".join(enrichment_notes)

        # 4. Execute either workspace coding agent or universal direct synthesis
        edits: List[AgentEdit] = []
        verification: List[VerificationResult] = []
        sandbox_results: List[SandboxResult] = []
        direct_answer = ""
        iterations = 1
        needs_user_input = False
        question = None
        error = None
        summary = ""

        if workspace:
            ready = plan.ready_tasks()
            active_task_id = ready[0].id if ready else plan.tasks[-1].id
            plan.mark_executing(active_task_id)

            agent_outcome = self.coding_agent.run(
                goal=augmented_goal,
                workspace_files=workspace,
                guild_prompt=composite_prompt,
                max_iterations=max_iterations,
            )
            edits = agent_outcome.edits
            verification = agent_outcome.verification
            iterations = agent_outcome.iterations
            needs_user_input = agent_outcome.needs_user_input
            question = agent_outcome.question
            error = agent_outcome.error
            summary = agent_outcome.summary

            if agent_outcome.success:
                plan.mark_completed(active_task_id, summary)
            else:
                plan.mark_failed(active_task_id, error or "Agent execution failed", max_attempts=1)

            # Apply edits to candidate workspace for optional sandbox verification
            candidate_ws = dict(workspace)
            for edit in edits:
                candidate_ws[edit.path] = edit.content

            if enable_sandbox and self.sandbox_executor is not None:
                self.sandbox_executor.policy.allow_execution = True
                sandbox_results = self.sandbox_executor.verify_workspace_tests(candidate_ws)
        else:
            # Universal non-workspace problem solving (architecture, math, science, Q&A, code generation)
            ready = plan.ready_tasks()
            active_task_id = ready[0].id if ready else plan.tasks[-1].id
            plan.mark_executing(active_task_id)

            direct_answer = self.generator.generate(
                system_prompt=composite_prompt,
                user_prompt=augmented_goal,
                context="",
                history=None,
            )
            summary = "Generated universal multi-guild solution."
            plan.mark_completed(active_task_id, summary)

        # 5. Adversarial Critic Audit
        critic_report = self.critic.audit(
            edits=edits,
            verification=verification,
            sandbox_results=sandbox_results,
            direct_answer=direct_answer,
        )

        # Mark final verification task in DAG
        for task in plan.ready_tasks():
            plan.mark_executing(task.id)
            if critic_report.passed and not error:
                plan.mark_completed(task.id, f"Critic score: {critic_report.score}")
            else:
                plan.mark_failed(
                    task.id,
                    "; ".join(critic_report.issues) or (error or "Verification failed"),
                    max_attempts=1,
                )

        overall_success = (not error) and (needs_user_input or critic_report.passed)

        return SwarmOutcome(
            goal=goal,
            summary=summary,
            success=overall_success,
            plan=plan.to_dict(),
            activated_guilds=activated_dicts,
            edits=edits,
            verification=verification,
            critic_report=critic_report,
            tool_results=tool_results,
            sandbox_results=[s.to_dict() for s in sandbox_results],
            direct_answer=direct_answer,
            iterations=iterations,
            needs_user_input=needs_user_input,
            question=question,
            error=error,
        )

    @staticmethod
    def _extract_math_expression(text: str) -> Optional[str]:
        """Detect explicit arithmetic/mathematical expressions in user queries."""
        match = re.search(
            r"(?:calculate|compute|evaluate|solve)\s*[:=]?\s*([0-9+\-*/^().\s]+(?:sqrt|sin|cos|tan|log|factorial|pi|e)?[0-9+\-*/^().\s]*)",
            text,
            re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip()
            if any(ch.isdigit() for ch in candidate) and len(candidate) >= 3:
                return candidate
        return None
