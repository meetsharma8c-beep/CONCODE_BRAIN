"""
CONCODE Neural Brain v4.0 APEX -- Live Generative MCTS, System-3 Metacognitive
Supervisor, and Unified Cross-Project Frontier Orchestrator

Replaces static/hardcoded reasoning demos with an executable test-time compute engine:
  1. System-3 Metacognitive Supervisor:
     - Semantic cycle-detection ring buffer (cosine similarity > 0.92 + Lyapunov stall |dV| < eps)
     - Epistemic vs. Aleatoric uncertainty estimation across rollouts
  2. Live LLM-Backed MCTS Search Engine:
     - UCT selection over dynamically generated candidate branches
     - Real deterministic Process Reward scoring via FormalVerifier
     - Counterexample-guided <backtrack> injection using compiler/CWE/SMT diagnostics
  3. Unified ApexCognitiveEngine:
     - Binds ProjectManifest + LifelongGraphRAG + 18-Guild Router + FrontierMoEMesh +
       System-3 MCTS/MoA + FormalVerifier + Continual Learning Harvester.
"""

from __future__ import annotations

import logging
import math
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.brain.formal_verifier import FormalProofResult, FormalVerifier, VerificationReport
from src.brain.frontier_mesh import (
    MODE_APEX_MCTS,
    MODE_APEX_MOA_SWARM,
    MODE_DEEP_SINGLE,
    MODE_REFLEX_O1,
    FrontierMoEMesh,
    MoDDecision,
)
from src.brain.graph_rag import LifelongGraphRAG
from src.brain.project_manifest import (
    ProjectManifest,
    ProjectManifestRegistry,
    WorkspaceGraphSnippet,
    build_dynamic_system_context,
)

logger = logging.getLogger("concode.apex")


# ==============================================================================
# 1. SYSTEM-3 METACOGNITIVE SUPERVISOR
# ==============================================================================

