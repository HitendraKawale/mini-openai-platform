from fastapi import APIRouter

from app.config import settings
from app.services.ollama_client import ollama_client

router = APIRouter()


@router.get("/health")
async def health_check():
    available_models = await ollama_client.list_models()
    ollama_reachable = bool(available_models)

    return {
        "status": "ok" if ollama_reachable else "degraded",
        "service": "llm-service",
        "provider": "ollama",
        "routing_enabled": settings.ROUTING_ENABLED,
        "small_model": settings.OLLAMA_SMALL_MODEL,
        "large_model": settings.OLLAMA_LARGE_MODEL,
        "small_model_available": settings.OLLAMA_SMALL_MODEL in available_models,
        "large_model_available": settings.OLLAMA_LARGE_MODEL in available_models,
        "ollama_reachable": ollama_reachable,
    }
