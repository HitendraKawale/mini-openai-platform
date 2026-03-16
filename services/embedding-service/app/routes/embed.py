import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.config import settings
from app.models.embeddings import EmbeddingRequest, EmbeddingResponse
from app.services.embedding_registry import embedding_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["embeddings"])


@router.post("/embed", response_model=EmbeddingResponse)
async def create_embeddings(payload: EmbeddingRequest, request: Request):
    try:
        texts = payload.input if isinstance(payload.input, list) else [payload.input]
        normalize = (
            payload.normalize
            if payload.normalize is not None
            else settings.NORMALIZE_EMBEDDINGS
        )

        result = embedding_registry.embed(texts=texts, normalize=normalize)
        request.state.embedding_usage = result["usage"]

        return result

    except Exception as exc:
        logger.exception("embedding_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Embedding failed: {str(exc)}",
        ) from exc