@dataclass
class MetacognitiveTelemetry:
    """Real-time System-3 supervisory metrics over a reasoning trajectory."""

    epistemic_uncertainty: float = 0.0
    aleatoric_uncertainty: float = 0.0
    lyapunov_deltas: List[float] = field(default_factory=list)
    stalls_detected: int = 0
    forced_backtracks: int = 0
    max_cosine_similarity: float = 0.0
    clarification_recommended: bool = False
    routing_advice: str = "proceed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class System3MetacognitiveMonitor:
    """
    Higher-order supervisory policy monitoring reasoning trajectory progress:
      - Detects semantic cycles via cosine similarity on a rolling ring buffer.
      - Tracks Lyapunov progress potential dV_t = V(s_t) - V(s_{t-1}).
      - Estimates aleatoric prompt ambiguity vs. epistemic rollout disagreement.
    """

    def __init__(
        self,
        ring_capacity: int = 8,
        cycle_similarity_threshold: float = 0.92,
        stall_epsilon: float = 0.02,
    ):
        self.ring_capacity = ring_capacity
        self.cycle_similarity_threshold = cycle_similarity_threshold
        self.stall_epsilon = stall_epsilon
        self._vectors: List[Counter] = []
        self._scores: List[float] = []
        self.telemetry = MetacognitiveTelemetry()

    @staticmethod
    def _vectorize(text: str) -> Counter:
        tokens = re.findall(r"[a-z0-9_]{2,}", text.lower())
        return Counter(tokens)

    @staticmethod
    def cosine_similarity(v1: Counter, v2: Counter) -> float:
        if not v1 or not v2:
            return 0.0
        common = set(v1.keys()) & set(v2.keys())
        dot = sum(v1[k] * v2[k] for k in common)
        norm1 = math.sqrt(sum(c * c for c in v1.values()))
        norm2 = math.sqrt(sum(c * c for c in v2.values()))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return round(dot / (norm1 * norm2), 4)

    def assess_aleatoric_uncertainty(self, goal: str, workspace_files: Optional[Dict[str, str]] = None) -> float:
        """Estimate prompt ambiguity (underspecified requirements or missing context)."""
        words = goal.strip().split()
        score = 0.05
        if len(words) < 5:
            score += 0.45
        elif len(words) < 10:
            score += 0.20
        vague_terms = ("something", "fix it", "make it better", "do it", "stuff", "whatever")
        if any(v in goal.lower() for v in vague_terms):
            score += 0.35
        if workspace_files:
            score = max(0.05, score - 0.20)
        score = round(min(score, 1.0), 3)
        self.telemetry.aleatoric_uncertainty = score
        if score >= 0.65:
            self.telemetry.clarification_recommended = True
            self.telemetry.routing_advice = "clarify_underspecified_prompt"
        return score

    def observe_step(self, candidate_text: str, prm_score: float) -> Tuple[bool, float, float]:
        """
        Record a candidate step and check for a Lyapunov stall / semantic cycle.
        Returns (should_force_backtrack, max_sim, lyapunov_delta).
        """
        vec = self._vectorize(candidate_text)
        max_sim = 0.0
        for prev in self._vectors:
            sim = self.cosine_similarity(vec, prev)
            if sim > max_sim:
                max_sim = sim

        prev_score = self._scores[-1] if self._scores else 0.0
        delta_v = round(prm_score - prev_score, 4)

        self._vectors.append(vec)
        self._scores.append(prm_score)
        if len(self._vectors) > self.ring_capacity:
            self._vectors.pop(0)
            self._scores.pop(0)

        self.telemetry.lyapunov_deltas.append(delta_v)
        if max_sim > self.telemetry.max_cosine_similarity:
            self.telemetry.max_cosine_similarity = max_sim

        # Update epistemic uncertainty as dispersion across observed candidate rewards
        if len(self._scores) >= 2:
            mean = sum(self._scores) / len(self._scores)
            variance = sum((s - mean) ** 2 for s in self._scores) / len(self._scores)
            self.telemetry.epistemic_uncertainty = round(min(1.0, math.sqrt(variance) * 2.0), 4)

        is_stalled = (max_sim >= self.cycle_similarity_threshold) and (abs(delta_v) < self.stall_epsilon)
        if is_stalled:
            self.telemetry.stalls_detected += 1
            self.telemetry.forced_backtracks += 1
            self.telemetry.routing_advice = "forced_backtrack_cycle_interrupt"
        return is_stalled, max_sim, delta_v


# ==============================================================================
# 2. LIVE LLM-BACKED MCTS ENGINE
# ==============================================================================

@dataclass
class LiveMCTSNode:
    node_id: str
    step_type: str  # root | candidate | backtrack | verified
    response_text: str
    parent: Optional["LiveMCTSNode"] = None
    children: List["LiveMCTSNode"] = field(default_factory=list)
    visits: int = 0
    total_value: float = 0.0
    prior_prob: float = 1.0
    verification: Optional[VerificationReport] = None
    diagnostics_injected: List[str] = field(default_factory=list)

    @property
    def q_value(self) -> float:
        return self.total_value / self.visits if self.visits > 0 else 0.0


@dataclass
class MCTSOutcome:
    best_response: str
    best_verification: VerificationReport
    rollouts_executed: int
    backtracks_performed: int
    explored_rewards: List[float]
    grpo_advantages: List[float]
    metacognition: MetacognitiveTelemetry
    rejected_candidate: Optional[str] = None


