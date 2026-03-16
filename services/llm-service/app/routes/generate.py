import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.models.generation import GenerationRequest, GenerationResponse
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenerationResponse)
async def generate_text(payload: GenerationRequest, request: Request):
    try:
        result = await ollama_client.generate(
            prompt=payload.prompt,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
            do_sample=payload.do_sample,
        )

        request.state.token_usage = result["usage"]
        return result

    except Exception as exc:
        logger.exception("generation_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(exc)}",
        ) from exc