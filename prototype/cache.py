import time
from typing import Any


def normalize_query(query: str) -> str:
    return " ".join(query.lower().strip().split())


def cache_key(query: str, zip_code: str) -> str:
    return f"{zip_code}:{normalize_query(query)}"


class TTLCache:
    def __init__(self, default_ttl_seconds: int = 45) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def _purge_expired(self) -> None:
        now = time.time()
        dead = [k for k, (exp, _) in self._store.items() if now >= exp]
        for key in dead:
            self._store.pop(key, None)

    def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._store[key] = (time.time() + ttl, value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def size(self) -> int:
        self._purge_expired()
        return len(self._store)
