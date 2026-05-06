"""Tests for OddsScraper — hardcoded sample data provider."""

import tempfile
from pathlib import Path

from backend.models.domain import Market, MarketType
from backend.scrapers import OddsScraper


class TestOddsScraper:
    """Unit tests for OddsScraper."""

    def test_init_loads_config(self):
        scraper = OddsScraper(config_file='config.json')
        assert scraper.config == {
            'sportsbooks': {
                'espn': {'enabled': True, 'url': 'https://www.espn.com/nba/odds'},
                'draftkings': {'enabled': True},
                'fanduel': {'enabled': True},
            },
            'sport': 'NBA',
            'season': '2025-26',
            'export_format': 'csv',
        }

    def test_init_missing_config_returns_empty_dict(self):
        scraper = OddsScraper(config_file='nonexistent_config.json')
        assert scraper.config == {}

    def test_load_config_file_not_found(self):
        scraper = OddsScraper()
        result = scraper.load_config('nonexistent_file.json')
        assert result == {}

    def test_scrape_espn_odds_returns_markets(self):
        scraper = OddsScraper()
        markets = scraper.scrape_espn_odds()
        assert isinstance(markets, list)
        assert all(isinstance(m, Market) for m in markets)
        # 2 games x 3 market types (h2h, spreads, totals) = 6
        assert len(markets) == 6

    def test_scrape_espn_odds_has_required_market_types(self):
        scraper = OddsScraper()
        markets = scraper.scrape_espn_odds()
        types = {m.market_type for m in markets}
        assert MarketType.H2H in types
        assert MarketType.SPREADS in types
        assert MarketType.TOTALS in types

    def test_scrape_espn_odds_keys_start_with_espn(self):
        scraper = OddsScraper()
        for market in scraper.scrape_espn_odds():
            assert market.key.startswith('espn_')

    def test_scrape_draftkings_odds_returns_markets(self):
        scraper = OddsScraper()
        markets = scraper.scrape_draftkings_odds()
        assert isinstance(markets, list)
        assert all(isinstance(m, Market) for m in markets)
        assert len(markets) == 6

    def test_scrape_draftkings_odds_keys_start_with_draftkings(self):
        scraper = OddsScraper()
        for market in scraper.scrape_draftkings_odds():
            assert market.key.startswith('draftkings_')

    def test_scrape_fanduel_odds_returns_markets(self):
        scraper = OddsScraper()
        markets = scraper.scrape_fanduel_odds()
        assert isinstance(markets, list)
        assert all(isinstance(m, Market) for m in markets)
        assert len(markets) == 6

    def test_scrape_fanduel_odds_keys_start_with_fanduel(self):
        scraper = OddsScraper()
        for market in scraper.scrape_fanduel_odds():
            assert market.key.startswith('fanduel_')

    def test_markets_have_valid_outcomes(self):
        """Each market should have 2 outcomes with NormalizedOdds prices."""
        scraper = OddsScraper()
        for markets in [
            scraper.scrape_espn_odds(),
            scraper.scrape_draftkings_odds(),
            scraper.scrape_fanduel_odds(),
        ]:
            for market in markets:
                assert len(market.outcomes) == 2
                for outcome in market.outcomes:
                    assert outcome.name
                    assert outcome.price.american != 0
                    assert outcome.price.decimal > 1.0
                    assert 0 < outcome.price.implied_probability < 1.0

    def test_get_all_odds_respects_config(self):
        """When all sportsbooks are enabled, 18 markets are returned (6 per sportsbook)."""
        scraper = OddsScraper()
        markets = scraper.get_all_odds()
        assert len(markets) == 18

    def test_get_all_odds_with_disabled_books(self):
        """Test that disabled books are skipped."""
        scraper = OddsScraper()
        scraper.config = {
            'sportsbooks': {
                'espn': {'enabled': False},
                'draftkings': {'enabled': True},
                'fanduel': {'enabled': False},
            }
        }
        markets = scraper.get_all_odds()
        assert len(markets) == 6
        for market in markets:
            assert market.key.startswith('draftkings_')

    def test_export_to_csv_writes_file(self):
        """Export creates a CSV file in the temp directory."""
        scraper = OddsScraper()
        scraper.scraped_odds = scraper.scrape_espn_odds()

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / 'test_odds.csv'
            scraper.export_to_csv(filename=str(filepath))
            assert filepath.exists()
            content = filepath.read_text()
            assert 'OKC Thunder' in content
            assert 'market_type' in content

    def test_export_to_csv_no_data_does_nothing(self):
        """Export with no scraped data prints a message but doesn't crash."""
        scraper = OddsScraper()
        scraper.export_to_csv(filename='data/nonexistent.csv')
        # Should not raise — just prints warning

    def test_timestamp_is_set_on_init(self):
        scraper = OddsScraper()
        assert scraper.timestamp
        assert ':' in scraper.timestamp  # datetime format

    def test_scrape_base_method_returns_all_odds(self):
        """BaseScraper.scrape() delegates to get_all_odds."""
        scraper = OddsScraper()
        markets = scraper.scrape()
        assert len(markets) == 18
        assert all(isinstance(m, Market) for m in markets)
