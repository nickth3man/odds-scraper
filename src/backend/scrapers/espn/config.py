"""Source-specific URLs and request parameters for the ESPN odds adapter."""

from __future__ import annotations

ESPN_API_URL = 'https://site.web.api.espn.com/apis/v2/scoreboard/header'
ESPN_SCOREBOARD_API_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
ESPN_API_PARAMS: dict[str, str] = {
    'sport': 'basketball',
    'league': 'nba',
    'region': 'us',
    'lang': 'en',
    'contentorigin': 'espn',
    'buyWindow': '1m',
    'showAirings': 'buy,live,replay',
    'tz': 'America/New_York',
}
