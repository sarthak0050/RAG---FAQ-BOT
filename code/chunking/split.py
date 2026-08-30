from __future__ import annotations


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split one document's text. Never called on concatenated multi-URL text."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    body = (text or "").strip()
    if not body:
        return []
    if len(body) <= chunk_size:
        return [body]

    pieces: list[str] = []
    start = 0
    n = len(body)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            window = body[start:end]
            break_at = _best_break(window)
            if break_at is not None:
                end = start + break_at
        piece = body[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= n:
            break
        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = end
        start = next_start
    return pieces


def _best_break(window: str) -> int | None:
    """Prefer a newline in the latter part of the window so FAQ key lines stay intact."""
    min_pos = max(len(window) // 4, 1)
    newline = window.rfind("\n")
    if newline >= min_pos:
        return newline
    space = window.rfind(" ")
    if space >= min_pos:
        return space
    return None
