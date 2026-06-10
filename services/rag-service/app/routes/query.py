import logging
import time

import httpx
from fastapi import APIRouter, HTTPException, Request, status

from app.config import settings
from app.models.query import RagQueryRequest, RagQueryResponse
from app.services.clients import embed_texts, generate_answer
from app.services.prompt_builder import build_rag_prompt
from app.services.semantic_cache import semantic_cache
from app.services.store import vector_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])


@router.post("/query", response_model=RagQueryResponse)
async def rag_query(payload: RagQueryRequest, request: Request):
    try:
        if vector_store.chunk_count() == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents have been indexed yet",
            )

        top_k = payload.top_k or settings.DEFAULT_TOP_K

        query_embedding = await embed_texts([payload.query])

        cached = semantic_cache.lookup(query_embedding[0], top_k=top_k)
        if cached is not None:
            logger.info(
                "semantic_cache_hit",
                extra={
                    "similarity": cached["similarity"],
                    "matched_query": cached["matched_query"],
                },
            )
            request.state.query_stats = {
                "query_count": 1,
                "cache_hit": True,
                "latency_saved_seconds": cached["generation_seconds"],
            }
            return {
                "answer": cached["answer"],
                "query": payload.query,
                "top_k": top_k,
                "sources": cached["sources"],
                "cached": True,
            }

        retrieved = vector_store.search(query_embedding[0], top_k=top_k)

        if not retrieved:
            return {
                "answer": "No relevant context was found.",
                "query": payload.query,
                "top_k": top_k,
                "sources": [],
            }

        context_chunks = [item["text"] for item in retrieved]
        prompt = build_rag_prompt(payload.query, context_chunks)

        generation_start = time.perf_counter()
        answer = await generate_answer(prompt)
        generation_seconds = time.perf_counter() - generation_start

        sources = [
            {
                "document_id": item["document_id"],
                "chunk_id": item["chunk_id"],
                "score": item["score"],
                "text": item["text"],
            }
            for item in retrieved
        ]

        semantic_cache.store(
            query=payload.query,
            query_embedding=query_embedding[0],
            top_k=top_k,
            answer=answer,
            sources=sources,
            generation_seconds=generation_seconds,
        )

        request.state.query_stats = {
            "query_count": 1,
            "cache_hit": False,
            "latency_saved_seconds": 0.0,
        }

        return {
            "answer": answer,
            "query": payload.query,
            "top_k": top_k,
            "sources": sources,
            "cached": False,
        }

    except httpx.HTTPError as exc:
        logger.exception("downstream_service_failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Downstream service failed: {str(exc)}",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("rag_query_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(exc)}",
        ) from exc
