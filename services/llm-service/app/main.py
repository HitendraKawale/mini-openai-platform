import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from app.config import settings
from app.logging_config import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.routes.generate import router as generate_router
from app.routes.health import router as health_router

REQUEST_COUNT = Counter(
    "llm_request_count",
    "Total number of HTTP requests for llm-service",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "llm_request_latency_seconds",
    "HTTP request latency in seconds for llm-service",
    ["method", "path"],
)

TOKEN_USAGE = Counter(
    "llm_token_usage_total",
    "Total token usage for llm-service",
    ["type"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    yield


app = FastAPI(
    title="Mini OpenAI LLM Service",
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
async def token_metrics_middleware(request: Request, call_next):
    response = await call_next(request)

    usage = getattr(request.state, "token_usage", None)
    if usage:
        TOKEN_USAGE.labels(type="input").inc(usage["input_tokens"])
        TOKEN_USAGE.labels(type="output").inc(usage["output_tokens"])
        TOKEN_USAGE.labels(type="total").inc(usage["total_tokens"])

    return response


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(health_router)
app.include_router(generate_router)