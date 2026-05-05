"""Simple TTL-based in-memory cache for stats.nba.com responses."""

from __future__ import annotations

import time
from typing import TypeVar

T = TypeVar('T')


class TTLCache[T]:
    """Thread-safe TTL cache. Team stats cache for 4 hours, standings for 24 hours."""

    def __init__(self, default_ttl: float = 14400.0):
        self._store: dict[str, tuple[float, T]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: T, ttl: float | None = None) -> None:
        expires_at = time.monotonic() + (ttl or self._default_ttl)
        self._store[key] = (expires_at, value)

    def clear(self) -> None:
        self._store.clear()
