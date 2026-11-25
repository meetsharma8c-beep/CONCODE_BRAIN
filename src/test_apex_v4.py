"""Unit and integration tests for CONCODE Neural Brain v4.0 APEX Frontier subsystems."""

import tempfile
import unittest
from pathlib import Path

from src.brain.apex_reasoner import (
    ApexCognitiveEngine,
    LiveMCTSEngine,
    System3MetacognitiveMonitor,
)
from src.brain.evolution import EvolutionHarvester
from src.brain.formal_verifier import FormalVerifier
from src.brain.frontier_mesh import (
    MODE_APEX_MCTS,
    MODE_APEX_MOA_SWARM,
    MODE_REFLEX_O1,
    FrontierMoEMesh,
    FrontierNodeConfig,
)
from src.brain.graph_rag import KnowledgeNode, LifelongGraphRAG
from src.brain.memory import CognitiveMemoryManager
from src.brain.project_manifest import (
    ProjectManifest,
    ProjectManifestRegistry,
    build_dynamic_system_context,
)


class _StubSequenceGenerator:
    """Deterministic generator returning a scripted sequence of responses for testing."""

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []
        self.is_loaded = True
        self.model_path = "stub_frontier_moe"

    def generate(self, system_prompt, user_prompt, context="", history=None):
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if self.outputs:
            return self.outputs.pop(0)
        return self.calls[-1]["user_prompt"]


