"""ESPN NBA odds source adapter.

This module owns ESPN-specific fetching, fallback selection, and JSON-shape
parsing. Browser/DraftKings parsing remains separate so API and DOM concerns do
not leak into each other.
"""

from __future__ import annotations

import contextlib
import re
from datetime import datetime

import httpx
from loguru import logger

from backend.models.domain import Market, MarketType, NormalizedOdds, Outcome

from ..shared.http_client import HttpClient
from .config import ESPN_API_PARAMS, ESPN_API_URL, ESPN_SCOREBOARD_API_URL


def _parse_float_line(value: str | int | float | None) -> float | None:
    """Strip leading alpha chars and convert to float."""
    if value is None:
        return None
    cleaned = re.sub(r'^[a-zA-Z]+', '', str(value))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


class EspnOddsScraper:
    """Fetch and normalize NBA odds from ESPN JSON APIs."""

    def __init__(self, http: HttpClient | None = None):
        self._http = http or HttpClient()

    def scrape_nba_odds(self) -> list[Market]:
        """
        Scrape and return normalized live NBA odds from ESPN, using the header API with a scoreboard fallback.

        Attempts to fetch and parse odds from ESPN's header API; if the header request or parse fails, the function falls back to the ESPN scoreboard fetch and returns its results. When the header response contains no games, an empty list is returned without attempting the fallback.

        Returns:
            list[Market]: List of normalized market objects (empty list if no games are found).
        """
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
            markets = self.parse_header_events(events)

            if markets:
                logger.info(
                    'Scrape complete', source='ESPN', market_count=len(markets), action='complete'
                )
                return markets

            logger.warning('No upcoming games found', source='ESPN')
            return []

        except (httpx.HTTPError, KeyError, IndexError, ValueError) as error:
            logger.warning(
                'Header API failed, falling back to scoreboard', source='ESPN', error=str(error)
            )
            return self.scrape_scoreboard_fallback()

    def parse_header_events(self, events: list) -> list[Market]:
        """
        Normalize ESPN header API event objects into a list of Market objects.

        For each event, up to three Market objects are produced: H2H (moneyline),
        SPREADS, and TOTALS.

        Parameters:
            events (list): List of event objects returned by the ESPN header API.

        Returns:
            list[Market]: A list of Market objects parsed from header API events.
        """
        markets: list[Market] = []

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
                event_id = event.get('id', '')

                # --- Extract raw numeric values ---
                away_team_odds = odds.get('awayTeamOdds', {})
                home_team_odds = odds.get('homeTeamOdds', {})
                away_ml_raw = away_team_odds.get('moneyLine')
                home_ml_raw = home_team_odds.get('moneyLine')

                away_spread_raw: float | None = None
                raw_home_spread = odds.get('spread')
                if raw_home_spread is not None:
                    with contextlib.suppress(ValueError):
                        away_spread_raw = -float(raw_home_spread)

                total_raw: float | None = None
                if odds.get('overUnder') is not None:
                    with contextlib.suppress(ValueError):
                        total_raw = float(odds['overUnder'])

                # --- Build markets ---
                event_markets = self._build_event_markets(
                    event_id=event_id,
                    away_team=away_team,
                    home_team=home_team,
                    away_ml_raw=away_ml_raw,
                    home_ml_raw=home_ml_raw,
                    away_spread_raw=away_spread_raw,
                    total_raw=total_raw,
                )
                markets.extend(event_markets)

            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as error:
                logger.warning('Failed to parse ESPN event: {}', error)
                continue

        return markets

    def scrape_scoreboard_fallback(self) -> list[Market]:
        """
        Fetches and normalizes NBA odds from ESPN's scoreboard API.

        Returns:
            list[Market]: A list of Market objects parsed from the scoreboard
            response. Returns an empty list if no games are found or if the
            fetch/parse fails.
        """
        try:
            response = self._http.get(
                ESPN_SCOREBOARD_API_URL,
                params={'dates': datetime.now().strftime('%Y%m%d'), 'limit': 100},
            )
            markets = self.parse_scoreboard_events(response.json().get('events', []))
        except (httpx.HTTPError, ValueError, AttributeError) as error:
            logger.error('Scoreboard fallback failed', source='ESPN', error=str(error))
            return []

        if markets:
            logger.info(
                'Fallback scrape complete',
                source='ESPN',
                market_count=len(markets),
                action='complete',
            )
            return markets

        logger.warning('Fallback: no upcoming games found', source='ESPN')
        return []

    def parse_scoreboard_events(self, events: list) -> list[Market]:
        """
        Parse ESPN scoreboard API event objects into Market objects.

        Parameters:
            events (list): A list of event objects returned by the ESPN scoreboard API.

        Returns:
            list[Market]: A list of Market objects (H2H, SPREADS, TOTALS) parsed
            from scoreboard events.
        """
        markets: list[Market] = []

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
                event_id = event.get('id', '')

                home_ml_dict = odds.get('moneyline', {}).get('home', {}).get('close', {})
                away_ml_dict = odds.get('moneyline', {}).get('away', {}).get('close', {})
                away_ml_raw = away_ml_dict.get('odds')
                home_ml_raw = home_ml_dict.get('odds')

                away_spread_dict = odds.get('pointSpread', {}).get('away', {}).get('close', {})
                away_spread_raw: float | None = None
                raw_spread_line = away_spread_dict.get('line')
                if raw_spread_line is not None:
                    away_spread_raw = _parse_float_line(raw_spread_line)
                over_total_dict = odds.get('total', {}).get('over', {}).get('close', {})
                total_raw = _parse_float_line(over_total_dict.get('line'))

                event_markets = self._build_event_markets(
                    event_id=event_id,
                    away_team=away_team,
                    home_team=home_team,
                    away_ml_raw=away_ml_raw,
                    home_ml_raw=home_ml_raw,
                    away_spread_raw=away_spread_raw,
                    total_raw=total_raw,
                )
                markets.extend(event_markets)

            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as error:
                logger.warning('Failed to parse ESPN scoreboard event: {}', error)
                continue

        return markets

    def select_scoreboard_odds(self, odds_list: list) -> dict | None:
        for odds in odds_list:
            provider = odds.get('provider', {})
            provider_name = provider.get('displayName') or provider.get('name') or ''
            if 'draft' in provider_name.lower():
                return odds
        return odds_list[0] if odds_list else None

    def _build_event_markets(
        self,
        event_id: str,
        away_team: str,
        home_team: str,
        away_ml_raw: int | float | None,
        home_ml_raw: int | float | None,
        away_spread_raw: float | None,
        total_raw: float | None,
    ) -> list[Market]:
        """Build H2H, SPREADS, and TOTALS markets from raw extracted values.

        Markets with missing required data (e.g. no moneyline values) are
        silently skipped.
        """
        result: list[Market] = []

        # H2H (moneyline)
        if away_ml_raw is not None and home_ml_raw is not None:
            result.append(
                Market(
                    key=f'espn_h2h_{event_id}',
                    name=f'{away_team} vs {home_team} Moneyline',
                    sport='nba',
                    event_id=event_id,
                    market_type=MarketType.H2H,
                    outcomes=[
                        Outcome(
                            name=away_team,
                            price=NormalizedOdds.from_american(float(away_ml_raw)),
                        ),
                        Outcome(
                            name=home_team,
                            price=NormalizedOdds.from_american(float(home_ml_raw)),
                        ),
                    ],
                )
            )

        # Spreads
        if away_spread_raw is not None:
            result.append(
                Market(
                    key=f'espn_spreads_{event_id}',
                    name=f'{away_team} vs {home_team} Spread',
                    sport='nba',
                    event_id=event_id,
                    market_type=MarketType.SPREADS,
                    outcomes=[
                        Outcome(
                            name=away_team,
                            price=NormalizedOdds.from_american(-110),
                            point=away_spread_raw,
                        ),
                        Outcome(
                            name=home_team,
                            price=NormalizedOdds.from_american(-110),
                            point=-away_spread_raw,
                        ),
                    ],
                )
            )

        # Totals
        if total_raw is not None:
            result.append(
                Market(
                    key=f'espn_totals_{event_id}',
                    name=f'{away_team} vs {home_team} Total',
                    sport='nba',
                    event_id=event_id,
                    market_type=MarketType.TOTALS,
                    outcomes=[
                        Outcome(
                            name='Over',
                            price=NormalizedOdds.from_american(-110),
                            point=total_raw,
                        ),
                        Outcome(
                            name='Under',
                            price=NormalizedOdds.from_american(-110),
                            point=total_raw,
                        ),
                    ],
                )
            )

        return result
