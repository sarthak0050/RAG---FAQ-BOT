from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from code.embedding.model import embed_query
from code.generation.mistral import GenerationError, generate_answer
from code.retrieval.gates import check_pii, detect_intent, named_corpus_funds, off_corpus_fund
from code.vector_store.store import (
    collection_info,
    query_collection,
    query_with_filter,
)

TOP_K = 5
RETRIEVE_K = 12
WEAK_THRESHOLD = 0.30
_EMPTY_WORDS = ("", "?", "???", "...", "-")

_FACT_TOKENS = {
    "expense_ratio": ("expense_ratio", "expense ratio", "expense"),
    "exit_load": ("exit_load", "exit load", "exit_loads"),
    "lock_in": ("lock_in", "lock in", "lock-in"),
    "minimum_sip": ("minimum_sip", "minimum sip", "min sip", "sip"),
    "riskometer": ("riskometer", "riskometer"),
    "benchmark": ("benchmark", "benchmark"),
}
_DATED_DATE = re.compile(r"as_on_date:\s*(\d{4}-\d{2}-\d{2})")


@dataclass
class Retrieval:
    chunks: list[dict[str, Any]] = field(default_factory=list)
    best_score: float = 0.0
    returned: int = 0

    @property
    def weak(self) -> bool:
        return self.returned == 0 or self.best_score < WEAK_THRESHOLD


def retrieve(question: str, k: int = TOP_K, db_dir: Path | None = None) -> Retrieval:
    """Embed a question and return the nearest Chroma chunks (ask path, step 4-5)."""
    query = (question or "").strip()
    if not query or query.lower() in _EMPTY_WORDS:
        return Retrieval()
    embedding = embed_query(query)
    rows = query_collection(embedding, k=k, db_dir=db_dir)
    return Retrieval(chunks=rows, best_score=rows[0]["score"] if rows else 0.0, returned=len(rows))


def answer_question(question: str, k: int = TOP_K, db_dir: Path | None = None) -> dict[str, Any]:
    """Full ask path: gates -> retrieve -> generate -> compose (Phase E)."""
    raw = (question or "").strip()

    if not raw or raw.lower() in _EMPTY_WORDS:
        return _refusal("empty", "Please ask a factual question about these funds.")

    pii = check_pii(raw)
    query = _strip_pii_placeholder(pii.cleaned)
    if not query.strip():
        return _refusal("empty", "Please re-ask without personal identifiers.")

    intent = detect_intent(query)
    if intent.kind == "advice":
        return _refusal("advice", None, retrieved=[], warning=pii.warning)
    if intent.kind == "returns":
        return _refusal("returns", None, retrieved=[], warning=pii.warning)
    if off_corpus_fund(query):
        return _refusal("off_corpus", None, retrieved=[], warning=pii.warning)

    res = retrieve(query, k=RETRIEVE_K, db_dir=db_dir)
    named = named_corpus_funds(query)
    supported = bool(named) and any(
        c.get("source_url") in named for c in res.chunks
    )
    if res.returned == 0 or (res.weak and not supported):
        return _refusal(
            "off_corpus",
            None,
            retrieved=_summary(res.chunks),
            warning=pii.warning,
        )

    if named:
        _prefer_fund(res, named)
    boosted = _spot_boost(query, named, db_dir) if named else []
    context = _dedupe(boosted + res.chunks)[:k]
    citation = _pick_citation(query, context)
    body: str = ""
    generation_error = ""
    try:
        body = generate_answer(query, context, citation)
    except GenerationError as exc:
        generation_error = str(exc)

    return {
        "kind": "answer",
        "answer": body,
        "source_url": citation,
        "last_updated": _last_updated(db_dir),
        "warning": pii.warning,
        "retrieved": _summary(context),
        "generation_error": generation_error,
    }


