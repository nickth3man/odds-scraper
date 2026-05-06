# odds-scraper Style Guide

## Architecture
- **Layered Architecture:** Frontend (NiceGUI) -> Orchestrator (LiveOddsScraper) -> Shared Infrastructure -> Models & Enrichment.
- **DraftKings parser fallback:** Follow the 3-layer parser fallback (parsel CSS selectors -> cb-market Playwright -> event-cell Playwright).
- **ESPN parser fallback:** JSON API -> scoreboard fallback.
- **Shared HTTP:** Use `HttpClient` in `src/backend/scrapers/shared/http_client.py` for all network calls (it handles retries, rate limiting, UA rotation, and TLS impersonation). Do not use bare `requests` or `httpx` outside this class.

## Security & Safety (BLOCKERS)
- **NO** cookies, authorization headers, account data, local browser profiles, or private location data committed.
- **NO** paid CI tools, paid security scanners, or paid SaaS dependencies (beyond CodeRabbit, Sourcery, Qodo).
- **NO** live network calls in tests. Tests must be offline-first using fixtures.
- Playwright operations must use `try/finally` for cleanup.

## Python Style & Best Practices
- **Version:** Python 3.12+ only.
- Require `from __future__ import annotations` at the top of every new Python file.
- Use Loguru (`from loguru import logger`) for logging. Do NOT use `print()`.
- `parse_american_odds()` must return `None` for malformed input, not raise an exception.
- Kelly criterion in EV calculations must be capped at 5% (0.05).
- Use TypedDict (`GameOdds`) with `total=False` for optional enrichment fields.
- Use Ruff for formatting (100 char limit, single quotes).
- Type checking uses pyright (blocking) and ty (advisory). Fix all pyright errors.

## Testing
- Ensure tests are offline and fixture-based.
- Use `FakeElement` / `FakePage` for offline Playwright mocks.
- Maintain test coverage > 80%.
