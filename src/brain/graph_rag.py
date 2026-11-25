"""
CONCODE Neural Brain v4.0 APEX -- Lifelong Temporal Knowledge Graph and GraphRAG

Persistent directed multigraph with:
  1. Project-scoped and global entities (services, tables, APIs, invariants, hazards).
  2. Exponential temporal decay w(t) = w0 * exp(-lambda * (t - t0)) for episodic memory.
  3. Sticky pinning (pinned=True, lambda=0) for immutable security, financial, and safety invariants.
  4. k-hop BFS subgraph extraction and automated conflict detection for <graph_rag_context> injection.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("concode.graph_rag")


@dataclass
class KnowledgeNode:
    """Entity or invariant vertex inside CONCODE's lifelong knowledge graph."""

    node_id: str
    entity_type: str
    label: str
    project_id: str = "global"
    domain: str = "system_architecture"
    attributes: Dict[str, Any] = field(default_factory=dict)
    aliases: List[str] = field(default_factory=list)
    base_weight: float = 1.0
    decay_lambda: float = 0.0001
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    pinned: bool = False

    def current_weight(self, now: Optional[float] = None) -> float:
        if self.pinned:
            return self.base_weight
        current_time = now if now is not None else time.time()
        delta_t = max(0.0, current_time - self.last_accessed)
        return round(self.base_weight * math.exp(-self.decay_lambda * delta_t), 6)

    def touch(self, now: Optional[float] = None) -> None:
        self.last_accessed = now if now is not None else time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "entity_type": self.entity_type,
            "label": self.label,
            "project_id": self.project_id,
            "domain": self.domain,
            "attributes": self.attributes,
            "aliases": self.aliases,
            "base_weight": self.base_weight,
            "decay_lambda": self.decay_lambda,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeNode":
        return cls(
            node_id=data["node_id"],
            entity_type=data.get("entity_type", "Entity"),
            label=data.get("label", data["node_id"]),
            project_id=data.get("project_id", "global"),
            domain=data.get("domain", "system_architecture"),
            attributes=dict(data.get("attributes", {})),
            aliases=list(data.get("aliases", [])),
            base_weight=float(data.get("base_weight", 1.0)),
            decay_lambda=float(data.get("decay_lambda", 0.0001)),
            created_at=float(data.get("created_at", time.time())),
            last_accessed=float(data.get("last_accessed", time.time())),
            pinned=bool(data.get("pinned", False)),
        )


@dataclass
class KnowledgeEdge:
    """Directed weighted relation between two KnowledgeNodes."""

    source_id: str
    target_id: str
    relation: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    base_weight: float = 1.0
    decay_lambda: float = 0.0001
    created_at: float = field(default_factory=time.time)
    pinned: bool = False

    def current_weight(self, now: Optional[float] = None) -> float:
        if self.pinned:
            return self.base_weight
        current_time = now if now is not None else time.time()
        delta_t = max(0.0, current_time - self.created_at)
        return round(self.base_weight * math.exp(-self.decay_lambda * delta_t), 6)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "metadata": self.metadata,
            "base_weight": self.base_weight,
            "decay_lambda": self.decay_lambda,
            "created_at": self.created_at,
            "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeEdge":
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation=data["relation"],
            metadata=dict(data.get("metadata", {})),
            base_weight=float(data.get("base_weight", 1.0)),
            decay_lambda=float(data.get("decay_lambda", 0.0001)),
            created_at=float(data.get("created_at", time.time())),
            pinned=bool(data.get("pinned", False)),
        )


