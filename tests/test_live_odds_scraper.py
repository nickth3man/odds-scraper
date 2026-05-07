import json
from pathlib import Path

from backend.models.domain import Market, MarketType, NormalizedOdds, Outcome
from backend.scrapers import LiveOddsScraper
from backend.scrapers.draftkings import DraftKingsScraper
from backend.scrapers.espn import EspnOddsScraper
from tests.browser_fakes import FakeElement, FakePage


class _JsonResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _load_fixture(filename: str) -> dict:
    """
    Load a JSON fixture file from the repository's test fixtures directory.

    Parameters:
        filename (str): Name of the fixture file (including extension) located in src/backend/fixtures.

    Returns:
        dict: Parsed JSON content of the fixture file.
    """
    fixture_path = Path(__file__).parent.parent / 'src' / 'backend' / 'fixtures' / filename
    with open(fixture_path) as f:
        return json.load(f)


def _make_sample_market() -> Market:
    """
    Create a sample ESPN-style head-to-head Market for use in tests.

    Returns:
        market (Market): A H2H Market for an NBA event with two outcomes:
            - "OKC Thunder" with american odds -135
            - "Boston Celtics" with american odds +120
    """
    return Market(
        key='espn_h2h_1',
        name='OKC Thunder vs Boston Celtics Moneyline',
        sport='nba',
        event_id='1',
        market_type=MarketType.H2H,
        outcomes=[
            Outcome(
                name='OKC Thunder',
                price=NormalizedOdds.from_american(-135),
            ),
            Outcome(
                name='Boston Celtics',
                price=NormalizedOdds.from_american(120),
            ),
        ],
    )


def test_get_all_games_resets_previous_results(monkeypatch):
    scraper = LiveOddsScraper()
    market = _make_sample_market()

    def scrape_espn(self):
        """
        Append a market to the scraper's internal games list and return it as a single-item list.

        Returns:
            list: A list containing the appended market.
        """
        self.games.extend([market])
        return [market]

    def scrape_no_draftkings_games(self):
        """
        Produce an empty list indicating no DraftKings games are available.

        Returns:
            list: An empty list representing no DraftKings games.
        """
        return []

    def suppress_display(self, *_args):
        return None

    monkeypatch.setattr(LiveOddsScraper, 'scrape_espn_nba_odds', scrape_espn)
    monkeypatch.setattr(LiveOddsScraper, 'scrape_draftkings_odds', scrape_no_draftkings_games)
    monkeypatch.setattr(LiveOddsScraper, 'display_games', suppress_display)

    assert scraper.get_all_games() == [market]
    assert scraper.get_all_games() == [market]


def test_scrape_draftkings_odds_appends_games(monkeypatch):
    scraper = LiveOddsScraper()
    games = [{'matchup': 'OKC Thunder @ Boston Celtics'}]

    def return_games():
        return games

    monkeypatch.setattr(scraper._draftkings, 'scrape_odds', return_games)

    assert scraper.scrape_draftkings_odds() == games
    assert scraper.games == games


def test_scrape_draftkings_odds_skips_empty_results(monkeypatch):
    scraper = LiveOddsScraper()

    def return_no_games():
        return []

    monkeypatch.setattr(scraper._draftkings, 'scrape_odds', return_no_games)

    assert scraper.scrape_draftkings_odds() == []
    assert scraper.games == []


def test_parse_draftkings_html_delegates_to_scraper(monkeypatch):
    def parse_html_stub(html_content: str):
        return [{'html': html_content}]

    monkeypatch.setattr(DraftKingsScraper, 'parse_html', parse_html_stub)

    assert LiveOddsScraper.parse_draftkings_html('<html></html>') == [{'html': '<html></html>'}]


def test_export_to_csv_returns_none_when_no_games(capsys, loguru_to_stderr):
    scraper = LiveOddsScraper()

    assert scraper.export_to_csv([]) is None
    assert 'No games to export' in capsys.readouterr().err


