from fastapi import APIRouter

from app.services.embedding_registry import embedding_registry

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "embedding-service",
        "model_loaded": embedding_registry.is_ready(),
        "model_name": embedding_registry.model_name,
    }