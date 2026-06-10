import os


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings:
    APP_NAME: str = "api-gateway"
    APP_VERSION: str = "0.1.0"
    # API_GATEWAY_API_KEYS takes a comma-separated list; the singular
    # API_GATEWAY_API_KEY is kept for backwards compatibility.
    API_KEYS: frozenset = frozenset(
        _parse_csv(
            os.getenv("API_GATEWAY_API_KEYS")
            or os.getenv("API_GATEWAY_API_KEY", "dev-secret-key")
        )
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    CORS_ALLOWED_ORIGINS: list = _parse_csv(
        os.getenv("CORS_ALLOWED_ORIGINS", "*")
    )

    MAX_UPLOAD_BYTES: int = int(
        os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024))
    )

    LLM_SERVICE_URL: str = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")
    EMBEDDING_SERVICE_URL: str = os.getenv(
        "EMBEDDING_SERVICE_URL",
        "http://localhost:8002",
    )
    RAG_SERVICE_URL: str = os.getenv("RAG_SERVICE_URL", "http://localhost:8003")

    REQUEST_TIMEOUT_SECONDS: float = float(
        os.getenv("REQUEST_TIMEOUT_SECONDS", "120")
    )

    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(
        os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    )

    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "120"))


settings = Settings()