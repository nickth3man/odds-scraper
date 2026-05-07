"""Tests for NBA team enrichment — no live network calls."""

from __future__ import annotations

import time

import pytest

from backend.enrichment.cache import TTLCache
from backend.enrichment.probability import compute_model_probability
from backend.enrichment.team_stats import TeamEnrichmentService, TeamStats


def _make_stats(
    team: str,
    net: float,
    win_pct: float = 0.5,
    wins: int = 41,
    losses: int = 41,
) -> TeamStats:
    """
    Create a TeamStats instance for tests with sensible default ratings and record fields.

    Parameters:
        team (str): Full team name; `abbreviation` will be the first three characters uppercased.
        net (float): Net rating to assign to `net_rating`; `def_rating` is set to 110.0 - net.
        win_pct (float): Team winning percentage.
        wins (int): Number of wins.
        losses (int): Number of losses.

    Returns:
        TeamStats: A TeamStats object populated with the provided values and fixed defaults for
        `off_rating`, `pace`, `recent_wins`, and `recent_losses`.
    """
    return TeamStats(
        team_name=team,
        abbreviation=team[:3].upper(),
        wins=wins,
        losses=losses,
        win_pct=win_pct,
        off_rating=110.0,
        def_rating=110.0 - net,
        net_rating=net,
        pace=100.0,
        recent_wins=5,
        recent_losses=5,
    )


class TestProbabilityModel:
    """Verify the win probability model produces reasonable outputs."""

    def test_equal_teams_slight_home_favorite(self) -> None:
        """Evenly matched teams — home team should have slight edge from HCA."""
        home = _make_stats('BOS', net=0.0, win_pct=0.5)
        away = _make_stats('OKC', net=0.0, win_pct=0.5)
        prob = compute_model_probability(home, away)
        assert 0.50 < prob < 0.60, f'Expected 50-60%%, got {prob}'

    def test_strong_home_team_heavily_favored(self) -> None:
        """Strong home team with positive net rating should be favored."""
        home = _make_stats('Boston Celtics', net=10.0, win_pct=0.70, wins=58, losses=24)
        away = _make_stats('Washington Wizards', net=-5.0, win_pct=0.30, wins=25, losses=57)
        prob = compute_model_probability(home, away)
        assert prob > 0.65, f'Expected >65%%, got {prob}'

    def test_probability_bounded_to_0_01__0_99(self) -> None:
        """Output is always between 1% and 99%."""
        home = _make_stats('A', net=50.0, win_pct=0.99)
        away = _make_stats('B', net=-50.0, win_pct=0.01)
        prob = compute_model_probability(home, away)
        assert 0.01 <= prob <= 0.99, f'Expected bounded, got {prob}'


class TestTTLCache:
    """Verify the TTL cache behaves correctly."""

    def test_miss_returns_none(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl=1.0)
        assert cache.get('missing') is None

    def test_set_and_get(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl=100.0)
        cache.set('key', 'value')
        assert cache.get('key') == 'value'

    def test_expired_entry_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl=0.01)
        cache.set('key', 'value')
        monkeypatch.setattr(time, 'monotonic', lambda: 999999.0)
        assert cache.get('key') is None

    def test_overwrite_existing_key(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl=100.0)
        cache.set('key', 'first')
        cache.set('key', 'second')
        assert cache.get('key') == 'second'

    def test_clear_removes_all(self) -> None:
        cache: TTLCache[str] = TTLCache(default_ttl=100.0)
        cache.set('a', '1')
        cache.set('b', '2')
        cache.clear()
        assert cache.get('a') is None
        assert cache.get('b') is None

    def test_generic_type_works_with_dict(self) -> None:
        cache: TTLCache[dict[str, TeamStats]] = TTLCache(default_ttl=100.0)
        stats = _make_stats('BOS', net=5.0)
        cache.set('teams', {'BOS': stats})
        result = cache.get('teams')
        assert result is not None
        assert 'BOS' in result


class TestTeamEnrichmentServiceWithCache:
    """Verify TeamEnrichmentService works with pre-populated cache — zero network calls."""

    def test_get_team_stats_from_cache_exact_match(self) -> None:
        service = TeamEnrichmentService(cache_ttl=9999.0)
        bos_stats = _make_stats('Boston Celtics', net=5.0, win_pct=0.65, wins=54, losses=28)
        service._cache.set('all_teams', {'BOS': bos_stats})
        result = service.get_team_stats('Boston Celtics')
        assert result is not None
        assert result.net_rating == 5.0
        assert result.wins == 54

    def test_get_team_stats_not_found_returns_none(self) -> None:
        service = TeamEnrichmentService(cache_ttl=9999.0)
        service._cache.set('all_teams', {})
        assert service.get_team_stats('Unknown Team') is None

    def test_get_team_stats_substring_fallback(self) -> None:
        """Fallback matches team if name is a substring of an actual team."""
        service = TeamEnrichmentService(cache_ttl=9999.0)
        bos_stats = _make_stats('Boston Celtics', net=5.0)
        service._cache.set('all_teams', {'BOS': bos_stats})
        result = service.get_team_stats('Celtics')
        assert result is not None

    def test_get_team_stats_empty_cache_returns_none(self) -> None:
        """
        Verify TeamEnrichmentService.get_team_stats behavior when the internal cache is empty and no API call is performed.

        Asserts that the method yields `None` in this scenario without performing network requests.
        """
        service = TeamEnrichmentService(cache_ttl=9999.0)
        service._cache.clear()
        service._fetch_from_nba_api = lambda: {}  # type: ignore[method-assign]
        result = service.get_team_stats('Boston Celtics')
        assert result is None


class TestTeamStatsDataclass:
    """Verify TeamStats dataclass is frozen and has correct fields."""

    def test_team_stats_creation(self) -> None:
        stats = TeamStats(
            team_name='Boston Celtics',
            abbreviation='BOS',
            wins=54,
            losses=28,
            win_pct=0.659,
            off_rating=120.5,
            def_rating=110.2,
            net_rating=10.3,
            pace=99.8,
            recent_wins=7,
            recent_losses=3,
        )
        assert stats.team_name == 'Boston Celtics'
        assert stats.win_pct == 0.659
        assert stats.net_rating == 10.3

    def test_team_stats_is_frozen(self) -> None:
        """
        Verify that assigning to a field on a TeamStats instance raises AttributeError, confirming the dataclass is frozen/immutable.
        """
        stats = _make_stats('BOS', net=5.0)
        with pytest.raises(AttributeError):
            stats.wins = 999  # type: ignore[misc]
