import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.config import settings
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.routes.chat import router as chat_router
from app.routes.documents import router as documents_router
from app.routes.embeddings import router as embeddings_router
from app.routes.health import router as health_router
from app.routes.rag import router as rag_router

REQUEST_COUNT = Counter(
    "request_count", 
    "Total number of HTTP requests",
    ["method", "path", "status_code" ],
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    yield


app = FastAPI(
    title="Mini OpenAI API Gateway",
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


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(chat_router)
app.include_router(embeddings_router)
app.include_router(rag_router)
app.include_router(documents_router)