class LiveMCTSEngine:
    """
    Generative Test-Time Compute MCTS engine backed by the active FrontierMoEMesh,
    scored deterministically by FormalVerifier and supervised by System-3 Metacognition.
    """

    def __init__(
        self,
        mesh: FrontierMoEMesh,
        verifier: FormalVerifier,
        c_puct: float = 1.414,
    ):
        self.mesh = mesh
        self.verifier = verifier
        self.c_puct = c_puct

    def _uct_select(self, node: LiveMCTSNode) -> LiveMCTSNode:
        best_score = -float("inf")
        best_child = node.children[0]
        sqrt_parent = math.sqrt(max(1, node.visits))
        for child in node.children:
            uct = child.q_value + self.c_puct * child.prior_prob * (sqrt_parent / (1 + child.visits))
            if uct > best_score:
                best_score = uct
                best_child = child
        return best_child

    @staticmethod
    def _backpropagate(node: LiveMCTSNode, value: float) -> None:
        curr: Optional[LiveMCTSNode] = node
        while curr is not None:
            curr.visits += 1
            curr.total_value += value
            curr = curr.parent

    def search(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        formal_constraints: Optional[Dict[str, Any]] = None,
        max_rollouts: int = 3,
        prefer_frontier: bool = True,
    ) -> MCTSOutcome:
        """
        Execute bounded live UCT MCTS rollouts:
          - Rollout 1: Initial synthesis with structured <concode_think> reasoning.
          - Subsequent rollouts: If the current best candidate has verification failures,
            CWE findings, formal UNSAT conflicts, or a System-3 semantic cycle stall,
            expand a counterexample-guided <backtrack> refinement branch.
        """
        monitor = System3MetacognitiveMonitor()
        monitor.assess_aleatoric_uncertainty(user_prompt)

        root = LiveMCTSNode(node_id="root", step_type="root", response_text=user_prompt, visits=1)
        all_candidates: List[LiveMCTSNode] = []
        backtracks_performed = 0
        rollouts_run = 0

        for rollout_idx in range(1, max(1, min(max_rollouts, 6)) + 1):
            rollouts_run += 1
            parent = root if not root.children else self._uct_select(root)

            if parent is root:
                prompt_for_step = user_prompt
                step_type = "candidate"
                injected_diags: List[str] = []
                temp = 0.20 + 0.08 * (rollout_idx - 1)
            else:
                prev_ver = parent.verification
                injected_diags = list(prev_ver.diagnostics) if prev_ver else []
                if not injected_diags:
                    injected_diags = [
                        "Deepen edge-case verification, provide complete runnable code, and explicitly compare Option A vs. Option B."
                    ]
                step_type = "backtrack"
                backtracks_performed += 1
                temp = 0.15
                prompt_for_step = (
                    f"{user_prompt}\n\n"
                    "<system3_backtrack_directive>\n"
                    "The previous candidate had the following deterministic verification issues that MUST be fixed:\n"
                    + "\n".join(f"- {d}" for d in injected_diags)
                    + "\nProduce a hardened, verified solution inside <concode_think> with an explicit <backtrack> block "
                    "followed by the complete corrected final answer.\n"
                    "</system3_backtrack_directive>"
                )

            candidate_text = self.mesh.generate(
                system_prompt=system_prompt,
                user_prompt=prompt_for_step,
                context=context,
                history=history,
                prefer_frontier=prefer_frontier,
                temperature=temp,
            )
            ver = self.verifier.verify_response(
                candidate_text,
                formal_constraints=formal_constraints,
                require_reasoning_contract=True,
            )
            stalled, _, _ = monitor.observe_step(candidate_text, ver.r_total)
            reward = max(0.0, ver.r_total - (0.15 if stalled else 0.0))

            child = LiveMCTSNode(
                node_id=f"r{rollout_idx}_{step_type}",
                step_type="verified" if ver.passed else step_type,
                response_text=candidate_text,
                parent=parent,
                prior_prob=0.5 if step_type == "backtrack" else 1.0,
                verification=ver,
                diagnostics_injected=injected_diags,
            )
            parent.children.append(child)
            self._backpropagate(child, reward)
            all_candidates.append(child)

            # Early stopping if candidate passes all formal & security checks with high confidence
            if ver.passed and ver.r_total >= 0.94 and not stalled:
                break

        all_candidates.sort(
            key=lambda n: (bool(n.verification and n.verification.passed), n.verification.r_total if n.verification else 0.0),
            reverse=True,
        )
        best = all_candidates[0]
        worst = all_candidates[-1] if len(all_candidates) > 1 else None
        rewards = [c.verification.r_total for c in all_candidates if c.verification]
        advantages = self.verifier.grpo_group_advantages(rewards)

        rejected_text = None
        if worst is not None and worst is not best and worst.verification and best.verification:
            if best.verification.r_total > worst.verification.r_total:
                rejected_text = worst.response_text

        return MCTSOutcome(
            best_response=best.response_text,
            best_verification=best.verification or self.verifier.verify_response(best.response_text),
            rollouts_executed=rollouts_run,
            backtracks_performed=backtracks_performed,
            explored_rewards=rewards,
            grpo_advantages=advantages,
            metacognition=monitor.telemetry,
            rejected_candidate=rejected_text,
        )


