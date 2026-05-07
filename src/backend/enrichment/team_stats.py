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

    @staticmethod
    def _current_nba_season() -> str:
        """
        Return the NBA season identifier in 'YYYY-YY' format for today's date.
        
        If today's month is October or later the season start year is the current year; otherwise the start year is the previous year.
        
        Returns:
            season (str): Season string formatted as 'YYYY-YY', e.g., '2024-25'.
        """
        from datetime import date

        today = date.today()
        start_year = today.year if today.month >= 10 else today.year - 1
        return f'{start_year}-{str(start_year + 1)[2:]}'

    def __init__(self, cache_ttl: float = 14400.0):
        """
        Create a TeamEnrichmentService and initialize its TTL cache.
        
        Parameters:
            cache_ttl (float): Time-to-live for cached entries in seconds (default 14400.0, 4 hours).
        """
        self._cache: TTLCache[dict[str, TeamStats]] = TTLCache(default_ttl=cache_ttl)

    def get_team_stats(self, team_name: str) -> TeamStats | None:
        """
        Get aggregated TeamStats for a team identified by its display name or a substring of its display name.
        
        Parameters:
            team_name (str): Official team display name, 3-letter tricode, or any substring of the display name used to locate the team.
        
        Returns:
            TeamStats | None: `TeamStats` for the matched team if found, `None` otherwise.
        """
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
        """
        Retrieve a mapping of all teams' aggregated statistics, using a cached dataset when available.
        
        If no cached data exists the method attempts to fetch fresh data from the NBA API; returns `None` if retrieval fails.
        
        Returns:
            dict[str, TeamStats] | None: Mapping from three-letter team abbreviation to `TeamStats`, or `None` if data could not be obtained.
        """
        cached = self._cache.get('all_teams')
        if cached is not None:
            return cached
        try:
            return self._fetch_from_nba_api()
        except Exception as error:
            logger.error('Failed to fetch team stats from nba_api', error=str(error))
            return None

    def _fetch_from_nba_api(self) -> dict[str, TeamStats]:
        """
        Fetches current NBA team advanced statistics and standings from stats.nba.com, combines them into TeamStats objects, caches the result under 'all_teams', and returns a mapping keyed by team abbreviation.

        Returns:
            dict[str, TeamStats]: Mapping from three-letter team abbreviation (e.g., "LAL") to the corresponding TeamStats instance.
        """
        from nba_api.stats.endpoints import leaguedashteamstats, leaguestandings

        logger.info('Fetching team stats from nba_api', action='fetch')
        stats_dict: dict[str, TeamStats] = {}

        advanced = leaguedashteamstats.LeagueDashTeamStats(
            measure_type_detailed_defense='Advanced',
            season=self._current_nba_season(),
            season_type_all_star='Regular Season',
        )
        advanced_rows = advanced.get_dict()['resultSets'][0]['rowSet']
        advanced_headers = advanced.get_dict()['resultSets'][0]['headers']

        team_id_idx = advanced_headers.index('TEAM_ID')
        team_idx = advanced_headers.index('TEAM_NAME')
        abbr_idx = advanced_headers.index('TEAM_ABBREVIATION')
        off_idx = advanced_headers.index('OFF_RATING')
        def_idx = advanced_headers.index('DEF_RATING')
        net_idx = advanced_headers.index('NET_RATING')
        pace_idx = advanced_headers.index('PACE')

        advanced_data: dict[str, dict[str, Any]] = {}
        for row in advanced_rows:
            team_id = str(row[team_id_idx])
            abbr = str(row[abbr_idx])
            advanced_data[team_id] = {
                'team_name': row[team_idx],
                'abbreviation': abbr,
                'off_rating': row[off_idx],
                'def_rating': row[def_idx],
                'net_rating': row[net_idx],
                'pace': row[pace_idx],
            }

        standings = leaguestandings.LeagueStandings(
            season=self._current_nba_season(),
            season_type='Regular Season',
        )
        standings_rows = standings.get_dict()['resultSets'][0]['rowSet']
        standings_headers = standings.get_dict()['resultSets'][0]['headers']

        w_idx = standings_headers.index('WINS')
        l_idx = standings_headers.index('LOSSES')
        wp_idx = standings_headers.index('WinPCT')
        tid_idx = standings_headers.index('TeamID')

        for row in standings_rows:
            team_id = str(row[tid_idx])
            advances = advanced_data.get(team_id)
            if advances is None:
                continue
            abbr = str(advances['abbreviation'])
            stats_dict[abbr] = TeamStats(
                team_name=str(advances['team_name']),
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
