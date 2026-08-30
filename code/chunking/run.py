from __future__ import annotations

import sys
from collections import Counter

from code.chunking.chunker import ChunkingError, chunk_corpus
from code.chunking.config import CHUNK_OVERLAP, CHUNK_SIZE
from code.paths import DATA_CHUNKS


def main() -> int:
    try:
        chunks = chunk_corpus()
    except ChunkingError as exc:
        print(f"CHUNKING FAILED: {exc}", file=sys.stderr)
        return 1

    by_url = Counter(c["source_url"] for c in chunks)
    print(
        f"Wrote {len(chunks)} chunks to {DATA_CHUNKS} "
        f"(size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})"
    )
    for url, count in by_url.items():
        print(f"  - {count} chunks  {url}")
    return 0
