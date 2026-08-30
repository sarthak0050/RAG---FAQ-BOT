from __future__ import annotations

import sys

from code.loading.fetch import FetchError
from code.loading.loader import EmptyDocumentError, load_corpus
from code.paths import DATA_RAW


def main() -> int:
    try:
        documents = load_corpus()
    except (FetchError, EmptyDocumentError) as exc:
        print(f"DATA LOADING FAILED: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {len(documents)} documents to {DATA_RAW}")
    for doc in documents:
        print(f"  - {doc['theme']}: {doc['fund_name']} ({len(doc['text'])} chars)")
    print(f"Last updated from sources: {documents[0]['ingested_at']}")
    return 0
