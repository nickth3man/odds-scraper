"""Unit tests for EVCalculator — expected value, Kelly criterion, and bet evaluation."""

import pytest

from backend.models.ev_calculator import EVCalculator

# ---------------------------------------------------------------------------
# convert_american_to_probability
# ---------------------------------------------------------------------------


def test_american_to_probability_negative_odds():
    """Convert negative American odds (-110, -200) to implied probability."""
    calculator = EVCalculator()
    assert calculator.convert_american_to_probability(-110) == pytest.approx(110 / 210)
    assert calculator.convert_american_to_probability(-200) == pytest.approx(200 / 300)


def test_american_to_probability_positive_odds():
    """Convert positive American odds (+150, +200) to implied probability."""
    calculator = EVCalculator()
    assert calculator.convert_american_to_probability(150) == pytest.approx(100 / 250)
    assert calculator.convert_american_to_probability(200) == pytest.approx(100 / 300)


def test_american_to_probability_zero():
    """Odds of 0 → 100% implied probability (degenerate)."""
    calculator = EVCalculator()
    assert calculator.convert_american_to_probability(0) == pytest.approx(1.0)


def test_american_to_probability_extreme():
    """Very large positive/negative odds map to near-0 and near-1."""
    calculator = EVCalculator()
    assert calculator.convert_american_to_probability(10000) == pytest.approx(100 / 10100)
    assert calculator.convert_american_to_probability(-10000) == pytest.approx(10000 / 10100)


def test_american_to_probability_requires_numeric_input():
    calculator = EVCalculator()

    with pytest.raises(TypeError, match='american_odds must be numeric'):
        calculator.convert_american_to_probability('bad')  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# calculate_expected_value
# ---------------------------------------------------------------------------


def test_calculate_expected_value_positive_scenario():
    """Expected value is positive when model probability exceeds implied probability."""
    calculator = EVCalculator()
    # -110 → implied 52.38%.  Model says 60%.  Edge → positive expected value.
    expected_value = calculator.calculate_expected_value(
        model_probability=0.60, american_odds=-110, stake=100
    )
    # payout = 100 * (100/110) = 90.909...
    # expected value = 0.60 * 90.909 - 0.40 * 100 = 54.545 - 40 = 14.545...
    assert expected_value > 0
    assert expected_value == pytest.approx(14.545, abs=0.01)


def test_calculate_expected_value_negative_scenario():
    """Expected value is negative when model probability is below implied probability."""
    calculator = EVCalculator()
    # -110 → implied 52.38%.  Model says 40%.  Edge → negative expected value.
    expected_value = calculator.calculate_expected_value(
        model_probability=0.40, american_odds=-110, stake=100
    )
    assert expected_value < 0
    assert expected_value == pytest.approx(-23.636, abs=0.01)


def test_calculate_expected_value_break_even():
    """Expected value ≈ 0 when model probability matches the implied probability."""
    calculator = EVCalculator()
    # +150 → implied 40%.  Use model_probability=0.40 → breakeven.
    expected_value = calculator.calculate_expected_value(
        model_probability=0.40, american_odds=150, stake=100
    )
    assert expected_value == pytest.approx(0.0, abs=1e-9)


def test_calculate_expected_value_positive_odds_payout():
    """Positive American odds produce correct payout and expected value."""
    calculator = EVCalculator()
    # +200 → payout = stake * (200/100) = 200 on $100
    expected_value = calculator.calculate_expected_value(
        model_probability=0.50, american_odds=200, stake=100
    )
    # expected value = 0.50 * 200 - 0.50 * 100 = 100 - 50 = 50
    assert expected_value == pytest.approx(50.0)


def test_calculate_expected_value_with_extreme_odds():
    """Extreme odds (+10000) produce very large positive expected value for high model prob."""
    calculator = EVCalculator()
    # +10000 → payout = 100 * 100 = 10000 on $100, expected value = 0.95*10000 - 0.05*100
    expected_value = calculator.calculate_expected_value(
        model_probability=0.95, american_odds=10000, stake=100
    )
    assert expected_value == pytest.approx(9495.0, abs=0.01)


def test_calculate_expected_value_zero_stake():
    """Zero stake produces zero expected value regardless of odds or probability."""
    calculator = EVCalculator()
    expected_value = calculator.calculate_expected_value(
        model_probability=0.50, american_odds=-110, stake=0
    )
    assert expected_value == 0.0


# ---------------------------------------------------------------------------
# evaluate_bet
# ---------------------------------------------------------------------------


def test_evaluate_bet_positive_ev():
    """Full evaluation returns correct dict when EV > 0."""
    calculator = EVCalculator()
    result = calculator.evaluate_bet(
        team='OKC Thunder', model_probability=0.78, american_odds=-175, stake=100
    )

    assert result['team'] == 'OKC Thunder'
    assert result['model_probability'] == '78.0%'
    assert result['sportsbook_probability'] == '63.6%'  # 175/275 ≈ 63.6%
    assert result['american_odds'] == -175
    assert result['expected_value_per_stake'] == '$22.57'
    assert result['expected_value_percent'] == '22.6%'
    assert result['recommendation'] == '[BET] Positive Expected Value'


