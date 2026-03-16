import logging

import httpx
from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status

from app.models.documents import DocumentUploadResponse
from app.services.chunking import chunk_text
from app.services.clients import embed_texts
from app.services.store import new_document_id, vector_store
from app.services.text_extractor import TextExtractionError, extract_text

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(request: Request, file: UploadFile = File(...)):
    try:
        raw_content = await file.read()
        text = extract_text(file.filename, raw_content)
        chunks = chunk_text(text)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No chunks were created from the document",
            )

        embeddings = await embed_texts(chunks)

        document_id = new_document_id()
        vector_store.add_document_chunks(
            document_id=document_id,
            filename=file.filename,
            chunks=chunks,
            embeddings=embeddings,
        )

        request.state.document_upload_stats = {
            "chunk_count": len(chunks),
        }

        return {
            "document_id": document_id,
            "filename": file.filename,
            "chunk_count": len(chunks),
            "chunks": chunks,
        }

    except TextExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("embedding_service_call_failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Embedding service failed: {str(exc)}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("document_upload_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(exc)}",
        ) from exc