def test_export_to_csv_writes_dataframe(tmp_path, capsys, loguru_to_stderr):
    scraper = LiveOddsScraper()
    games = [{'matchup': 'OKC Thunder @ Boston Celtics', 'moneyline': '-135'}]
    output = tmp_path / 'live-odds.csv'

    frame = scraper.export_to_csv(games, filename=str(output))

    assert frame is not None
    assert output.exists()
    printed = capsys.readouterr().err
    assert 'Exported live odds' in printed


def test_display_games_formats_table(capsys, loguru_to_stderr):
    scraper = LiveOddsScraper()
    games = [{'matchup': 'OKC Thunder @ Boston Celtics', 'moneyline': '-135'}]

    scraper.display_games(games, source='ESPN')

    output = capsys.readouterr().err
    assert 'Displaying games' in output
    assert 'OKC Thunder @ Boston Celtics' in output


def test_display_games_skips_empty_input(capsys):
    scraper = LiveOddsScraper()

    scraper.display_games([], source='ESPN')

    assert capsys.readouterr().out == ''


def test_parse_draftkings_games_extracts_spread_moneyline_and_total():
    outcome_cells = [
        FakeElement(
            text='OKC Thunder -2.5\n-110',
            attrs={
                'aria-label': 'OKC Thunder Spread -2.5 -110',
                'class': 'sportsbook-outcome-cell__body',
            },
        ),
        FakeElement(
            text='Boston Celtics +2.5\n-110',
            attrs={
                'aria-label': 'Boston Celtics Spread +2.5 -110',
                'class': 'sportsbook-outcome-cell__body',
            },
        ),
        FakeElement(
            text='OKC Thunder\n-135',
            attrs={
                'aria-label': 'OKC Thunder Moneyline -135',
                'class': 'sportsbook-outcome-cell__body',
            },
        ),
        FakeElement(
            text='Boston Celtics\n+115',
            attrs={
                'aria-label': 'Boston Celtics Moneyline +115',
                'class': 'sportsbook-outcome-cell__body',
            },
        ),
        FakeElement(
            text='Over 223.5\n-110',
            attrs={
                'aria-label': 'Over 223.5 Total Points -110',
                'class': 'sportsbook-outcome-cell__body',
            },
        ),
        FakeElement(
            text='Under 223.5\n-110',
            attrs={
                'aria-label': 'Under 223.5 Total Points -110',
                'class': 'sportsbook-outcome-cell__body',
            },
        ),
    ]
    game_block = FakeElement(children=outcome_cells)
    team_elements = [
        FakeElement(
            text='OKC Thunder', attrs={'class': 'event-cell__name-text'}, parent=game_block
        ),
        FakeElement(
            text='Boston Celtics', attrs={'class': 'event-cell__name-text'}, parent=game_block
        ),
    ]
    page = FakePage(elements=team_elements)

    markets = DraftKingsScraper().parse_games(page)

    # Should produce H2H, SPREADS, and TOTALS markets
    h2h = next((m for m in markets if m.market_type == MarketType.H2H), None)
    spreads = next((m for m in markets if m.market_type == MarketType.SPREADS), None)
    totals = next((m for m in markets if m.market_type == MarketType.TOTALS), None)

    assert h2h is not None
    assert spreads is not None
    assert totals is not None

    # H2H: away moneyline -135
    assert h2h.outcomes[0].name == 'OKC Thunder'
    assert h2h.outcomes[0].price.american == -135.0

    # SPREADS: away spread -2.5
    assert spreads.outcomes[0].name == 'OKC Thunder'
    assert spreads.outcomes[0].point == -2.5

    # TOTALS: over/under 223.5
    assert totals.outcomes[0].name == 'Over'
    assert totals.outcomes[0].point == 223.5


