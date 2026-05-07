# Agent instructions

This repository is a Python 3.12+ project managed with uv and built with hatchling.

## Required local checks

Run these before proposing code changes:

```bash
uv sync --locked --group dev
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pyright
uv run pytest
```

`ty` is useful as a fast signal, but `pyright` is the blocking type checker.

## Style

- Use Ruff for formatting and linting.
- Keep single quotes and 100-character lines.
- Prefer explicit, typed functions for scraper and parser boundaries.
- Prefer explicit, typed functions for historical data ingestion, feature engineering, and model
  evaluation boundaries.
- Keep parser tests deterministic and fixture-based.
- Avoid live sportsbook network calls in tests.
- Keep model/data tests deterministic with small synthetic fixtures; do not require `raw/` data in CI.

## Architecture

- Backend scraping, HTTP, parsing, and EV logic live under `src/backend/`.
- Betting domain models live in `src/backend/models/domain.py`.
- Scrapers should emit `list[Market]` using `Market`, `Outcome`, and `NormalizedOdds`.
- Odds enrichment lives in `src/backend/models/odds_enrichment.py` and must drop rows when
  true probability cannot be computed.
- Historical NBA ingestion, feature engineering, model baselines, evaluation, and backtesting
  live under `src/backend/data/`.
- NiceGUI dashboard code lives under `src/frontend/gui/`.
- ESPN uses JSON APIs plus scoreboard fallback.
- DraftKings uses Playwright with parser fallback layers.

## Data and modeling rules

- Raw historical datasets live under `raw/` and must not be committed.
- Build pre-game features only from data available before the game.
- Rolling features must be lagged (`shift(1)` or equivalent) to avoid target leakage.
- Prefer chronological or walk-forward validation; do not use random splits for sports time series.
- Evaluate probability models with Brier score and log-loss; accuracy alone is not enough.
- Compare model output against de-vigged market-implied probabilities.
- Backtests must use odds snapshots available at the simulated bet time.

## Safety and maintenance

- Do not commit cookies, authorization headers, account data, local browser profiles, or private location data.
- Do not add paid CI, paid security scanners, or paid SaaS dependencies beyond CodeRabbit, Sourcery, and Qodo.
- Prefer open-source tools that run in GitHub Actions.
- For scraper changes, include fixture updates and document selector assumptions.
