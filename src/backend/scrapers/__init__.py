"""Scraper package for multi-sportsbook odds collection.

Sub-packages hold ESPN, DraftKings, and future platform-specific adapters.
Shared infrastructure (http_client, parsers) lives in ``.shared``.
"""

from __future__ import annotations

from backend.scrapers.base import BaseScraper
from backend.scrapers.comparison import OddsComparison
from backend.scrapers.draftkings.scraper import DraftKingsScraper
from backend.scrapers.espn.scraper import EspnOddsScraper
from backend.scrapers.orchestrator import LiveOddsScraper
from backend.scrapers.sample import OddsScraper
from backend.scrapers.shared.http_client import HttpClient
from backend.scrapers.shared.parsers import GameOdds

__all__ = [
    'BaseScraper',
    'DraftKingsScraper',
    'EspnOddsScraper',
    'GameOdds',
    'HttpClient',
    'LiveOddsScraper',
    'OddsComparison',
    'OddsScraper',
]
