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


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    vector_store.initialize()
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

    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(documents_router)
app.include_router(query_router)