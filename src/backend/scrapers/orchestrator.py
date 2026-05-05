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
        """
        Write a list of game odds to a CSV file.
        
        If `games` is empty or falsey, the function returns `None`. Otherwise the games are converted to a pandas DataFrame and written to `filename`.
        
        Parameters:
            games (list|iterable): Iterable of game odds objects or dicts to export.
            filename (str): Filesystem path where the CSV will be written. Defaults to 'data/live_odds.csv'.
        
        Returns:
            pandas.DataFrame or None: A DataFrame containing the exported games, or `None` if `games` was empty.
        """
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
        """
        Logs a formatted table of game odds at debug level.
        
        Parameters:
            games (Iterable[dict|GameOdds]): Sequence of game records to display; each item will be converted to a pandas DataFrame row.
            source (str): Optional source label included in the log context (e.g., "ESPN", "DRAFTKINGS").
        """
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
        """
        Orchestrates scraping of NBA odds from ESPN and DraftKings and aggregates the results.
        
        Resets the internal games list, runs each source scraper, conditionally displays each source's results, and logs scraping activity within a per-run `scrape_session` context attached to log entries.
        
        Returns:
            list[GameOdds]: Aggregated list of scraped games (may be empty).
        """
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
