import secrets

from fastapi import Header, HTTPException, status
from app.config import settings

async def verify_api_key(authorization: str = Header(default=None)) -> None:
    if authorization is None or not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    token = authorization.removeprefix("Bearer ").strip()

    authorized = any(
        secrets.compare_digest(token, key) for key in settings.API_KEYS
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