class ApexV4FrontierTests(unittest.TestCase):
    def test_project_manifest_registry_persistence_and_xml_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            reg_path = Path(tmp) / "manifests.json"
            reg = ProjectManifestRegistry(storage_path=reg_path)
            self.assertTrue(reg.has("tripverse"))
            self.assertTrue(reg.has("nexus_fintech"))

            custom = ProjectManifest(
                project_id="carepulse_ai",
                project_name="CarePulse Clinical AI",
                assistant_persona="CarePulse Copilot",
                domain_type="healthtech",
                tech_stack=["Python FastAPI", "PostgreSQL", "FHIR"],
                critical_invariants=["Scrub all PHI before logging (HIPAA)."],
                supported_ui_actions=["none", "hipaa_lock"],
            )
            reg.register(custom)

            # Reload from disk to verify persistence
            reg2 = ProjectManifestRegistry(storage_path=reg_path)
            loaded = reg2.get("carepulse_ai")
            self.assertEqual(loaded.project_name, "CarePulse Clinical AI")
            xml = build_dynamic_system_context(loaded)
            self.assertIn("<project_id>carepulse_ai</project_id>", xml)
            self.assertIn("Scrub all PHI before logging (HIPAA).", xml)

    def test_lifelong_graph_rag_decay_pinning_and_subgraph_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph_path = Path(tmp) / "graph.json"
            graph = LifelongGraphRAG(graph_path=graph_path)
            graph.ingest_project_manifest(
                {
                    "project_id": "carepulse_ai",
                    "project_name": "CarePulse Clinical AI",
                    "domain_type": "healthtech",
                    "tech_stack": ["FastAPI", "PostgreSQL"],
                    "critical_invariants": ["Always verify HIPAA PHI redaction on webhook logs."],
                }
            )
            ephemeral = KnowledgeNode(
                node_id="temp_session_note",
                entity_type="SessionNote",
                label="Temporary Webhook Note",
                project_id="carepulse_ai",
                aliases=["webhook"],
                base_weight=1.0,
                decay_lambda=0.01,
                created_at=1000.0,
                last_accessed=1000.0,
                pinned=False,
            )
            graph.upsert_node(ephemeral)

            # Pinned invariants never decay; ephemeral node decays sharply after 500s
            self.assertEqual(graph.nodes["inv_cwe_208_timing"].current_weight(now=9999999.0), 1.0)
            self.assertLess(ephemeral.current_weight(now=2000.0), 0.01)

            xml, count = graph.format_graph_rag_context(
                query="Implement HIPAA webhook signature verification",
                project_id="carepulse_ai",
            )
            self.assertGreaterEqual(count, 2)
            self.assertIn("<graph_rag_context>", xml)
            self.assertIn("CWE-208", xml)

    def test_formal_verifier_smt_deadlock_security_and_grpo(self):
        verifier = FormalVerifier()

        # 1. SAT allocation witness
        allocs = [("stay", 8000, 14000), ("transport", 9000, 15000), ("food", 5000, 8000)]
        sat = verifier.verify_linear_allocations(25000, allocs)
        self.assertTrue(sat.is_satisfiable)
        self.assertEqual(sat.status, "PROVEN_SAT")
        self.assertLessEqual(sum(sat.witness.values()), 25000)

        # 2. UNSAT conflict core
        unsat = verifier.verify_linear_allocations(18000, allocs)
        self.assertFalse(unsat.is_satisfiable)
        self.assertEqual(unsat.status, "UNSAT_CONFLICT")
        self.assertTrue(len(unsat.unsat_core) >= 2)

        # 3. Deadlock cycle detection vs acyclic DAG
        dl = verifier.verify_deadlock_freedom(
            [("Thread_A", "Lock_2"), ("Lock_2", "Thread_B"), ("Thread_B", "Lock_1"), ("Lock_1", "Thread_A")]
        )
        self.assertFalse(dl.is_satisfiable)
        self.assertIn("Deadlock cycle proven", dl.remediation_guidance)

        dag = verifier.verify_deadlock_freedom([("Thread_A", "Lock_1"), ("Thread_B", "Lock_2")])
        self.assertTrue(dag.is_satisfiable)

        # 4. Security taint audit catches CWE-208 and CWE-94
        bad_code = (
            "```python\n"
            "def check(signature, expected):\n"
            "    if signature == expected:\n"
            "        return eval('1+1')\n"
            "```\n"
        )
        bad_report = verifier.verify_response(bad_code)
        self.assertFalse(bad_report.passed)
        cwe_ids = {f.cwe_id for f in bad_report.security_findings}
        self.assertIn("CWE-208", cwe_ids)
        self.assertIn("CWE-94", cwe_ids)

        # 5. Clean verified response passes
        good_resp = (
            "<concode_think>\n<step>Use hmac.compare_digest.</step>\n"
            "<verify>Constant-time check eliminates CWE-208.</verify>\n</concode_think>\n"
            "```python\nimport hmac\ndef check(signature: str, expected: str) -> bool:\n"
            "    return hmac.compare_digest(signature, expected)\n```\n"
        )
        good_report = verifier.verify_response(good_resp, require_reasoning_contract=True)
        self.assertTrue(good_report.passed)
        self.assertGreaterEqual(good_report.r_total, 0.95)

        # 6. GRPO group advantage normalization sums to ~0
        adv = verifier.grpo_group_advantages([0.4, 0.95, 0.75])
        self.assertEqual(len(adv), 3)
        self.assertAlmostEqual(sum(adv), 0.0, places=4)
        self.assertGreater(adv[1], adv[0])

    def test_system3_metacognition_detects_semantic_cycle_stall(self):
        monitor = System3MetacognitiveMonitor(cycle_similarity_threshold=0.90, stall_epsilon=0.02)
        stalled1, _, _ = monitor.observe_step("Use standard retry loop with lock acquisition on table orders", 0.60)
        self.assertFalse(stalled1)
        stalled2, sim, dv = monitor.observe_step("Use standard retry loop with lock acquisition on table orders", 0.60)
        self.assertTrue(stalled2)
        self.assertGreaterEqual(sim, 0.95)
        self.assertEqual(dv, 0.0)
        self.assertEqual(monitor.telemetry.forced_backtracks, 1)

    def test_live_mcts_backtracks_and_heals_vulnerable_candidate(self):
        bad_first = (
            "<concode_think><step>Compare token directly.</step><verify>Quick check.</verify></concode_think>\n"
            "```python\ndef auth(api_key, secret_token):\n    return api_key == secret_token\n```\n"
        )
        healed_second = (
            "<concode_think><step>Use constant-time comparison.</step>"
            "<verify>Check CWE-208 timing side-channel.</verify>"
            "<backtrack>Rejected == comparison; switched to hmac.compare_digest.</backtrack></concode_think>\n"
            "Option A: Constant-time HMAC verification.\nOption B: Asymmetric Ed25519 signature verification.\n"
            "```python\nimport hmac\ndef auth(api_key: str, secret_token: str) -> bool:\n"
            "    return hmac.compare_digest(api_key, secret_token)\n```\n"
        )
        stub = _StubSequenceGenerator([bad_first, healed_second])
        verifier = FormalVerifier()
        mesh = FrontierMoEMesh(local_generator=stub, verifier=verifier)
        mcts = LiveMCTSEngine(mesh=mesh, verifier=verifier)

        outcome = mcts.search(
            system_prompt="You are CONCODE APEX.",
            user_prompt="Write a timing-safe API key comparator in Python.",
            max_rollouts=3,
        )
        self.assertTrue(outcome.best_verification.passed)
        self.assertEqual(outcome.backtracks_performed, 1)
        self.assertIn("hmac.compare_digest", outcome.best_response)
        self.assertIsNotNone(outcome.rejected_candidate)
        self.assertIn("CWE-208", stub.calls[1]["user_prompt"])

    def test_frontier_mesh_mod_routing_and_moa_synthesis_end_to_end(self):
        weak_prop = (
            "```python\ndef verify_sig(signature, expected):\n    return signature == expected\n```\n"
        )
        strong_prop = (
            "<concode_think><step>Analyze HMAC timing.</step><verify>No CWE-208.</verify></concode_think>\n"
            "```python\nimport hmac\ndef verify_sig(signature: str, expected: str) -> bool:\n"
            "    return hmac.compare_digest(signature, expected)\n```\n"
        )
        synthesized = (
            "<concode_think><step>Fuse best security proposal.</step>"
            "<verify>Zero CWE findings; compiles cleanly.</verify></concode_think>\n"
            "[STATE:excited][ACTION:security_block]\n"
            "Option A: `hmac.compare_digest` with UTF-8 encoding.\n"
            "Option B: Mutual TLS client certificates for service-to-service auth.\n"
            "```python\nimport hmac\ndef verify_sig(signature: str, expected: str) -> bool:\n"
            "    return hmac.compare_digest(signature.encode('utf-8'), expected.encode('utf-8'))\n```\n"
        )
        stub = _StubSequenceGenerator([weak_prop, strong_prop, synthesized])

        with tempfile.TemporaryDirectory() as tmp:
            reg = ProjectManifestRegistry(storage_path=Path(tmp) / "manifests.json")
            graph = LifelongGraphRAG(graph_path=Path(tmp) / "graph.json")
            verifier = FormalVerifier()
            mesh = FrontierMoEMesh(local_generator=stub, verifier=verifier)
            harvester = EvolutionHarvester(
                trajectories_path=Path(tmp) / "trajs.jsonl",
                dpo_path=Path(tmp) / "dpo.jsonl",
            )
            memory = CognitiveMemoryManager(episodic_path=Path(tmp) / "episodes.jsonl")

            # Verify MoD routing escalation logic
            mod_low = mesh.route_mod(goal="hello")
            self.assertEqual(mod_low.compute_mode, MODE_REFLEX_O1)
            mod_high = mesh.route_mod(
                goal="Architect a deadlock-free distributed fintech ledger with CWE-208 HMAC verification and formal proof",
                active_guilds=["system_architect", "security", "database"],
                has_formal_constraints=True,
            )
            self.assertEqual(mod_high.compute_mode, MODE_APEX_MOA_SWARM)

            # Verify dynamic 1T+ Frontier MoE node registration validates HTTPS/localhost
            ok = mesh.register_node(
                FrontierNodeConfig(
                    node_id="kimi_k2_1t",
                    base_url="https://api.example-moe.ai/v1",
                    model="moonshotai/Kimi-K2-Instruct",
                    api_key="test-token-12345",
                    total_params_b=1000,
                    active_params_b=32,
                )
            )
            self.assertTrue(ok)
            total_b, active_b = mesh.total_mesh_capacity()
            self.assertEqual(total_b, 1007)
            self.assertEqual(active_b, 32)
            # Clear external mock node before local stub MoA run
            mesh.nodes.clear()

            engine = ApexCognitiveEngine(
                manifest_registry=reg,
                graph_rag=graph,
                frontier_mesh=mesh,
                formal_verifier=verifier,
                evolution_harvester=harvester,
                cognitive_memory=memory,
            )
            outcome = engine.solve(
                goal="Harden webhook signature verification against CWE-208 timing leaks",
                project_id="nexus_fintech",
                compute_mode="apex_moa",
                formal_constraints={
                    "lock_edges": [("WorkerA", "Lock1"), ("WorkerB", "Lock2")],
                },
            )
            self.assertTrue(outcome.success)
            self.assertEqual(outcome.project_id, "nexus_fintech")
            self.assertGreaterEqual(outcome.graph_rag_nodes_used, 1)
            self.assertEqual(len(outcome.moa_proposals), 2)
            self.assertTrue(outcome.harvested_to_flywheel)
            self.assertEqual(harvester.trajectory_count, 1)
            self.assertEqual(harvester.dpo_count, 1)
            self.assertEqual(outcome.formal_proofs[0]["status"], "PROVEN_SAT")


if __name__ == "__main__":
    unittest.main()
