from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from code.loading.corpus import CORPUS
from code.loading.extract import is_empty_document, parse_readable_text
from code.loading.fetch import fetch_html
from code.paths import DATA_RAW


class EmptyDocumentError(RuntimeError):
    pass


def load_corpus(output_dir: Path | None = None) -> list[dict[str, Any]]:
    """Fetch the five PRD URLs only. Fail loudly on empty or unreadable pages."""
    dest = output_dir or DATA_RAW
    dest.mkdir(parents=True, exist_ok=True)
    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    documents: list[dict[str, Any]] = []

    for entry in CORPUS:
        html = fetch_html(entry["source_url"])
        text = parse_readable_text(html)
        if is_empty_document(text):
            raise EmptyDocumentError(
                f"No usable text from {entry['source_url']}; "
                "not substituting another URL or source."
            )
        document = {
            "source_url": entry["source_url"],
            "fund_name": entry["fund_name"],
            "theme": entry["theme"],
            "ingested_at": ingested_at,
            "text": text,
        }
        path = dest / f"{entry['slug']}.json"
        path.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        documents.append(document)

    return documents
