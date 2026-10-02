from __future__ import annotations

import threading

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    """Load MiniLM once. Same instance is used for chunks and questions.

    Double-checked locking: the UI warms this in a background thread while the
    page renders, so an early question must block on the same load rather than
    starting a second one.
    """
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            _model = SentenceTransformer(MODEL_NAME)
        return _model


def embed_texts(texts: list[str], show_progress: bool = False) -> np.ndarray:
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    vectors = get_model().encode(
        texts,
        batch_size=64,
        show_progress_bar=show_progress,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return np.asarray(vectors, dtype=np.float32)


def embed_query(question: str) -> np.ndarray:
    """Query-time embedding: identical model and normalization as corpus vectors."""
    return embed_texts([question])[0]
