from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load MiniLM once. Same instance is used for chunks and questions."""
    global _model
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
