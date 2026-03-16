from fastapi import APIRouter

from app.services.ollama_client import ollama_client

router = APIRouter()


@router.get("/health")
async def health_check():
    ollama_reachable = await ollama_client.health_check()

    return {
        "status": "ok" if ollama_reachable else "degraded",
        "service": "llm-service",
        "provider": "ollama",
        "model_name": ollama_client.model_name,
        "ollama_reachable": ollama_reachable,
    }