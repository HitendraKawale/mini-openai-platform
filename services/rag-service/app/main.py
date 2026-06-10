import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.config import settings
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.routes.documents import router as documents_router
from app.routes.health import router as health_router
from app.routes.query import router as query_router
from app.services.semantic_cache import semantic_cache
from app.services.store import vector_store

REQUEST_COUNT = Counter(
    "rag_request_count",
    "Total number of HTTP requests for rag-service",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "rag_request_latency_seconds",
    "HTTP request latency in seconds for rag-service",
    ["method", "path"],
)

UPLOADED_CHUNKS = Counter(
    "rag_uploaded_chunks_total",
    "Total number of chunks uploaded to rag-service",
)

RAG_QUERIES = Counter(
    "rag_queries_total",
    "Total number of RAG queries handled",
)

SEMANTIC_CACHE_HITS = Counter(
    "rag_semantic_cache_hits_total",
    "Total number of RAG queries served from the semantic cache",
)

SEMANTIC_CACHE_MISSES = Counter(
    "rag_semantic_cache_misses_total",
    "Total number of RAG queries that missed the semantic cache",
)

SEMANTIC_CACHE_LATENCY_SAVED = Counter(
    "rag_semantic_cache_latency_saved_seconds_total",
    "Estimated LLM generation seconds skipped thanks to semantic cache hits",
)

RETRIEVAL_TOP_SCORE = Histogram(
    "rag_retrieval_top_score",
    "Similarity score of the best retrieved chunk per query",
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
)

INSUFFICIENT_CONTEXT_ANSWERS = Counter(
    "rag_insufficient_context_answers_total",
    "Number of generated answers that said the context was insufficient",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    vector_store.initialize()
    semantic_cache.initialize()
    yield


app = FastAPI(
    title="Mini OpenAI RAG Service",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestContextMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status_code=str(response.status_code),
    ).inc()

    REQUEST_LATENCY.labels(
        method=request.method,
        path=request.url.path,
    ).observe(duration)

    return response


@app.middleware("http")
async def rag_stats_middleware(request: Request, call_next):
    response = await call_next(request)

    document_stats = getattr(request.state, "document_upload_stats", None)
    if document_stats:
        UPLOADED_CHUNKS.inc(document_stats["chunk_count"])

    query_stats = getattr(request.state, "query_stats", None)
    if query_stats:
        RAG_QUERIES.inc(query_stats["query_count"])

        if query_stats.get("cache_hit"):
            SEMANTIC_CACHE_HITS.inc()
            SEMANTIC_CACHE_LATENCY_SAVED.inc(
                query_stats.get("latency_saved_seconds", 0.0)
            )
        elif "cache_hit" in query_stats:
            SEMANTIC_CACHE_MISSES.inc()

        if query_stats.get("top_score") is not None:
            RETRIEVAL_TOP_SCORE.observe(query_stats["top_score"])

        if query_stats.get("insufficient_context"):
            INSUFFICIENT_CONTEXT_ANSWERS.inc()

    retrieval_stats = getattr(request.state, "retrieval_stats", None)
    if retrieval_stats and retrieval_stats.get("top_score") is not None:
        RETRIEVAL_TOP_SCORE.observe(retrieval_stats["top_score"])

    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(documents_router)
app.include_router(query_router)