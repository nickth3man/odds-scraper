"""Simple win probability model from team statistics."""

from __future__ import annotations

from .team_stats import TeamStats


def compute_model_probability(home_stats: TeamStats, away_stats: TeamStats) -> float:
    """Estimate home team win probability from team stats.

    Uses a simplified logistic approach based on net rating differential
    with a standard 3-point home court advantage.
    """
    home_advantage = 3.0
    home_net = home_stats.net_rating + home_advantage
    away_net = away_stats.net_rating
    differential = home_net - away_net

    probability = 1.0 / (1.0 + 2.71828 ** (-0.03 * differential))

    home_expected = home_stats.win_pct
    away_expected = 1.0 - away_stats.win_pct
    blended = 0.6 * probability + 0.4 * ((home_expected + away_expected) / 2)

    return round(max(0.01, min(0.99, blended)), 4)
