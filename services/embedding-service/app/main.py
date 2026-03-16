import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.config import settings
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.routes.embed import router as embed_router
from app.routes.health import router as health_router
from app.services.embedding_registry import embedding_registry

REQUEST_COUNT = Counter(
    "embedding_request_count",
    "Total number of HTTP requests for embedding-service",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "embedding_request_latency_seconds",
    "HTTP request latency in seconds for embedding-service",
    ["method", "path"],
)

EMBED_INPUT_COUNT = Counter(
    "embedding_input_total",
    "Total number of texts embedded",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    embedding_registry.load()
    yield


app = FastAPI(
    title="Mini OpenAI Embedding Service",
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
async def embedding_metrics_middleware(request: Request, call_next):
    response = await call_next(request)

    usage = getattr(request.state, "embedding_usage", None)
    if usage:
        EMBED_INPUT_COUNT.inc(usage["input_count"])

    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(embed_router)