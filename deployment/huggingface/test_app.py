"""Contract tests for the lightweight Hugging Face travel API."""

import json
import os
import sys
import unittest
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

os.environ.setdefault("CONCODE_API_KEY", "test-concode-api-key-at-least-32-characters")
os.environ.setdefault("CONCODE_REMOTE_LLM_BASE_URL", "https://provider.example/v1")
os.environ.setdefault("CONCODE_REMOTE_LLM_MODEL", "test-travel-model")
os.environ.setdefault("CONCODE_REMOTE_LLM_API_KEY", "provider-test-key")
sys.path.insert(0, os.path.dirname(__file__))

import app as concode_app  # noqa: E402


class _FakeResponse:
    def __init__(self, content=None, error=None):
        self.status_code = 200
        self.content = content
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error
        return None

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


class _FakeAsyncClient:
    response_content = ""
    responses = []
    response_index = 0
    captured = {}

    def __init__(self, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def post(self, url, *, headers, json):
        self.captured = {
            "url": url,
            "headers": headers,
            "payload": json,
        }
        _FakeAsyncClient.captured.setdefault("calls", []).append(self.captured)
        if _FakeAsyncClient.responses:
            response = _FakeAsyncClient.responses[_FakeAsyncClient.response_index]
            _FakeAsyncClient.response_index += 1
            return response
        return _FakeResponse(self.response_content)


class HuggingFaceTravelApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(concode_app.app)
        cls.api_key = os.environ["CONCODE_API_KEY"]

    def setUp(self):
        _FakeAsyncClient.responses = []
        _FakeAsyncClient.response_index = 0
        _FakeAsyncClient.captured = {}

    def test_travel_requires_concode_api_key(self):
        response = self.client.post("/api/v1/travel", json={"query": "Plan a trip"})
        self.assertEqual(response.status_code, 401)

    def test_itinerary_uses_private_provider_key_and_returns_concode_contract(self):
        _FakeAsyncClient.response_content = json.dumps({
            "itinerary": [{
                "dayNumber": 1,
                "title": "A day in Goa",
                "theme": "Coast and food",
                "activities": [{
                    "time": "10:00",
                    "title": "Beach walk",
                    "type": "viewpoint",
                    "location": "Goa",
                    "description": "A suggested walk.",
                    "estimatedCost": 0,
                    "preferenceMatch": "scenic",
                    "durationMin": 60,
                }],
            }],
        })
        with patch.object(concode_app.httpx, "AsyncClient", _FakeAsyncClient):
            response = self.client.post(
                "/api/v1/travel",
                headers={"X-API-Key": self.api_key},
                json={
                    "query": "Create a day plan",
                    "trip_context": {"destination": "Goa", "duration_days": 1},
                    "mode": "itinerary",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model_backend"], "remote")
        self.assertTrue(body["is_estimate"])
        self.assertEqual(json.loads(body["reply"])["itinerary"][0]["activities"][0]["title"], "Beach walk")
        call = _FakeAsyncClient.captured["calls"][0]
        self.assertEqual(call["url"], "https://provider.example/v1/chat/completions")
        self.assertEqual(
            call["headers"]["Authorization"],
            "Bearer provider-test-key",
        )
        self.assertNotIn("provider-test-key", json.dumps(body))

    def test_uses_configured_fallback_when_primary_provider_fails(self):
        primary_error = httpx.HTTPStatusError(
            "primary provider unavailable",
            request=httpx.Request("POST", "https://provider.example/v1/chat/completions"),
            response=httpx.Response(503),
        )
        _FakeAsyncClient.responses = [
            _FakeResponse(error=primary_error),
            _FakeResponse(content="A relaxed day plan."),
        ]
        with patch.object(concode_app, "REMOTE_BASE_URL", "https://primary.example/v1"), \
                patch.object(concode_app, "REMOTE_MODEL", "primary-model"), \
                patch.object(concode_app, "REMOTE_API_KEY", "primary-secret"), \
                patch.object(concode_app, "FALLBACK_BASE_URL", "https://fallback.example/v1"), \
                patch.object(concode_app, "FALLBACK_MODEL", "fallback-model"), \
                patch.object(concode_app, "FALLBACK_API_KEY", "fallback-secret"), \
                patch.object(concode_app.httpx, "AsyncClient", _FakeAsyncClient):
            response = self.client.post(
                "/api/v1/travel",
                headers={"X-API-Key": self.api_key},
                json={"query": "Suggest a relaxed day", "mode": "text"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["reply"], "A relaxed day plan.")
        self.assertEqual(
            [call["payload"]["model"] for call in _FakeAsyncClient.captured["calls"]],
            ["primary-model", "fallback-model"],
        )
        self.assertEqual(
            _FakeAsyncClient.captured["calls"][1]["headers"]["Authorization"],
            "Bearer fallback-secret",
        )

    def test_itinerary_rejects_unstructured_or_wrong_day_count_output(self):
        _FakeAsyncClient.response_content = '{"itinerary":[]}'
        with patch.object(concode_app.httpx, "AsyncClient", _FakeAsyncClient):
            response = self.client.post(
                "/api/v1/travel",
                headers={"X-API-Key": self.api_key},
                json={
                    "query": "Create a one-day plan",
                    "trip_context": {"destination": "Goa", "duration_days": 1},
                    "mode": "itinerary",
                },
            )
        self.assertEqual(response.status_code, 502)

    def test_rejects_oversized_request(self):
        response = self.client.post(
            "/api/v1/travel",
            headers={"X-API-Key": self.api_key},
            content=b" " * 16_385,
        )
        self.assertEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
