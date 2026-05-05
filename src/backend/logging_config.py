"""Central loguru configuration for the odds-scraper project.

Called once from the GUI entry point. Provides:
- Colored, human-readable console output (dev)
- Daily-rotating JSON log files (production)
- stdlib logging interception for NiceGUI and third-party libs
- Scrape-session trace IDs
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    """Redirect stdlib logging records into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 0
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, '{}', record.getMessage())


_LOG_DIR = Path('logs')


def configure_logging(
    *,
    level: str = 'INFO',
    json_file: bool = True,
    rotation: str = '1 day',
    retention: str = '7 days',
) -> None:
    """Initialize loguru sinks. Call once at app startup."""
    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        format=(
            '<green>{time:HH:mm:ss}</green> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | '
            '<level>{message}</level>'
        ),
        colorize=True,
    )

    if json_file:
        _LOG_DIR.mkdir(exist_ok=True)
        logger.add(
            _LOG_DIR / 'odds-scraper_{time:YYYY-MM-DD}.jsonl',
            level='DEBUG',
            serialize=True,
            rotation=rotation,
            retention=retention,
            compression='gz',
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for noisy in ('httpx', 'httpcore', 'tenacity', 'urllib3', 'parsel', 'playwright'):
        logging.getLogger(noisy).setLevel(logging.WARNING)
