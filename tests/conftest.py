"""Shared pytest fixtures for the odds-scraper test suite."""

from __future__ import annotations

import sys

import pytest
from loguru import logger

from tests.browser_fakes import FakeElement, FakePage  # noqa: F401


@pytest.fixture
def loguru_to_stderr(capsys: pytest.CaptureFixture[str]):
    """Re-add loguru sink to capsys-redirected sys.stderr."""
    handler_id = logger.add(sys.stderr, format='{message}')
    yield
    logger.remove(handler_id)
