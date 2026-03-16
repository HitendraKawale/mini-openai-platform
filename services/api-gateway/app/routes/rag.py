import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.middleware.auth import verify_api_key
from app.models.rag import RagQueryRequest
from app.services.downstream_client import post_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/rag", tags=["rag"])


@router.post("/query", dependencies=[Depends(verify_api_key)])
async def rag_query(payload: RagQueryRequest, request: Request):
    try:
        downstream_payload = {
            "query": payload.query,
            "top_k": payload.top_k,
        }

        result = await post_json(
            url=f"{settings.RAG_SERVICE_URL}/query",
            payload=downstream_payload,
            request_id=request.state.request_id,
        )

        return result

    except httpx.HTTPStatusError as exc:
        logger.exception("rag_service_http_error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"RAG service returned an error: {exc.response.text}",
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("rag_service_unreachable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"RAG service unreachable: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.exception("rag_query_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway RAG query failed: {str(exc)}",
        ) from exc