class LifelongGraphRAG:
    """
    Persistent temporal knowledge graph powering cross-project invariant lookup,
    k-hop context retrieval, and automatic violation detection.
    """

    def __init__(self, graph_path: Optional[Path] = None):
        self.graph_path = Path(graph_path) if graph_path else None
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: List[KnowledgeEdge] = []
        self._adjacency: Dict[str, List[KnowledgeEdge]] = {}
        self._reverse_adj: Dict[str, List[KnowledgeEdge]] = {}
        self._seed_core_invariants()
        self._load()

    def _seed_core_invariants(self) -> None:
        """Install immutable engineering and security axioms present across all projects."""
        core_nodes = [
            KnowledgeNode(
                node_id="inv_cwe_208_timing",
                entity_type="SecurityInvariant",
                label="Constant-Time Secret Comparison (CWE-208)",
                project_id="global",
                domain="security",
                attributes={
                    "rule": "Use hmac.compare_digest or crypto.timingSafeEqual for all token, HMAC, and signature checks.",
                    "anti_pattern": "Direct == comparison on secrets or HMAC digests",
                },
                aliases=["hmac", "signature", "token", "webhook", "auth", "secret", "timing", "cwe-208"],
                base_weight=1.0,
                pinned=True,
            ),
            KnowledgeNode(
                node_id="inv_cwe_639_idor",
                entity_type="SecurityInvariant",
                label="Multi-Tenant Isolation and IDOR Guard (CWE-639)",
                project_id="global",
                domain="security",
                attributes={
                    "rule": "Every database read/write must scope by authenticated tenant_id or user_id via RLS or composite WHERE.",
                    "anti_pattern": "Querying by primary record id alone without ownership predicate",
                },
                aliases=["tenant", "idor", "bola", "rls", "multi-tenant", "sql", "postgres", "cwe-639"],
                base_weight=1.0,
                pinned=True,
            ),
            KnowledgeNode(
                node_id="inv_cwe_918_ssrf",
                entity_type="SecurityInvariant",
                label="SSRF Egress Validation (CWE-918)",
                project_id="global",
                domain="security",
                attributes={
                    "rule": "Resolve DNS and reject RFC1918, loopback, link-local, and cloud metadata IPs before outbound fetch.",
                    "anti_pattern": "Direct fetch() or requests.get() on user-controlled URLs",
                },
                aliases=["ssrf", "webhook", "url", "fetch", "http", "proxy", "metadata", "cwe-918"],
                base_weight=1.0,
                pinned=True,
            ),
            KnowledgeNode(
                node_id="inv_distributed_lock_fencing",
                entity_type="ArchitectureInvariant",
                label="Distributed Lock Fencing Token and Atomic Release",
                project_id="global",
                domain="distributed_systems",
                attributes={
                    "rule": "Use monotonic fencing tokens and atomic Lua compare-and-delete when releasing leases.",
                    "anti_pattern": "Direct Redis DEL without owner token verification",
                },
                aliases=["redis", "lock", "lease", "raft", "consensus", "split-brain", "distributed", "deadlock"],
                base_weight=1.0,
                pinned=True,
            ),
            KnowledgeNode(
                node_id="inv_fintech_integer_math",
                entity_type="FinancialInvariant",
                label="Exact Integer Minor-Unit Ledger Arithmetic",
                project_id="global",
                domain="fintech",
                attributes={
                    "rule": "Represent currency in 64-bit integer paise/cents with atomic ON CONFLICT idempotency barriers.",
                    "anti_pattern": "IEEE-754 floating-point currency math or SELECT-then-INSERT race windows",
                },
                aliases=["payment", "ledger", "refund", "razorpay", "stripe", "budget", "fintech", "idempotency"],
                base_weight=1.0,
                pinned=True,
            ),
            KnowledgeNode(
                node_id="inv_travel_safety_altitude",
                entity_type="SafetyThreshold",
                label="High-Altitude Acclimatization and Transit Fatigue Guard",
                project_id="tripverse",
                domain="travel_logistics",
                attributes={
                    "rule": "Flag ascents above 3,000m without acclimatization rest and driving days above 450 km.",
                    "max_safe_drive_km_per_day": 450,
                    "ams_threshold_meters": 3000,
                },
                aliases=["leh", "ladakh", "spiti", "manali", "chandratal", "altitude", "monsoon", "road trip", "tripverse"],
                base_weight=1.0,
                pinned=True,
            ),
        ]
        for node in core_nodes:
            self.upsert_node(node, persist=False)

    def _load(self) -> None:
        if not self.graph_path or not self.graph_path.exists():
            return
        try:
            with open(self.graph_path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
            for item in raw.get("nodes", []):
                node = KnowledgeNode.from_dict(item)
                self.nodes[node.node_id] = node
            self.edges = []
            self._adjacency.clear()
            self._reverse_adj.clear()
            for item in raw.get("edges", []):
                self.add_edge(KnowledgeEdge.from_dict(item), persist=False)
            logger.info("Loaded LifelongGraphRAG (%d nodes, %d edges)", len(self.nodes), len(self.edges))
        except Exception as exc:
            logger.warning("Failed to load LifelongGraphRAG from %s: %s", self.graph_path, exc)

    def save(self) -> None:
        if not self.graph_path:
            return
        try:
            self.graph_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "edges": [e.to_dict() for e in self.edges],
            }
            with open(self.graph_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
        except Exception as exc:
            logger.warning("Failed to save LifelongGraphRAG: %s", exc)

    def upsert_node(self, node: KnowledgeNode, persist: bool = True) -> KnowledgeNode:
        self.nodes[node.node_id] = node
        if persist:
            self.save()
        return node

    def add_edge(self, edge: KnowledgeEdge, persist: bool = True) -> KnowledgeEdge:
        for existing in self._adjacency.get(edge.source_id, []):
            if existing.target_id == edge.target_id and existing.relation == edge.relation:
                return existing
        self.edges.append(edge)
        self._adjacency.setdefault(edge.source_id, []).append(edge)
        self._reverse_adj.setdefault(edge.target_id, []).append(edge)
        if persist:
            self.save()
        return edge

    def ingest_project_manifest(self, manifest_dict: Dict[str, Any]) -> int:
        """Bind a project manifest and its critical invariants as pinned nodes in the graph."""
        project_id = str(manifest_dict.get("project_id", "universal")).lower()
        project_name = str(manifest_dict.get("project_name", project_id))
        domain = str(manifest_dict.get("domain_type", "universal-systems"))
        tech_stack = [str(t) for t in manifest_dict.get("tech_stack", [])]

        root_id = f"proj_{project_id}"
        self.upsert_node(
            KnowledgeNode(
                node_id=root_id,
                entity_type="Project",
                label=project_name,
                project_id=project_id,
                domain=domain,
                attributes={"tech_stack": tech_stack},
                aliases=[project_id, project_name.lower()] + [t.lower() for t in tech_stack],
                base_weight=1.0,
                pinned=True,
            ),
            persist=False,
        )

        added = 1
        for idx, inv in enumerate(manifest_dict.get("critical_invariants", []), start=1):
            inv_id = f"inv_{project_id}_{idx}"
            tokens = [tok for tok in re.findall(r"[a-zA-Z0-9_-]{3,}", str(inv).lower())][:12]
            self.upsert_node(
                KnowledgeNode(
                    node_id=inv_id,
                    entity_type="ProjectInvariant",
                    label=f"{project_name} Invariant #{idx}",
                    project_id=project_id,
                    domain=domain,
                    attributes={"rule": str(inv)},
                    aliases=tokens + [project_id],
                    base_weight=1.0,
                    pinned=True,
                ),
                persist=False,
            )
            self.add_edge(
                KnowledgeEdge(
                    source_id=root_id,
                    target_id=inv_id,
                    relation="ENFORCES_INVARIANT",
                    pinned=True,
                ),
                persist=False,
            )
            added += 1

        self.save()
        return added

    def record_verified_insight(
        self,
        project_id: str,
        label: str,
        summary: str,
        tags: Optional[List[str]] = None,
        pinned: bool = False,
    ) -> KnowledgeNode:
        """Store a newly verified architectural or debugging insight in lifelong memory."""
        slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")[:40]
        node_id = f"insight_{project_id}_{slug}_{int(time.time()) % 10000}"
        node = KnowledgeNode(
            node_id=node_id,
            entity_type="VerifiedInsight",
            label=label[:140],
            project_id=project_id,
            domain="episodic_knowledge",
            attributes={"summary": summary[:600]},
            aliases=[t.lower() for t in (tags or [])] + re.findall(r"[a-z0-9_-]{3,}", label.lower())[:10],
            base_weight=0.95,
            decay_lambda=0.0 if pinned else 0.00005,
            pinned=pinned,
        )
        self.upsert_node(node, persist=False)
        root_id = f"proj_{project_id}"
        if root_id in self.nodes:
            self.add_edge(
                KnowledgeEdge(source_id=root_id, target_id=node_id, relation="LEARNED_INSIGHT", pinned=pinned),
                persist=False,
            )
        self.save()
        return node

    def retrieve_subgraph(
        self,
        query: str,
        project_id: str = "universal",
        k_hops: int = 2,
        top_k: int = 8,
        min_weight: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Perform lexical + alias seed matching followed by k-hop BFS traversal,
        filtering decayed nodes while always honoring pinned project invariants.
        """
        now = time.time()
        query_lower = query.lower()
        query_tokens = set(re.findall(r"[a-z0-9_-]{3,}", query_lower))
        norm_project = (project_id or "universal").lower()

        scored_seeds: List[Tuple[float, KnowledgeNode]] = []
        for node in self.nodes.values():
            if node.project_id not in ("global", norm_project):
                continue
            weight = node.current_weight(now)
            if weight < min_weight:
                continue

            hit_score = 0.0
            if node.project_id == norm_project and node.pinned:
                hit_score += 0.35
            for alias in node.aliases:
                al = alias.lower()
                if al in query_lower:
                    hit_score += 0.45
                elif al in query_tokens:
                    hit_score += 0.30
            label_tokens = set(re.findall(r"[a-z0-9_-]{3,}", node.label.lower()))
            overlap = len(query_tokens & label_tokens)
            if overlap:
                hit_score += 0.25 * overlap

            if hit_score > 0.0:
                scored_seeds.append((round(hit_score * weight, 4), node))

        scored_seeds.sort(key=lambda x: x[0], reverse=True)
        seed_nodes = [n for _, n in scored_seeds[:top_k]]

        visited_ids: Set[str] = set()
        collected_nodes: List[KnowledgeNode] = []
        collected_edges: List[KnowledgeEdge] = []
        queue: deque[Tuple[str, int]] = deque()

        for seed in seed_nodes:
            seed.touch(now)
            visited_ids.add(seed.node_id)
            collected_nodes.append(seed)
            queue.append((seed.node_id, 0))

        while queue and len(collected_nodes) < top_k * 2:
            curr_id, depth = queue.popleft()
            if depth >= k_hops:
                continue
            neighbors = self._adjacency.get(curr_id, []) + self._reverse_adj.get(curr_id, [])
            for edge in neighbors:
                if edge.current_weight(now) < min_weight:
                    continue
                next_id = edge.target_id if edge.source_id == curr_id else edge.source_id
                next_node = self.nodes.get(next_id)
                if not next_node or next_node.project_id not in ("global", norm_project):
                    continue
                collected_edges.append(edge)
                if next_id not in visited_ids:
                    visited_ids.add(next_id)
                    collected_nodes.append(next_node)
                    queue.append((next_id, depth + 1))

        return {
            "nodes": [
                {
                    "node_id": n.node_id,
                    "entity_type": n.entity_type,
                    "label": n.label,
                    "project_id": n.project_id,
                    "pinned": n.pinned,
                    "weight": n.current_weight(now),
                    "attributes": n.attributes,
                }
                for n in collected_nodes[: top_k * 2]
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "relation": e.relation,
                    "target": e.target_id,
                }
                for e in collected_edges[: top_k * 2]
            ],
        }

    def format_graph_rag_context(self, query: str, project_id: str = "universal", top_k: int = 6) -> Tuple[str, int]:
        """Render the retrieved k-hop subgraph as <graph_rag_context> XML for prompt injection."""
        subgraph = self.retrieve_subgraph(query=query, project_id=project_id, top_k=top_k)
        nodes = subgraph["nodes"]
        if not nodes:
            return "", 0

        lines = ["<graph_rag_context>"]
        for item in nodes:
            pin_tag = "PINNED" if item["pinned"] else f"w={item['weight']}"
            rule = item["attributes"].get("rule") or item["attributes"].get("summary") or json.dumps(item["attributes"])
            lines.append(f'  <node type="{item["entity_type"]}" status="{pin_tag}" label="{item["label"]}">{rule}</node>')
        for edge in subgraph["edges"][:8]:
            lines.append(f'  <relation>{edge["source"]} --[{edge["relation"]}]--> {edge["target"]}</relation>')
        lines.append("</graph_rag_context>")
        return "\n".join(lines), len(nodes)

    def stats(self) -> Dict[str, Any]:
        pinned_count = sum(1 for n in self.nodes.values() if n.pinned)
        return {
            "total_nodes": len(self.nodes),
            "pinned_invariants": pinned_count,
            "total_edges": len(self.edges),
        }
