import os


class Settings:
    APP_NAME: str = "llm-service"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:latest")
    DEFAULT_MAX_NEW_TOKENS: int = int(os.getenv("DEFAULT_MAX_NEW_TOKENS", "128"))
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))

    ROUTING_ENABLED: bool = (
        os.getenv("ROUTING_ENABLED", "false").lower() == "true"
    )
    OLLAMA_SMALL_MODEL: str = os.getenv("OLLAMA_SMALL_MODEL", "llama3.2:3b")
    OLLAMA_LARGE_MODEL: str = os.getenv(
        "OLLAMA_LARGE_MODEL",
        os.getenv("OLLAMA_MODEL", "phi3:latest"),
    )
    ROUTING_THRESHOLD: float = float(os.getenv("ROUTING_THRESHOLD", "0.3"))


settings = Settings()