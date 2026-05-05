"""Simple win probability model from team statistics."""

from __future__ import annotations

from .team_stats import TeamStats


def compute_model_probability(home_stats: TeamStats, away_stats: TeamStats) -> float:
    """
    Estimate the home team's win probability using net-rating and recent win percentages.
    
    Parameters:
        home_stats (TeamStats): Home team statistics; must provide `net_rating` and `win_pct`.
        away_stats (TeamStats): Away team statistics; must provide `net_rating` and `win_pct`.
    
    Returns:
        probability (float): Estimated home win probability constrained to the interval [0.01, 0.99] and rounded to 4 decimal places.
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
