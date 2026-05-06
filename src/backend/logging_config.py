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
        """
        Forward a standard-library LogRecord into Loguru, preserving level and origin.

        Attempts to map the record's level name to a Loguru level and falls back to the numeric level if unknown. Computes a call-stack depth that skips frames originating from the standard `logging` module so Loguru reports the original call site, and forwards the message and any exception information to Loguru.

        Parameters:
            record (logging.LogRecord): The standard-library log record to forward into Loguru.
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(), 1
        while frame.f_back is not None:
            frame = frame.f_back
            if frame.f_code.co_filename == logging.__file__:
                depth += 1
            else:
                break
        logger.opt(depth=depth, exception=record.exc_info).log(level, '{}', record.getMessage())


_LOG_DIR = Path('logs')


def configure_logging(
    *,
    level: str = 'INFO',
    json_file: bool = True,
    rotation: str = '1 day',
    retention: str = '7 days',
) -> None:
    """
    Configure Loguru and standard-library logging for the application.

    Sets up a colored, human-readable console sink; optionally adds a daily-rotated, compressed JSONL file sink under the module's logs directory; installs the InterceptHandler so stdlib `logging` records are routed into Loguru; and raises the log level for noisy third-party libraries. Call once at application startup.

    Parameters:
        level (str): Minimum log level for the console sink (e.g., 'DEBUG', 'INFO').
        json_file (bool): If True, enable writing structured JSONL logs to files.
        rotation (str): Loguru rotation policy for the file sink (e.g., '1 day', '100 MB').
        retention (str): Loguru retention policy for the file sink (e.g., '7 days', '30 days').
    """
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
