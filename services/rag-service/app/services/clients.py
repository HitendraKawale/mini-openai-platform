import httpx

from app.config import settings


async def embed_texts(texts: list[str]) -> list[list[float]]:
    payload = {
        "input": texts,
    }

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{settings.EMBEDDING_SERVICE_URL}/embed",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return [item["embedding"] for item in data["data"]]


async def generate_answer(prompt: str, max_new_tokens: int = 160) -> str:
    payload = {
        "prompt": prompt,
        "max_new_tokens": max_new_tokens,
        "temperature": 0.2,
        "do_sample": True,
    }

    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        response = await client.post(
            f"{settings.LLM_SERVICE_URL}/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return data["generated_text"]