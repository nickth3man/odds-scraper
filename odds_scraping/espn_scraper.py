"""ESPN NBA odds source adapter.

This module owns ESPN-specific fetching, fallback selection, and JSON-shape
parsing. Browser/DraftKings parsing remains separate so API and DOM concerns do
not leak into each other.
"""

from __future__ import annotations

import contextlib
import logging
from datetime import datetime

import httpx

from .http_client import HttpClient
from .parsers import format_american_odds, format_event_date, format_line

logger = logging.getLogger(__name__)

_ESPN_API_URL = 'https://site.web.api.espn.com/apis/v2/scoreboard/header'
_ESPN_SCOREBOARD_API_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
_ESPN_API_PARAMS = {
    'sport': 'basketball',
    'league': 'nba',
    'region': 'us',
    'lang': 'en',
    'contentorigin': 'espn',
    'buyWindow': '1m',
    'showAirings': 'buy,live,replay',
    'tz': 'America/New_York',
}


class EspnOddsScraper:
    """Fetch and normalize NBA odds from ESPN JSON APIs."""

    def __init__(self, http: HttpClient | None = None):
        self._http = http or HttpClient()

    def scrape_nba_odds(self) -> list[dict]:
        """Fetch live NBA odds from ESPN's header API with scoreboard fallback."""
        print('[Fetching] Live NBA odds from ESPN API...\n')

        try:
            response = self._http.get(
                _ESPN_API_URL,
                params=_ESPN_API_PARAMS,
            )
            data = response.json()

            sports = data.get('sports') or []
            leagues = sports[0].get('leagues', []) if sports else []
            events = leagues[0].get('events', []) if leagues else []
            games = self.parse_header_events(events)

            if games:
                print(f'[OK] ESPN: Found {len(games)} games\n')
                return games

            print('[WARN] ESPN: No upcoming games found\n')
            return []

        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            print(f'[WARN] ESPN header API failed: {e}')
            return self.scrape_scoreboard_fallback()

    def parse_header_events(self, events: list) -> list[dict]:
        """Parse ESPN header API event objects into the live odds schema."""
        games = []

        for event in events:
            try:
                odds = event.get('odds')
                if not odds:
                    continue

                competitors = event.get('competitors', [])
                if len(competitors) < 2:
                    continue

                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                if not home or not away:
                    continue

                home_team = home.get('displayName', 'Unknown')
                away_team = away.get('displayName', 'Unknown')
                spread = 'N/A'
                home_spread = odds.get('spread')
                if home_spread is not None:
                    with contextlib.suppress(ValueError):
                        spread_val = -float(home_spread)
                        spread = f'+{spread_val}' if spread_val > 0 else str(spread_val)

                ou = str(odds['overUnder']) if odds.get('overUnder') is not None else 'N/A'

                away_team_odds = odds.get('awayTeamOdds', {})
                home_team_odds = odds.get('homeTeamOdds', {})
                away_moneyline = format_american_odds(away_team_odds.get('moneyLine'))
                home_moneyline = format_american_odds(home_team_odds.get('moneyLine'))

                games.append(
                    {
                        'date': format_event_date(event.get('date', '')),
                        'home_team': home_team,
                        'away_team': away_team,
                        'matchup': f'{away_team} @ {home_team}',
                        'spread': spread,
                        'moneyline': away_moneyline,
                        'home_moneyline': home_moneyline,
                        'over_under': ou,
                        'source': 'ESPN',
                    }
                )

            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as e:
                logger.warning('Failed to parse ESPN event: %s', e)
                continue

        return games

    def scrape_scoreboard_fallback(self) -> list[dict]:
        """Fetch equivalent normalized odds from ESPN's scoreboard API shape."""
        try:
            response = self._http.get(
                _ESPN_SCOREBOARD_API_URL,
                params={'dates': datetime.now().strftime('%Y%m%d'), 'limit': 100},
            )
            games = self.parse_scoreboard_events(response.json().get('events', []))
        except (httpx.HTTPError, ValueError, AttributeError) as e:
            print(f'[ERROR] ESPN Error: {e}\n')
            return []

        if games:
            print(f'[OK] ESPN fallback: Found {len(games)} games\n')
            return games

        print('[WARN] ESPN fallback: No upcoming games found\n')
        return []

    def parse_scoreboard_events(self, events: list) -> list[dict]:
        games = []

        for event in events:
            try:
                competition = (event.get('competitions') or [{}])[0]
                competitors = competition.get('competitors', [])
                home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
                away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
                if not home or not away:
                    continue

                odds = self.select_scoreboard_odds(competition.get('odds', []))
                if not odds:
                    continue

                home_team = home.get('team', {}).get('displayName', 'Unknown')
                away_team = away.get('team', {}).get('displayName', 'Unknown')
                home_moneyline = odds.get('moneyline', {}).get('home', {}).get('close', {})
                away_moneyline = odds.get('moneyline', {}).get('away', {}).get('close', {})
                away_spread = odds.get('pointSpread', {}).get('away', {}).get('close', {})
                over_total = odds.get('total', {}).get('over', {}).get('close', {})

                games.append(
                    {
                        'date': format_event_date(event.get('date', '')),
                        'home_team': home_team,
                        'away_team': away_team,
                        'matchup': f'{away_team} @ {home_team}',
                        'spread': format_line(away_spread.get('line')),
                        'moneyline': format_american_odds(away_moneyline.get('odds')),
                        'home_moneyline': format_american_odds(home_moneyline.get('odds')),
                        'over_under': format_line(over_total.get('line')),
                        'source': 'ESPN',
                    }
                )
            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as e:
                logger.warning('Failed to parse ESPN scoreboard event: %s', e)
                continue

        return games

    def select_scoreboard_odds(self, odds_list: list) -> dict | None:
        for odds in odds_list:
            provider = odds.get('provider', {})
            provider_name = provider.get('displayName') or provider.get('name') or ''
            if 'draft' in provider_name.lower():
                return odds
        return odds_list[0] if odds_list else None
