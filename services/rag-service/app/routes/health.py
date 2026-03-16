import httpx
from fastapi import APIRouter

from app.config import settings
from app.services.store import vector_store

router = APIRouter()


@router.get("/health")
async def health_check():
    embedding_ok = False
    llm_ok = False

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            embed_resp = await client.get(f"{settings.EMBEDDING_SERVICE_URL}/health")
            embedding_ok = embed_resp.status_code == 200
        except Exception:
            embedding_ok = False

        try:
            llm_resp = await client.get(f"{settings.LLM_SERVICE_URL}/health")
            llm_ok = llm_resp.status_code == 200
        except Exception:
            llm_ok = False

    return {
        "status": "ok" if embedding_ok and llm_ok else "degraded",
        "service": "rag-service",
        "embedding_service_reachable": embedding_ok,
        "llm_service_reachable": llm_ok,
        "indexed_documents": vector_store.document_count(),
        "indexed_chunks": vector_store.chunk_count(),
    }