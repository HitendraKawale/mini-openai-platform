from app.config import settings


def chunk_text(
    text: str,
    chunk_size_words: int | None = None,
    chunk_overlap_words: int | None = None,
) -> list[str]:
    chunk_size = chunk_size_words or settings.CHUNK_SIZE_WORDS
    overlap = chunk_overlap_words or settings.CHUNK_OVERLAP_WORDS

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    step = max(chunk_size - overlap, 1)

    for start in range(0, len(words), step):
        end = start + chunk_size
        chunk_words = words[start:end]
        if not chunk_words:
            continue

        chunk = " ".join(chunk_words).strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

    return chunks