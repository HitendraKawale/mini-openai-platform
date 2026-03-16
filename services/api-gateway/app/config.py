import os

class Settings:
    APP_NAME: str = "api-gateway" 
    APP_VERSION: str = "0.1.0"
    API_KEY: str = os.getenv("API_GATEWAY_APP_KEY", "dev-secret-key")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()