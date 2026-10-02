"""Warm the heavy resources while the page renders.

Streamlit Community Cloud sleeps idle apps, and the first request after a wake
pays for importing torch/sentence-transformers (~9s) and opening the Chroma
store before it can embed anything. Doing that work on a background thread as
the app starts overlaps it with the user reading the page, so the first question
is served warm instead of appearing to hang.

This is best-effort: any failure is swallowed and the request path loads the
resources itself.
"""

from __future__ import annotations

import threading
import time
from typing import Any

# Set to True once the resources are ready; the UI reads it to explain a slow
# first answer instead of showing a frozen spinner.
_ready = threading.Event()
_thread: threading.Thread | None = None
_lock = threading.Lock()


def is_ready() -> bool:
    return _ready.is_set()


def _load() -> None:
    from code.embedding.model import get_model
    from code.vector_store.store import get_collection

    get_model()
    get_collection()
    _ready.set()


def warm_async() -> bool:
    """Start warming in the background once per process.

    Streamlit reruns this script on every interaction, so a single-flight guard
    is required: without it each click would spawn another loader thread.
    Returns True if resources are ready (no warming needed).
    """
    global _thread
    if _ready.is_set():
        return True
    with _lock:
        if _ready.is_set():
            return True
        if _thread is not None and _thread.is_alive():
            return False

        def target() -> None:
            try:
                _load()
            except Exception:
                pass  # best-effort; the request path loads on demand

        _thread = threading.Thread(target=target, name="warmup", daemon=True)
        _thread.start()
        return False


def wait_ready(timeout: float = 30.0) -> bool:
    """Block until warm (used by tests and scripts, not by the UI thread)."""
    return _ready.wait(timeout)


def seconds_since_start() -> float:
    return time.monotonic() - _STARTED


_STARTED = time.monotonic()