def test_evaluate_bet_sportsbook_probability_field_is_float_str():
    """sportsbook_probability in result dict is the formatted string of the float value."""
    calculator = EVCalculator()
    result = calculator.evaluate_bet(
        team='Test', model_probability=0.5, american_odds=200, stake=100
    )
    # 200 → implied = 100/300 = 33.333... → '33.3%'
    assert result['sportsbook_probability'] == '33.3%'


def test_evaluate_bet_strong_negative_ev():
    """Recommendation is Strong Negative EV when EV < -5."""
    calculator = EVCalculator()
    # -110, model_probability=0.20 → EV ≈ -61.82 → < -5 → Strong Negative
    result = calculator.evaluate_bet(
        team='Bad Bet', model_probability=0.20, american_odds=-110, stake=100
    )
    assert result['recommendation'] == '[AVOID] Strong Negative Expected Value'


def test_evaluate_bet_slight_negative_ev():
    """Recommendation is Slight Negative EV when -5 <= EV <= 0."""
    calculator = EVCalculator()
    # -110, model_probability=0.50 → EV ≈ -4.55 → > -5 → Slight Negative
    result = calculator.evaluate_bet(
        team='Meh', model_probability=0.50, american_odds=-110, stake=100
    )
    assert result['recommendation'] == '[PASS] Slight Negative Expected Value'


def test_evaluate_bet_appends_to_bets_list():
    """Each evaluation appends to the instance bets list."""
    calculator = EVCalculator()
    assert len(calculator.bets) == 0
    calculator.evaluate_bet(team='A', model_probability=0.5, american_odds=-110)
    assert len(calculator.bets) == 1
    calculator.evaluate_bet(team='B', model_probability=0.5, american_odds=-110)
    assert len(calculator.bets) == 2
    assert calculator.bets[0]['team'] == 'A'
    assert calculator.bets[1]['team'] == 'B'


# ---------------------------------------------------------------------------
# calculate_kelly_criterion
# ---------------------------------------------------------------------------


def test_kelly_criterion_capped_at_five_percent():
    """Full Kelly above 5% is capped at 0.05 for bankroll safety."""
    calculator = EVCalculator()
    # win_prob=0.60, odds=-110 → full Kelly ≈ 16%, capped at 5%
    kelly = calculator.calculate_kelly_criterion(win_probability=0.60, american_odds=-110)
    assert kelly == pytest.approx(0.05)


def test_kelly_criterion_below_cap():
    """Kelly below 5% returns the uncapped value."""
    calculator = EVCalculator()
    # win_prob=0.525, odds=-105 → full Kelly = 2.625% (below cap)
    kelly = calculator.calculate_kelly_criterion(win_probability=0.525, american_odds=-105)
    assert 0 < kelly < 0.05
    # decimal_odds = 100/105 = 20/21; kelly = (0.525*20/21 - 0.475) / (20/21)
    # 0.525 * 20/21 = 0.5; kelly = (0.5-0.475) * 21/20 = 0.025 * 21/20 = 0.02625
    assert kelly == pytest.approx(0.02625, rel=1e-5)


def test_kelly_criterion_positive_odds():
    """Kelly works correctly with positive American odds."""
    calculator = EVCalculator()
    # win_prob=0.45, odds=+150 → full Kelly ≈ 23%, capped at 5%
    kelly = calculator.calculate_kelly_criterion(win_probability=0.45, american_odds=150)
    assert kelly == pytest.approx(0.05)


def test_kelly_criterion_zero_probability():
    """Probability of 0 yields Kelly of 0 (no bet)."""
    calculator = EVCalculator()
    kelly = calculator.calculate_kelly_criterion(win_probability=0.0, american_odds=-110)
    assert kelly == 0.0


def test_kelly_criterion_certainty():
    """Probability of 1.0 → uncapped Kelly > 5%, returns capped 0.05."""
    calculator = EVCalculator()
    kelly = calculator.calculate_kelly_criterion(win_probability=1.0, american_odds=-110)
    assert kelly == pytest.approx(0.05)


def test_kelly_criterion_negative_expected_value():
    """When expected value is negative, Kelly returns 0 (no bet recommended)."""
    calculator = EVCalculator()
    # win_prob=0.30, odds=-110 → negative expected value, Kelly should be 0
    kelly = calculator.calculate_kelly_criterion(win_probability=0.30, american_odds=-110)
    assert kelly == 0.0


def test_display_bet_analysis_prints_formatted_rows(capsys):
    calculator = EVCalculator()

    calculator.display_bet_analysis(
        [
            {
                'team': 'OKC Thunder',
                'model_probability': '60.0%',
                'sportsbook_probability': '52.4%',
                'american_odds': -110,
                'expected_value_per_stake': '$14.55',
                'expected_value_percent': '14.5%',
                'recommendation': '[BET] Positive Expected Value',
            }
        ]
    )

    output = capsys.readouterr().out
    assert 'BET ANALYSIS' in output
    assert 'TEAM: OKC Thunder' in output
    assert 'Recommendation:        [BET] Positive Expected Value' in output
