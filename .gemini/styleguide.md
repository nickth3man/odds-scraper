# odds-scraper Style Guide

## Architecture
- **Layered Architecture:** Frontend (NiceGUI) -> Orchestrator (LiveOddsScraper) -> Shared Infrastructure -> Domain Models, Enrichment, and Historical Data.
- **Domain model:** Scrapers emit `list[Market]` using `Market`, `Outcome`, and `NormalizedOdds` from `src/backend/models/domain.py`.
- **Historical data/modeling:** NBA ingestion, leak-free rolling features, Elo/historical baselines, evaluation, and backtesting live in `src/backend/data/`.
- **DraftKings parser fallback:** Follow the 3-layer parser fallback (parsel CSS selectors -> cb-market Playwright -> event-cell Playwright).
- **ESPN parser fallback:** JSON API -> scoreboard fallback.
- **Shared HTTP:** Use `HttpClient` in `src/backend/scrapers/shared/http_client.py` for all network calls (it handles retries, rate limiting, UA rotation, and TLS impersonation). Do not use bare `requests` or `httpx` outside this class.

## Security & Safety (BLOCKERS)
- **NO** cookies, authorization headers, account data, local browser profiles, or private location data committed.
- **NO** paid CI tools, paid security scanners, or paid SaaS dependencies (beyond CodeRabbit, Sourcery, Qodo).
- **NO** live network calls in tests. Tests must be offline-first using fixtures.
- **NO** committed raw datasets, generated model artifacts, or sportsbook account/location data.
- Playwright operations must use `try/finally` for cleanup.

## Python Style & Best Practices
- **Version:** Python 3.12+ only.
- Require `from __future__ import annotations` at the top of every new Python file.
- Use Loguru (`from loguru import logger`) for logging. Do NOT use `print()`.
- Parser helpers such as `parse_american_odds()` must return `None` for malformed sportsbook input, not raise an exception.
- Kelly criterion in EV calculations must be capped at 5% (0.05).
- Use TypedDict (`GameOdds`) with `total=False` for optional enrichment fields.
- Use Ruff for formatting (100 char limit, single quotes).
- Type checking uses pyright (blocking) and ty (advisory). Fix all pyright errors.

## Data & Modeling
- Build pre-game features only from data available before the game.
- Rolling features must be lagged (`shift(1)` or equivalent) and season-scoped unless an explicit prior is documented.
- Use chronological or walk-forward validation; do not use random splits for sports time-series data.
- Evaluate probability models with Brier score and log-loss. Accuracy alone is not sufficient.
- Compare model probabilities against de-vigged market-implied probabilities.
- Backtests must use odds snapshots available at the simulated bet time.
- Invalid or unavailable true probability data should drop the bet row; do not add manual/default probability fallbacks.

## Testing
- Ensure tests are offline and fixture-based.
- Use `FakeElement` / `FakePage` for offline Playwright mocks.
- Use small synthetic SQLite fixtures for data/modeling tests; do not require `raw/` data in CI.
- Maintain test coverage > 80%.
