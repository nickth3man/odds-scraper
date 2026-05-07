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
    """
    Convert an ESPN line string or numeric value into a float after removing any leading alphabetic characters.

    Parameters:
        value (str | int | float | None): Input value which may include leading letters (e.g., "o220.5", "u210"). If `None`, returns `None`.

    Returns:
        float | None: The parsed float if conversion succeeds, `None` if the input is `None` or cannot be converted to a float.
    """
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
        """
        Initialize the scraper with an HTTP client.

        If `http` is provided it is used as the instance HTTP client; otherwise a new `HttpClient` is created and assigned to `self._http`.

        Parameters:
            http (HttpClient | None): Optional HTTP client to use for network requests. If `None`, a new `HttpClient` is created.
        """
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
        Convert ESPN header API event objects into normalized Market objects.

        Parses each event to extract teams and raw odds, producing up to three Market objects per event: moneyline (H2H), spreads, and totals. Events missing required fields are skipped; parse errors for individual events are caught and logged.

        Parameters:
            events (list): Iterable of ESPN header API event dictionaries.

        Returns:
            list[Market]: A list of normalized Market objects built from the provided events.
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
                away_spread_odds_raw = away_team_odds.get('spreadOdds')
                home_spread_odds_raw = home_team_odds.get('spreadOdds')

                away_spread_raw: float | None = None
                raw_home_spread = odds.get('spread')
                if raw_home_spread is not None:
                    with contextlib.suppress(ValueError):
                        away_spread_raw = -float(raw_home_spread)

                total_raw: float | None = None
                if odds.get('overUnder') is not None:
                    with contextlib.suppress(ValueError):
                        total_raw = float(odds['overUnder'])
                over_odds_raw = odds.get('overOdds')
                under_odds_raw = odds.get('underOdds')

                # --- Build markets ---
                event_markets = self._build_event_markets(
                    event_id=event_id,
                    away_team=away_team,
                    home_team=home_team,
                    away_ml_raw=away_ml_raw,
                    home_ml_raw=home_ml_raw,
                    away_spread_raw=away_spread_raw,
                    away_spread_odds_raw=away_spread_odds_raw,
                    home_spread_odds_raw=home_spread_odds_raw,
                    total_raw=total_raw,
                    over_odds_raw=over_odds_raw,
                    under_odds_raw=under_odds_raw,
                )
                markets.extend(event_markets)

            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as error:
                logger.warning('Failed to parse ESPN event: {}', error)
                continue

        return markets

    def scrape_scoreboard_fallback(self) -> list[Market]:
        """
        Attempt to fetch NBA odds from ESPN's scoreboard API and convert them into Market objects.

        Returns:
            list[Market]: Market objects parsed from the scoreboard response; an empty list if no games are found or if the fetch/parse fails.
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
                home_spread_dict = odds.get('pointSpread', {}).get('home', {}).get('close', {})
                away_spread_raw: float | None = None
                raw_spread_line = away_spread_dict.get('line')
                if raw_spread_line is not None:
                    away_spread_raw = _parse_float_line(raw_spread_line)
                over_total_dict = odds.get('total', {}).get('over', {}).get('close', {})
                under_total_dict = odds.get('total', {}).get('under', {}).get('close', {})
                total_raw = _parse_float_line(over_total_dict.get('line'))

                event_markets = self._build_event_markets(
                    event_id=event_id,
                    away_team=away_team,
                    home_team=home_team,
                    away_ml_raw=away_ml_raw,
                    home_ml_raw=home_ml_raw,
                    away_spread_raw=away_spread_raw,
                    away_spread_odds_raw=away_spread_dict.get('odds'),
                    home_spread_odds_raw=home_spread_dict.get('odds'),
                    total_raw=total_raw,
                    over_odds_raw=over_total_dict.get('odds'),
                    under_odds_raw=under_total_dict.get('odds'),
                )
                markets.extend(event_markets)

            except (KeyError, IndexError, ValueError, AttributeError, TypeError) as error:
                logger.warning('Failed to parse ESPN scoreboard event: {}', error)
                continue

        return markets

    def select_scoreboard_odds(self, odds_list: list) -> dict | None:
        """
        Select the preferred odds entry from a scoreboard odds list, preferring providers whose name contains "draft".

        Parameters:
            odds_list (list): A list of odds dictionaries returned by ESPN scoreboard data, each optionally containing a `provider` mapping with `displayName` or `name`.

        Returns:
            dict | None: The first odds dictionary whose provider `displayName` or `name` contains "draft" (case-insensitive); if none match, the first element of `odds_list` when non-empty; otherwise `None`.
        """
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
        away_spread_odds_raw: int | float | str | None,
        home_spread_odds_raw: int | float | str | None,
        total_raw: float | None,
        over_odds_raw: int | float | str | None,
        under_odds_raw: int | float | str | None,
    ) -> list[Market]:
        """
        Build H2H, SPREADS, and TOTALS Market objects for a single event from extracted raw values.

        Only markets with the required raw inputs are created: H2H requires both away and home moneyline values; SPREADS requires an away spread; TOTALS requires a total line. When created, spread and total outcomes use a default price equivalent to American -110.

        Returns:
            list[Market]: A list of constructed Market objects (zero to three), one per market type that had sufficient input data.
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

        away_spread_odds = _parse_float_line(away_spread_odds_raw)
        home_spread_odds = _parse_float_line(home_spread_odds_raw)
        if (
            away_spread_raw is not None
            and away_spread_odds is not None
            and home_spread_odds is not None
        ):
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
                            price=NormalizedOdds.from_american(away_spread_odds),
                            point=away_spread_raw,
                        ),
                        Outcome(
                            name=home_team,
                            price=NormalizedOdds.from_american(home_spread_odds),
                            point=-away_spread_raw,
                        ),
                    ],
                )
            )

        over_odds = _parse_float_line(over_odds_raw)
        under_odds = _parse_float_line(under_odds_raw)
        if total_raw is not None and over_odds is not None and under_odds is not None:
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
                            price=NormalizedOdds.from_american(over_odds),
                            point=total_raw,
                        ),
                        Outcome(
                            name='Under',
                            price=NormalizedOdds.from_american(under_odds),
                            point=total_raw,
                        ),
                    ],
                )
            )

        return result
