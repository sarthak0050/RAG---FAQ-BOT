from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from code.embedding.model import MODEL_NAME, embed_texts
from code.loading.corpus import CORPUS
from code.paths import DATA_CHUNKS, DATA_EMBEDDINGS


class EmbeddingError(RuntimeError):
    pass


def embed_corpus(
    chunks_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Embed each chunk 1:1 with MiniLM. Does not use any other embedding API."""
    src = chunks_dir or DATA_CHUNKS
    dest = output_dir or DATA_EMBEDDINGS
    dest.mkdir(parents=True, exist_ok=True)

    chunks = _load_chunks(src)
    texts = [chunk["text"] for chunk in chunks]
    if any(not (text or "").strip() for text in texts):
        raise EmbeddingError("A chunk has empty text; re-run chunking.")

    vectors = embed_texts(texts, show_progress=True)
    if vectors.shape[0] != len(chunks):
        raise EmbeddingError(
            f"Embedding count {vectors.shape[0]} != chunk count {len(chunks)}"
        )

    ids = [chunk["chunk_id"] for chunk in chunks]
    np.save(dest / "embeddings.npy", vectors)
    (dest / "ids.json").write_text(
        json.dumps(ids, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    meta = {
        "model": MODEL_NAME,
        "count": int(vectors.shape[0]),
        "dim": int(vectors.shape[1]),
        "normalized": True,
        "chunk_ids_path": "ids.json",
        "embeddings_path": "embeddings.npy",
    }
    (dest / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta


def _load_chunks(chunks_dir: Path) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for entry in CORPUS:
        path = chunks_dir / f"{entry['slug']}.json"
        if not path.is_file():
            raise EmbeddingError(
                f"Missing chunks file {path.name}; run chunking first."
            )
        fund_chunks = json.loads(path.read_text(encoding="utf-8"))
        if not fund_chunks:
            raise EmbeddingError(f"No chunks in {path.name}")
        for chunk in fund_chunks:
            if chunk.get("source_url") != entry["source_url"]:
                raise EmbeddingError(
                    f"Chunk {chunk.get('chunk_id')} source_url does not match corpus."
                )
            chunk_id = chunk.get("chunk_id")
            if not chunk_id or chunk_id in seen_ids:
                raise EmbeddingError(f"Invalid or duplicate chunk_id: {chunk_id}")
            seen_ids.add(chunk_id)
            chunks.append(chunk)
    return chunks
