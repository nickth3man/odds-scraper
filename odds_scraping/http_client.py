"""HTTP client with retry logic, domain-aware rate limiting, and User-Agent rotation.

Replaces bare ``requests.get()`` calls with a resilient http layer that
handles transient failures transparently and respects per-domain crawl
delays to avoid overloading upstream APIs.
"""

from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

import httpx
from courlan.urlutils import get_hostinfo
from fake_useragent import UserAgent
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Shared UserAgent (caches browser list internally)
_ua_generator = UserAgent()

# Exceptions we consider transient and worth retrying
_TRANSIENT_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
    httpx.HTTPStatusError,
)


class HttpClient:
    """Thin wrapper around ``httpx`` with tenacity retry + per-domain rate limiting.

    Usage::

        http = HttpClient()
        response = http.get(url, params={'sport': 'basketball'})
        data = response.json()
        http.close()
    """

    def __init__(
        self,
        *,
        min_delay: float = 1.0,
        max_retries: int = 3,
        default_timeout: float = 10.0,
    ):
        self._min_delay = min_delay
        self._max_retries = max_retries
        self._default_timeout = default_timeout

        # Track last-request timestamp per *effective domain* (e.g. espn.com)
        self._domain_timestamps: dict[str, float] = {}

        # Create a single httpx.Client (connection pooling, keep-alive)
        self._client = httpx.Client(
            timeout=httpx.Timeout(self._default_timeout),
            headers=self._build_headers(),
        )

        # Persistent URL store to reject duplicates across the session
        self._store = self._new_url_store()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET *url* with automatic retry, rate limiting, and UA rotation.

        Raises the last ``httpx.HTTPError`` subclass after exhausting retries.
        """
        domain = self._resolve_domain(url)
        self._wait_for_domain(domain)

        # Rotate User-Agent + merge caller overrides
        merged_headers = {**self._build_headers(), **(headers or {})}

        # Build a retry decorator that retries on transient failures
        _retryer = retry(
            retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
            before_sleep=self._log_retry_attempt,
        )

        @_retryer
        def _do_request() -> httpx.Response:
            response = self._client.get(url, params=params, headers=merged_headers)
            response.raise_for_status()
            return response

        self._domain_timestamps[domain] = time.monotonic()
        return _do_request()

    def close(self) -> None:
        """Close the underlying ``httpx.Client`` and free resources."""
        self._client.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_headers() -> dict[str, str]:
        return {
            'User-Agent': _ua_generator.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    @staticmethod
    def _new_url_store():
        """Return a fresh courlan.UrlStore (no compression, default settings)."""
        from courlan import UrlStore

        return UrlStore(compressed=False)

    def _resolve_domain(self, url: str) -> str:
        """Extract a rate-limiting key from *url* (e.g. 'espn.com')."""
        hostinfo = get_hostinfo(url)
        if hostinfo is not None and hostinfo[0] is not None:
            return hostinfo[0]
        return urlparse(url).netloc

    def _wait_for_domain(self, domain: str) -> None:
        """Sleep if *domain* was accessed too recently."""
        if domain not in self._domain_timestamps:
            return
        elapsed = time.monotonic() - self._domain_timestamps[domain]
        wait_time = self._min_delay - elapsed
        if wait_time > 0:
            logger.debug('Rate limiting %s: sleeping %.2fs', domain, wait_time)
            time.sleep(wait_time)

    @staticmethod
    def _log_retry_attempt(retry_state) -> None:
        """Callback invoked by tenacity before each retry sleep."""
        attempt = retry_state.attempt_number
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        logger.warning(
            'HTTP retry %d/%d — %s: %s',
            attempt,
            retry_state.retry_object.stop.max_attempt_number,  # type: ignore[union-attr]
            type(exc).__name__ if exc else 'unknown',
            exc,
        )
