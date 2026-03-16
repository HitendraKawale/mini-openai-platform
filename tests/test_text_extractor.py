import pytest

from app.services.text_extractor import TextExtractionError, extract_text


def test_extract_text_accepts_txt():
    content = b"hello from a text file"
    result = extract_text("notes.txt", content)

    assert result == "hello from a text file"


def test_extract_text_rejects_unsupported_extension():
    content = b"%PDF-1.4 fake data"

    with pytest.raises(TextExtractionError):
        extract_text("document.pdf", content)
