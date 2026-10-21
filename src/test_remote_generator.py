"""Unit tests for the self-hosted remote model client; no network is used."""

import json
import unittest
from unittest.mock import patch

from src.brain.generator import ModelGenerationError, RemoteCodeGenerator


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class RemoteGeneratorTests(unittest.TestCase):
    def test_posts_to_own_openai_compatible_endpoint(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["headers"] = dict(request.header_items())
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _Response({"choices": [{"message": {"content": "def add(a, b): return a + b"}}]})

        generator = RemoteCodeGenerator(
            base_url="https://gpu.example.test/v1",
            model="concode-coder",
            api_key="private-token",
            timeout_seconds=45,
        )
        with patch("src.brain.generator.urlopen", fake_urlopen):
            output = generator.generate("Write precise code.", "Add two integers.")

        self.assertEqual(output, "def add(a, b): return a + b")
        self.assertEqual(captured["url"], "https://gpu.example.test/v1/chat/completions")
        self.assertEqual(captured["payload"]["model"], "concode-coder")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer private-token")
        self.assertEqual(captured["timeout"], 45)

    def test_rejects_non_https_and_missing_token(self):
        generator = RemoteCodeGenerator(
            base_url="http://gpu.example.test/v1",
            model="concode-coder",
            api_key="",
        )
        self.assertFalse(generator.is_loaded)
        with self.assertRaises(ModelGenerationError):
            generator.generate("system", "task")


if __name__ == "__main__":
    unittest.main()
