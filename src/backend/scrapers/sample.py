from __future__ import annotations

import json
from datetime import datetime

from loguru import logger

from backend.models.domain import Market, MarketType, NormalizedOdds, Outcome
from backend.scrapers.base import BaseScraper


class OddsScraper(BaseScraper):
    """Scrapes NBA odds from ESPN and other sportsbooks"""

    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize an OddsScraper instance and load its configuration.
        
        Parameters:
            config_file (str): Path to a JSON configuration file that controls enabled sportsbooks and scraper behavior; defaults to 'config.json'. If the file cannot be found or parsed, an empty configuration will be used.
        
        Notes:
            Initializes the following instance attributes:
              - scraped_odds: empty list to hold generated Market objects.
              - timestamp: current datetime formatted as '%Y-%m-%d %H:%M:%S'.
        """
        self.config = self.load_config(config_file)
        self.scraped_odds: list[Market] = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def load_config(self, config_file: str) -> dict:
        """
        Load and parse a JSON configuration file.
        
        If the file cannot be found, returns an empty dictionary.
        
        Parameters:
            config_file (str): Path to the JSON configuration file.
        
        Returns:
            dict: Parsed configuration object, or an empty dict if the file was not found.
        """
        try:
            with open(config_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning('Config file not found', path=config_file)
            return {}

    def scrape(self) -> list[Market]:
        """
        Retrieve normalized betting markets for the current slate.
        
        Returns:
            list[Market]: A list of normalized Market objects collected from enabled sportsbooks per the scraper configuration.
        """
        return self.get_all_odds()

    def scrape_espn_odds(self) -> list[Market]:
        """
        Build sample ESPN NBA odds and convert them into normalized Market objects.
        
        For each sample game produces three markets: H2H (moneyline), SPREADS, and TOTALS; outcomes include normalized odds and appropriate point values.
        
        Returns:
            list[Market]: List of Market objects for the ESPN sample data.
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
        Produce sample NBA betting markets for DraftKings.
        
        Two hard-coded sample games are represented as Market objects covering head-to-head, spreads, and totals markets for each event.
        
        Returns:
            list[Market]: A list of Market objects containing DraftKings sample odds.
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
        Provide sample FanDuel NBA markets constructed from hard-coded game odds.
        
        Returns:
            list[Market]: A list of Market objects representing the sample FanDuel markets.
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
        """
        Convert a list of game dictionaries into normalized Market objects for H2H, spreads, and totals.
        
        Parameters:
            games (list[dict]): Game dictionaries containing keys: 'game_id', 'away_team', 'home_team',
                'away_moneyline', 'home_moneyline', 'away_spread', 'home_spread', and 'total'.
            source (str): Sportsbook name used as the prefix for each market `key` and included in the market `name`.
        
        Returns:
            list[Market]: A list of Market objects; three markets are produced per game:
                - H2H (moneyline) with outcomes for away and home using the provided moneyline odds.
                - SPREADS with away/home outcomes using American -110 odds and the corresponding spread `point`.
                - TOTALS with Over/Under outcomes using American -110 odds and the game `total` as `point`.
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
        """
        Collect aggregated odds from all configured and enabled sportsbooks and update the instance cache.
        
        Calls each enabled sportsbook-specific scraper, combines their returned Market lists into a single list, and assigns that list to `self.scraped_odds`.
        
        Returns:
        	all_odds (list[Market]): Aggregated list of Market objects collected from enabled sportsbooks.
        """
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
