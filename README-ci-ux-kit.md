# odds-scraper CI and UX kit

Copy these files into the repository root. They are designed for the stated 2026 stack:
Python 3.12+, uv, hatchling, Ruff, pyright, ty, pytest-cov, NiceGUI, and Playwright.

## Apply

```bash
rsync -av odds-scraper-ci-ux-kit/ /path/to/odds-scraper/
cd /path/to/odds-scraper
uv sync --locked --group dev
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pyright
uv run pytest --cov=src --cov-fail-under=80
```

Also update `pyproject.toml` coverage from `65` to `80`. A patch is included at `patches/pyproject-coverage-80.patch`, but your current file may be formatted as one line on GitHub, so applying the intent manually may be cleaner.

## Paid-service boundary

The only external review services represented here are CodeRabbit, Sourcery, and Qodo. Other additions are GitHub-native or open-source tools runnable in GitHub Actions.
