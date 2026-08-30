from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
import chromadb.api
import numpy as np

from code.embedding.model import MODEL_NAME
from code.loading.corpus import CORPUS
from code.paths import DATA_CHROMA, DATA_CHUNKS, DATA_EMBEDDINGS, DATA_RAW

COLLECTION_NAME = "groww_hdfc_faq"
_BATCH_SIZE = 500


class VectorStoreError(RuntimeError):
    pass


def get_client(db_dir: Path | None = None) -> chromadb.api.ClientAPI:
    """Persistent ChromaDB client rooted at data/chroma."""
    dest = db_dir or DATA_CHROMA
    dest.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(dest))


def get_collection(
    db_dir: Path | None = None,
) -> chromadb.api.CollectionAPI:
    try:
        return get_client(db_dir).get_collection(COLLECTION_NAME)
    except Exception as exc:
        raise VectorStoreError(
            f"Collection '{COLLECTION_NAME}' missing; run the index step first."
        ) from exc


def index_corpus(
    chunks_dir: Path | None = None,
    embeddings_dir: Path | None = None,
    raw_dir: Path | None = None,
    db_dir: Path | None = None,
) -> dict[str, Any]:
    """Upsert every chunk + its MiniLM vector into Chroma in one offline run.

    Prototype policy: wipe-and-rebuild on every re-ingest (architecture §6).
    """
    dest = db_dir or DATA_CHROMA
    dest.mkdir(parents=True, exist_ok=True)
    client = get_client(dest)
    for existing in client.list_collections():
        if existing.name == COLLECTION_NAME:
            client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine", "model": MODEL_NAME},
    )

    records = _load_records(chunks_dir, embeddings_dir, raw_dir)
    for start in range(0, len(records), _BATCH_SIZE):
        batch = records[start : start + _BATCH_SIZE]
        collection.upsert(
            ids=[r["chunk_id"] for r in batch],
            documents=[r["text"] for r in batch],
            embeddings=[r["embedding"] for r in batch],
            metadatas=[r["metadata"] for r in batch],
        )

    meta = {
        "collection": COLLECTION_NAME,
        "space": "cosine",
        "model": MODEL_NAME,
        "count": int(collection.count()),
        "dim": int(len(records[0]["embedding"])),
        "ingested_at": _ingest_date(raw_dir),
    }
    (dest / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta


def query_collection(
    query_embedding: np.ndarray,
    k: int = 5,
    db_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Top-k nearest chunks. Returns ascending cosine distance order."""
    return query_with_filter(query_embedding, k=k, db_dir=db_dir)


def query_with_filter(
    query_embedding: np.ndarray,
    k: int = 5,
    where: dict[str, Any] | None = None,
    where_document: dict[str, Any] | None = None,
    db_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Top-k nearest chunks optionally restricted by metadata / document filters."""
    collection = get_collection(db_dir)
    result = collection.query(
        query_embeddings=[np.asarray(query_embedding, dtype=np.float32).tolist()],
        n_results=k,
        include=["documents", "metadatas", "distances"],
        where=where,
        where_document=where_document,
    )
    return _parse_query(result)


def collection_info(db_dir: Path | None = None) -> dict[str, Any]:
    collection = get_collection(db_dir)
    info: dict[str, Any] = {"collection": COLLECTION_NAME, "count": collection.count()}
    metadata = collection.metadata or {}
    info["model"] = metadata.get("model")
    info["space"] = metadata.get("hnsw:space")
    info["ingested_at"] = _ingest_date(db_dir)
    return info


def _load_records(
    chunks_dir: Path | None,
    embeddings_dir: Path | None,
    raw_dir: Path | None,
) -> list[dict[str, Any]]:
    src_chunks = chunks_dir or DATA_CHUNKS
    src_embeddings = embeddings_dir or DATA_EMBEDDINGS

    ids_path = src_embeddings / "ids.json"
    vectors_path = src_embeddings / "embeddings.npy"
    if not ids_path.is_file() or not vectors_path.is_file():
        raise VectorStoreError(
            "Missing embedding outputs; run the embedding phase first."
        )

    vectors = np.load(vectors_path)
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    if vectors.shape[0] != len(ids):
        raise VectorStoreError(
            f"Embedding count {vectors.shape[0]} != id count {len(ids)}."
        )
    vector_by_id = {chunk_id: vectors[i, :] for i, chunk_id in enumerate(ids)}

    records: list[dict[str, Any]] = []
    for entry in CORPUS:
        path = src_chunks / f"{entry['slug']}.json"
        if not path.is_file():
            raise VectorStoreError(
                f"Missing chunks file {path.name}; run chunking first."
            )
        chunks = json.loads(path.read_text(encoding="utf-8"))
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id")
            if not chunk_id:
                raise VectorStoreError(f"Chunk without chunk_id in {path.name}.")
            embedding = vector_by_id.pop(chunk_id, None)
            if embedding is None:
                raise VectorStoreError(
                    f"No embedding for {chunk_id}; re-run the embedding phase."
                )
            if not (chunk.get("text") or "").strip():
                raise VectorStoreError(f"Empty text on {chunk_id}.")
            records.append(
                {
                    "chunk_id": chunk_id,
                    "text": chunk["text"],
                    "embedding": [float(v) for v in embedding],
                    "metadata": {
                        "source_url": chunk["source_url"],
                        "fund_name": chunk["fund_name"],
                        "theme": entry["theme"],
                        "chunk_id": chunk_id,
                    },
                }
            )

    if vector_by_id:
        leftover = next(iter(vector_by_id))
        raise VectorStoreError(
            f"Orphan embedding {leftover} with no matching chunk; re-run phases."
        )
    if not records:
        raise VectorStoreError("No chunks to index.")
    return records


def _parse_query(result: dict[str, Any]) -> list[dict[str, Any]]:
    ids = result["ids"][0]
    distances = result.get("distances", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    documents = result.get("documents", [[]])[0]

    rows: list[dict[str, Any]] = []
    for i, chunk_id in enumerate(ids):
        metadata = metadatas[i] if metadatas else {}
        distance = float(distances[i]) if distances else 1.0
        rows.append(
            {
                "chunk_id": chunk_id,
                "text": documents[i] if documents else "",
                "source_url": metadata.get("source_url"),
                "fund_name": metadata.get("fund_name"),
                "theme": metadata.get("theme"),
                "distance": distance,
                "score": float(1.0 - distance),
            }
        )
    return rows


def _ingest_date(db_dir: Path | None) -> str:
    meta = (db_dir or DATA_CHROMA) / "meta.json"
    if meta.is_file():
        stored = json.loads(meta.read_text(encoding="utf-8")).get("ingested_at")
        if stored:
            return stored

    dates: list[str] = []
    raw_dir = DATA_RAW
    for entry in CORPUS:
        path = raw_dir / f"{entry['slug']}.json"
        if path.is_file():
            document = json.loads(path.read_text(encoding="utf-8"))
            dates.append(str(document.get("ingested_at", "")))
    dates = [d for d in dates if d]
    return max(dates) if dates else ""