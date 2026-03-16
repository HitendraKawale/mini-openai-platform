import hashlib
import json
import time
from typing import Any


class TTLCache:
    def __init__(self) -> None:
        self.store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self.store.get(key)
        if entry is None:
            return None

        expires_at, value = entry
        if time.monotonic() >= expires_at:
            self.store.pop(key, None)
            return None

        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        expires_at = time.monotonic() + ttl_seconds
        self.store[key] = (expires_at, value)

    def make_key(self, namespace: str, payload: dict) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"


gateway_cache = TTLCache()