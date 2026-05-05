"""Shared pytest fixtures for the odds-scraper test suite."""

from __future__ import annotations

import sys

import pytest
from loguru import logger

from tests.browser_fakes import FakeElement, FakePage  # noqa: F401


@pytest.fixture
def loguru_to_stderr(capsys: pytest.CaptureFixture[str]):
    """
    Attach a temporary Loguru sink that directs logger output to sys.stderr for the duration of a test.

    The fixture adds a Loguru handler using the format '{message}', yields control so the test runs with the sink active, and removes the handler after the test completes.

    Parameters:
        capsys (pytest.CaptureFixture[str]): Pytest capture fixture used to capture and inspect sys.stderr output during the test.
    """
    handler_id = logger.add(sys.stderr, format='{message}')
    yield
    logger.remove(handler_id)
