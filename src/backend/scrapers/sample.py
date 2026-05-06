from __future__ import annotations

import json
from datetime import datetime

from loguru import logger

from backend.models.domain import Market, MarketType, NormalizedOdds, Outcome
from backend.scrapers.base import BaseScraper


class OddsScraper(BaseScraper):
    """Scrapes NBA odds from ESPN and other sportsbooks"""

    def __init__(self, config_file: str = 'config.json'):
        """Initialize the odds scraper"""
        self.config = self.load_config(config_file)
        self.scraped_odds: list[Market] = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def load_config(self, config_file: str) -> dict:
        """
        Load JSON configuration from the given file path.

        If the file does not exist, logs a warning and returns an empty dictionary.

        Parameters:
            config_file (str): Path to the JSON configuration file.

        Returns:
            dict: Parsed configuration object from the file, or an empty dict if the file was not found.
        """
        try:
            with open(config_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning('Config file not found', path=config_file)
            return {}

    def scrape(self) -> list[Market]:
        """Fetch and return normalized odds for the current slate.

        Delegates to :meth:`get_all_odds` to respect config-driven source
        selection.

        Returns:
            list[Market]: A list of normalized market objects.
        """
        return self.get_all_odds()

    def scrape_espn_odds(self) -> list[Market]:
        """
        Return a list of sample NBA odds markets from ESPN.

        For each game, three Market objects are produced: H2H (moneyline),
        SPREADS, and TOTALS.

        Returns:
            list[Market]: A list of Market objects for ESPN sample data.
        """
        logger.info('Scraping odds', sportsbook='ESPN')

        # Sample NBA odds data for 2025-26 season (paired per game)
        games: list[dict] = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'away_team': 'OKC Thunder',
                'home_team': 'Boston Celtics',
                'away_moneyline': -180,
                'home_moneyline': 150,
                'away_spread': -7.5,
                'home_spread': 7.5,
                'total': 214.5,
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'away_team': 'Denver Nuggets',
                'home_team': 'Lakers',
                'away_moneyline': 150,
                'home_moneyline': -130,
                'away_spread': 4.5,
                'home_spread': -4.5,
                'total': 223.5,
            },
        ]

        return self._build_markets(games, 'ESPN')

    def scrape_draftkings_odds(self) -> list[Market]:
        """
        Return a list of sample NBA odds markets from DraftKings.

        Returns:
            list[Market]: A list of Market objects for DraftKings sample data.
        """
        logger.info('Scraping odds', sportsbook='DraftKings')

        games: list[dict] = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'away_team': 'OKC Thunder',
                'home_team': 'Boston Celtics',
                'away_moneyline': -175,
                'home_moneyline': 155,
                'away_spread': -7.0,
                'home_spread': 7.0,
                'total': 214.0,
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'away_team': 'Denver Nuggets',
                'home_team': 'Lakers',
                'away_moneyline': 155,
                'home_moneyline': -125,
                'away_spread': 4.0,
                'home_spread': -4.0,
                'total': 223.0,
            },
        ]

        return self._build_markets(games, 'DraftKings')

    def scrape_fanduel_odds(self) -> list[Market]:
        """
        Return sample FanDuel NBA odds as Market objects.

        Returns:
            list[Market]: A list of Market objects for FanDuel sample data.
        """
        logger.info('Scraping odds', sportsbook='FanDuel')

        games: list[dict] = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'away_team': 'OKC Thunder',
                'home_team': 'Boston Celtics',
                'away_moneyline': -178,
                'home_moneyline': 152,
                'away_spread': -7.0,
                'home_spread': 7.0,
                'total': 214.5,
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'away_team': 'Denver Nuggets',
                'home_team': 'Lakers',
                'away_moneyline': 152,
                'home_moneyline': -128,
                'away_spread': 4.5,
                'home_spread': -4.5,
                'total': 223.5,
            },
        ]

        return self._build_markets(games, 'FanDuel')

    def _build_markets(self, games: list[dict], source: str) -> list[Market]:
        """Convert game dicts into H2H, SPREADS, and TOTALS Market objects.

        Parameters:
            games: List of game dicts with paired team odds.
            source: Sportsbook name for the ``key`` prefix and ``name``.

        Returns:
            Three Market objects per game (h2h, spreads, totals).
        """
        markets: list[Market] = []

        for game in games:
            event_id = str(game['game_id'])
            away = game['away_team']
            home = game['home_team']

            # H2H (moneyline)
            markets.append(
                Market(
                    key=f'{source.lower()}_h2h_{event_id}',
                    name=f'{away} vs {home} Moneyline',
                    sport='nba',
                    event_id=event_id,
                    market_type=MarketType.H2H,
                    outcomes=[
                        Outcome(
                            name=away,
                            price=NormalizedOdds.from_american(game['away_moneyline']),
                        ),
                        Outcome(
                            name=home,
                            price=NormalizedOdds.from_american(game['home_moneyline']),
                        ),
                    ],
                )
            )

            # Spreads
            markets.append(
                Market(
                    key=f'{source.lower()}_spreads_{event_id}',
                    name=f'{away} vs {home} Spread',
                    sport='nba',
                    event_id=event_id,
                    market_type=MarketType.SPREADS,
                    outcomes=[
                        Outcome(
                            name=away,
                            price=NormalizedOdds.from_american(-110),
                            point=game['away_spread'],
                        ),
                        Outcome(
                            name=home,
                            price=NormalizedOdds.from_american(-110),
                            point=game['home_spread'],
                        ),
                    ],
                )
            )

            # Totals
            markets.append(
                Market(
                    key=f'{source.lower()}_totals_{event_id}',
                    name=f'{away} vs {home} Total',
                    sport='nba',
                    event_id=event_id,
                    market_type=MarketType.TOTALS,
                    outcomes=[
                        Outcome(
                            name='Over',
                            price=NormalizedOdds.from_american(-110),
                            point=game['total'],
                        ),
                        Outcome(
                            name='Under',
                            price=NormalizedOdds.from_american(-110),
                            point=game['total'],
                        ),
                    ],
                )
            )

        return markets

    def get_all_odds(self) -> list[Market]:
        """Get odds from all enabled sportsbooks"""
        all_odds: list[Market] = []

        if self.config.get('sportsbooks', {}).get('espn', {}).get('enabled'):
            all_odds.extend(self.scrape_espn_odds())

        if self.config.get('sportsbooks', {}).get('draftkings', {}).get('enabled'):
            all_odds.extend(self.scrape_draftkings_odds())

        if self.config.get('sportsbooks', {}).get('fanduel', {}).get('enabled'):
            all_odds.extend(self.scrape_fanduel_odds())

        self.scraped_odds = all_odds
        return all_odds

    def export_to_csv(self, filename: str = 'data/sample_odds_data.csv') -> None:
        """
        Write the currently scraped odds to a CSV file.

        If no odds have been scraped, logs a warning and does not create a file.

        Parameters:
            filename (str): Path to write the CSV file. Defaults to 'data/sample_odds_data.csv'.
        """
        if not self.scraped_odds:
            logger.warning('No odds to export')
            return

        import pandas as pd

        rows = []
        for market in self.scraped_odds:
            for outcome in market.outcomes:
                rows.append(
                    {
                        'key': market.key,
                        'name': market.name,
                        'sport': market.sport,
                        'event_id': market.event_id,
                        'market_type': market.market_type.value,
                        'outcome_name': outcome.name,
                        'american': outcome.price.american,
                        'decimal': outcome.price.decimal,
                        'implied_probability': outcome.price.implied_probability,
                        'point': outcome.point,
                    }
                )

        odds_table = pd.DataFrame(rows)
        odds_table.to_csv(filename, index=False)
        logger.info('Sample odds exported', filename=filename, record_count=len(odds_table))
