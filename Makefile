PYTHON ?= 3.12
UV ?= uv

.PHONY: install sync browsers lint format type test cov ci build run clean

install sync:
	$(UV) sync --locked --group dev

browsers:
	$(UV) run playwright install chromium

lint:
	$(UV) run ruff format --check .
	$(UV) run ruff check .

format:
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

type:
	$(UV) run ty check
	$(UV) run pyright

test:
	$(UV) run pytest

cov:
	$(UV) run pytest --cov-report=term-missing

ci: lint type cov

build:
	$(UV) build

run:
	$(UV) run python -m frontend.gui.main

clean:
	rm -rf .coverage coverage.xml htmlcov dist build .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