# ==============================================================================
# 3. UNIFIED CONCODE v4.0 APEX ENGINE
# ==============================================================================

@dataclass
class ApexOutcome:
    """Complete verified result returned by POST /api/v1/apex."""

    response: str
    success: bool
    project_id: str
    project_name: str
    compute_routing: Dict[str, Any]
    activated_guilds: List[Dict[str, Any]]
    verification: Dict[str, Any]
    metacognition: Dict[str, Any]
    formal_proofs: List[Dict[str, Any]]
    graph_rag_nodes_used: int
    mcts_rollouts: int
    moa_proposals: List[Dict[str, Any]]
    grpo_advantages: List[float]
    harvested_to_flywheel: bool
    latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ApexCognitiveEngine:
    """
    Unified CONCODE v4.0 APEX Frontier Engine orchestrating all cross-project
    manifests, lifelong GraphRAG, 18 neural guilds, Frontier MoE Mesh, live MCTS,
    System-3 Metacognition, Formal Verification, and Continual RLVR Harvesting.
    """

    def __init__(
        self,
        manifest_registry: ProjectManifestRegistry,
        graph_rag: LifelongGraphRAG,
        frontier_mesh: FrontierMoEMesh,
        formal_verifier: FormalVerifier,
        intent_classifier: Any = None,
        guilds_data: Optional[Dict[str, Any]] = None,
        evolution_harvester: Any = None,
        cognitive_memory: Any = None,
    ):
        self.manifest_registry = manifest_registry
        self.graph_rag = graph_rag
        self.frontier_mesh = frontier_mesh
        self.formal_verifier = formal_verifier
        self.intent_classifier = intent_classifier
        self.guilds_data = guilds_data or {}
        self.evolution_harvester = evolution_harvester
        self.cognitive_memory = cognitive_memory
        self.mcts_engine = LiveMCTSEngine(mesh=frontier_mesh, verifier=formal_verifier)

    def solve(
        self,
        goal: str,
        project_id: str = "universal",
        inline_manifest: Optional[Dict[str, Any]] = None,
        workspace_files: Optional[Dict[str, str]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        compute_mode: str = "auto",
        formal_constraints: Optional[Dict[str, Any]] = None,
        max_mcts_rollouts: int = 3,
        sync_vault: bool = False,
    ) -> ApexOutcome:
        start_time = time.time()
        workspace_files = workspace_files or {}

        # 1. Bind Project Manifest (inline or registry lookup)
        if inline_manifest:
            manifest = ProjectManifest.from_dict(inline_manifest)
            self.manifest_registry.register(manifest)
            self.graph_rag.ingest_project_manifest(manifest.to_dict())
        else:
            manifest = self.manifest_registry.get(project_id)
            if f"proj_{manifest.project_id}" not in self.graph_rag.nodes:
                self.graph_rag.ingest_project_manifest(manifest.to_dict())

        # 2. Activate top specialist guilds via neural classifier
        activated_guilds: List[Dict[str, Any]] = []
        guild_prompts: List[str] = []
        if self.intent_classifier is not None and hasattr(self.intent_classifier, "predict_multi"):
            preds = self.intent_classifier.predict_multi(goal, top_k=3)
            for g_name, g_conf in preds:
                activated_guilds.append({"guild": g_name, "confidence": round(float(g_conf), 4)})
                gp = self.guilds_data.get(g_name, {}).get("system_prompt")
                if gp:
                    guild_prompts.append(f"[{g_name}] {gp}")
        else:
            activated_guilds.append({"guild": "system_architect", "confidence": 1.0})

        # 3. Retrieve Lifelong GraphRAG k-hop subgraph & pinned invariants
        graph_xml, graph_nodes_used = self.graph_rag.format_graph_rag_context(
            query=goal,
            project_id=manifest.project_id,
            top_k=6,
        )

        # 4. Run upfront deductive formal proofs (if caller supplied formal constraints)
        upfront_proofs: List[FormalProofResult] = []
        formal_prompt_note = ""
        if formal_constraints:
            if "allocations" in formal_constraints and "total_ceiling" in formal_constraints:
                allocs = [(str(a[0]), int(a[1]), int(a[2])) for a in formal_constraints["allocations"]]
                upfront_proofs.append(
                    self.formal_verifier.verify_linear_allocations(
                        total_ceiling=int(formal_constraints["total_ceiling"]),
                        allocations=allocs,
                        exact_sum=bool(formal_constraints.get("exact_sum", False)),
                    )
                )
            if "lock_edges" in formal_constraints:
                edges = [(str(e[0]), str(e[1])) for e in formal_constraints["lock_edges"]]
                upfront_proofs.append(self.formal_verifier.verify_deadlock_freedom(edges))

            if upfront_proofs:
                proof_lines = ["<formal_verifier_precheck>"]
                for p in upfront_proofs:
                    proof_lines.append(
                        f"  <proof engine=\"{p.solver_engine}\" status=\"{p.status}\">"
                        f"{p.remediation_guidance} | witness={p.witness} | unsat_core={p.unsat_core}"
                        "</proof>"
                    )
                proof_lines.append("</formal_verifier_precheck>")
                formal_prompt_note = "\n".join(proof_lines)

        # 5. Mixture-of-Depths (MoD) Compute Budget Routing
        effective_req_mode = compute_mode if compute_mode != "auto" else manifest.preferred_compute_tier
        mod_decision: MoDDecision = self.frontier_mesh.route_mod(
            goal=goal,
            workspace_files=workspace_files,
            active_guilds=[g["guild"] for g in activated_guilds],
            requested_mode=effective_req_mode,
            has_formal_constraints=bool(formal_constraints),
        )

        # 6. Build dynamic system prompt & workspace snippets (compact mode for local <=14B models)
        snippets = [
            WorkspaceGraphSnippet(
                file_path=path,
                symbol_type=path.rsplit(".", 1)[-1] if "." in path else "text",
                content=content[:4000],
            )
            for path, content in list(workspace_files.items())[:10]
        ]
        use_compact_prompt = (
            mod_decision.effective_total_params_b <= 14
            and not self.frontier_mesh.has_frontier_nodes
        )
        system_prompt = build_dynamic_system_context(
            manifest=manifest,
            graph_snippets=snippets,
            graph_rag_xml="\n\n".join(x for x in (graph_xml, formal_prompt_note) if x),
            guild_prompts=guild_prompts,
            include_master_prompt=True,
            compact=use_compact_prompt,
        )

        # 7. Execute selected compute path
        moa_proposals: List[Dict[str, Any]] = []
        mcts_rollouts = 0
        grpo_advantages: List[float] = []
        rejected_candidate: Optional[str] = None
        metacog = System3MetacognitiveMonitor()
        metacog.assess_aleatoric_uncertainty(goal, workspace_files)

        if mod_decision.compute_mode == MODE_APEX_MOA_SWARM:
            moa_out = self.frontier_mesh.run_moa_ensemble(
                system_prompt=system_prompt,
                user_prompt=goal,
                history=history,
                formal_constraints=formal_constraints,
            )
            final_text = moa_out.final_response
            final_ver = moa_out.final_verification
            moa_proposals = [p.to_summary_dict() for p in moa_out.proposals]
            grpo_advantages = moa_out.grpo_advantages
            for p in moa_out.proposals:
                metacog.observe_step(p.response, p.verification.r_total)
            if len(moa_out.proposals) >= 2 and moa_out.proposals[-1].verification.r_total < final_ver.r_total:
                rejected_candidate = moa_out.proposals[-1].response
            metacog_dict = metacog.telemetry.to_dict()

        elif mod_decision.compute_mode == MODE_APEX_MCTS:
            mcts_out = self.mcts_engine.search(
                system_prompt=system_prompt,
                user_prompt=goal,
                history=history,
                formal_constraints=formal_constraints,
                max_rollouts=max_mcts_rollouts,
                prefer_frontier=True,
            )
            final_text = mcts_out.best_response
            final_ver = mcts_out.best_verification
            mcts_rollouts = mcts_out.rollouts_executed
            grpo_advantages = mcts_out.grpo_advantages
            rejected_candidate = mcts_out.rejected_candidate
            metacog_dict = mcts_out.metacognition.to_dict()

        else:
            prefer_frontier = mod_decision.compute_mode != MODE_REFLEX_O1
            final_text = self.frontier_mesh.generate(
                system_prompt=system_prompt,
                user_prompt=goal,
                history=history,
                prefer_frontier=prefer_frontier,
            )
            final_ver = self.formal_verifier.verify_response(
                final_text,
                formal_constraints=formal_constraints,
                require_reasoning_contract=(mod_decision.compute_mode == MODE_DEEP_SINGLE),
            )
            metacog.observe_step(final_text, final_ver.r_total)
            metacog_dict = metacog.telemetry.to_dict()

        # 8. Continual Learning Flywheel (Harvest verified RLVR trajectories + DPO pairs + GraphRAG insight)
        harvested = False
        guild_names = [g["guild"] for g in activated_guilds] or ["system_architect"]
        if self.evolution_harvester is not None:
            if final_ver.r_total >= 0.80:
                harvested = bool(
                    self.evolution_harvester.harvest_trajectory(
                        prompt=f"[{manifest.project_id}] {goal}",
                        response=final_text,
                        guilds=guild_names,
                        critic_score=final_ver.r_total,
                        plan_steps=[mod_decision.compute_mode, f"graph_nodes={graph_nodes_used}"],
                    )
                )
            if rejected_candidate:
                self.evolution_harvester.harvest_dpo_pair(
                    prompt=f"[{manifest.project_id}] {goal}",
                    chosen_response=final_text,
                    rejected_response=rejected_candidate,
                    guild=guild_names[0],
                    reason=f"apex_{mod_decision.compute_mode.lower()}_verification_repair",
                )

        if self.cognitive_memory is not None and final_ver.passed:
            self.cognitive_memory.record_episode(
                goal=f"[{manifest.project_id}] {goal}",
                guilds=guild_names,
                plan_steps=[mod_decision.compute_mode],
                solution_summary=final_text[:400],
                files_touched=list(workspace_files.keys())[:10],
                critic_score=final_ver.r_total,
                verified=True,
                sync_vault=sync_vault,
            )

        if final_ver.passed and final_ver.r_total >= 0.90:
            self.graph_rag.record_verified_insight(
                project_id=manifest.project_id,
                label=goal[:100],
                summary=final_text.split("</concode_think>")[-1].strip()[:400],
                tags=guild_names + [manifest.project_id],
                pinned=False,
            )

        all_proofs = [p.to_dict() for p in (upfront_proofs or final_ver.formal_proofs)]
        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ApexOutcome(
            response=final_text,
            success=final_ver.passed,
            project_id=manifest.project_id,
            project_name=manifest.project_name,
            compute_routing=mod_decision.to_dict(),
            activated_guilds=activated_guilds,
            verification=final_ver.to_dict(),
            metacognition=metacog_dict,
            formal_proofs=all_proofs,
            graph_rag_nodes_used=graph_nodes_used,
            mcts_rollouts=mcts_rollouts,
            moa_proposals=moa_proposals,
            grpo_advantages=grpo_advantages,
            harvested_to_flywheel=harvested,
            latency_ms=elapsed_ms,
        )
