import asyncio
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(deque)
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/metrics"}:
            return await call_next(request)

        identifier = self._get_identifier(request)
        now = time.monotonic()
        window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS

        async with self.lock:
            bucket = self.requests[identifier]

            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= settings.RATE_LIMIT_REQUESTS:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": (
                            f"Rate limit exceeded: max "
                            f"{settings.RATE_LIMIT_REQUESTS} requests per "
                            f"{settings.RATE_LIMIT_WINDOW_SECONDS} seconds"
                        )
                    },
                )

            bucket.append(now)

        return await call_next(request)

    def _get_identifier(self, request: Request) -> str:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            if token:
                return f"token:{token}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"