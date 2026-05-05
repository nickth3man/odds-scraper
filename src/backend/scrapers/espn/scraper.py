"""ESPN NBA odds source adapter.

This module owns ESPN-specific fetching, fallback selection, and JSON-shape
parsing. Browser/DraftKings parsing remains separate so API and DOM concerns do
not leak into each other.
"""

from __future__ import annotations

import contextlib
from datetime import datetime

import httpx
from loguru import logger

from ..shared.http_client import HttpClient
from ..shared.parsers import GameOdds, format_american_odds, format_event_date, format_line
from .config import ESPN_API_PARAMS, ESPN_API_URL, ESPN_SCOREBOARD_API_URL


class EspnOddsScraper:
    """Fetch and normalize NBA odds from ESPN JSON APIs."""

    def __init__(self, http: HttpClient | None = None):
        self._http = http or HttpClient()

    def scrape_nba_odds(self) -> list[GameOdds]:
        """Fetch live NBA odds from ESPN's header API with scoreboard fallback."""
        logger.info('Fetching live NBA odds', source='ESPN', action='fetch')

        try:
            response = self._http.get(
                ESPN_API_URL,
                params=ESPN_API_PARAMS,
            )
            response_data = response.json()

            sports = response_data.get('sports') or []
            leagues = sports[0].get('leagues', []) if sports else []
            events = leagues[0].get('events', []) if leagues else []
            games = self.parse_header_events(events)

            if games:
                logger.info(
                    'Scrape complete', source='ESPN', game_count=len(games), action='complete'
                )
                return games

            logger.warning('No upcoming games found', source='ESPN')
            return []

        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            logger.warning(
                'Header API failed, falling back to scoreboard', source='ESPN', error=str(error)
            )
            return self.scrape_scoreboard_fallback()

    def parse_header_events(self, events: list) -> list[GameOdds]:
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

                home_competitor = next(
                    (
                        competitor
                        for competitor in competitors
                        if competitor.get('homeAway') == 'home'
                    ),
                    None,
                )
                away_competitor = next(
                    (
                        competitor
                        for competitor in competitors
                        if competitor.get('homeAway') == 'away'
                    ),
                    None,
                )
                if not home_competitor or not away_competitor:
                    continue

                home_team = home_competitor.get('displayName', 'Unknown')
                away_team = away_competitor.get('displayName', 'Unknown')
                spread = 'N/A'
                raw_home_spread = odds.get('spread')
                if raw_home_spread is not None:
                    with contextlib.suppress(ValueError):
                        away_spread_value = -float(raw_home_spread)
                        spread = (
                            f'+{away_spread_value}'
                            if away_spread_value > 0
                            else str(away_spread_value)
                        )

                over_under = str(odds['overUnder']) if odds.get('overUnder') is not None else 'N/A'

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
                        'over_under': over_under,
                        'source': 'ESPN',
                    }
                )

            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as error:
                logger.warning('Failed to parse ESPN event: %s', error)
                continue

        return games

    def scrape_scoreboard_fallback(self) -> list[GameOdds]:
        """Fetch equivalent normalized odds from ESPN's scoreboard API shape."""
        try:
            response = self._http.get(
                ESPN_SCOREBOARD_API_URL,
                params={'dates': datetime.now().strftime('%Y%m%d'), 'limit': 100},
            )
            games = self.parse_scoreboard_events(response.json().get('events', []))
        except (httpx.HTTPError, ValueError, AttributeError) as error:
            logger.error('Scoreboard fallback failed', source='ESPN', error=str(error))
            return []

        if games:
            logger.info(
                'Fallback scrape complete', source='ESPN', game_count=len(games), action='complete'
            )
            return games

        logger.warning('Fallback: no upcoming games found', source='ESPN')
        return []

    def parse_scoreboard_events(self, events: list) -> list[GameOdds]:
        games = []

        for event in events:
            try:
                competition = (event.get('competitions') or [{}])[0]
                competitors = competition.get('competitors', [])
                home_competitor = next(
                    (
                        competitor
                        for competitor in competitors
                        if competitor.get('homeAway') == 'home'
                    ),
                    None,
                )
                away_competitor = next(
                    (
                        competitor
                        for competitor in competitors
                        if competitor.get('homeAway') == 'away'
                    ),
                    None,
                )
                if not home_competitor or not away_competitor:
                    continue

                odds = self.select_scoreboard_odds(competition.get('odds', []))
                if not odds:
                    continue

                home_team = home_competitor.get('team', {}).get('displayName', 'Unknown')
                away_team = away_competitor.get('team', {}).get('displayName', 'Unknown')
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
            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as error:
                logger.warning('Failed to parse ESPN scoreboard event: %s', error)
                continue

        return games

    def select_scoreboard_odds(self, odds_list: list) -> dict | None:
        for odds in odds_list:
            provider = odds.get('provider', {})
            provider_name = provider.get('displayName') or provider.get('name') or ''
            if 'draft' in provider_name.lower():
                return odds
        return odds_list[0] if odds_list else None
