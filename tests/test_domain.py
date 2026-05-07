"""Tests for core betting domain models and de-vigging logic."""

from __future__ import annotations

import pytest

from backend.models.domain import Market, MarketType, NormalizedOdds, Outcome
from backend.models.ev_calculator import EVCalculator, devig_market

# ---------------------------------------------------------------------------
# NormalizedOdds
# ---------------------------------------------------------------------------


class TestNormalizedOdds:
    def test_from_american_positive(self):
        """+150 → decimal 2.5, implied 0.4."""
        odds = NormalizedOdds.from_american(150)
        assert odds.american == 150
        assert odds.decimal == pytest.approx(2.5)
        assert odds.implied_probability == pytest.approx(0.4)

    def test_from_american_negative(self):
        """-110 → decimal ~1.909, implied ~0.5238."""
        odds = NormalizedOdds.from_american(-110)
        assert odds.american == -110
        assert odds.decimal == pytest.approx(100 / 110 + 1, abs=1e-9)
        assert odds.implied_probability == pytest.approx(110 / 210, abs=1e-9)

    def test_from_american_zero(self):
        """0 → decimal 1.0, implied 1.0 (degenerate)."""
        odds = NormalizedOdds.from_american(0)
        assert odds.decimal == 1.0
        assert odds.implied_probability == 1.0

    def test_from_american_extreme_positive(self):
        """Very large positive odds → near-zero probability."""
        odds = NormalizedOdds.from_american(10000)
        assert odds.implied_probability == pytest.approx(100 / 10100, abs=1e-9)

    def test_from_american_extreme_negative(self):
        """Very large negative odds → near-1 probability."""
        odds = NormalizedOdds.from_american(-10000)
        assert odds.implied_probability == pytest.approx(10000 / 10100, abs=1e-9)


# ---------------------------------------------------------------------------
# Outcome
# ---------------------------------------------------------------------------


class TestOutcome:
    def test_outcome_with_point(self):
        outcome = Outcome(
            name='Over',
            price=NormalizedOdds.from_american(-110),
            point=220.5,
        )
        assert outcome.name == 'Over'
        assert outcome.point == 220.5
        assert outcome.price.implied_probability == pytest.approx(110 / 210, abs=1e-9)

    def test_outcome_without_point(self):
        outcome = Outcome(
            name='Lakers',
            price=NormalizedOdds.from_american(+150),
        )
        assert outcome.point is None
        assert outcome.description is None


# ---------------------------------------------------------------------------
# Market
# ---------------------------------------------------------------------------


class TestMarket:
    def test_market_creation(self):
        market = Market(
            key='nba-001-spread',
            name='Spread',
            sport='nba',
            event_id='nba-001',
            market_type=MarketType.SPREADS,
            outcomes=[
                Outcome(name='Lakers -5.5', price=NormalizedOdds.from_american(-110), point=-5.5),
                Outcome(name='Celtics +5.5', price=NormalizedOdds.from_american(-110), point=5.5),
            ],
        )
        assert market.key == 'nba-001-spread'
        assert len(market.outcomes) == 2


# ---------------------------------------------------------------------------
# devig_market
# ---------------------------------------------------------------------------


class TestDevigMarket:
    def test_devig_two_way_market(self):
        """Standard -110/-110 market → true probabilities ~0.5 each."""
        market = Market(
            key='m1',
            name='Moneyline',
            sport='nba',
            market_type=MarketType.H2H,
            outcomes=[
                Outcome(name='A', price=NormalizedOdds.from_american(-110)),
                Outcome(name='B', price=NormalizedOdds.from_american(-110)),
            ],
        )
        true_probs = devig_market(market)
        assert len(true_probs) == 2
        assert true_probs[0] == pytest.approx(0.5, abs=1e-4)
        assert true_probs[1] == pytest.approx(0.5, abs=1e-4)
        assert sum(true_probs) == pytest.approx(1.0, abs=1e-9)

    def test_devig_unequal_odds(self):
        """+150 / -170 market → true probabilities sum to 1.0."""
        market = Market(
            key='m2',
            name='Moneyline',
            sport='nba',
            market_type=MarketType.H2H,
            outcomes=[
                Outcome(name='Underdog', price=NormalizedOdds.from_american(150)),
                Outcome(name='Favorite', price=NormalizedOdds.from_american(-170)),
            ],
        )
        true_probs = devig_market(market)
        assert len(true_probs) == 2
        assert sum(true_probs) == pytest.approx(1.0, abs=1e-9)
        # Underdog should have lower true probability than favorite
        assert true_probs[0] < true_probs[1]

    def test_devig_three_way_market(self):
        """Three-way market (e.g. soccer 1X2) also devigs correctly."""
        market = Market(
            key='m3',
            name='1X2',
            sport='soccer',
            market_type=MarketType.OUTRIGHTS,
            outcomes=[
                Outcome(name='Home', price=NormalizedOdds.from_american(200)),
                Outcome(name='Draw', price=NormalizedOdds.from_american(220)),
                Outcome(name='Away', price=NormalizedOdds.from_american(140)),
            ],
        )
        true_probs = devig_market(market)
        assert len(true_probs) == 3
        assert sum(true_probs) == pytest.approx(1.0, abs=1e-9)

    def test_devig_empty_market(self):
        """
        Verify devig_market handles a market with no outcomes.
        
        Constructs an empty Market and asserts that calling devig_market on it yields an empty list.
        """
        market = Market(
            key='m4',
            name='Empty',
            sport='nba',
            market_type=MarketType.H2H,
            outcomes=[],
        )
        assert devig_market(market) == []

    def test_devig_zero_probabilities(self):
        """Market with all zero implied probabilities returns zeros."""
        market = Market(
            key='m5',
            name='Degenerate',
            sport='nba',
            market_type=MarketType.H2H,
            outcomes=[
                Outcome(
                    name='A', price=NormalizedOdds(american=0, decimal=1.0, implied_probability=0.0)
                ),
                Outcome(
                    name='B', price=NormalizedOdds(american=0, decimal=1.0, implied_probability=0.0)
                ),
            ],
        )
        true_probs = devig_market(market)
        assert true_probs == [0.0, 0.0]


# ---------------------------------------------------------------------------
# EVCalculator with NormalizedOdds
# ---------------------------------------------------------------------------


class TestEVCalculatorWithNormalizedOdds:
    def test_calculate_expected_value_from_odds_positive(self):
        calculator = EVCalculator()
        odds = NormalizedOdds.from_american(-110)
        ev = calculator.calculate_expected_value_from_odds(
            model_probability=0.60, odds=odds, stake=100
        )
        # Same as calculate_expected_value with american_odds=-110
        expected = calculator.calculate_expected_value(0.60, -110, 100)
        assert ev == pytest.approx(expected, abs=1e-9)

    def test_calculate_expected_value_from_odds_negative(self):
        calculator = EVCalculator()
        odds = NormalizedOdds.from_american(150)
        ev = calculator.calculate_expected_value_from_odds(
            model_probability=0.30, odds=odds, stake=100
        )
        expected = calculator.calculate_expected_value(0.30, 150, 100)
        assert ev == pytest.approx(expected, abs=1e-9)
