"""
CONCODE Neural Brain v4.0 APEX -- Frontier Sparse MoE Mesh, Mixture-of-Agents (MoA),
and Mixture-of-Depths (MoD) Adaptive Compute Router

Enables CONCODE Brain to scale cleanly from local 7B Eco Metal inference up to
480B - 1T+ open-weight Sparse MoE frontier clusters (Kimi-K2 1T MoE, DeepSeek-R1/V3
671B MoE, Qwen3-Coder-480B-A35B MoE, Llama-4 Maverick 400B) via OpenAI-compatible
vLLM / SGLang / cloud endpoints, plus parallel Mixture-of-Agents cross-verification.
"""

from __future__ import annotations

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from src.brain.formal_verifier import FormalVerifier, VerificationReport
from src.brain.generator import ModelGenerationError

logger = logging.getLogger("concode.frontier_mesh")


MODE_REFLEX_O1 = "REFLEX_O1"
MODE_DEEP_SINGLE = "DEEP_SINGLE"
MODE_APEX_MCTS = "APEX_MCTS"
MODE_APEX_MOA_SWARM = "APEX_MOA_SWARM"


# Reference catalog of open-weight Frontier Sparse MoE models compatible with
# OpenAI / vLLM / SGLang inference endpoints.
FRONTIER_MOE_CATALOG: Dict[str, Dict[str, Any]] = {
    "kimi_k2_1t": {
        "model_id": "moonshotai/Kimi-K2-Instruct",
        "total_params_b": 1000,
        "active_params_b": 32,
        "architecture": "Sparse MoE (384 experts, 8 active)",
        "specialty": "Long-horizon architecture, multi-file engineering, agentic tool use",
    },
    "deepseek_r1_671b": {
        "model_id": "deepseek-ai/DeepSeek-R1",
        "total_params_b": 671,
        "active_params_b": 37,
        "architecture": "Sparse MoE (256 routed + 1 shared expert)",
        "specialty": "Deep formal reasoning, distributed algorithms, mathematical proofs",
    },
    "qwen3_coder_480b": {
        "model_id": "Qwen/Qwen3-Coder-480B-A35B-Instruct",
        "total_params_b": 480,
        "active_params_b": 35,
        "architecture": "Sparse MoE (160 experts, 8 active)",
        "specialty": "Polyglot software synthesis, repository refactoring, security hardening",
    },
    "llama4_maverick_400b": {
        "model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
        "total_params_b": 400,
        "active_params_b": 17,
        "architecture": "Sparse MoE (128 experts, 17B active)",
        "specialty": "Fast multimodal & high-throughput product reasoning",
    },
    "qwen3_235b": {
        "model_id": "Qwen/Qwen3-235B-A22B",
        "total_params_b": 235,
        "active_params_b": 22,
        "architecture": "Sparse MoE (128 experts, 8 active)",
        "specialty": "Hybrid thinking-mode general and code reasoning",
    },
    "local_eco_metal": {
        "model_id": "codellama-7b-concode.Q4_K_M.gguf",
        "total_params_b": 7,
        "active_params_b": 7,
        "architecture": "Dense Transformer (GGUF Q4_K_M Metal Eco)",
        "specialty": "Offline reflex execution and low-power local fallback",
    },
}


@dataclass
class FrontierNodeConfig:
    """Configuration for one inference node inside the Frontier MoE Mesh."""

    node_id: str
    base_url: str
    model: str
    api_key: str = ""
    role: str = "general"  # general | architect | coder | verifier | synthesizer
    total_params_b: int = 671
    active_params_b: int = 37
    max_tokens: int = 4096
    temperature: float = 0.25
    timeout_seconds: int = 120
    priority: int = 1

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "base_url": self.base_url,
            "model": self.model,
            "role": self.role,
            "total_params_b": self.total_params_b,
            "active_params_b": self.active_params_b,
            "max_tokens": self.max_tokens,
            "priority": self.priority,
            "configured": self.is_valid(),
        }

    def is_valid(self) -> bool:
        parsed = urlparse(self.base_url.strip())
        is_local = parsed.hostname in ("localhost", "127.0.0.1")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and is_local):
            return False
        if not parsed.netloc or not self.model.strip():
            return False
        if not is_local and not self.api_key.strip():
            return False
        return True


