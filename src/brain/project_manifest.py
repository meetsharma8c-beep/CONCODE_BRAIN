"""
CONCODE Neural Brain v4.0 APEX -- Cross-Project Manifest & Universal Prompt Engine

Decouples CONCODE Brain from single-application assumptions so any future startup,
microservice, mobile application, or AI platform can bind its domain invariants,
tech stack, and UI actions zero-shot at inference time without retraining weights.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("concode.manifest")


CONCODE_APEX_MASTER_PROMPT = """### ROLE AND UNIVERSAL IDENTITY
You are CONCODE_BRAIN v4.0 APEX, a Universal Cross-Project Foundation Reasoning Engine, Principal Systems Architect, and Formal Verification Co-Pilot. You power multiple production software systems, startups, developer platforms, and consumer applications.

### 1. DYNAMIC PROJECT ADAPTATION PROTOCOL
- Inspect any <project_manifest>, <workspace_context>, or <graph_rag_context> block supplied in context.
- Dynamically bind domain invariants, tech stack, currency/unit rules, and allowed [ACTION:...] tags to the active project with zero cross-project bleed.
- When no manifest is provided, operate in Universal Principal Architect Mode across Distributed Systems, Polyglot Full-Stack (Python, TypeScript, Go, Rust, SQL), Database Concurrency, Security Engineering, AI Systems, and Formal Verification.

### 2. MANDATORY TWO-PHASE STRUCTURED REASONING CONTRACT
Begin complex responses with an internal structured verification block before emitting visible headers or final output:

<concode_think>
<step>
Decode raw intent, active <project_manifest> constraints, scale requirements, and hidden edge cases.
</step>
<verify>
Audit for architectural bottlenecks, CWE security vulnerabilities (CWE-78, CWE-89, CWE-208, CWE-400, CWE-639, CWE-918), concurrency deadlocks, resource exhaustion, and mathematical/budget conflicts.
</verify>
<backtrack>
When verification detects any flaw, unsafe assumption, or formal counterexample, reject the naive path explicitly and formulate the hardened alternative.
</backtrack>
<step>
Synthesize the verified solution with production-ready code and clear Option A vs. Option B trade-offs.
</step>
</concode_think>

### 3. APPLICATION CONTROL HEADER
When operating inside an integrated application UI, emit one control header after </concode_think>:
[STATE:idle|excited|warning][ACTION:<allowed_action_or_none>]

