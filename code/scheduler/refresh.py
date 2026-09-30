from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from code.loading.corpus import CORPUS
from code.loading.extract import is_empty_document, parse_readable_text
from code.loading.fetch import FetchError, fetch_html
from code.loading.loader import EmptyDocumentError, load_corpus
from code.paths import DATA_RAW

REFRESH_STATUS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "refresh.json"


class RefreshError(RuntimeError):
    pass


@dataclass
class RefreshReport:
    changed: list[str] = field(default_factory=list)
    force: bool = False
    check_only: bool = False
    rebuilt: bool = False
    stages: dict[str, dict[str, Any]] = field(default_factory=dict)
    refetched_at: str = ""

    @property
    def any_change(self) -> bool:
        return bool(self.changed)


def _page_digest(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _stored_digest(slug: str) -> str | None:
    path = DATA_RAW / f"{slug}.json"
    if not path.is_file():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    text = document.get("text") or ""
    return _page_digest(text)


def _fetch_current() -> list[dict[str, Any]]:
    """Fetch and parse every corpus page. Fails loudly on empty/unreadable."""
    documents: list[dict[str, Any]] = []
    for entry in CORPUS:
        html = fetch_html(entry["source_url"])
        text = parse_readable_text(html)
        if is_empty_document(text):
            raise RefreshError(
                f"No usable text from {entry['source_url']}; "
                "not substituting another URL or source."
            )
        documents.append(
            {
                "slug": entry["slug"],
                "source_url": entry["source_url"],
                "text": text,
                "digest": _page_digest(text),
            }
        )
    return documents


def _changed_slugs(current: list[dict[str, Any]], force: bool) -> list[str]:
    if force:
        return [doc["slug"] for doc in current]
    changed: list[str] = []
    for doc in current:
        if _stored_digest(doc["slug"]) != doc["digest"]:
            changed.append(doc["slug"])
    return changed


def _rebuild() -> dict[str, dict[str, Any]]:
    """Run the full offline chain; each stage reports counts through stdout."""
    from code.chunking.chunker import ChunkingError, chunk_corpus
    from code.embedding.embedder import EmbeddingError, embed_corpus
    from code.vector_store.store import VectorStoreError, index_corpus

    stages: dict[str, dict[str, Any]] = {}

    try:
        documents = load_corpus()
        stages["loading"] = {"ok": True, "documents": len(documents)}
    except (FetchError, EmptyDocumentError) as exc:
        raise RefreshError(f"DATA LOADING FAILED: {exc}") from exc

    try:
        chunks = chunk_corpus()
        stages["chunking"] = {"ok": True, "chunks": len(chunks)}
    except ChunkingError as exc:
        raise RefreshError(f"CHUNKING FAILED: {exc}") from exc

    try:
        meta = embed_corpus()
        stages["embedding"] = {"ok": True, "count": meta.get("count"), "dim": meta.get("dim")}
    except EmbeddingError as exc:
        raise RefreshError(f"EMBEDDING FAILED: {exc}") from exc

    try:
        vmeta = index_corpus()
        stages["vector_store"] = {
            "ok": True,
            "count": vmeta.get("count"),
            "collection": vmeta.get("collection"),
        }
    except (VectorStoreError, RefreshError) as exc:
        raise RefreshError(f"VECTOR STORE FAILED: {exc}") from exc

    return stages


def _write_status(report: RefreshReport) -> None:
    payload = {
        "refreshed_at": report.refetched_at,
        "changed": report.changed,
        "rebuilt": report.rebuilt,
        "stages": report.stages,
    }
    REFRESH_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REFRESH_STATUS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def refresh(check_only: bool = False, force: bool = False) -> RefreshReport:
    """Compare fresh page text with the stored corpus, then refresh if needed.

    - check_only: report what would change without writing anything.
    - force: rebuild the corpus even if the source text is identical.
    """
    refetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    current = _fetch_current()
    changed = _changed_slugs(current, force)

    report = RefreshReport(
        changed=changed,
        force=force,
        check_only=check_only,
        refetched_at=refetched_at,
    )

    for doc in current:
        state = "changed" if doc["slug"] in changed else "unchanged"
        print(f"  [{state}] {doc['slug']}  {doc['digest'][:12]}…")

    if check_only:
        print("CHECK MODE: no files were written.")
        return report

    if not changed:
        print("UP TO DATE: corpus already matches the published fund pages.")
        return report

    print("CHANGE DETECTED: rebuilding the retrieval pipeline…")
    report.stages = _rebuild()
    report.rebuilt = True
    _write_status(report)
    return report