class FrontierNodeClient:
    """OpenAI-compatible HTTP client for a single Sparse MoE / vLLM / SGLang node."""

    def __init__(self, config: FrontierNodeConfig):
        self.config = config
        self.base_url = config.base_url.rstrip("/")

    @property
    def is_loaded(self) -> bool:
        return self.config.is_valid()

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        if not self.is_loaded:
            raise ModelGenerationError(f"Frontier node '{self.config.node_id}' is not validly configured.")

        sys_text = system_prompt.strip()
        if context:
            sys_text += f"\n\nWorkspace / Reference Context:\n{context}"

        messages: List[Dict[str, str]] = [{"role": "system", "content": sys_text}]
        for turn in history or []:
            if turn.get("role") in ("user", "assistant") and isinstance(turn.get("content"), str):
                messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": user_prompt})

        endpoint = (
            f"{self.base_url}/chat/completions"
            if self.base_url.endswith("/v1")
            else f"{self.base_url}/v1/chat/completions"
        )
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": int(max_tokens or self.config.max_tokens),
            "temperature": float(self.config.temperature if temperature is None else temperature),
            "top_p": 0.9,
        }
        headers = {"Content-Type": "application/json"}
        if self.config.api_key.strip():
            headers["Authorization"] = f"Bearer {self.config.api_key.strip()}"

        req = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.config.timeout_seconds) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            msg = body["choices"][0]["message"]
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning_content") or ""
            if reasoning and "<concode_think>" not in content:
                content = f"<concode_think>\n<step>{reasoning.strip()}</step>\n</concode_think>\n\n{content.strip()}"
            if not content.strip():
                raise ValueError("Frontier node returned empty content.")
            return content.strip()
        except (HTTPError, URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Frontier node '%s' failed: %s", self.config.node_id, exc)
            raise ModelGenerationError(f"Frontier node '{self.config.node_id}' failed: {exc}") from exc


@dataclass
class MoDDecision:
    """Mixture-of-Depths adaptive compute budget decision."""

    compute_mode: str  # REFLEX_O1 | DEEP_SINGLE | APEX_MCTS | APEX_MOA_SWARM
    complexity_score: float
    selected_nodes: List[str]
    effective_total_params_b: int
    effective_active_params_b: int
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MoAProposal:
    """Single proposer output inside Mixture-of-Agents parallel synthesis."""

    proposer_id: str
    role: str
    model: str
    total_params_b: int
    response: str
    verification: VerificationReport
    latency_ms: float

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "proposer_id": self.proposer_id,
            "role": self.role,
            "model": self.model,
            "total_params_b": self.total_params_b,
            "r_total": self.verification.r_total,
            "passed": self.verification.passed,
            "security_findings": len(self.verification.security_findings),
            "latency_ms": self.latency_ms,
        }


@dataclass
class MoAOutcome:
    """Final verified output from parallel Mixture-of-Agents synthesis."""

    final_response: str
    final_verification: VerificationReport
    proposals: List[MoAProposal] = field(default_factory=list)
    synthesizer_used: str = ""
    total_params_consulted_b: int = 0
    grpo_advantages: List[float] = field(default_factory=list)


