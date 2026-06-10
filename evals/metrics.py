"""Pure metric functions for the RAG evaluation harness."""

import re


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def find_hit_rank(source_texts: list[str], expected_phrases: list[str]) -> int | None:
    """1-based rank of the first retrieved chunk containing any expected
    phrase, or None if no chunk matches."""
    phrases = [normalize(p) for p in expected_phrases]

    for rank, text in enumerate(source_texts, start=1):
        chunk = normalize(text)
        if any(phrase in chunk for phrase in phrases):
            return rank

    return None


def hit_rate(ranks: list[int | None]) -> float:
    """Fraction of queries where a relevant chunk was retrieved at all
    (recall@k for k = number of retrieved chunks)."""
    if not ranks:
        return 0.0
    return sum(1 for rank in ranks if rank is not None) / len(ranks)


def mean_reciprocal_rank(ranks: list[int | None]) -> float:
    if not ranks:
        return 0.0
    return sum(1.0 / rank for rank in ranks if rank is not None) / len(ranks)
