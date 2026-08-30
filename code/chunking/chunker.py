from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from code.chunking.config import CHUNK_OVERLAP, CHUNK_SIZE
from code.chunking.split import split_text
from code.loading.corpus import CORPUS
from code.paths import DATA_CHUNKS, DATA_RAW


class ChunkingError(RuntimeError):
    pass


def chunk_corpus(
    raw_dir: Path | None = None,
    output_dir: Path | None = None,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Chunk each Phase A document separately. Does not merge text across URLs."""
    src = raw_dir or DATA_RAW
    dest = output_dir or DATA_CHUNKS
    dest.mkdir(parents=True, exist_ok=True)

    all_chunks: list[dict[str, Any]] = []
    for entry in CORPUS:
        raw_path = src / f"{entry['slug']}.json"
        document = _read_document(raw_path, entry)
        chunks = _chunk_document(document, entry["slug"], chunk_size, chunk_overlap)
        if not chunks:
            raise ChunkingError(f"No chunks produced for {entry['source_url']}")
        fund_path = dest / f"{entry['slug']}.json"
        fund_path.write_text(
            json.dumps(chunks, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        all_chunks.extend(chunks)

    (dest / "all.json").write_text(
        json.dumps(all_chunks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return all_chunks


def _read_document(path: Path, entry: dict[str, str]) -> dict[str, Any]:
    if not path.is_file():
        raise ChunkingError(
            f"Missing raw document {path.name}; run data loading first."
        )
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("source_url") != entry["source_url"]:
        raise ChunkingError(
            f"Raw file {path.name} source_url does not match corpus URL."
        )
    if not (document.get("text") or "").strip():
        raise ChunkingError(f"Empty text in {path.name}")
    return document


def _chunk_document(
    document: dict[str, Any],
    slug: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, Any]]:
    pieces = split_text(document["text"], chunk_size, chunk_overlap)
    chunks: list[dict[str, Any]] = []
    for index, piece in enumerate(pieces):
        chunks.append(
            {
                "chunk_id": f"{slug}::{index:04d}",
                "text": piece,
                "source_url": document["source_url"],
                "fund_name": document["fund_name"],
            }
        )
    return chunks
