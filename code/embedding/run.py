from __future__ import annotations

import sys

from code.embedding.embedder import EmbeddingError, embed_corpus
from code.embedding.model import MODEL_NAME, embed_query
from code.paths import DATA_EMBEDDINGS


def main() -> int:
    try:
        meta = embed_corpus()
    except EmbeddingError as exc:
        print(f"EMBEDDING FAILED: {exc}", file=sys.stderr)
        return 1

    print(
        f"Wrote {meta['count']} x {meta['dim']} embeddings to {DATA_EMBEDDINGS} "
        f"({MODEL_NAME})"
    )
    probe = embed_query("What is the expense ratio?")
    print(f"Query embedding available; dim={probe.shape[0]}")
    return 0
