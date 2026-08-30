from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from code.paths import ROOT

load_dotenv(ROOT / ".env")

API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = "mistral-small-latest"


class GenerationError(RuntimeError):
    pass


_SYSTEM_PROMPT = (
    "You are a facts-only FAQ assistant for five HDFC Direct Growth mutual funds "
    "listed on Groww. Answer ONLY from the page excerpts provided. Never use any "
    "outside knowledge or memory for numbers, charges, periods, or policies. The "
    "excerpts may contain facts as embedded key-value text (for example "
    "'lock_in_yrs: 3', 'expense_ratio: 1.02', 'analysis_desc: Lock-in period: 3Y'); "
    "parse those values from the excerpts. When a fact has a dated series (e.g. "
    "'historic_fund_expense[N].as_on_date' with 'expense_ratio'), use the entry with "
    "the MOST RECENT as_on_date as the current figure. Never print raw field names "
    "or 'key: value' syntax in your answer. Never give investment advice. Never "
    "compute, compare, or estimate returns. Answer body must be at most 3 sentences. "
    "If the requested fact does not appear in the excerpts, answer exactly: "
    "'That fact is not on these five pages.' Never invent numbers or URLs. Cite "
    "nothing beyond the excerpts."
)


def generate_answer(question: str, chunks: list[dict[str, Any]], citation_url: str) -> str:
    """Ground Mistral on top-k chunks; return the answer body only (≤3 sentences)."""
    key = os.environ.get("MISTRAL_API_KEY")
    if not key:
        raise GenerationError("MISTRAL_API_KEY not set; cannot generate an answer.")

    context = _context_block(chunks)
    user = (
        f"Page excerpts (source pages are in brackets):\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer in at most 3 sentences using only the excerpts above. "
        "Say 'not on these pages' if the fact is missing."
    )
    model = os.environ.get("MISTRAL_MODEL", DEFAULT_MODEL)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "temperature": 0.1,
        "max_tokens": 220,
    }
    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise GenerationError(f"Mistral API call failed: {exc}") from exc

    body = response.json()["choices"][0]["message"]["content"].strip()
    return body


def _context_block(chunks: list[dict[str, Any]]) -> str:
    blocks = []
    for chunk in chunks:
        blocks.append(
            "[chunk: {chunk_id}] (source: {source_url})\n{text}".format(
                chunk_id=chunk.get("chunk_id", "?"),
                source_url=chunk.get("source_url", "?"),
                text=(chunk.get("text") or "").strip(),
            )
        )
    return "\n\n---\n\n".join(blocks)