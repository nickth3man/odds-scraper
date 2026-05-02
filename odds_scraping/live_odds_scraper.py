import logging

import pandas as pd

from .draftkings_scraper import DraftKingsScraper
from .espn_scraper import EspnOddsScraper
from .http_client import HttpClient

logger = logging.getLogger(__name__)


class LiveOddsScraper:
    """Scrape live odds from ESPN and DraftKings for real games."""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        self._http = HttpClient()
        self.all_games = []

    def _espn_scraper(self) -> EspnOddsScraper:
        return EspnOddsScraper(self._http)

    def _draftkings_scraper(self) -> DraftKingsScraper:
        return DraftKingsScraper()

    # ============ ESPN SCRAPING (JSON API) ============

    def scrape_espn_nba_odds(self):
        """Scrape live NBA odds from ESPN's JSON API."""
        games = self._espn_scraper().scrape_nba_odds()
        self.all_games.extend(games)
        return games

    def _parse_espn_events(self, events: list) -> list:
        """Parse game data from ESPN JSON API events list."""
        return self._espn_scraper().parse_header_events(events)

    def _scrape_espn_scoreboard_fallback(self) -> list:
        """Fetch equivalent normalized odds from ESPN's scoreboard API shape."""
        games = self._espn_scraper().scrape_scoreboard_fallback()
        self.all_games.extend(games)
        return games

    def _parse_espn_scoreboard_events(self, events: list) -> list:
        return self._espn_scraper().parse_scoreboard_events(events)

    def _select_scoreboard_odds(self, odds_list: list) -> dict | None:
        return self._espn_scraper().select_scoreboard_odds(odds_list)

    # ============ DRAFTKINGS SCRAPING (Selenium) ============

    def scrape_draftkings_odds(self):
        """Scrape live odds from DraftKings using Selenium."""
        games = self._draftkings_scraper().scrape_odds()
        if games:
            self.all_games.extend(games)
        return games

    @staticmethod
    def parse_draftkings_html(html: str) -> list:
        """Parse DraftKings NBA page HTML using parsel CSS selectors."""
        return DraftKingsScraper.parse_html(html)

    def _parse_draftkings_games(self, driver) -> list:
        """Parse games from DraftKings page using Selenium."""
        return self._draftkings_scraper().parse_games(driver)

    def _parse_draftkings_cb_market(self, driver) -> list:
        """Parse DraftKings games using cb-market__template structure."""
        return self._draftkings_scraper().parse_cb_market(driver)

    def _parse_draftkings_event_cells(self, driver) -> list:
        """Parse DraftKings games using legacy event-cell structure."""
        return self._draftkings_scraper().parse_event_cells(driver)

    def _parse_draftkings_markets(self, outcome_cells, team_name: str) -> tuple[str, str, str]:
        return self._draftkings_scraper().parse_markets(outcome_cells, team_name)

    # ============ EXPORT & DISPLAY ============

    def export_to_csv(self, games, filename='data/live_odds.csv'):
        """Export live odds to CSV."""
        if not games:
            print('No games to export')
            return None

        df = pd.DataFrame(games)
        df.to_csv(filename, index=False)
        print(f'[OK] Live odds exported to {filename}')
        print(f'   Total games: {len(df)}\n')

        return df

    def display_games(self, games, source=''):
        """Display games in a formatted table."""
        if not games:
            return

        df = pd.DataFrame(games)

        print('=' * 100)
        print(f'LIVE {source} GAMES')
        print('=' * 100)
        print(df.to_string(index=False))
        print()

    def get_all_games(self):
        """Scrape both ESPN and DraftKings."""
        print('NBA Live odds from all sources\n')
        self.all_games = []

        espn_games = self.scrape_espn_nba_odds()
        if espn_games:
            self.display_games(espn_games, 'ESPN')

        dk_games = self.scrape_draftkings_odds()
        if dk_games:
            self.display_games(dk_games, 'DRAFTKINGS')

        return self.all_games
