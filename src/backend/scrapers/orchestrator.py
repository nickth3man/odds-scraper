import uuid

import pandas as pd
from loguru import logger

from .draftkings.scraper import DraftKingsScraper
from .espn.scraper import EspnOddsScraper
from .shared.http_client import HttpClient
from .shared.parsers import GameOdds


class LiveOddsScraper:
    """Scrape live odds from ESPN and DraftKings for real games."""

    def __init__(self, http: HttpClient | None = None):
        self._http = http or HttpClient()
        self._espn = EspnOddsScraper(self._http)
        self._draftkings = DraftKingsScraper()
        self.games = []

    # ============ ESPN SCRAPING (JSON API) ============

    def scrape_espn_nba_odds(self):
        """Scrape live NBA odds from ESPN's JSON API."""
        games = self._espn.scrape_nba_odds()
        self.games.extend(games)
        return games

    # ============ DRAFTKINGS SCRAPING (Playwright) ============

    def scrape_draftkings_odds(self):
        """Scrape live odds from DraftKings using Playwright."""
        games = self._draftkings.scrape_odds()
        if games:
            self.games.extend(games)
        return games

    @staticmethod
    def parse_draftkings_html(html: str) -> list[GameOdds]:
        """Compatibility wrapper for offline HTML parsing.

        Delegates to DraftKingsScraper.parse_html for consumers that still
        call LiveOddsScraper.parse_draftkings_html(...).
        """
        return DraftKingsScraper.parse_html(html)

    # ============ EXPORT & DISPLAY ============

    def export_to_csv(self, games, filename='data/live_odds.csv'):
        """Export live odds to CSV."""
        if not games:
            logger.warning('No games to export')
            return None

        games_table = pd.DataFrame(games)
        games_table.to_csv(filename, index=False)
        logger.info(
            'Exported live odds', filename=filename, game_count=len(games_table), action='export'
        )

        return games_table

    def display_games(self, games, source=''):
        """Display games in a formatted table."""
        if not games:
            return

        games_table = pd.DataFrame(games)

        logger.debug(
            'Displaying games',
            source=source,
            count=len(games),
            table=games_table.to_string(index=False),
        )

    def get_all_games(self):
        """Scrape both ESPN and DraftKings."""
        session_id = uuid.uuid4().hex[:8]
        with logger.contextualize(scrape_session=session_id):
            logger.info('Scraping all sources', action='fetch_all')
            self.games = []

            espn_games = self.scrape_espn_nba_odds()
            if espn_games:
                self.display_games(espn_games, 'ESPN')

            draftkings_games = self.scrape_draftkings_odds()
            if draftkings_games:
                self.display_games(draftkings_games, 'DRAFTKINGS')

            return self.games
