from fastapi import APIRouter, Depends, Request

from app.middleware.auth import verify_api_key
from app.models.embeddings import EmbeddingRequest

router = APIRouter(prefix="/v1", tags=["embeddings"])

@router.post("/embeddings", dependencies=[Depends(verify_api_key)])
async def create_embeddings(payload: EmbeddingRequest, request: Request):
    input_count = len(payload.input) if isinstance(payload.input, list) else 1

    return {
        "message": "Emeddings endpoint reached",
        "request_id": request.state.request_id,
        "received_model": payload.model,
        "received_input_count": input_count
    } 