# Contributing

## Setup

```bash
uv sync --locked --group dev
uv run playwright install chromium
```

## Run the app

```bash
uv run python -m frontend.gui.main
```

Open `http://localhost:8080`.

## Quality checks

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pyright
uv run pytest
```

Use `make ci` as a shorter local equivalent when `make` is available.

## Pull request expectations

- Keep PRs small and focused.
- Include tests for parser, HTTP retry, EV calculation, and UI behavior changes.
- Prefer fixture-based tests over live sportsbook requests.
- Update docs when commands, configuration, routes, or scraper assumptions change.
- Add a screenshot or short UX note for NiceGUI changes.

## Scraper development notes

Sportsbook pages and unofficial ESPN endpoints can change without notice. Defensive parsers, clear failure states, and offline fixtures are expected for scraper changes. Never commit account cookies, browser profiles, or private headers.

## Dependency updates

Dependabot opens grouped weekly pull requests for uv and GitHub Actions. Review `uv.lock` changes carefully, especially for scraping, TLS, browser automation, and parsing packages.
