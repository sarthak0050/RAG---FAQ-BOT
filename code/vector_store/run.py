from __future__ import annotations

import sys

from code.paths import DATA_CHROMA
from code.vector_store.store import VectorStoreError, index_corpus


def main() -> int:
    try:
        meta = index_corpus()
    except VectorStoreError as exc:
        print(f"VECTOR STORE FAILED: {exc}", file=sys.stderr)
        return 1

    print(
        f"Indexed {meta['count']} chunks into ChromaDB collection "
        f"'{meta['collection']}' at {DATA_CHROMA}"
    )
    print(
        f"  model={meta['model']}  dim={meta['dim']}  space={meta['space']}  "
        f"ingested_at={meta['ingested_at']}"
    )
    return 0