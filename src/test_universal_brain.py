"""Unit tests for the Universal Cognitive Evolution v3.0 subsystems (Phases 1-5)."""

import json
import tempfile
import unittest
from pathlib import Path

from src.brain.evolution import EvolutionHarvester
from src.brain.intent import IntentClassifier
from src.brain.memory import CognitiveMemoryManager
from src.brain.planner import ExecutionPlan, ExecutivePlanner, PlanTask
from src.brain.router import (
    TIER_1_REFLEX,
    TIER_2_DEEP_LOCAL,
    TIER_3_FRONTIER,
    HybridComputeRouter,
)
from src.brain.sandbox import SandboxPolicy, SandboxedExecutor
from src.brain.swarm import CriticAuditor, MultiGuildSwarm
from src.brain.tools import (
    PERM_EXTERNAL_NETWORK,
    PERM_READ_ONLY,
    PERM_SANDBOX_EXEC,
    PERM_WORKSPACE_WRITE,
    UniversalToolBus,
)
from src.config import GUILDS_YAML, INTENT_MODEL_DIR


class _ScriptedGenerator:
    def __init__(self, responses, loaded=True, fail=False):
        self.responses = iter(responses)
        self.is_loaded = loaded
        self.fail = fail

    def generate(self, **_kwargs):
        if self.fail:
            raise RuntimeError("Primary generator simulated failure")
        return next(self.responses)


