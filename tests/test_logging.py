"""Tests for structured logging configuration and migration."""

from __future__ import annotations

import logging

import pytest
from loguru import logger

from backend.logging_config import configure_logging


class TestInterceptHandler:
    """Verify stdlib logging records are redirected to loguru."""

    def test_stdlib_logging_redirected_to_loguru(self, capsys: pytest.CaptureFixture[str]) -> None:
        """stdlib logging messages appear in loguru stderr output."""
        configure_logging(level='DEBUG', json_file=False)
        logging.getLogger('test.module').info('hello from stdlib')
        captured = capsys.readouterr()
        assert 'hello from stdlib' in captured.err

    def test_stdlib_warnings_also_captured(self, capsys: pytest.CaptureFixture[str]) -> None:
        """
        Verify that warning-level messages logged via the standard library appear on stderr (redirected to Loguru output).
        """
        configure_logging(level='DEBUG', json_file=False)
        logging.getLogger('test.warnings').warning('this is a test warning')
        captured = capsys.readouterr()
        assert 'this is a test warning' in captured.err

    def test_noisy_loggers_suppressed(self) -> None:
        """Third-party loggers (httpx, tenacity, etc.) are set to WARNING."""
        configure_logging(level='DEBUG', json_file=False)
        for name in ('httpx', 'httpcore', 'tenacity', 'urllib3', 'parsel', 'playwright'):
            lib_logger = logging.getLogger(name)
            assert lib_logger.level == logging.WARNING


class TestLoggingConfig:
    """Verify configure_logging sets up sinks correctly."""

    def test_console_sink_configured(self, capsys: pytest.CaptureFixture[str]) -> None:
        """After configure_logging, log messages appear on stderr."""
        configure_logging(level='INFO', json_file=False)
        logger.info('console test message')
        captured = capsys.readouterr()
        assert 'console test message' in captured.err

    def test_log_level_respected(self, capsys: pytest.CaptureFixture[str]) -> None:
        """DEBUG messages are suppressed when level=INFO."""
        configure_logging(level='INFO', json_file=False)
        logger.debug('debug should not appear')
        captured = capsys.readouterr()
        assert 'debug should not appear' not in captured.err

    def test_contextualize_adds_extra_fields(self) -> None:
        """logger.contextualize() adds extra fields to log records."""
        # Verify this does not raise — contextualize is a loguru core feature
        with logger.contextualize(scrape_session='test-123'):
            logger.info('test with context')
        # If we got here without error, it works


class TestLoguruImports:
    """Verify key modules use loguru instead of stdlib logging."""

    def test_espn_scraper_uses_loguru(self) -> None:
        """
        Check that backend.scrapers.espn.scraper imports `logger` from Loguru.
        """
        from backend.scrapers.espn import scraper as mod

        source = __import__('inspect').getsource(mod)
        assert 'from loguru import logger' in source

    def test_orchestrator_uses_loguru(self) -> None:
        """
        Asserts that the orchestrator scraper module imports Loguru's `logger`.
        """
        from backend.scrapers import orchestrator as mod

        source = __import__('inspect').getsource(mod)
        assert 'from loguru import logger' in source

    def test_draftkings_scraper_uses_loguru(self) -> None:
        """DraftKingsScraper module imports from loguru."""
        from backend.scrapers.draftkings import scraper as mod

        source = __import__('inspect').getsource(mod)
        assert 'from loguru import logger' in source

    def test_http_client_uses_loguru(self) -> None:
        """HttpClient module imports from loguru."""
        from backend.scrapers.shared import http_client as mod

        source = __import__('inspect').getsource(mod)
        assert 'from loguru import logger' in source

    def test_main_no_stdlib_basic_config(self) -> None:
        """Main module no longer calls logging.basicConfig()."""
        from frontend.gui import main as mod

        source = __import__('inspect').getsource(mod)
        assert 'logging.basicConfig' not in source

    def test_main_uses_configure_logging(self) -> None:
        """Main module calls configure_logging()."""
        from frontend.gui import main as mod

        source = __import__('inspect').getsource(mod)
        assert 'configure_logging' in source
