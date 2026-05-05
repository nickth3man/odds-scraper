"""Simple TTL-based in-memory cache for stats.nba.com responses."""

from __future__ import annotations

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

    def get(self, key: str) -> T | None:
        """
        Retrieve the cached value for `key` if it exists and has not expired.
        
        If the stored entry has expired, it is removed from the cache and `None` is returned.
        
        Returns:
            The cached value for `key` if present and not expired, `None` otherwise.
        """
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
        Store a value in the cache under the given key with an associated time-to-live.
        
        If `ttl` is provided it overrides the cache's default TTL; `ttl` is specified in seconds and controls how long the entry remains valid before expiring.
        
        Parameters:
        	key (str): Cache key to store the value under.
        	value (T): Value to cache.
        	ttl (float | None): Optional time-to-live in seconds; when `None` the cache's default TTL is used.
        """
        expires_at = time.monotonic() + (ttl or self._default_ttl)
        self._store[key] = (expires_at, value)

    def clear(self) -> None:
        """
        Clear all entries from the cache.
        
        Removes every stored key and value (including expired and unexpired entries), resetting the cache to an empty state.
        """
        self._store.clear()
