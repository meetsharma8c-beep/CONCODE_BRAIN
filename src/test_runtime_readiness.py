"""Tests for the deployment readiness endpoint without loading model weights."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from src import service


class _Generator:
    def __init__(self, loaded):
        self.is_loaded = loaded


class RuntimeReadinessTests(unittest.TestCase):
    def test_not_ready_when_generator_is_missing(self):
        with patch.object(service, "generator", None):
            with self.assertRaises(HTTPException) as raised:
                service.readiness()

        self.assertEqual(raised.exception.status_code, 503)

    def test_not_ready_when_generator_failed_to_load(self):
        with patch.object(service, "generator", _Generator(False)):
            with self.assertRaises(HTTPException) as raised:
                service.readiness()

        self.assertEqual(raised.exception.status_code, 503)

    def test_ready_when_generator_is_loaded(self):
        with patch.object(service, "generator", _Generator(True)):
            self.assertEqual(
                service.readiness(),
                {"status": "ready", "backend": service.INFERENCE_BACKEND},
            )


if __name__ == "__main__":
    unittest.main()
