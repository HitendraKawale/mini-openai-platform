from app.services.chunking import chunk_text


def test_chunk_text_returns_overlapping_chunks():
    text = " ".join([f"word{i}" for i in range(300)])

    chunks = chunk_text(
        text,
        chunk_size_words=100,
        chunk_overlap_words=20,
    )

    assert len(chunks) == 4
    assert chunks[0].startswith("word0")
    assert chunks[1].startswith("word80")
    assert chunks[2].startswith("word160")
    assert chunks[3].startswith("word240")


def test_chunk_text_handles_short_input():
    text = "vector databases support semantic search"

    chunks = chunk_text(
        text,
        chunk_size_words=100,
        chunk_overlap_words=20,
    )

    assert len(chunks) == 1
    assert chunks[0] == text
