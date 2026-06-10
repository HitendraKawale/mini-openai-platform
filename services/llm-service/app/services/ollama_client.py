import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_MODEL
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                return True
        except Exception:
            logger.exception("ollama_health_check_failed")
            return False

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception:
            logger.exception("ollama_list_models_failed")
            return []

    async def generate(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        do_sample: bool,
        model: str | None = None,
    ) -> dict:
        model_name = model or self.model_name

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_new_tokens,
                "temperature": temperature,
            },
        }

        logger.info(
            "ollama_generate_request",
            extra={
                "model_name": model_name,
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "do_sample": do_sample,
            },
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        generated_text = data.get("response", "").strip()
        input_tokens = int(data.get("prompt_eval_count", 0))
        output_tokens = int(data.get("eval_count", 0))
        total_tokens = input_tokens + output_tokens

        return {
            "generated_text": generated_text,
            "model_name": data.get("model", model_name),
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            },
        }


ollama_client = OllamaClient()