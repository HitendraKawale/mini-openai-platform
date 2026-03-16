from pathlib import Path


class TextExtractionError(Exception):
    pass


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix not in {".txt", ".md"}:
        raise TextExtractionError(
            "Only .txt and .md files are supported in Stage 6"
        )

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TextExtractionError("File must be valid UTF-8 text") from exc

    cleaned = text.strip()
    if not cleaned:
        raise TextExtractionError("Uploaded file is empty")

    return cleaned