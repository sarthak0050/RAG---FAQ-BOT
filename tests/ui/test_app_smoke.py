"""Smoke test: the Streamlit app boots and renders without raising.

Uses Streamlit's own AppTest runner, so this executes code/ui/app.py for real
(streamlit_app.py is only a runpy shim over it) and would catch an import or
render error that only shows up in the cloud.

Runs hermetically: no Mistral call is made. Skips if the search index or
Streamlit's testing helper is unavailable.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from code.paths import DATA_CHROMA  # noqa: E402


class AppSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        if not (DATA_CHROMA.exists() and any(DATA_CHROMA.iterdir())):
            self.skipTest(f"no Chroma index at {DATA_CHROMA}")
        try:
            from streamlit.testing.v1 import AppTest
        except ImportError as exc:
            self.skipTest(f"streamlit.testing unavailable: {exc}")
        self.AppTest = AppTest

    def test_app_renders_without_exception(self) -> None:
        at = self.AppTest.from_file(str(REPO / "code" / "ui" / "app.py"), default_timeout=120)
        at.run()

        self.assertEqual([str(e.value) for e in at.exception], [])
        self.assertTrue(any("Ask about" in str(ci.placeholder or "") for ci in at.chat_input))
        self.assertGreater(len(at.markdown), 0, "page rendered no content")

    def test_session_id_is_established_and_stable(self) -> None:
        """The transcript key must exist so history survives a wake."""
        at = self.AppTest.from_file(str(REPO / "code" / "ui" / "app.py"), default_timeout=120)
        at.run()

        self.assertIn("session_id", at.session_state)
        first = at.session_state["session_id"]
        self.assertTrue(first)

        at.run()  # a rerun must not invent a new session
        self.assertEqual(at.session_state["session_id"], first)

    def test_messages_start_empty(self) -> None:
        at = self.AppTest.from_file(str(REPO / "code" / "ui" / "app.py"), default_timeout=120)
        at.run()
        self.assertEqual(at.session_state["messages"], [])


if __name__ == "__main__":
    unittest.main()