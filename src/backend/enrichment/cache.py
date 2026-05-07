"""Simple TTL-based in-memory cache for stats.nba.com responses."""

from __future__ import annotations

import threading
import time
from typing import TypeVar

T = TypeVar('T')


class TTLCache[T]:
    """Thread-safe TTL cache. Team stats cache for 4 hours, standings for 24 hours."""

    def __init__(self, default_ttl: float = 14400.0):
        """
        Initialize the TTLCache with an optional default time-to-live for entries and an empty internal store.

        Parameters:
            default_ttl (float): Default time-to-live for cache entries in seconds (defaults to 14400.0, i.e., 4 hours).
        """
        self._store: dict[str, tuple[float, T]] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> T | None:
        """
        Retrieve the cached value for the given key if present and not expired.
        
        If the entry exists but has expired, it is removed from the cache.
        
        Returns:
            The cached value associated with `key` if present and not expired, `None` otherwise.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: T, ttl: float | None = None) -> None:
        """
        Store a value under the given key with an expiration based on the provided TTL or the cache's default.
        
        The entry will be considered expired after `ttl` seconds from now or after the cache's default TTL when `ttl` is `None`.
        
        Parameters:
            key (str): Cache key.
            value (T): Value to store.
            ttl (float | None): Optional time-to-live in seconds; if `None`, the cache's default TTL is used.
        """
        with self._lock:
            expires_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
            self._store[key] = (expires_at, value)

    def clear(self) -> None:
        """
        Clear all entries from the cache.

        Removes every stored key and value (including expired and unexpired entries), resetting the cache to an empty state.
        """
        with self._lock:
            self._store.clear()