def test_scrape_espn_uses_scoreboard_fallback_when_header_api_returns_non_json(monkeypatch):
    class HeaderResponse:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError('not json')

    class ScoreboardResponse:
        def raise_for_status(self):
            return None

        def json(self):
            """
            Mock ESPN-style JSON payload representing a single event with odds.

            The returned dictionary mimics an ESPN scoreboard/header response containing one event:
            - events: list of event objects
              - id (str): event identifier ('401869412')
              - date (str): ISO-8601 timestamp ('2026-04-30T23:00Z')
              - competitions: list with a single competition containing:
                - competitors: two competitors with 'homeAway' set to 'away' and 'home' and nested team.displayName values ('OKC Thunder', 'Boston Celtics')
                - odds: list containing one provider entry (provider.displayName == 'Draft Kings') with:
                  - moneyline: numeric american-style odds under away.close.odds (-135) and home.close.odds (120)
                  - pointSpread: away.close.line present (-2.5)
                  - total: over.close.line present (223.5)

            Returns:
                dict: A synthetic ESPN-style payload matching the structure described above.
            """
            return {
                'events': [
                    {
                        'id': '401869412',
                        'date': '2026-04-30T23:00Z',
                        'competitions': [
                            {
                                'competitors': [
                                    {
                                        'homeAway': 'away',
                                        'team': {'displayName': 'OKC Thunder'},
                                    },
                                    {
                                        'homeAway': 'home',
                                        'team': {'displayName': 'Boston Celtics'},
                                    },
                                ],
                                'odds': [
                                    {
                                        'provider': {'displayName': 'Draft Kings'},
                                        'moneyline': {
                                            'away': {'close': {'odds': -135}},
                                            'home': {'close': {'odds': 120}},
                                        },
                                        'pointSpread': {
                                            'away': {'close': {'line': -2.5, 'odds': -110}},
                                            'home': {'close': {'line': 2.5, 'odds': -110}},
                                        },
                                        'total': {
                                            'over': {'close': {'line': 223.5, 'odds': -110}},
                                            'under': {'close': {'line': 223.5, 'odds': -110}},
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }

    scraper = LiveOddsScraper()
    responses = iter([HeaderResponse(), ScoreboardResponse()])
    monkeypatch.setattr(scraper._http, 'get', lambda *_args, **_kwargs: next(responses))

    markets = scraper.scrape_espn_nba_odds()

    # Should produce 3 markets: h2h, spreads, totals
    assert len(markets) == 3

    h2h = next(m for m in markets if m.market_type == MarketType.H2H)
    assert h2h.outcomes[0].name == 'OKC Thunder'
    assert h2h.outcomes[0].price.american == -135
    assert h2h.outcomes[1].name == 'Boston Celtics'
    assert h2h.outcomes[1].price.american == 120

    spreads = next(m for m in markets if m.market_type == MarketType.SPREADS)
    assert spreads.outcomes[0].point == -2.5

    totals = next(m for m in markets if m.market_type == MarketType.TOTALS)
    assert totals.outcomes[0].point == 223.5


def test_parse_espn_header_api_fixture():
    scraper = EspnOddsScraper()
    data = _load_fixture('espn_header_api.json')
    events = data['sports'][0]['leagues'][0]['events']

    markets = scraper.parse_header_events(events)

    # 3 events x 3 market types = 9 markets
    assert len(markets) == 9

    # Helper to find markets by event_id
    def find(event_id: str, mtype: MarketType) -> Market:
        """
        Finds the Market with the given event identifier and market type.

        Parameters:
            event_id (str): Identifier of the event to match.
            mtype (MarketType): Type of market to match.

        Returns:
            Market: The first Market whose `event_id` equals `event_id` and whose `market_type` equals `mtype`.

        Raises:
            StopIteration: If no matching Market is found.
        """
        return next(m for m in markets if m.event_id == event_id and m.market_type == mtype)

    # DET @ ORL -- away (DET) favored by 3.5
    det_orl_h2h = find('401869417', MarketType.H2H)
    assert det_orl_h2h.outcomes[0].name == 'Detroit Pistons'
    assert det_orl_h2h.outcomes[0].price.american == -162
    assert det_orl_h2h.outcomes[1].name == 'Orlando Magic'
    assert det_orl_h2h.outcomes[1].price.american == 136

    det_orl_spread = find('401869417', MarketType.SPREADS)
    assert det_orl_spread.outcomes[0].point == -3.5  # away spread
    assert det_orl_spread.outcomes[1].point == 3.5  # home spread

    det_orl_totals = find('401869417', MarketType.TOTALS)
    assert det_orl_totals.outcomes[0].point == 210.5

    # CLE @ TOR -- away (CLE) favored by 4.5
    cle_tor_h2h = find('401869381', MarketType.H2H)
    assert cle_tor_h2h.outcomes[0].name == 'Cleveland Cavaliers'
    assert cle_tor_h2h.outcomes[0].price.american == -198
    assert cle_tor_h2h.outcomes[1].name == 'Toronto Raptors'
    assert cle_tor_h2h.outcomes[1].price.american == 164

    cle_tor_spread = find('401869381', MarketType.SPREADS)
    assert cle_tor_spread.outcomes[0].point == -4.5

    cle_tor_totals = find('401869381', MarketType.TOTALS)
    assert cle_tor_totals.outcomes[0].point == 218.5

    # LAL @ HOU -- home (HOU) favored by 5.5, so away is +5.5
    lal_hou_h2h = find('401869409', MarketType.H2H)
    assert lal_hou_h2h.outcomes[0].name == 'Los Angeles Lakers'
    assert lal_hou_h2h.outcomes[0].price.american == 160
    assert lal_hou_h2h.outcomes[1].name == 'Houston Rockets'
    assert lal_hou_h2h.outcomes[1].price.american == -192

    lal_hou_spread = find('401869409', MarketType.SPREADS)
    assert lal_hou_spread.outcomes[0].point == 5.5  # away +5.5

    lal_hou_totals = find('401869409', MarketType.TOTALS)
    assert lal_hou_totals.outcomes[0].point == 203.5

    # All markets share common attributes
    for market in markets:
        assert market.sport == 'nba'
        assert market.event_id


def test_parse_espn_scoreboard_api_fixture():
    scraper = EspnOddsScraper()
    data = _load_fixture('espn_scoreboard_api.json')
    events = data.get('events', [])

    markets = scraper.parse_scoreboard_events(events)

    # 1 event x 3 market types = 3 markets
    assert len(markets) == 3

    def find(mtype: MarketType) -> Market:
        """
        Select the first market from the surrounding `markets` collection matching the given market type.

        Parameters:
            mtype (MarketType): The market type to find.

        Returns:
            Market: The first Market whose `market_type` equals `mtype`.

        Raises:
            StopIteration: If no matching market is found.
        """
        return next(m for m in markets if m.market_type == mtype)

    h2h = find(MarketType.H2H)
    assert h2h.outcomes[0].name == 'Philadelphia 76ers'
    assert h2h.outcomes[1].name == 'Boston Celtics'
    assert h2h.outcomes[0].price.american == 215
    assert h2h.outcomes[1].price.american == -265

    spreads = find(MarketType.SPREADS)
    assert spreads.outcomes[0].point == 7.5  # away spread +7.5
    assert spreads.outcomes[1].point == -7.5

    totals = find(MarketType.TOTALS)
    assert totals.outcomes[0].point == 205.5


def test_draftkings_fixture_no_odds_table_fails_gracefully():
    fixture_path = (
        Path(__file__).parent.parent / 'src' / 'backend' / 'fixtures' / 'dk-game-lines.html'
    )
    with open(fixture_path, encoding='utf-8') as f:
        html = f.read()

    assert len(html) > 10000
    assert 'DraftKings' in html
    assert 'NBA' in html
    # event-cell__name-text (what the Playwright scraper looks for) is NOT present
    assert 'event-cell__name-text' not in html


def test_select_scoreboard_odds_prefers_draftkings():
    scraper = EspnOddsScraper()
    odds_list = [
        {'provider': {'displayName': 'Caesars'}, 'id': '1'},
        {'provider': {'name': 'Draft Kings'}, 'id': '2'},
        {'provider': {'displayName': 'FanDuel'}, 'id': '3'},
    ]
    selected = scraper.select_scoreboard_odds(odds_list)
    assert selected is not None
    assert selected['id'] == '2'


def test_select_scoreboard_odds_falls_back_to_first():
    scraper = EspnOddsScraper()
    odds_list = [
        {'provider': {'displayName': 'Caesars'}, 'id': '1'},
        {'provider': {'displayName': 'FanDuel'}, 'id': '2'},
    ]
    selected = scraper.select_scoreboard_odds(odds_list)
    assert selected is not None
    assert selected['id'] == '1'


def test_scrape_espn_nba_odds_returns_empty_when_header_api_has_no_games(
    monkeypatch, capsys, loguru_to_stderr
):
    scraper = EspnOddsScraper()

    def return_empty_sports(*_args, **_kwargs):
        """
        Produce a fake HTTP JSON response for tests with an empty 'sports' list.

        Returns:
            _JsonResponse: Response whose JSON payload is {'sports': []}.
        """
        return _JsonResponse({'sports': []})

    monkeypatch.setattr(
        scraper._http,
        'get',
        return_empty_sports,
    )

    assert scraper.scrape_nba_odds() == []
    assert 'No upcoming games found' in capsys.readouterr().err


def test_parse_header_events_skips_invalid_entries_and_logs_warning(capsys, loguru_to_stderr):
    scraper = EspnOddsScraper()
    events = [
        {'competitors': []},
        {
            'odds': {'spread': -2.5},
            'competitors': [{'homeAway': 'home', 'displayName': 'Boston Celtics'}],
        },
        {
            'odds': {'spread': -2.5},
            'competitors': [
                {'homeAway': 'neutral', 'displayName': 'Boston Celtics'},
                {'homeAway': 'away', 'displayName': 'OKC Thunder'},
            ],
        },
        {
            'odds': 'bad',
            'competitors': [
                {'homeAway': 'home', 'displayName': 'Boston Celtics'},
                {'homeAway': 'away', 'displayName': 'OKC Thunder'},
            ],
        },
    ]

    assert scraper.parse_header_events(events) == []

    assert 'Failed to parse ESPN event' in capsys.readouterr().err


def test_scrape_scoreboard_fallback_returns_empty_on_fetch_error(
    monkeypatch, capsys, loguru_to_stderr
):
    scraper = EspnOddsScraper()

    def raise_bad_payload(*_args, **_kwargs):
        """
        Always raises a ValueError indicating a bad payload.

        Raises:
            ValueError: with message 'bad payload'.
        """
        raise ValueError('bad payload')

    monkeypatch.setattr(
        scraper._http,
        'get',
        raise_bad_payload,
    )

    assert scraper.scrape_scoreboard_fallback() == []
    assert 'Scoreboard fallback failed' in capsys.readouterr().err


def test_scrape_scoreboard_fallback_returns_empty_when_no_games(
    monkeypatch, capsys, loguru_to_stderr
):
    scraper = EspnOddsScraper()

    def return_empty_events(*_args, **_kwargs):
        """
        Create a fake JSON HTTP response representing no events.

        This test helper ignores any positional or keyword arguments and returns an _JsonResponse
        whose JSON payload is {'events': []}.
        """
        return _JsonResponse({'events': []})

    monkeypatch.setattr(
        scraper._http,
        'get',
        return_empty_events,
    )

    assert scraper.scrape_scoreboard_fallback() == []
    assert 'Fallback: no upcoming games found' in capsys.readouterr().err


def test_parse_scoreboard_events_skips_invalid_entries_and_logs_warning(capsys, loguru_to_stderr):
    scraper = EspnOddsScraper()
    events = [
        {
            'competitions': [
                {
                    'competitors': [{'homeAway': 'away', 'team': {'displayName': 'OKC Thunder'}}],
                    'odds': [{}],
                }
            ]
        },
        {
            'competitions': [
                {
                    'competitors': [
                        {'homeAway': 'away', 'team': {'displayName': 'OKC Thunder'}},
                        {'homeAway': 'home', 'team': {'displayName': 'Boston Celtics'}},
                    ],
                    'odds': [],
                }
            ]
        },
        {
            'competitions': [
                {
                    'competitors': [
                        {'homeAway': 'away', 'team': {'displayName': 'OKC Thunder'}},
                        {'homeAway': 'home', 'team': {'displayName': 'Boston Celtics'}},
                    ],
                    'odds': [{'moneyline': 'bad'}],
                }
            ]
        },
    ]

    assert scraper.parse_scoreboard_events(events) == []

    assert 'Failed to parse ESPN scoreboard event' in capsys.readouterr().err


# ============ cb-market (component-builder) structure tests ============


def test_parse_draftkings_cb_market_structure():
    """Test parsing DraftKings cb-market template (component-builder layout)."""
    away_spread_button = FakeElement(
        text='+7.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0HC84578437P750_1'},
    )
    away_spread_button._children = [
        FakeElement(text='+7.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeElement(text='-102', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    home_spread_button = FakeElement(
        text='-7.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0HC84578437N750_3'},
    )
    home_spread_button._children = [
        FakeElement(text='-7.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeElement(text='-118', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    over_button = FakeElement(
        text='O 205.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0OU84578437O20550_1'},
    )
    over_button._children = [
        FakeElement(text='O', attrs={'data-testid': 'button-title-market-board'}),
        FakeElement(text='205.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeElement(text='-110', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    under_button = FakeElement(
        text='U 205.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0OU84578437U20550_2'},
    )
    under_button._children = [
        FakeElement(text='U', attrs={'data-testid': 'button-title-market-board'}),
        FakeElement(text='205.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeElement(text='-110', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    away_moneyline_button = FakeElement(
        text='+215', attrs={'data-testid': 'component-builder-market-button-34077039-0ML84578437_1'}
    )
    away_moneyline_button._children = [
        FakeElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    home_moneyline_button = FakeElement(
        text='-265', attrs={'data-testid': 'component-builder-market-button-34077039-0ML84578437_3'}
    )
    home_moneyline_button._children = [
        FakeElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    away_team_element = FakeElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team_element = FakeElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )

    game_template = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[
            away_team_element,
            home_team_element,
            away_spread_button,
            home_spread_button,
            over_button,
            under_button,
            away_moneyline_button,
            home_moneyline_button,
        ],
    )

    page = FakePage(elements=[game_template])
    markets = DraftKingsScraper().parse_cb_market(page)

    # Should produce 3 markets: H2H, SPREADS, TOTALS
    assert len(markets) == 3

    h2h = next(m for m in markets if m.market_type == MarketType.H2H)
    spreads = next(m for m in markets if m.market_type == MarketType.SPREADS)
    totals = next(m for m in markets if m.market_type == MarketType.TOTALS)

    # H2H: PHI 76ers +215, BOS Celtics -265
    assert h2h.outcomes[0].name == 'PHI 76ers'
    assert h2h.outcomes[0].price.american == 215.0
    assert h2h.outcomes[1].name == 'BOS Celtics'
    assert h2h.outcomes[1].price.american == -265.0

    # SPREADS: away +7.5
    assert spreads.outcomes[0].name == 'PHI 76ers'
    assert spreads.outcomes[0].point == 7.5

    # TOTALS: 205.5
    assert totals.outcomes[0].name == 'Over'
    assert totals.outcomes[0].point == 205.5


def test_parse_draftkings_games_prefers_cb_market():
    """Test parse_games tries cb-market first, then falls back."""
    away_team_element = FakeElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team_element = FakeElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_moneyline_button = FakeElement(
        text='+215', attrs={'data-testid': 'component-builder-market-button-0ML_1'}
    )
    away_moneyline_button._children = [
        FakeElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    home_moneyline_button = FakeElement(
        text='-265', attrs={'data-testid': 'component-builder-market-button-0ML_3'}
    )
    home_moneyline_button._children = [
        FakeElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    game_template = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[
            away_team_element,
            home_team_element,
            away_moneyline_button,
            home_moneyline_button,
        ],
    )

    page = FakePage(elements=[game_template])
    markets = DraftKingsScraper().parse_games(page)

    # Only moneyline buttons provided — should produce H2H market only
    assert len(markets) >= 1
    h2h = next(m for m in markets if m.market_type == MarketType.H2H)
    assert h2h.outcomes[0].name == 'PHI 76ers'
    assert h2h.outcomes[1].name == 'BOS Celtics'


def test_parse_draftkings_cb_market_skips_incomplete_games():
    """Games with fewer than 2 teams are skipped."""
    away_team_element = FakeElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    game_template = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team_element],
    )

    page = FakePage(elements=[game_template])
    games = DraftKingsScraper().parse_cb_market(page)
    assert len(games) == 0


def test_parse_draftkings_cb_market_multiple_games():
    """Parse multiple games from cb-market templates."""
    away_team_element_1 = FakeElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team_element_1 = FakeElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_moneyline_button_1 = FakeElement(
        text='+215', attrs={'data-testid': 'component-builder-market-button-game1-0ML_1'}
    )
    away_moneyline_button_1._children = [
        FakeElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    home_moneyline_button_1 = FakeElement(
        text='-265', attrs={'data-testid': 'component-builder-market-button-game1-0ML_3'}
    )
    home_moneyline_button_1._children = [
        FakeElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    template1 = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[
            away_team_element_1,
            home_team_element_1,
            away_moneyline_button_1,
            home_moneyline_button_1,
        ],
    )

    away_team_element_2 = FakeElement(
        text='ORL Magic', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team_element_2 = FakeElement(
        text='DET Pistons', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_moneyline_button_2 = FakeElement(
        text='+280', attrs={'data-testid': 'component-builder-market-button-game2-0ML_1'}
    )
    away_moneyline_button_2._children = [
        FakeElement(text='+280', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    home_moneyline_button_2 = FakeElement(
        text='-350', attrs={'data-testid': 'component-builder-market-button-game2-0ML_3'}
    )
    home_moneyline_button_2._children = [
        FakeElement(text='-350', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    template2 = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[
            away_team_element_2,
            home_team_element_2,
            away_moneyline_button_2,
            home_moneyline_button_2,
        ],
    )

    page = FakePage(elements=[template1, template2])
    markets = DraftKingsScraper().parse_cb_market(page)

    # Each game produces 1 H2H market (moneyline for both sides, no spread/total)
    assert len(markets) == 2
    # Check teams via H2H outcomes
    game1_h2h = markets[0]
    assert game1_h2h.market_type == MarketType.H2H
    assert game1_h2h.outcomes[0].name == 'PHI 76ers'
    game2_h2h = markets[1]
    assert game2_h2h.market_type == MarketType.H2H
    assert game2_h2h.outcomes[0].name == 'ORL Magic'


# ============ futures champion tests ============


def test_parse_futures_champion_extracts_team_and_odds():
    """Parse DraftKings futures champion market structure."""
    # Each button has: button-title-market-board (team) + button-odds-market-board (odds)
    team_element_1 = FakeElement(
        text='OKC Thunder', attrs={'data-testid': 'button-title-market-board'}
    )
    odds_element_1 = FakeElement(text='-130', attrs={'data-testid': 'button-odds-market-board'})
    button_1 = FakeElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team_element_1, odds_element_1],
    )

    team_element_2 = FakeElement(
        text='BOS Celtics', attrs={'data-testid': 'button-title-market-board'}
    )
    odds_element_2 = FakeElement(text='+650', attrs={'data-testid': 'button-odds-market-board'})
    button_2 = FakeElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team_element_2, odds_element_2],
    )

    team_element_3 = FakeElement(
        text='NY Knicks', attrs={'data-testid': 'button-title-market-board'}
    )
    odds_element_3 = FakeElement(
        text='  +1800  ', attrs={'data-testid': 'button-odds-market-board'}
    )
    button_3 = FakeElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team_element_3, odds_element_3],
    )

    template = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[button_1, button_2, button_3],
    )

    page = FakePage(elements=[template])
    results = DraftKingsScraper().parse_futures_champion(page)

    assert len(results) == 3
    assert results[0] == {
        'team': 'OKC Thunder',
        'odds': '-130',
        'bet_type': 'champion',
        'source': 'DraftKings',
    }
    assert results[1]['team'] == 'BOS Celtics'
    assert results[1]['odds'] == '+650'
    assert results[2]['team'] == 'NY Knicks'
    assert results[2]['odds'] == '+1800'


def test_parse_futures_champion_empty_when_no_button_elements():
    """Return empty list when no champion market buttons exist."""
    page = FakePage(elements=[])
    results = DraftKingsScraper().parse_futures_champion(page)
    assert results == []


def test_parse_futures_category_extracts_accordion_team_rows():
    """Parse the sportsbook-accordion hierarchy used by DraftKings futures pages."""
    team_element_1 = FakeElement(
        text='OKC Thunder',
        attrs={'tag': 'a'},
    )
    odds_element_1 = FakeElement(
        text='OKC Thunder -130',
        attrs={'tag': 'button'},
    )
    row1 = FakeElement(
        attrs={'class': 'content-sports-hierarchy-teams__team'},
        children=[team_element_1, odds_element_1],
    )
    team_element_2 = FakeElement(
        text='BOS Celtics',
        attrs={'tag': 'a'},
    )
    odds_element_2 = FakeElement(
        text='BOS Celtics +650',
        attrs={'tag': 'button'},
    )
    row2 = FakeElement(
        attrs={'class': 'content-sports-hierarchy-teams__team'},
        children=[team_element_2, odds_element_2],
    )
    wrapper = FakeElement(
        attrs={'class': 'sportsbook-accordion__wrapper'},
        children=[row1, row2],
    )

    results = DraftKingsScraper().parse_futures_category(FakePage(elements=[wrapper]), 'champion')

    assert results == [
        {
            'team': 'OKC Thunder',
            'odds': '-130',
            'bet_type': 'champion',
            'source': 'DraftKings',
        },
        {
            'team': 'BOS Celtics',
            'odds': '+650',
            'bet_type': 'champion',
            'source': 'DraftKings',
        },
    ]


def test_parse_futures_category_passes_bet_type():
    """Verify bet_type parameter is set in each output dict."""
    team_element = FakeElement(
        text='LAL Lakers', attrs={'data-testid': 'button-title-market-board'}
    )
    odds_element = FakeElement(text='+1200', attrs={'data-testid': 'button-odds-market-board'})
    button = FakeElement(
        attrs={'class': 'cb-market__button cb-market__button--regular'},
        children=[team_element, odds_element],
    )
    template = FakeElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[button],
    )
    page = FakePage(elements=[template])
    results = DraftKingsScraper().parse_futures_category(page, 'playoffs')

    assert len(results) == 1
    assert results[0]['bet_type'] == 'playoffs'
    assert results[0]['team'] == 'LAL Lakers'
    assert results[0]['odds'] == '+1200'
    assert results[0]['source'] == 'DraftKings'
