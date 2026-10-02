"""Tests for sleep/wake behaviour: background warm-up, Chroma client reuse, and
transcripts that survive a session reset.

Run: python3 -m unittest discover -s tests -t .
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.ui import session_store, warmup  # noqa: E402


class WarmupTests(unittest.TestCase):
    def setUp(self) -> None:
        warmup._ready.clear()
        warmup._thread = None
        self.addCleanup(self._reset)

    def _reset(self) -> None:
        if warmup._thread is not None and warmup._thread.is_alive():
            warmup._thread.join(timeout=5)
        warmup._ready.clear()
        warmup._thread = None

    def test_short_circuits_when_already_warm(self) -> None:
        warmup._ready.set()
        self.assertTrue(warmup.warm_async())

    def test_reruns_do_not_spawn_a_second_loader(self) -> None:
        """Streamlit reruns the script on every click; loading must happen once."""
        loads: list[int] = []

        def fake_load() -> None:
            loads.append(1)
            warmup._ready.set()

        with mock.patch.object(warmup, "_load", fake_load):
            self.assertFalse(warmup.warm_async())
            first_thread = warmup._thread
            warmup.warm_async()
            warmup.warm_async()
            second_thread = warmup._thread

        self.assertIsNotNone(first_thread)
        if first_thread is not None:
            first_thread.join(timeout=5)
        self.assertIs(first_thread, second_thread)
        self.assertEqual(len(loads), 1, "loader ran more than once")

    def test_wait_ready_reports_completion(self) -> None:
        with mock.patch.object(warmup, "_load", lambda: warmup._ready.set()):
            warmup.warm_async()
            self.assertTrue(warmup.wait_ready(timeout=10))
        self.assertTrue(warmup.is_ready())

    def test_load_failure_does_not_raise_into_the_ui(self) -> None:
        def boom() -> None:
            raise RuntimeError("index missing")

        with mock.patch.object(warmup, "_load", boom):
            warmup.warm_async()
            if warmup._thread is not None:
                warmup._thread.join(timeout=5)
        self.assertFalse(warmup.is_ready())


class ChromaClientReuseTests(unittest.TestCase):
    def test_client_is_memoized_per_path(self) -> None:
        try:
            from code.vector_store import store
        except ImportError as exc:  # chromadb not installed
            self.skipTest(f"chromadb unavailable: {exc}")

        with tempfile.TemporaryDirectory() as tmp:
            one = Path(tmp) / "a"
            two = Path(tmp) / "b"
            store.reset_client_cache()
            first = store.get_client(one)
            second = store.get_client(one)
            other = store.get_client(two)
            store.reset_client_cache()

        self.assertIs(first, second, "repeat query rebuilt the Chroma client")
        self.assertIsNot(first, other, "different db_dir must not share a client")


class SessionStoreTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            session_store, "store_dir", lambda: Path(tmp)
        ):
            sid = session_store.new_session_id()
            messages = [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "result": {"answer": "hello"}},
            ]
            session_store.save(sid, messages)
            self.assertEqual(session_store.load(sid), messages)

    def test_history_survives_a_fresh_process_view(self) -> None:
        """A woken Streamlit app is a new session; the transcript must persist."""
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(session_store, "store_dir", lambda: Path(tmp)):
                sid = session_store.new_session_id()
                session_store.save(sid, [{"role": "user", "content": "remember me"}])
                import importlib

                reloaded = importlib.reload(session_store)
                with mock.patch.object(reloaded, "store_dir", lambda: Path(tmp)):
                    self.assertEqual(reloaded.load(sid), [{"role": "user", "content": "remember me"}])
            importlib.reload(session_store)

    def test_transcript_is_capped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            session_store, "store_dir", lambda: Path(tmp)
        ):
            sid = session_store.new_session_id()
            session_store.save(sid, [{"role": "user", "content": str(i)} for i in range(500)])
            self.assertEqual(len(session_store.load(sid)), session_store.MAX_TURNS)

    def test_missing_or_corrupt_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            session_store, "store_dir", lambda: Path(tmp)
        ):
            self.assertEqual(session_store.load("never-written"), [])
            path = session_store._path("broken")
            path.write_text("{not json", encoding="utf-8")
            self.assertEqual(session_store.load("broken"), [])

    def test_session_id_cannot_escape_the_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            session_store, "store_dir", lambda: Path(tmp)
        ):
            path = session_store._path("../../../etc/passwd")
            self.assertEqual(path.parent, Path(tmp))

    def test_clear_removes_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            session_store, "store_dir", lambda: Path(tmp)
        ):
            sid = session_store.new_session_id()
            session_store.save(sid, [{"role": "user", "content": "x"}])
            session_store.clear(sid)
            self.assertEqual(session_store.load(sid), [])


if __name__ == "__main__":
    unittest.main()