def _refusal(
    kind: str,
    message: str | None,
    retrieved: list[dict[str, Any]] | None = None,
    warning: str = "",
) -> dict[str, Any]:
    next_line = " " if kind == "empty" else "\n"
    messages = {
        "advice": (
            "I can't advise on buying, selling, or which fund is best for you. "
            "I only share facts from these five Groww fund pages.\n"
            "Educational link: https://groww.in/p/mutual-funds/"
        ),
        "returns": (
            "I don't compute or compare returns. Please check the fund's factsheet "
            "or the fund page itself for return figures.\n"
            "You can find factsheets under the fund page on Groww."
        ),
        "off_corpus": (
            "I can't answer that from the five HDFC Direct Growth pages on Groww "
            "(Large Cap, Flexi Cap, ELSS Tax Saver, Small Cap, Balanced Advantage). "
            "That fact is not on these pages, so I won't guess."
        ),
        "empty": "Please ask a factual question about these funds.",
    }
    final = message or messages[kind]
    return {
        "kind": final_kind(kind),
        "answer": final,
        "source_url": _refusal_link(kind),
        "last_updated": _last_updated(),
        "warning": warning,
        "retrieved": retrieved or [],
        "generation_error": "",
    }


def final_kind(kind: str) -> str:
    return "off_corpus" if kind == "empty" else kind


def _refusal_link(kind: str) -> str:
    if kind == "returns":
        return "https://groww.in/mutual-funds"
    if kind in ("advice",):
        return "https://groww.in/p/mutual-funds/"
    return "" if kind == "empty" else ""


def _pick_citation(query: str, chunks: list[dict[str, Any]]) -> str:
    """Prefer the fund named in the question; else the top chunk's URL."""
    hits = named_corpus_funds(query)
    for chunk in chunks:
        if chunk.get("source_url") in hits:
            return chunk["source_url"]
    return chunks[0]["source_url"] if chunks else ""


def _prefer_fund(chunks_rows: Retrieval, source_urls: list[str]) -> None:
    """Move chunks from the fund named in the question to the front, in place."""
    preferred = [c for c in chunks_rows.chunks if c.get("source_url") in source_urls]
    rest = [c for c in chunks_rows.chunks if c.get("source_url") not in source_urls]
    chunks_rows.chunks = preferred + rest


def _spot_boost(
    query: str,
    source_urls: list[str],
    db_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Surface chunks that literally contain the fact field asked about.

    MiniLM can rank glossy fund-overview chunks above dense key-value data, so for
    a named fund we also run a document-filtered search for the fact token and give
    those chunks priority. Dated series (expense_ratio) prefer the newest entry.
    """
    primary = source_urls[0]
    q_norm = re.sub(r"[_\-]", " ", (query or "").lower())
    embedding = embed_query(query)
    boosted: list[dict[str, Any]] = []
    for token, surfaces in _FACT_TOKENS.items():
        token_norm = re.sub(r"[_\-]", " ", token)
        if token_norm not in q_norm:
            continue
        for surface in surfaces:
            rows = query_with_filter(
                embedding,
                k=10,
                where={"source_url": primary},
                where_document={"$contains": surface},
                db_dir=db_dir,
            )
            if not rows:
                continue
            boosted.extend(_boost_pick(token, rows))
            break
    return _dedupe(boosted)


def _boost_pick(token: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if token == "expense_ratio":
        dated = [r for r in rows if _DATED_DATE.search(r.get("text") or "")]
        if dated:
            return [_newest_dated(dated)]
    return rows[:1]


def _newest_dated(rows: list[dict[str, Any]]) -> dict[str, Any]:
    best, best_date = rows[0], ""
    for row in rows:
        dates = max(_DATED_DATE.findall(row.get("text") or ""), default="")
        if dates and dates > best_date:
            best, best_date = row, dates
    return best


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        cid = row.get("chunk_id")
        if cid in seen:
            continue
        seen.add(cid)
        out.append(row)
    return out


def _strip_pii_placeholder(text: str) -> str:
    """Remove masked identifiers before embedding so the query stays clean."""
    return re.sub(r"\s+", " ", re.sub(r"\[redacted\]\s*", " ", text)).strip()


def _summary(chunks: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "chunk_id": c.get("chunk_id", ""),
            "source_url": c.get("source_url", ""),
            "fund_name": c.get("fund_name", ""),
            "score": f"{c.get('score', 0.0):.3f}",
        }
        for c in chunks
    ]


def _last_updated(db_dir: Path | None = None) -> str:
    try:
        stamp = collection_info(db_dir).get("ingested_at")
        return datetime.fromisoformat(stamp).date().isoformat()
    except Exception:
        return ""