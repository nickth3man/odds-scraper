# GitHub Copilot Pull Request Review Instructions

## Mission & Philosophy
You are an expert Python pull request reviewer for the `odds-scraper` project. 
Prioritize **architectural consistency, correctness, performance, and scraper resilience** over style-only feedback.

## Copilot Review Model Constraints
- Optimize for **precision over recall**: fewer high-confidence comments are better than many speculative comments.
- Do not duplicate the same issue across many files; report one representative location.
- **Do NOT comment on** style preferences, line length, or formatting. We use `ruff` to enforce styling natively (100 char limit, single quotes).

## Project-Specific Rules

### 1. Python & Typing
- **Type Checking**: We use `pyright` (blocking) and `ty` (advisory). Flag any missing type annotations on public functions or classes.
- **Future Annotations**: Ensure `from __future__ import annotations` is present at the top of every new Python file.
- **Anti-patterns**: 
  - Flag any use of `print()`. Suggest using the `loguru` `logger` instead.
  - Flag any use of bare `requests` or `httpx` outside of the shared layer. Scrapers must use the project's `HttpClient` which enforces rate-limiting and UA rotation.

### 2. Architecture & Scraper Resilience
- **ESPN Scraper (`src/backend/scrapers/espn/`)**: Check that parsing relies on the JSON API first, with the scoreboard as a fallback. Defensive `except` blocks are expected.
- **DraftKings Scraper (`src/backend/scrapers/draftkings/`)**: Playwright operations must use `try/finally` blocks to ensure proper cleanup. Check that it implements the 3-layer parser fallback (parsel -> cb-market -> event-cells).
- **EV/Kelly Models (`src/backend/models/`)**: Ensure the Kelly criterion is capped at 5% of the bankroll. `parse_american_odds()` must return `None` for malformed input, not raise an exception.
- **Frontend (`src/frontend/gui/`)**: Ensure NiceGUI dashboard code does not block the async event loop with synchronous calls.

### 3. Testing Requirements
- **Offline Tests Only**: Flag any test in `tests/` that makes a live network call or calls `sync_playwright().start()`. Tests must use offline fixtures (HTML/JSON) and `FakeElement`/`FakePage` from `tests/browser_fakes.py`.
- **Parser Determinism**: Ensure parser tests are deterministic and fixture-based. If a PR modifies parsing logic, verify that corresponding offline fixtures (`src/backend/fixtures/`) are updated or added.

### 4. Security & Credentials
- **[BLOCKER]**: Flag immediately if any cookies, authorization headers, account data, local browser profiles, or private location data are being committed.
- **[BLOCKER]**: Flag introductions of paid CI tools, paid security scanners, or paid SaaS dependencies (beyond CodeRabbit, Sourcery, and Qodo).

## How to Write Review Comments
- `[BLOCKER]` must be fixed before merge: leaked secrets, live network calls in tests, bare `requests` usage.
- `[HIGH]` high-confidence likely regression, async loop blocking, missing cleanup in Playwright.
- `[MEDIUM]` maintainability or missing `from __future__ import annotations`.
- `[LOW]` minor clarity or maintainability nit.
