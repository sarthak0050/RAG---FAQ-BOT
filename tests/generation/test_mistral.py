"""Answer-generation tests (stdlib unittest — no extra dependency).

Run: python3 -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.generation import mistral  # noqa: E402


CHUNKS = [
    {
        "chunk_id": "t1",
        "source_url": "https://example.invalid/fund",
        "text": "lock_in_yrs: 3 | exit_load: 0",
    }
]


def _response(status: int, payload: dict | None = None) -> mock.Mock:
    resp = mock.Mock()
    resp.status_code = status
    resp.text = "" if payload is None else str(payload)
    resp.json.return_value = payload or {}
    return resp


class ReadSecretTests(unittest.TestCase):
    def test_reads_from_environment(self) -> None:
        with mock.patch.dict(os.environ, {"SOME_SECRET": "from-env"}):
            self.assertEqual(mistral.read_secret("SOME_SECRET"), "from-env")

    def test_returns_none_when_absent(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(mistral, "load_dotenv", create=True):
                self.assertIsNone(mistral.read_secret("DEFINITELY_NOT_SET_12345"))

    def test_falls_back_to_streamlit_secrets(self) -> None:
        """Cloud deployments expose dashboard secrets via st.secrets, not os.environ."""
        fake_st = mock.Mock()
        fake_st.secrets.get.return_value = "from-streamlit"
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.dict(sys.modules, {"streamlit": fake_st}):
                self.assertEqual(mistral.read_secret("ANY_SECRET"), "from-streamlit")
        fake_st.secrets.get.assert_called_once_with("ANY_SECRET")


class GenerateAnswerTests(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch.dict(os.environ, {"MISTRAL_API_KEY": "test-key"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_falls_back_to_next_model_when_primary_is_rate_limited(self) -> None:
        """A 429 on the preferred model must degrade, not fail the answer."""
        calls: list[str] = []

        def fake_post(url, headers=None, json=None, timeout=None):
            calls.append(json["model"])
            if json["model"] == mistral.DEFAULT_MODEL:
                return _response(429, {"message": "Rate limit exceeded"})
            return _response(200, {"choices": [{"message": {"content": "  no load, 3 year lock-in  "}}]})

        with mock.patch.object(mistral, "requests", mock.Mock(post=fake_post)):
            with mock.patch.object(mistral, "time", mock.Mock(sleep=lambda *_: None)):
                answer = mistral.generate_answer("exit load?", CHUNKS, CHUNKS[0]["source_url"])

        self.assertEqual(answer, "no load, 3 year lock-in")
        # one retry on the 429, then straight to the next model
        self.assertEqual(calls, [mistral.DEFAULT_MODEL, mistral.DEFAULT_MODEL, mistral._FALLBACK_MODELS[0]])

    def test_retries_transient_failure_then_succeeds(self) -> None:
        attempts = {"n": 0}

        def fake_post(url, headers=None, json=None, timeout=None):
            attempts["n"] += 1
            if attempts["n"] < 3:
                return _response(503, {"message": "service unavailable"})
            return _response(200, {"choices": [{"message": {"content": "recovered"}}]})

        with mock.patch.object(mistral, "requests", mock.Mock(post=fake_post)):
            with mock.patch.object(mistral, "time", mock.Mock(sleep=lambda *_: None)):
                answer = mistral.generate_answer("fee?", CHUNKS, CHUNKS[0]["source_url"])

        self.assertEqual(answer, "recovered")
        self.assertEqual(attempts["n"], 3)

    def test_does_not_retry_client_errors(self) -> None:
        calls = {"n": 0}

        def fake_post(url, headers=None, json=None, timeout=None):
            calls["n"] += 1
            return _response(401, {"message": "unauthorized"})

        with mock.patch.object(mistral, "requests", mock.Mock(post=fake_post)):
            with mock.patch.object(mistral, "time", mock.Mock(sleep=lambda *_: None)):
                with self.assertRaises(mistral.GenerationError) as ctx:
                    mistral.generate_answer("fee?", CHUNKS, CHUNKS[0]["source_url"])

        # 401 is fatal: no retry, no fallback models
        self.assertEqual(calls["n"], 1)
        self.assertIn("401", str(ctx.exception))

    def test_all_models_failing_raises_actionable_error(self) -> None:
        def fake_post(url, headers=None, json=None, timeout=None):
            return _response(429, {"message": "Rate limit exceeded"})

        with mock.patch.object(mistral, "requests", mock.Mock(post=fake_post)):
            with mock.patch.object(mistral, "time", mock.Mock(sleep=lambda *_: None)):
                with self.assertRaises(mistral.GenerationError) as ctx:
                    mistral.generate_answer("fee?", CHUNKS, CHUNKS[0]["source_url"])

        message = str(ctx.exception)
        self.assertIn("MISTRAL_MODEL", message)
        for model in (mistral.DEFAULT_MODEL, *mistral._FALLBACK_MODELS):
            self.assertIn(model, message)

    def test_missing_key_raises_before_any_request(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(mistral, "requests", mock.Mock()) as req:
                with self.assertRaises(mistral.GenerationError):
                    mistral.generate_answer("fee?", CHUNKS, CHUNKS[0]["source_url"])
        req.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()