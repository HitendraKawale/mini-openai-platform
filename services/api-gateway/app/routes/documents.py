import logging

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.config import settings
from app.middleware.auth import verify_api_key
from app.services.downstream_client import post_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.post("/upload", dependencies=[Depends(verify_api_key)])
async def upload_document(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()

        result = await post_file(
            url=f"{settings.RAG_SERVICE_URL}/documents/upload",
            filename=file.filename,
            content=contents,
            content_type=file.content_type,
            request_id=request.state.request_id,
        )

        return result

    except httpx.HTTPStatusError as exc:
        logger.exception("rag_document_upload_http_error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"RAG service returned an error: {exc.response.text}",
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("rag_document_upload_unreachable")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"RAG service unreachable: {str(exc)}",
        ) from exc
    except Exception as exc:
        logger.exception("gateway_document_upload_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway document upload failed: {str(exc)}",
        ) from exc