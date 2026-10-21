"""Fast, model-free tests for the bounded coding-agent core."""

import json
import unittest

from src.brain.agent import CodingAgent


class _ScriptedGenerator:
    def __init__(self, responses):
        self.responses = iter(responses)

    def generate(self, **_kwargs):
        return next(self.responses)


def _decision(edits, **overrides):
    decision = {
        "summary": "Updated the requested file.",
        "plan": ["Inspect the file", "Apply the smallest fix", "Verify syntax"],
        "edits": edits,
        "needs_user_input": False,
        "question": None,
    }
    decision.update(overrides)
    return json.dumps(decision)


class CodingAgentTests(unittest.TestCase):
    def test_applies_and_verifies_a_python_replacement(self):
        generator = _ScriptedGenerator([
            _decision([{
                "path": "app.py",
                "content": "def greeting(name: str) -> str:\n    return f'Hello, {name}'\n",
                "reason": "Add the requested greeting implementation.",
            }])
        ])
        result = CodingAgent(generator).run(
            goal="Implement a greeting function.",
            workspace_files={"app.py": "def greeting(name):\n    pass\n"},
            guild_prompt="Write clean Python.",
        )

        self.assertTrue(result.success)
        self.assertEqual(len(result.edits), 1)
        self.assertIn("Hello", result.edits[0].content)
        self.assertEqual(result.verification[0].status, "passed")
        self.assertIn("a/app.py", result.edits[0].diff)

    def test_retries_when_the_first_change_fails_verification(self):
        generator = _ScriptedGenerator([
            _decision([{
                "path": "app.py",
                "content": "def greeting(:\n    return 'Hello'\n",
                "reason": "Initial attempt.",
            }]),
            _decision([{
                "path": "app.py",
                "content": "def greeting():\n    return 'Hello'\n",
                "reason": "Correct the function signature.",
            }]),
        ])
        result = CodingAgent(generator).run(
            goal="Fix app.py.",
            workspace_files={"app.py": "def greeting():\n    pass\n"},
            guild_prompt="Write clean Python.",
            max_iterations=2,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.iterations, 2)
        self.assertEqual(len(result.edits), 1)
        self.assertEqual(result.edits[0].content, "def greeting():\n    return 'Hello'\n")
        self.assertEqual(result.verification[0].status, "failed")
        self.assertEqual(result.verification[-1].status, "passed")

    def test_rejects_unsafe_edit_paths(self):
        generator = _ScriptedGenerator([
            _decision([{
                "path": "../secrets.py",
                "content": "stolen = True\n",
                "reason": "Invalid path.",
            }])
        ])
        result = CodingAgent(generator).run(
            goal="Change a file.",
            workspace_files={"app.py": "pass\n"},
            guild_prompt="Write safe code.",
            max_iterations=1,
        )

        self.assertFalse(result.success)
        self.assertIn("Unsafe edit path", result.error)

    def test_returns_clarifying_question_without_edits(self):
        generator = _ScriptedGenerator([
            _decision([], needs_user_input=True, question="Which authentication provider should be used?")
        ])
        result = CodingAgent(generator).run(
            goal="Add authentication.",
            workspace_files={"app.py": "pass\n"},
            guild_prompt="Write safe code.",
        )

        self.assertTrue(result.needs_user_input)
        self.assertFalse(result.edits)
        self.assertIn("provider", result.question)

    def test_converts_an_unstructured_code_block_when_file_is_unambiguous(self):
        generator = _ScriptedGenerator([
            "Here is the implementation:\n```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```"
        ])
        result = CodingAgent(generator).run(
            goal="Add two integers.",
            workspace_files={"math_utils.py": "# Math utilities\n"},
            guild_prompt="Write clean Python.",
        )

        self.assertTrue(result.success)
        self.assertIn("def add", result.edits[0].content)
        self.assertIn("Math utilities", result.edits[0].content)
        self.assertIn("structured", result.edits[0].reason)


if __name__ == "__main__":
    unittest.main()