### 4. ENGINEERING RIGOR AND DECISION PROTOCOL
- Never fabricate APIs, test results, live availability, or unverified benchmark claims.
- Present high-impact architectural decisions as Option A (Immediate Pragmatic Path) vs. Option B (High-Scale / Hardened Path) with explicit latency, cost, and failure-mode trade-offs.
- Treat every pinned invariant in <project_manifest> and <graph_rag_context> as non-negotiable."""


@dataclass
class ProjectManifest:
    """Declarative specification binding CONCODE Brain to any target project."""

    project_id: str
    project_name: str
    assistant_persona: str
    domain_type: str
    tech_stack: List[str] = field(default_factory=list)
    critical_invariants: List[str] = field(default_factory=list)
    supported_ui_actions: List[str] = field(default_factory=lambda: ["none"])
    preferred_compute_tier: str = "auto"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectManifest":
        return cls(
            project_id=str(data["project_id"]).strip().lower().replace(" ", "_"),
            project_name=str(data.get("project_name", data["project_id"])),
            assistant_persona=str(data.get("assistant_persona", "CONCODE_BRAIN")),
            domain_type=str(data.get("domain_type", "universal-systems")),
            tech_stack=[str(x) for x in data.get("tech_stack", [])],
            critical_invariants=[str(x) for x in data.get("critical_invariants", [])],
            supported_ui_actions=[str(x) for x in data.get("supported_ui_actions", ["none"])],
            preferred_compute_tier=str(data.get("preferred_compute_tier", "auto")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class WorkspaceGraphSnippet:
    """Code or schema excerpt injected inside <workspace_context>."""

    file_path: str
    symbol_type: str
    content: str


DEFAULT_PROJECT_MANIFESTS: Dict[str, ProjectManifest] = {
    "universal": ProjectManifest(
        project_id="universal",
        project_name="Universal Software Architecture",
        assistant_persona="CONCODE_BRAIN v4.0 APEX",
        domain_type="universal-systems",
        tech_stack=["Python", "TypeScript", "Go", "Rust", "SQL", "Kubernetes"],
        critical_invariants=[
            "Analyze first-principles failure modes before emitting code.",
            "Audit all boundaries for OWASP Top 10, CWE vulnerabilities, and concurrency races.",
            "Structure architectural decisions using Option A vs. Option B trade-offs.",
        ],
        supported_ui_actions=["none", "code_diff", "security_alert", "arch_preview"],
    ),
    "tripverse": ProjectManifest(
        project_id="tripverse",
        project_name="TripVerse (trip-verse.com)",
        assistant_persona="CONCODE Travel Co-Pilot",
        domain_type="travel-concierge",
        tech_stack=[
            "React 19",
            "TypeScript",
            "Tailwind CSS",
            "Supabase PostgreSQL",
            "Leaflet",
            "Capacitor",
            "Three.js",
        ],
        critical_invariants=[
            "All budgets must be reconciled exactly in integer currency units per traveler and group.",
            "Enforce life-safety high-altitude acclimatization (>3,000m ascent requires rest buffer).",
            "Warn and backtrack on monsoon landslide corridors, fatigue hazards (>450 km/day), and severe weather.",
            "Distinguish mountain/remote destinations from their nearest rail/airport transit hubs.",
        ],
        supported_ui_actions=["none", "route_preview", "budget_split", "weather_alert", "lock_day", "safety_block"],
    ),
    "nexus_fintech": ProjectManifest(
        project_id="nexus_fintech",
        project_name="NexusPay Multi-Tenant Ledger Engine",
        assistant_persona="CONCODE Sentinel",
        domain_type="fintech-saas",
        tech_stack=["Go 1.24", "PostgreSQL 17", "Redis 7", "Next.js 15", "Kafka", "Docker"],
        critical_invariants=[
            "Never use IEEE-754 floats for monetary math; enforce 64-bit integer minor units.",
            "All SQL mutations must bind tenant_id via composite WHERE or transaction-local RLS.",
            "All payment webhooks require atomic ON CONFLICT idempotency keys and constant-time HMAC.",
            "Outbound webhook requests must enforce DNS-resolved SSRF egress guards (CWE-918).",
        ],
        supported_ui_actions=["none", "audit_lock", "tenant_isolation", "db_triage", "security_block"],
    ),
    "devtools_ide": ProjectManifest(
        project_id="devtools_ide",
        project_name="Autonomous AI Coding and Agent IDE",
        assistant_persona="CONCODE Architect",
        domain_type="devtools-ide",
        tech_stack=["Rust", "Tauri", "TypeScript", "WebAssembly", "pgvector", "vLLM"],
        critical_invariants=[
            "Never execute raw shell commands outside isolated sandbox capability boundaries.",
            "All automated code edits must pass AST syntax and unit test verification before commit.",
            "In-memory vector indices must enforce bounded capacity and TTL eviction.",
        ],
        supported_ui_actions=["none", "ast_diff", "compile_check", "sandbox_exec", "pr_review"],
    ),
}


class ProjectManifestRegistry:
    """
    Persistent registry of ProjectManifest specifications enabling zero-shot
    adaptation of CONCODE Brain across unlimited future projects.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._manifests: Dict[str, ProjectManifest] = {
            k: ProjectManifest.from_dict(v.to_dict())
            for k, v in DEFAULT_PROJECT_MANIFESTS.items()
        }
        self._load()

    def _load(self) -> None:
        if not self.storage_path or not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            if isinstance(raw, dict):
                for key, item in raw.items():
                    if isinstance(item, dict) and "project_id" in item:
                        manifest = ProjectManifest.from_dict(item)
                        self._manifests[manifest.project_id] = manifest
            logger.info("Loaded %d project manifests from %s", len(self._manifests), self.storage_path)
        except Exception as exc:
            logger.warning("Failed to load project manifests: %s", exc)

    def _save(self) -> None:
        if not self.storage_path:
            return
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {k: v.to_dict() for k, v in self._manifests.items()}
            with open(self.storage_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Failed to persist project manifests: %s", exc)

    def register(self, manifest: ProjectManifest) -> ProjectManifest:
        """Register or update a project manifest and persist to disk."""
        clean_id = manifest.project_id.strip().lower().replace(" ", "_")
        manifest.project_id = clean_id
        self._manifests[clean_id] = manifest
        self._save()
        return manifest

    def get(self, project_id: str) -> ProjectManifest:
        """Resolve a project manifest by ID, falling back to 'universal'."""
        key = (project_id or "universal").strip().lower()
        return self._manifests.get(key, self._manifests["universal"])

    def has(self, project_id: str) -> bool:
        return (project_id or "").strip().lower() in self._manifests

    def list_all(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._manifests.values()]

    @property
    def count(self) -> int:
        return len(self._manifests)


CONCODE_COMPACT_LOCAL_PROMPT = (
    "You are CONCODE v4.0 APEX, an expert software engineer and systems architect. "
    "Answer directly, accurately, and concisely. Write complete, runnable, security-hardened code "
    "inside fenced markdown code blocks (e.g. ```python ... ```). "
    "Avoid unsafe patterns (never use eval/exec, SQL string interpolation, shell=True, or == on secrets; "
    "use hmac.compare_digest for secret comparisons). "
    "Do not repeat these instructions."
)


def build_dynamic_system_context(
    manifest: ProjectManifest,
    graph_snippets: Optional[List[WorkspaceGraphSnippet]] = None,
    graph_rag_xml: str = "",
    guild_prompts: Optional[List[str]] = None,
    include_master_prompt: bool = True,
    compact: bool = False,
) -> str:
    """
    Assemble the complete zero-shot system prompt binding CONCODE v4.0 APEX to
    a specific project manifest, workspace context, GraphRAG invariants, and active guilds.
    When compact=True (local 7B Eco models), keeps context concise to avoid prompt echo
    and preserve context budget for code generation.
    """
    if compact:
        lines = [CONCODE_COMPACT_LOCAL_PROMPT]
        lines.append(f"Active Project: {manifest.project_name} ({manifest.domain_type})")
        if manifest.tech_stack:
            lines.append(f"Stack: {', '.join(manifest.tech_stack[:6])}")
        if manifest.critical_invariants:
            lines.append("Key rules: " + "; ".join(manifest.critical_invariants[:3]))
        if graph_snippets:
            lines.append("Open Workspace Files:")
            for snippet in graph_snippets[:3]:
                lines.append(f"--- {snippet.file_path} ---\n{snippet.content[:900]}")
        return "\n".join(lines)

    sections: List[str] = []
    if include_master_prompt:
        sections.append(CONCODE_APEX_MASTER_PROMPT)

    manifest_lines = [
        "<project_manifest>",
        f"  <project_id>{manifest.project_id}</project_id>",
        f"  <project_name>{manifest.project_name}</project_name>",
        f"  <assistant_persona>{manifest.assistant_persona} (CONCODE Universal Engine)</assistant_persona>",
        f"  <domain_type>{manifest.domain_type}</domain_type>",
        f"  <tech_stack>{', '.join(manifest.tech_stack)}</tech_stack>",
        "  <domain_invariants>",
    ]
    for inv in manifest.critical_invariants:
        manifest_lines.append(f"    - {inv}")
    manifest_lines.append("  </domain_invariants>")
    manifest_lines.append(f"  <allowed_ui_actions>{' | '.join(manifest.supported_ui_actions)}</allowed_ui_actions>")
    manifest_lines.append("</project_manifest>")
    sections.append("\n".join(manifest_lines))

    if graph_rag_xml:
        sections.append(graph_rag_xml.strip())

    if guild_prompts:
        guild_block = ["<active_expert_guilds>"]
        for gp in guild_prompts:
            if gp and gp.strip():
                guild_block.append(f"  - {gp.strip()}")
        guild_block.append("</active_expert_guilds>")
        sections.append("\n".join(guild_block))

    if graph_snippets:
        workspace_lines = ["<workspace_context>"]
        for snippet in graph_snippets:
            workspace_lines.append(
                f'  <file path="{snippet.file_path}" type="{snippet.symbol_type}">\n{snippet.content}\n  </file>'
            )
        workspace_lines.append("</workspace_context>")
        sections.append("\n".join(workspace_lines))

    return "\n\n".join(sections)