class UniversalBrainEvolutionTests(unittest.TestCase):
    # ── Phase 1: Executive Meta-Planner & DAG Validation ──────────
    def test_planner_decomposes_goal_into_valid_dag_and_backtracks(self):
        planner = ExecutivePlanner()
        plan = planner.decompose(
            goal="1. Design the database schema\n2. Implement the FastAPI endpoint\n3. Add unit tests",
            workspace_files={"app.py": "pass\n", "models.py": "pass\n", "test_app.py": "pass\n"},
        )
        valid, err = plan.validate_dag()
        self.assertTrue(valid, err)
        self.assertGreaterEqual(len(plan.tasks), 3)

        # Only the root task should be ready initially
        ready = plan.ready_tasks()
        self.assertEqual(len(ready), 1)
        root_id = ready[0].id
        plan.mark_executing(root_id)

        # Simulate a recoverable failure that triggers BACKTRACKING
        can_retry = plan.mark_failed(root_id, "Temporary failure", max_attempts=2)
        self.assertTrue(can_retry)
        self.assertEqual(plan.state, "BACKTRACKING")
        self.assertEqual(plan.ready_tasks()[0].id, root_id)

        # Complete the root task and verify downstream task unlocks
        plan.mark_executing(root_id)
        plan.mark_completed(root_id, "Analysis complete")
        next_ready = plan.ready_tasks()
        self.assertEqual(len(next_ready), 1)
        self.assertNotEqual(next_ready[0].id, root_id)

    def test_planner_detects_dependency_cycles(self):
        cyclic_plan = ExecutionPlan(
            goal="Cyclic test",
            tasks=[
                PlanTask(id="a", title="A", description="A", guild="fullstack", dependencies=["b"]),
                PlanTask(id="b", title="B", description="B", guild="fullstack", dependencies=["a"]),
            ],
        )
        valid, err = cyclic_plan.validate_dag()
        self.assertFalse(valid)
        self.assertIn("Cycle", err)

    # ── Phase 2: Universal Tool Bus & Sandboxed Executor ─────────
    def test_tool_bus_permissions_math_ast_and_mcp_registration(self):
        bus = UniversalToolBus(granted_permissions={PERM_READ_ONLY})

        # Safe AST math evaluation
        math_res = bus.invoke("math_evaluate", expression="sqrt(144) + factorial(5)")
        self.assertTrue(math_res.success)
        self.assertEqual(math_res.output["result"], 132.0)

        # AST inspection of Python workspace
        ast_res = bus.invoke(
            "ast_inspect",
            workspace_files={"service.py": "import os\nclass Engine:\n    def run(self):\n        return 1\n"},
        )
        self.assertTrue(ast_res.success)
        self.assertEqual(ast_res.output["files"]["service.py"]["classes"], ["Engine"])
        self.assertEqual(ast_res.output["files"]["service.py"]["functions"], ["run"])

        # Sandbox tool should be denied when PERM_SANDBOX_EXEC is not granted
        denied = bus.invoke("sandbox_run", code="print(2 + 2)", language="python")
        self.assertFalse(denied.success)
        self.assertIn("Permission denied", denied.error)

        # Register and invoke an MCP tool after granting permission
        bus.granted_permissions.add(PERM_EXTERNAL_NETWORK)
        mcp_name = bus.register_mcp_tool(
            server_name="weather",
            tool_name="forecast",
            description="Get weather forecast",
            handler=lambda city="Tokyo": {"city": city, "temp_c": 22},
        )
        mcp_res = bus.invoke(mcp_name, city="Kyoto")
        self.assertTrue(mcp_res.success)
        self.assertEqual(mcp_res.output["city"], "Kyoto")

        # SSRF protection on web_fetch should block localhost/private IPs
        ssrf_res = bus.invoke("web_fetch", url="http://127.0.0.1:8000/health")
        self.assertFalse(ssrf_res.success)
        self.assertIn("Blocked unsafe or private URL", ssrf_res.error)

        # git_status_diff should succeed on the workspace repository
        git_res = bus.invoke("git_status_diff")
        self.assertTrue(git_res.success)
        self.assertIn("status", git_res.output)

        # filesystem_transaction should commit valid writes and rollback on path traversal
        bus.granted_permissions.add(PERM_WORKSPACE_WRITE)
        with tempfile.TemporaryDirectory() as tmp:
            tx_ok = bus.invoke(
                "filesystem_transaction",
                target_dir=tmp,
                files={"sub/hello.txt": "world\n"},
            )
            self.assertTrue(tx_ok.success)
            self.assertEqual((Path(tmp) / "sub" / "hello.txt").read_text(), "world\n")

            tx_bad = bus.invoke(
                "filesystem_transaction",
                target_dir=tmp,
                files={"sub/hello.txt": "corrupted\n", "../escape.txt": "hack\n"},
            )
            self.assertFalse(tx_bad.success)
            # Verify rollback preserved original content
            self.assertEqual((Path(tmp) / "sub" / "hello.txt").read_text(), "world\n")

    def test_sandbox_executes_isolated_python_and_workspace_unittest(self):
        executor = SandboxedExecutor(SandboxPolicy(allow_execution=True, timeout_seconds=4.0))
        snippet_res = executor.run_snippet("print(6 * 7)", language="python")
        self.assertTrue(snippet_res.passed)
        self.assertEqual(snippet_res.stdout.strip(), "42")

        ws = {
            "calc.py": "def multiply(a, b):\n    return a * b\n",
            "test_calc.py": (
                "import unittest\n"
                "from calc import multiply\n"
                "class CalcTest(unittest.TestCase):\n"
                "    def test_multiply(self):\n"
                "        self.assertEqual(multiply(3, 4), 12)\n"
            ),
        }
        test_results = executor.verify_workspace_tests(ws)
        self.assertEqual(len(test_results), 1)
        self.assertTrue(test_results[0].passed)

    # ── Phase 3: Multi-Guild Swarm & Adversarial Critic Gate ─────
    def test_multi_guild_prediction_and_critic_security_audit(self):
        classifier = IntentClassifier(
            model_dir=str(INTENT_MODEL_DIR),
            guilds_yaml=str(GUILDS_YAML),
        )
        multi = classifier.predict_multi(
            "Design a distributed consensus architecture with cap theorem and raft",
            top_k=3,
        )
        guild_names = [g for g, _ in multi]
        self.assertIn("system_architect", guild_names)

        # Critic should flag hardcoded API keys
        from src.brain.agent import AgentEdit, VerificationResult

        critic = CriticAuditor()
        bad_edit = AgentEdit(
            path="config.py",
            content='API_KEY = "sk_live_1234567890abcdef123456"\n',
            reason="Add key",
        )
        report = critic.audit(
            edits=[bad_edit],
            verification=[VerificationResult("config.py", "passed", "Python syntax parsed.")],
            sandbox_results=[],
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("Security" in issue for issue in report.issues))

    def test_swarm_executes_workspace_task_with_sandbox_and_critic(self):
        decision_json = json.dumps({
            "summary": "Implemented safe fibonacci function.",
            "plan": ["Implement fib", "Verify syntax and unit tests"],
            "edits": [{
                "path": "fib.py",
                "content": "def fib(n: int) -> int:\n    return n if n <= 1 else fib(n - 1) + fib(n - 2)\n",
                "reason": "Implement recursive fibonacci.",
            }],
            "needs_user_input": False,
            "question": None,
        })
        gen = _ScriptedGenerator([decision_json])
        sandbox = SandboxedExecutor(SandboxPolicy(allow_execution=True, timeout_seconds=4.0))
        bus = UniversalToolBus(sandbox_executor=sandbox, granted_permissions={PERM_READ_ONLY, PERM_SANDBOX_EXEC})
        swarm = MultiGuildSwarm(
            intent_classifier=None,
            guilds_data={"fullstack": {"system_prompt": "Write clean code."}},
            generator=gen,
            tool_bus=bus,
            sandbox_executor=sandbox,
        )

        outcome = swarm.execute(
            goal="Implement fib(n) and calculate: 10 + 5",
            workspace_files={
                "fib.py": "def fib(n):\n    return 0\n",
                "test_fib.py": (
                    "import unittest\n"
                    "from fib import fib\n"
                    "class FibTests(unittest.TestCase):\n"
                    "    def test_fib_five(self):\n"
                    "        self.assertEqual(fib(5), 5)\n"
                ),
            },
            enable_sandbox=True,
        )
        self.assertTrue(outcome.success)
        self.assertTrue(outcome.critic_report.passed)
        self.assertEqual(len(outcome.sandbox_results), 1)
        self.assertTrue(outcome.sandbox_results[0]["passed"])
        # Verify math_evaluate and ast_inspect tools were both invoked automatically
        invoked_tools = {t["tool_name"] for t in outcome.tool_results}
        self.assertIn("ast_inspect", invoked_tools)
        self.assertIn("math_evaluate", invoked_tools)

    # ── Phase 4: Persistent Episodic & Incremental Memory ────────
    def test_episodic_memory_recall_and_incremental_indexing_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem_path = Path(tmp) / "episodes.jsonl"
            mem = CognitiveMemoryManager(episodic_path=mem_path, vault_dir=Path(tmp))
            mem.record_episode(
                goal="Implement JWT token authentication middleware in FastAPI",
                guilds=["security", "api"],
                plan_steps=["Analyze headers", "Verify signature"],
                solution_summary="Added constant-time JWT bearer verification middleware.",
                files_touched=["auth.py"],
                critic_score=0.95,
            )

            recalled = mem.recall_similar("Build FastAPI JWT authentication middleware", top_k=2)
            self.assertEqual(len(recalled), 1)
            self.assertIn("security", recalled[0]["guilds"])

            # Verify persistence across reload
            mem_reloaded = CognitiveMemoryManager(episodic_path=mem_path, vault_dir=Path(tmp))
            self.assertEqual(mem_reloaded.episode_count, 1)

    # ── Phase 5: Hybrid Compute Router & Continual Evolution ─────
    def test_compute_router_escalates_on_primary_failure_and_harvester_logs(self):
        failing_primary = _ScriptedGenerator([], loaded=True, fail=True)
        backup_frontier = _ScriptedGenerator(["Escalated frontier solution."], loaded=True)
        router = HybridComputeRouter(
            primary_generator=failing_primary,
            secondary_generator=backup_frontier,
        )

        decision = router.estimate_complexity(
            goal="Architect a global multi-region distributed database with consensus " * 5,
            workspace_files={f"mod_{i}.py": "x = 1\n" * 500 for i in range(10)},
            active_guilds=["system_architect", "database", "security"],
        )
        self.assertEqual(decision.tier, TIER_3_FRONTIER)

        reply = router.generate(system_prompt="sys", user_prompt="goal")
        self.assertEqual(reply, "Escalated frontier solution.")

        with tempfile.TemporaryDirectory() as tmp:
            traj_path = Path(tmp) / "traj.jsonl"
            dpo_path = Path(tmp) / "dpo.jsonl"
            harvester = EvolutionHarvester(trajectories_path=traj_path, dpo_path=dpo_path)
            self.assertTrue(
                harvester.harvest_trajectory(
                    prompt="Write binary search",
                    response="def bs(arr, x): ...",
                    guilds=["fullstack"],
                    critic_score=0.95,
                )
            )
            self.assertTrue(
                harvester.harvest_dpo_pair(
                    prompt="Fix function",
                    chosen_response="def f(): return 1",
                    rejected_response="def f(: return 1",
                    guild="debugger",
                )
            )
            self.assertEqual(harvester.stats()["harvested_trajectories"], 1)
            self.assertEqual(harvester.stats()["harvested_dpo_pairs"], 1)


if __name__ == "__main__":
    unittest.main()
