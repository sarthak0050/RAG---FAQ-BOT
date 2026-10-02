"""Chat history that survives a Streamlit session reset.

Streamlit Community Cloud sleeps idle apps, and a woken app starts a brand new
browser session: ``st.session_state`` is empty, so a returning user loses their
conversation. This keeps the transcript in a small JSON file under the system
temp directory, keyed by a session id carried in the URL query string, so the
history survives both a sleep/wake and a process restart.

The store lives outside the repository on purpose - nothing written here can be
picked up by the corpus/changelog workflows that commit the repo.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

MAX_SESSIONS = 50
MAX_TURNS = 40
_TTL_SECONDS = 7 * 24 * 3600


def store_dir() -> Path:
    path = Path(tempfile.gettempdir()) / "groww-faq-sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path(session_id: str) -> Path:
    safe = "".join(ch for ch in session_id if ch.isalnum() or ch in "-_")
    return store_dir() / f"{safe or 'default'}.json"


def new_session_id() -> str:
    return uuid.uuid4().hex[:16]


def load(session_id: str) -> list[dict[str, Any]]:
    file = _path(session_id)
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    messages = data.get("messages")
    return messages if isinstance(messages, list) else []


def save(session_id: str, messages: list[dict[str, Any]]) -> None:
    trimmed = messages[-MAX_TURNS:]
    file = _path(session_id)
    try:
        tmp = file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"saved_at": time.time(), "messages": trimmed}, default=str),
            encoding="utf-8",
        )
        tmp.replace(file)  # atomic: a crashed write cannot corrupt the transcript
    except OSError:
        pass
    _prune()


def clear(session_id: str) -> None:
    try:
        _path(session_id).unlink()
    except OSError:
        pass


def _prune() -> None:
    """Drop stale sessions and cap the directory size."""
    files = sorted(
        store_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    now = time.time()
    for old in files[MAX_SESSIONS:]:
        try:
            if now - old.stat().st_mtime > _TTL_SECONDS:
                old.unlink()
        except OSError:
            pass
    for path in files[:MAX_SESSIONS]:
        try:
            if now - path.stat().st_mtime > _TTL_SECONDS:
                path.unlink()
        except OSError:
            pass


def env_note() -> str:  # pragma: no cover - diagnostics only
    return f"sessions stored in {os.environ.get('TMPDIR', tempfile.gettempdir())}"