from fastapi import APIRouter,  Depends, Request
from app.middleware.auth import verify_api_key
from app.models.rag import RagQueryRequest

router = APIRouter(
    prefix="/v1/rag",
    tags=["RAG"],
)

@router.post("/query", dependencies=[Depends(verify_api_key)])
async def query_rag(request: Request, payload: RagQueryRequest):
    return {
        "message": "RAG query point reached",
        "request_id": request.state.request_id, 
        "query": payload.query,
        "top_k": payload.top_k,
    }