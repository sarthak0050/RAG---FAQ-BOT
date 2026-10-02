from __future__ import annotations

import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

from code.paths import ROOT

load_dotenv(ROOT / ".env")

API_URL = "https://api.mistral.ai/v1/chat/completions"
DEFAULT_MODEL = "mistral-small-latest"

# Tried in order when the preferred model is unavailable. Per-key quotas differ
# per model, so a rate-limited primary degrades instead of failing.
_FALLBACK_MODELS = (
    "ministral-8b-latest",
    "mistral-tiny-latest",
)


class GenerationError(RuntimeError):
    pass


def read_secret(name: str) -> str | None:
    """Read a secret from the process environment, then from Streamlit's store.

    Streamlit Community Cloud and Hugging Face Spaces expose dashboard secrets
    through ``st.secrets`` and *not* through ``os.environ``, so a plain
    ``os.environ.get`` silently disables answer generation in the cloud even
    when the secret has been configured. Local runs use ``.env`` (loaded above).
    """
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st
    except ImportError:
        return None
    try:
        return st.secrets.get(name)
    except Exception:  # no secrets file, or st.secrets unavailable in this context
        return None


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


def generate_answer(question: str, chunks: list[dict], citation_url: str) -> str:
    """Ground Mistral on top-k chunks; return the answer body only (≤3 sentences).

    Tries the preferred model first, then the fallbacks. Per-model quotas are not
    uniform on Mistral (a key can be rate-limited on one model and fine on
    another), so a 429 on the preferred model degrades to a smaller one instead of
    failing the answer outright.
    """
    key = read_secret("MISTRAL_API_KEY")
    if not key:
        raise GenerationError("MISTRAL_API_KEY not set; cannot generate an answer.")

    context = _context_block(chunks)
    user = (
        f"Page excerpts (source pages are in brackets):\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer in at most 3 sentences using only the excerpts above. "
        "Say 'not on these pages' if the fact is missing."
    )
    preferred = read_secret("MISTRAL_MODEL") or DEFAULT_MODEL
    models = [preferred] + [m for m in _FALLBACK_MODELS if m != preferred]

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    failures: list[str] = []
    for model in models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "max_tokens": 220,
        }
        body, reason, fatal = _post_with_retry(payload, headers)
        if body is not None:
            return body
        failures.append(f"{model}: {reason}")
        if fatal:
            # Auth/quota-at-account errors affect every model; do not keep trying.
            break

    raise GenerationError(
        "Mistral API call failed for every model tried ("
        + "; ".join(failures)
        + "). Set MISTRAL_MODEL to a model this key has quota for."
    )


def _post_with_retry(
    payload: dict,
    headers: dict,
    server_attempts: int = 3,
    rate_limit_attempts: int = 2,
    backoff: float = 1.5,
) -> tuple[str | None, str, bool]:
    """POST with backoff, returning (answer_body, reason, fatal).

    ``fatal`` marks errors that no other model can fix (401/403), so the caller
    stops instead of walking the whole fallback chain. Rate limits get one retry
    then move to the next model: a per-model quota exhaustion will not clear
    within seconds, and a slow fallback hurts the user more than an immediate
    second model.
    """
    reason = "unknown error"
    limit = server_attempts
    for attempt in range(server_attempts):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        except requests.RequestException as exc:
            reason = str(exc)
            if attempt < server_attempts - 1:
                time.sleep(backoff * (2**attempt))
            continue
        if response.status_code == 200:
            try:
                content = response.json()["choices"][0]["message"]["content"]
            except (ValueError, KeyError, IndexError) as exc:
                return None, f"malformed response body ({exc})", False
            return (content or "").strip(), "", False
        reason = f"HTTP {response.status_code} {response.text[:120]}"
        if response.status_code in (401, 403):
            return None, reason, True
        if response.status_code == 429:
            limit = min(limit, rate_limit_attempts)
        elif response.status_code not in (500, 502, 503, 504):
            return None, reason, False
        if attempt < limit - 1:
            time.sleep(backoff * (2**attempt))
        else:
            break
    return None, reason, False


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