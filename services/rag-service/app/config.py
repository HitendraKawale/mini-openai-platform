import os


class Settings:
    APP_NAME: str = "rag-service"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    EMBEDDING_SERVICE_URL: str = os.getenv(
        "EMBEDDING_SERVICE_URL",
        "http://localhost:8002",
    )
    LLM_SERVICE_URL: str = os.getenv(
        "LLM_SERVICE_URL",
        "http://localhost:8001",
    )

    REQUEST_TIMEOUT_SECONDS: float = float(
        os.getenv("REQUEST_TIMEOUT_SECONDS", "120")
    )

    CHUNK_SIZE_WORDS: int = int(os.getenv("CHUNK_SIZE_WORDS", "120"))
    CHUNK_OVERLAP_WORDS: int = int(os.getenv("CHUNK_OVERLAP_WORDS", "20"))
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "3"))

    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION_NAME: str = os.getenv(
        "QDRANT_COLLECTION_NAME",
        "rag_chunks",
    )
    QDRANT_TIMEOUT_SECONDS: float = float(
        os.getenv("QDRANT_TIMEOUT_SECONDS", "30")
    )
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE", "384"))

    SEMANTIC_CACHE_ENABLED: bool = (
        os.getenv("SEMANTIC_CACHE_ENABLED", "true").lower() == "true"
    )
    SEMANTIC_CACHE_COLLECTION_NAME: str = os.getenv(
        "SEMANTIC_CACHE_COLLECTION_NAME",
        "rag_semantic_cache",
    )
    SEMANTIC_CACHE_SIMILARITY_THRESHOLD: float = float(
        os.getenv("SEMANTIC_CACHE_SIMILARITY_THRESHOLD", "0.95")
    )
    SEMANTIC_CACHE_TTL_SECONDS: float = float(
        os.getenv("SEMANTIC_CACHE_TTL_SECONDS", "600")
    )


settings = Settings()