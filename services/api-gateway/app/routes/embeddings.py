import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.middleware.auth import verify_api_key
from app.models.embeddings import EmbeddingRequest
from app.services.cache import gateway_cache
from app.services.downstream_client import post_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["embeddings"])


@router.post("/embeddings", dependencies=[Depends(verify_api_key)])
async def create_embeddings(payload: EmbeddingRequest, request: Request):
    try:
        downstream_payload = {
            "input": payload.input,
        }

        cache_key = gateway_cache.make_key("embeddings", downstream_payload)

        if settings.CACHE_ENABLED:
            cached = gateway_cache.get(cache_key)
            if cached is not None:
                return cached

        result = await post_json(
            url=f"{settings.EMBEDDING_SERVICE_URL}/embed",
            payload=downstream_payload,
            request_id=request.state.request_id,
        )

        response_payload = {
            "object": "list",
            "model": result["model_name"],
            "data": result["data"],
            "usage": result["usage"],
        }

        if settings.CACHE_ENABLED:
            gateway_cache.set(
                cache_key,
                response_payload,
                settings.CACHE_TTL_SECONDS,
            )

        return response_payload

    except httpx.HTTPStatusError as exc:
        logger.exception("embedding_service_http_error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding service returned an error: {exc.response.text}",
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("embedding_service_unreachable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding service unreachable: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.exception("embedding_request_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway embedding request failed: {str(exc)}",
        ) from exc