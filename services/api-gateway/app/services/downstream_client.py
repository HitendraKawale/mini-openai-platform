import httpx

from app.config import settings


async def post_json(
    url: str,
    payload: dict,
    request_id: str,
) -> dict:
    headers = {
        "X-Request-ID": request_id,
    }

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


async def post_file(
    url: str,
    filename: str,
    content: bytes,
    content_type: str | None,
    request_id: str,
) -> dict:
    headers = {
        "X-Request-ID": request_id,
    }

    files = {
        "file": (
            filename,
            content,
            content_type or "application/octet-stream",
        )
    }

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(url, files=files, headers=headers)
        response.raise_for_status()
        return response.json()