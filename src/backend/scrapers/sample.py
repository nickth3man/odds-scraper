import json
from datetime import datetime

import pandas as pd
from loguru import logger


class OddsScraper:
    """Scrapes NBA odds from ESPN and other sportsbooks"""

    def __init__(self, config_file='config.json'):
        """Initialize the odds scraper"""
        self.config = self.load_config(config_file)
        self.scraped_odds = []
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def load_config(self, config_file):
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

    def scrape_espn_odds(self):
        """
        Return a list of sample NBA odds from ESPN.

        Each item in the returned list is a dictionary representing a single game's odds with the following keys:
        - `game_id` (int): Unique identifier for the game.
        - `date` (str): Game date in ISO format (YYYY-MM-DD).
        - `team` (str): The team the odds apply to.
        - `opponent` (str): The opposing team.
        - `moneyline` (int): Moneyline odds for the team.
        - `spread` (float): Point spread for the team (negative for favored).
        - `over_under` (float): Total points line for the game.
        - `sportsbook` (str): Source sportsbook name (`"ESPN"`).

        Returns:
            list[dict]: A list of ESPN odds dictionaries as described above.
        """
        logger.info('Scraping odds', sportsbook='ESPN')

        # Sample NBA odds data for 2025-26 season
        espn_odds = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'team': 'OKC Thunder',
                'opponent': 'Boston Celtics',
                'moneyline': -180,
                'spread': -7.5,
                'over_under': 214.5,
                'sportsbook': 'ESPN',
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'team': 'Denver Nuggets',
                'opponent': 'Lakers',
                'moneyline': 150,
                'spread': 4.5,
                'over_under': 223.5,
                'sportsbook': 'ESPN',
            },
            {
                'game_id': 3,
                'date': '2026-04-30',
                'team': 'Boston Celtics',
                'opponent': 'OKC Thunder',
                'moneyline': 150,
                'spread': 7.5,
                'over_under': 214.5,
                'sportsbook': 'ESPN',
            },
            {
                'game_id': 4,
                'date': '2026-04-30',
                'team': 'Lakers',
                'opponent': 'Denver Nuggets',
                'moneyline': -130,
                'spread': -4.5,
                'over_under': 223.5,
                'sportsbook': 'ESPN',
            },
        ]

        return espn_odds

    def scrape_draftkings_odds(self):
        """
        Return a list of sample NBA odds entries representing DraftKings sportsbook data.

        Each list item is a dictionary describing a game's odds with keys such as `game_id`, `date`, `team`, `opponent`, `moneyline`, `spread`, `over_under`, and `sportsbook`.

        Returns:
            draftkings_odds (list[dict]): Sample DraftKings odds for multiple games.
        """
        logger.info('Scraping odds', sportsbook='DraftKings')

        # Sample DraftKings odds (slightly different lines)
        draftkings_odds = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'team': 'OKC Thunder',
                'opponent': 'Boston Celtics',
                'moneyline': -175,
                'spread': -7.0,
                'over_under': 214.0,
                'sportsbook': 'DraftKings',
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'team': 'Denver Nuggets',
                'opponent': 'Lakers',
                'moneyline': 155,
                'spread': 4.0,
                'over_under': 223.0,
                'sportsbook': 'DraftKings',
            },
            {
                'game_id': 3,
                'date': '2026-04-30',
                'team': 'Boston Celtics',
                'opponent': 'OKC Thunder',
                'moneyline': 155,
                'spread': 7.0,
                'over_under': 214.0,
                'sportsbook': 'DraftKings',
            },
            {
                'game_id': 4,
                'date': '2026-04-30',
                'team': 'Lakers',
                'opponent': 'Denver Nuggets',
                'moneyline': -125,
                'spread': -4.0,
                'over_under': 223.0,
                'sportsbook': 'DraftKings',
            },
        ]

        return draftkings_odds

    def scrape_fanduel_odds(self):
        """
        Return sample FanDuel NBA odds for use by the scraper.

        Returns:
            fanduel_odds (list[dict]): A list of dictionaries, each representing odds for a single game with keys
            'game_id', 'date', 'team', 'opponent', 'moneyline', 'spread', 'over_under', and 'sportsbook'.
        """
        logger.info('Scraping odds', sportsbook='FanDuel')

        # Sample FanDuel odds
        fanduel_odds = [
            {
                'game_id': 1,
                'date': '2026-04-30',
                'team': 'OKC Thunder',
                'opponent': 'Boston Celtics',
                'moneyline': -178,
                'spread': -7.0,
                'over_under': 214.5,
                'sportsbook': 'FanDuel',
            },
            {
                'game_id': 2,
                'date': '2026-04-30',
                'team': 'Denver Nuggets',
                'opponent': 'Lakers',
                'moneyline': 152,
                'spread': 4.5,
                'over_under': 223.5,
                'sportsbook': 'FanDuel',
            },
            {
                'game_id': 3,
                'date': '2026-04-30',
                'team': 'Boston Celtics',
                'opponent': 'OKC Thunder',
                'moneyline': 152,
                'spread': 7.0,
                'over_under': 214.5,
                'sportsbook': 'FanDuel',
            },
            {
                'game_id': 4,
                'date': '2026-04-30',
                'team': 'Lakers',
                'opponent': 'Denver Nuggets',
                'moneyline': -128,
                'spread': -4.5,
                'over_under': 223.5,
                'sportsbook': 'FanDuel',
            },
        ]

        return fanduel_odds

    def get_all_odds(self):
        """Get odds from all enabled sportsbooks"""
        all_odds = []

        if self.config['sportsbooks']['espn']['enabled']:
            all_odds.extend(self.scrape_espn_odds())

        if self.config['sportsbooks']['draftkings']['enabled']:
            all_odds.extend(self.scrape_draftkings_odds())

        if self.config['sportsbooks']['fanduel']['enabled']:
            all_odds.extend(self.scrape_fanduel_odds())

        self.scraped_odds = all_odds
        return all_odds

    def export_to_csv(self, filename='data/sample_odds_data.csv'):
        """
        Write the currently scraped odds to a CSV file.

        If no odds have been scraped, logs a warning and does not create a file. Otherwise converts the stored odds into a pandas DataFrame and writes it to the given path with no index, then logs the output filename and number of records.

        Parameters:
            filename (str): Path to write the CSV file. Defaults to 'data/sample_odds_data.csv'.
        """
        if not self.scraped_odds:
            logger.warning('No odds to export')
            return

        odds_table = pd.DataFrame(self.scraped_odds)
        odds_table.to_csv(filename, index=False)
        logger.info('Sample odds exported', filename=filename, record_count=len(odds_table))
