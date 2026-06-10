import logging
import time

from fastapi import APIRouter, HTTPException, Request, status

from app.config import settings
from app.models.generation import GenerationRequest, GenerationResponse
from app.services.model_router import choose_model, fallback_model
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generation"])


@router.post("/generate", response_model=GenerationResponse)
async def generate_text(payload: GenerationRequest, request: Request):
    decision = choose_model(
        prompt=payload.prompt,
        requested_model=payload.model,
        small_model=settings.OLLAMA_SMALL_MODEL,
        large_model=settings.OLLAMA_LARGE_MODEL,
        routing_enabled=settings.ROUTING_ENABLED,
        threshold=settings.ROUTING_THRESHOLD,
    )

    logger.info(
        "model_routing_decision",
        extra={
            "model_name": decision.model,
            "decision": decision.decision,
            "difficulty": decision.difficulty,
        },
    )

    fallback_used = False
    start_time = time.perf_counter()

    try:
        try:
            result = await ollama_client.generate(
                prompt=payload.prompt,
                max_new_tokens=payload.max_new_tokens,
                temperature=payload.temperature,
                do_sample=payload.do_sample,
                model=decision.model,
            )
        except Exception:
            fallback = fallback_model(
                decision.model,
                settings.OLLAMA_SMALL_MODEL,
                settings.OLLAMA_LARGE_MODEL,
            )
            if fallback is None or decision.decision == "explicit":
                raise

            logger.exception(
                "generation_failed_falling_back",
                extra={"model_name": decision.model, "fallback_model": fallback},
            )
            fallback_used = True
            result = await ollama_client.generate(
                prompt=payload.prompt,
                max_new_tokens=payload.max_new_tokens,
                temperature=payload.temperature,
                do_sample=payload.do_sample,
                model=fallback,
            )

        duration = time.perf_counter() - start_time

        request.state.token_usage = result["usage"]
        request.state.generation_stats = {
            "model": result["model_name"],
            "decision": decision.decision,
            "fallback_used": fallback_used,
            "duration_seconds": duration,
        }

        result["routing"] = {
            "decision": decision.decision,
            "difficulty": decision.difficulty,
            "fallback_used": fallback_used,
        }
        return result

    except Exception as exc:
        logger.exception("generation_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(exc)}",
        ) from exc
