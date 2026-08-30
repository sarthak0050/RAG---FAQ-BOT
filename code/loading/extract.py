"""Turn a Groww fund HTML page into readable text. Does not fetch extra URLs."""

from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

_SKIP_MF_KEYS = frozenset(
    {
        "actions",
        "logo_url",
        "nfo_image_url",
        "video_url",
        "primary_action",
        "meta_robots",
    }
)
_DROP_TAGS = ("script", "style", "noscript", "svg", "iframe")
_MIN_TEXT_CHARS = 400


def parse_readable_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    structured = _structured_from_next_data(soup)
    visible = _visible_page_text(soup)
    parts = [p for p in (structured, visible) if p]
    return "\n\n".join(parts).strip()


def is_empty_document(text: str) -> bool:
    compact = re.sub(r"\s+", "", text or "")
    return len(compact) < _MIN_TEXT_CHARS


def _structured_from_next_data(soup: BeautifulSoup) -> str:
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        return ""
    try:
        payload = json.loads(tag.string)
    except json.JSONDecodeError:
        return ""
    mf = (
        payload.get("props", {})
        .get("pageProps", {})
        .get("mfServerSideData")
    )
    if not isinstance(mf, dict) or not mf:
        return ""
    lines = ["## Structured page data"]
    lines.extend(_flatten(mf, prefix=""))
    return "\n".join(lines)


def _flatten(value: Any, prefix: str) -> list[str]:
    if prefix.split(".")[-1] in _SKIP_MF_KEYS:
        return []
    if value is None:
        return []
    if isinstance(value, bool):
        return [f"{prefix}: {value}"] if prefix else []
    if isinstance(value, (int, float)):
        return [f"{prefix}: {value}"] if prefix else []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return [f"{prefix}: {text}"] if prefix else [text]
    if isinstance(value, dict):
        rows: list[str] = []
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten(child, path))
        return rows
    if isinstance(value, list):
        rows = []
        for i, child in enumerate(value):
            path = f"{prefix}[{i}]" if prefix else f"[{i}]"
            rows.extend(_flatten(child, path))
        return rows
    return []


def _visible_page_text(soup: BeautifulSoup) -> str:
    body = soup.body or soup
    for tag in body.find_all(_DROP_TAGS):
        tag.decompose()
    raw = body.get_text("\n", strip=True)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    if not raw.strip():
        return ""
    return "## Page text\n" + raw.strip()