class FrontierMoEMesh:
    """
    Unified Hybrid Compute Mesh combining:
      - Local Eco Reflex node (Apple Silicon Metal 7B-32B)
      - Multiple Cloud/Cluster Open-Weight Frontier Sparse MoE nodes (235B - 1T+ params)
      - Mixture-of-Depths (MoD) adaptive routing
      - Parallel Mixture-of-Agents (MoA) multi-proposer + formal-verifier synthesis
    """

    def __init__(
        self,
        local_generator: Any = None,
        frontier_nodes: Optional[Sequence[FrontierNodeConfig]] = None,
        verifier: Optional[FormalVerifier] = None,
    ):
        self.local_generator = local_generator
        self.verifier = verifier or FormalVerifier()
        self.nodes: Dict[str, FrontierNodeClient] = {}
        for cfg in frontier_nodes or []:
            if cfg.is_valid():
                self.nodes[cfg.node_id] = FrontierNodeClient(cfg)

    @classmethod
    def from_environment(
        cls,
        local_generator: Any = None,
        verifier: Optional[FormalVerifier] = None,
    ) -> "FrontierMoEMesh":
        """
        Build a FrontierMoEMesh from environment configuration:
          - CONCODE_FRONTIER_NODES: JSON array of node configs
          - CONCODE_FRONTIER_URL / CONCODE_FRONTIER_MODEL / CONCODE_FRONTIER_API_KEY
          - Fallback to CONCODE_REMOTE_LLM_BASE_URL if configured
        """
        configs: List[FrontierNodeConfig] = []

        raw_json = os.environ.get("CONCODE_FRONTIER_NODES", "").strip()
        if raw_json:
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, list):
                    for idx, item in enumerate(parsed):
                        if not isinstance(item, dict):
                            continue
                        configs.append(
                            FrontierNodeConfig(
                                node_id=str(item.get("node_id", f"frontier_{idx + 1}")),
                                base_url=str(item.get("base_url", "")),
                                model=str(item.get("model", "")),
                                api_key=str(item.get("api_key", "")),
                                role=str(item.get("role", "general")),
                                total_params_b=int(item.get("total_params_b", 671)),
                                active_params_b=int(item.get("active_params_b", 37)),
                                max_tokens=int(item.get("max_tokens", 4096)),
                                temperature=float(item.get("temperature", 0.25)),
                                timeout_seconds=int(item.get("timeout_seconds", 120)),
                                priority=int(item.get("priority", idx + 1)),
                            )
                        )
            except Exception as exc:
                logger.warning("Could not parse CONCODE_FRONTIER_NODES JSON: %s", exc)

        # Single frontier endpoint shorthand
        single_url = os.environ.get("CONCODE_FRONTIER_URL", "").strip()
        single_model = os.environ.get("CONCODE_FRONTIER_MODEL", "").strip()
        single_key = os.environ.get("CONCODE_FRONTIER_API_KEY", "").strip()
        if single_url and single_model:
            configs.append(
                FrontierNodeConfig(
                    node_id="frontier_primary",
                    base_url=single_url,
                    model=single_model,
                    api_key=single_key,
                    role="architect",
                    total_params_b=int(os.environ.get("CONCODE_FRONTIER_PARAMS_B", "671")),
                    active_params_b=int(os.environ.get("CONCODE_FRONTIER_ACTIVE_PARAMS_B", "37")),
                    max_tokens=int(os.environ.get("CONCODE_FRONTIER_MAX_TOKENS", "4096")),
                    priority=1,
                )
            )

        # Secondary compatibility with existing CONCODE_REMOTE_LLM_* env vars
        remote_url = os.environ.get("CONCODE_REMOTE_LLM_BASE_URL", "").strip()
        remote_model = os.environ.get("CONCODE_REMOTE_LLM_MODEL", "").strip()
        remote_key = os.environ.get("CONCODE_REMOTE_LLM_API_KEY", "").strip()
        if remote_url and remote_model and not any(c.base_url == remote_url and c.model == remote_model for c in configs):
            configs.append(
                FrontierNodeConfig(
                    node_id="remote_gpu_node",
                    base_url=remote_url,
                    model=remote_model,
                    api_key=remote_key,
                    role="coder",
                    total_params_b=int(os.environ.get("CONCODE_REMOTE_PARAMS_B", "70")),
                    active_params_b=int(os.environ.get("CONCODE_REMOTE_ACTIVE_PARAMS_B", "32")),
                    priority=2,
                )
            )

        return cls(local_generator=local_generator, frontier_nodes=configs, verifier=verifier)

    def register_node(self, config: FrontierNodeConfig) -> bool:
        """Dynamically attach a new Frontier Sparse MoE endpoint at runtime."""
        if not config.is_valid():
            return False
        self.nodes[config.node_id] = FrontierNodeClient(config)
        return True

    @property
    def has_frontier_nodes(self) -> bool:
        return len(self.nodes) > 0

    @property
    def is_loaded(self) -> bool:
        local_ok = self.local_generator is not None and getattr(self.local_generator, "is_loaded", False)
        return self.has_frontier_nodes or bool(local_ok)

    def _ordered_nodes(self) -> List[FrontierNodeClient]:
        return sorted(self.nodes.values(), key=lambda c: (c.config.priority, -c.config.total_params_b))

    def total_mesh_capacity(self) -> Tuple[int, int]:
        """Return (aggregate_total_params_b, max_active_params_b) across all connected nodes."""
        total_b = sum(c.config.total_params_b for c in self.nodes.values())
        active_b = max((c.config.active_params_b for c in self.nodes.values()), default=0)
        local_ok = self.local_generator is not None and getattr(self.local_generator, "is_loaded", False)
        if local_ok:
            total_b += 7
            active_b = max(active_b, 7)
        return total_b, active_b

    def route_mod(
        self,
        goal: str,
        workspace_files: Optional[Dict[str, str]] = None,
        active_guilds: Optional[Sequence[str]] = None,
        requested_mode: str = "auto",
        has_formal_constraints: bool = False,
    ) -> MoDDecision:
        """
        Mixture-of-Depths (MoD) adaptive compute router.
        Routes trivial tasks to O(1) Reflex while escalating hard engineering, security,
        distributed systems, or multi-file tasks to Frontier MoE MCTS / MoA Swarm.
        """
        workspace_files = workspace_files or {}
        active_guilds = active_guilds or []
        goal_lower = goal.lower()

        score = 0.15
        score += min(len(goal.split()) / 120.0, 0.25)
        score += min(len(workspace_files) / 8.0, 0.20)
        score += min(sum(len(v) for v in workspace_files.values()) / 20_000.0, 0.15)
        if len(active_guilds) >= 2:
            score += 0.12
        if has_formal_constraints:
            score += 0.20
        high_stakes_terms = (
            "distributed", "deadlock", "consensus", "raft", "security", "cwe",
            "ssrf", "idor", "timing", "fintech", "ledger", "idempotency",
            "trillion", "architecture", "microservice", "kubernetes", "formal",
            "proof", "optimize", "race condition", "concurrency", "refactor",
        )
        high_stakes_hits = sum(1 for term in high_stakes_terms if term in goal_lower)
        if high_stakes_hits > 0:
            score += min(0.32, 0.16 * high_stakes_hits)
        score = round(min(score, 1.0), 3)

        mode_map = {
            "reflex": MODE_REFLEX_O1,
            "deep": MODE_DEEP_SINGLE,
            "mcts": MODE_APEX_MCTS,
            "apex_moa": MODE_APEX_MOA_SWARM,
            "apex": MODE_APEX_MOA_SWARM,
        }
        if requested_mode in mode_map:
            compute_mode = mode_map[requested_mode]
            reason = f"Explicit compute mode '{requested_mode}' requested."
        elif score >= 0.80:
            compute_mode = MODE_APEX_MOA_SWARM
            reason = "Frontier-complexity multi-domain or high-stakes engineering goal; engaging MoA Swarm + Verification."
        elif score >= 0.58:
            compute_mode = MODE_APEX_MCTS
            reason = "High complexity; engaging live MCTS reasoning + System-3 metacognitive monitoring."
        elif score >= 0.35:
            compute_mode = MODE_DEEP_SINGLE
            reason = "Moderate engineering task; routing to single-pass deep model."
        else:
            compute_mode = MODE_REFLEX_O1
            reason = "Focused low-complexity query; routing to O(1) Eco Reflex path."

        ordered = self._ordered_nodes()
        if compute_mode == MODE_REFLEX_O1 and self.local_generator is not None and getattr(self.local_generator, "is_loaded", False):
            return MoDDecision(
                compute_mode=compute_mode,
                complexity_score=score,
                selected_nodes=["local_eco_metal"],
                effective_total_params_b=7,
                effective_active_params_b=7,
                reason=reason,
            )

        if ordered:
            chosen = ordered if compute_mode == MODE_APEX_MOA_SWARM else ordered[:1]
            return MoDDecision(
                compute_mode=compute_mode,
                complexity_score=score,
                selected_nodes=[c.config.node_id for c in chosen],
                effective_total_params_b=sum(c.config.total_params_b for c in chosen),
                effective_active_params_b=max(c.config.active_params_b for c in chosen),
                reason=reason,
            )

        return MoDDecision(
            compute_mode=compute_mode,
            complexity_score=score,
            selected_nodes=["local_eco_metal"],
            effective_total_params_b=7,
            effective_active_params_b=7,
            reason=f"{reason} (No cloud Frontier MoE nodes configured; operating on local Metal node.)",
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        prefer_frontier: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Standard generator interface routing to Frontier MoE nodes first (when preferred
        and configured) with seamless fallback to the local Eco Metal generator.
        """
        if prefer_frontier:
            for client in self._ordered_nodes():
                try:
                    return client.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        context=context,
                        history=history,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                except ModelGenerationError:
                    continue

        if self.local_generator is not None and getattr(self.local_generator, "is_loaded", False):
            return self.local_generator.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                context=context,
                history=history,
            )

        # Last chance: try frontier nodes even if prefer_frontier was False
        for client in self._ordered_nodes():
            try:
                return client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    context=context,
                    history=history,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except ModelGenerationError:
                continue

        raise ModelGenerationError("No operational Frontier MoE or local inference node is available.")

    def run_moa_ensemble(
        self,
        system_prompt: str,
        user_prompt: str,
        context: str = "",
        history: Optional[List[Dict[str, str]]] = None,
        formal_constraints: Optional[Dict[str, Any]] = None,
        specialist_roles: Optional[Sequence[Tuple[str, str]]] = None,
    ) -> MoAOutcome:
        """
        Execute true Mixture-of-Agents (MoA) multi-proposer parallel synthesis:
          1. Dispatch candidate generation across configured Frontier MoE nodes (or parallel
             specialist guild lenses when a single backend is attached).
          2. Score every proposal deterministically with FormalVerifier (compilation, CWE
             security audit, Z3/exact constraints, reasoning structure).
          3. Compute GRPO group-normalized advantages across proposals.
          4. Run an APEX Meta-Synthesizer pass that fuses the highest-scoring verified
             insights while explicitly eliminating every diagnostic/security finding.
        """
        roles = list(specialist_roles or [
            ("architect", "Focus on clean distributed architecture, edge-case resilience, and Option A vs Option B trade-offs."),
            ("security_auditor", "Focus on zero-trust security, CWE elimination, constant-time auth, and failure isolation."),
            ("systems_optimizer", "Focus on deterministic correctness, algorithmic complexity, concurrency safety, and complete runnable code."),
        ])

        ordered_frontier = self._ordered_nodes()
        tasks: List[Tuple[str, str, str, int, Any, float]] = []

        if len(ordered_frontier) >= 2:
            for idx, client in enumerate(ordered_frontier[:3]):
                role_name, role_hint = roles[idx % len(roles)]
                tasks.append((
                    client.config.node_id,
                    role_name,
                    client.config.model,
                    client.config.total_params_b,
                    client,
                    0.20 + 0.10 * idx,
                ))
        else:
            # Single frontier node or local node: run diverse temperature/role proposers
            base_client = ordered_frontier[0] if ordered_frontier else self.local_generator
            if base_client is None or not getattr(base_client, "is_loaded", False):
                raise ModelGenerationError("MoA ensemble requires at least one operational inference node.")
            model_name = (
                ordered_frontier[0].config.model
                if ordered_frontier
                else getattr(self.local_generator, "model_path", "local_eco_metal")
            )
            params_b = ordered_frontier[0].config.total_params_b if ordered_frontier else 7
            proposer_count = 3 if ordered_frontier else 2
            for idx in range(proposer_count):
                role_name, role_hint = roles[idx % len(roles)]
                tasks.append((
                    f"{role_name}_proposer_{idx + 1}",
                    role_name,
                    str(model_name),
                    params_b,
                    base_client,
                    0.20 + 0.15 * idx,
                ))

        def _invoke(task_tuple: Tuple[str, str, str, int, Any, float]) -> Optional[MoAProposal]:
            prop_id, role_name, model_label, params_b, client, temp = task_tuple
            t0 = time.time()
            role_directive = dict(roles).get(role_name, "")
            prompt_sys = f"{system_prompt}\n\n[MOA SPECIALIST LENS: {role_name.upper()}]\n{role_directive}"
            try:
                if isinstance(client, FrontierNodeClient):
                    raw = client.generate(
                        system_prompt=prompt_sys,
                        user_prompt=user_prompt,
                        context=context,
                        history=history,
                        temperature=temp,
                    )
                else:
                    raw = client.generate(
                        system_prompt=prompt_sys,
                        user_prompt=user_prompt,
                        context=context,
                        history=history,
                    )
                ver = self.verifier.verify_response(
                    raw,
                    formal_constraints=formal_constraints,
                    require_reasoning_contract=True,
                )
                return MoAProposal(
                    proposer_id=prop_id,
                    role=role_name,
                    model=model_label,
                    total_params_b=params_b,
                    response=raw,
                    verification=ver,
                    latency_ms=round((time.time() - t0) * 1000, 2),
                )
            except Exception as exc:
                logger.warning("MoA proposer '%s' failed: %s", prop_id, exc)
                return None

        proposals: List[MoAProposal] = []
        max_workers = min(len(tasks), 3) if ordered_frontier else 1
        if max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [pool.submit(_invoke, t) for t in tasks]
                for fut in as_completed(futures):
                    item = fut.result()
                    if item is not None:
                        proposals.append(item)
        else:
            for t in tasks:
                item = _invoke(t)
                if item is not None:
                    proposals.append(item)

        if not proposals:
            raise ModelGenerationError("All MoA proposers failed to generate a candidate.")

        proposals.sort(key=lambda p: (p.verification.passed, p.verification.r_total), reverse=True)
        advantages = self.verifier.grpo_group_advantages([p.verification.r_total for p in proposals])
        best = proposals[0]
        total_params_consulted = sum(p.total_params_b for p in proposals)

        # If we have multiple proposals and either multiple frontier nodes or defects to heal,
        # run a dedicated APEX Meta-Synthesizer pass.
        needs_synthesis = (len(proposals) >= 2 and (len(ordered_frontier) >= 1 or not best.verification.passed))
        if not needs_synthesis:
            return MoAOutcome(
                final_response=best.response,
                final_verification=best.verification,
                proposals=proposals,
                synthesizer_used=best.proposer_id,
                total_params_consulted_b=total_params_consulted,
                grpo_advantages=advantages,
            )

        synthesis_blocks = []
        for idx, prop in enumerate(proposals, start=1):
            diag = "; ".join(prop.verification.diagnostics[:4]) or "Clean deterministic verification"
            synthesis_blocks.append(
                f"=== CANDIDATE {idx} ({prop.role} | {prop.model} | R_total={prop.verification.r_total} | {diag}) ===\n"
                f"{prop.response[:3000]}"
            )

        synth_prompt = (
            "You are the CONCODE v4.0 APEX Meta-Synthesizer. Merge the strongest verified "
            "architectural and code elements from the candidates below into one superior, "
            "production-hardened final response. You MUST eliminate every listed compiler error, "
            "CWE security finding, or formal constraint violation.\n\n"
            f"Original Request:\n{user_prompt}\n\n"
            + "\n\n".join(synthesis_blocks)
        )

        try:
            synthesized = self.generate(
                system_prompt=system_prompt,
                user_prompt=synth_prompt,
                context=context,
                prefer_frontier=True,
                temperature=0.15,
            )
            synth_ver = self.verifier.verify_response(
                synthesized,
                formal_constraints=formal_constraints,
                require_reasoning_contract=True,
            )
            if synth_ver.r_total >= best.verification.r_total or (synth_ver.passed and not best.verification.passed):
                return MoAOutcome(
                    final_response=synthesized,
                    final_verification=synth_ver,
                    proposals=proposals,
                    synthesizer_used=(ordered_frontier[0].config.node_id if ordered_frontier else "local_eco_metal"),
                    total_params_consulted_b=total_params_consulted,
                    grpo_advantages=advantages,
                )
        except Exception as exc:
            logger.warning("MoA meta-synthesis skipped due to error: %s", exc)

        return MoAOutcome(
            final_response=best.response,
            final_verification=best.verification,
            proposals=proposals,
            synthesizer_used=best.proposer_id,
            total_params_consulted_b=total_params_consulted,
            grpo_advantages=advantages,
        )

    def status(self) -> Dict[str, Any]:
        total_b, active_b = self.total_mesh_capacity()
        return {
            "frontier_nodes_connected": len(self.nodes),
            "nodes": [c.config.to_public_dict() for c in self._ordered_nodes()],
            "local_eco_ready": bool(
                self.local_generator is not None and getattr(self.local_generator, "is_loaded", False)
            ),
            "aggregate_total_params_b": total_b,
            "max_active_params_b": active_b,
            "supported_catalog": FRONTIER_MOE_CATALOG,
        }
