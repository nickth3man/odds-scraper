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
uv run pytest --cov=src --cov-fail-under=80
```

`ty` is useful as a fast signal, but `pyright` is the blocking type checker.

## Style

- Use Ruff for formatting and linting.
- Keep single quotes and 100-character lines.
- Prefer explicit, typed functions for scraper and parser boundaries.
- Keep parser tests deterministic and fixture-based.
- Avoid live sportsbook network calls in tests.

## Architecture

- Backend scraping, HTTP, parsing, and EV logic live under `src/backend/`.
- NiceGUI dashboard code lives under `src/frontend/gui/`.
- ESPN uses JSON APIs plus scoreboard fallback.
- DraftKings uses Playwright with parser fallback layers.

## Safety and maintenance

- Do not commit cookies, authorization headers, account data, local browser profiles, or private location data.
- Do not add paid CI, paid security scanners, or paid SaaS dependencies beyond CodeRabbit, Sourcery, and Qodo.
- Prefer open-source tools that run in GitHub Actions.
- For scraper changes, include fixture updates and document selector assumptions.
