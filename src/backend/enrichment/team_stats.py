"""Fetch and cache NBA team statistics from stats.nba.com via nba_api."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from loguru import logger

from .cache import TTLCache


@dataclass(frozen=True)
class TeamStats:
    """Aggregated team statistics for win probability estimation."""

    team_name: str
    abbreviation: str
    wins: int
    losses: int
    win_pct: float
    off_rating: float
    def_rating: float
    net_rating: float
    pace: float
    recent_wins: int
    recent_losses: int


_TEAM_NAME_TO_TRICODE: dict[str, str] = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS',
}


class TeamEnrichmentService:
    """Fetch and cache team-level NBA statistics.

    Uses nba_api's league dash stats endpoints with a TTL cache
    to avoid hitting stats.nba.com on every scrape cycle.
    """

    def __init__(self, cache_ttl: float = 14400.0):
        self._cache: TTLCache[dict[str, TeamStats]] = TTLCache(default_ttl=cache_ttl)

    def get_team_stats(self, team_name: str) -> TeamStats | None:
        """Look up stats for a team by display name."""
        all_stats = self._get_all_team_stats()
        if all_stats is None:
            return None
        tricode = _TEAM_NAME_TO_TRICODE.get(team_name)
        if tricode and tricode in all_stats:
            return all_stats[tricode]
        for stats in all_stats.values():
            if team_name in stats.team_name:
                return stats
        logger.warning('Team not found in stats', team=team_name)
        return None

    def _get_all_team_stats(self) -> dict[str, TeamStats] | None:
        """Fetch all team stats from cache or nba_api."""
        cached = self._cache.get('all_teams')
        if cached is not None:
            return cached
        try:
            return self._fetch_from_nba_api()
        except Exception as error:
            logger.error('Failed to fetch team stats from nba_api', error=str(error))
            return None

    def _fetch_from_nba_api(self) -> dict[str, TeamStats]:
        """Live fetch from stats.nba.com. Raises on network failure."""
        from nba_api.stats.endpoints import leaguedashteamstats, leaguestandings

        logger.info('Fetching team stats from nba_api', action='fetch')
        stats_dict: dict[str, TeamStats] = {}

        advanced = leaguedashteamstats.LeagueDashTeamStats(
            measure_type_detailed_defense='Advanced',
            season='2025-26',
            season_type_all_star='Regular Season',
        )
        advanced_rows = advanced.get_dict()['resultSets'][0]['rowSet']
        advanced_headers = advanced.get_dict()['resultSets'][0]['headers']

        team_idx = advanced_headers.index('TEAM_NAME')
        abbr_idx = advanced_headers.index('TEAM_ABBREVIATION')
        off_idx = advanced_headers.index('OFF_RATING')
        def_idx = advanced_headers.index('DEF_RATING')
        net_idx = advanced_headers.index('NET_RATING')
        pace_idx = advanced_headers.index('PACE')

        advanced_data: dict[str, dict[str, Any]] = {}
        for row in advanced_rows:
            abbr = row[abbr_idx]
            advanced_data[abbr] = {
                'team_name': row[team_idx],
                'abbreviation': abbr,
                'off_rating': row[off_idx],
                'def_rating': row[def_idx],
                'net_rating': row[net_idx],
                'pace': row[pace_idx],
            }

        standings = leaguestandings.LeagueStandings(
            season='2025-26',
            season_type='Regular Season',
        )
        standings_rows = standings.get_dict()['resultSets'][0]['rowSet']
        standings_headers = standings.get_dict()['resultSets'][0]['headers']

        w_idx = standings_headers.index('WINS')
        l_idx = standings_headers.index('LOSSES')
        wp_idx = standings_headers.index('WinPct')
        ts_idx = standings_headers.index('TeamSlug')

        for row in standings_rows:
            slug: str = row[ts_idx]
            abbr = slug.split('-')[-1].upper()
            advances = advanced_data.get(abbr, {})
            stats_dict[abbr] = TeamStats(
                team_name=advances.get('team_name', abbr),
                abbreviation=abbr,
                wins=row[w_idx],
                losses=row[l_idx],
                win_pct=row[wp_idx],
                off_rating=advances.get('off_rating', 0.0),
                def_rating=advances.get('def_rating', 0.0),
                net_rating=advances.get('net_rating', 0.0),
                pace=advances.get('pace', 0.0),
                recent_wins=0,
                recent_losses=0,
            )

        self._cache.set('all_teams', stats_dict)
        logger.info('Team stats fetched and cached', team_count=len(stats_dict), action='complete')
        return stats_dict
