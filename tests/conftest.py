"""Shared pytest fixtures for the odds-scraper test suite."""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest
from loguru import logger

from tests.browser_fakes import FakeElement, FakePage  # noqa: F401


@pytest.fixture
def loguru_to_stderr(capsys: pytest.CaptureFixture[str]) -> Iterator[None]:
    """
    Temporarily route Loguru logger output to sys.stderr for the duration of a test.

    This pytest fixture adds a Loguru sink that directs logger output to sys.stderr while the test runs so pytest's capture mechanisms can record Loguru messages; the sink is removed after the test completes.

    Parameters:
        capsys (pytest.CaptureFixture[str]): Pytest capture fixture (provided for typing/context; pytest captures sys.stderr).
    """
    handler_id = logger.add(sys.stderr, format='{message}')
    yield
    logger.remove(handler_id)
