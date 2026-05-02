import json
import re
from pathlib import Path

from odds_scraping.live_odds_scraper import LiveOddsScraper


class FakeElement:
    def __init__(self, text='', attrs=None, parent=None, children=None):
        self.text = text
        self._attrs = attrs or {}
        self._parent = parent
        self._children = children or []

    def get_attribute(self, name):
        return self._attrs.get(name)

    def find_element(self, *_args):
        if self._parent is None:
            raise RuntimeError('no parent')
        return self._parent

    def find_elements(self, *_args):
        return self._children


class FakeDriver:
    def __init__(self, team_elements):
        self._team_elements = team_elements

    def find_elements(self, *_args):
        return self._team_elements


def _load_fixture(filename: str) -> dict:
    fixture_path = Path(__file__).parent.parent / 'fixtures' / filename
    with open(fixture_path) as f:
        return json.load(f)


def test_get_all_games_resets_previous_results(monkeypatch):
    scraper = LiveOddsScraper()
    game = {
        'date': '2026-04-30',
        'home_team': 'Boston Celtics',
        'away_team': 'OKC Thunder',
        'matchup': 'OKC Thunder @ Boston Celtics',
        'spread': '-2.5',
        'moneyline': '-135',
        'over_under': '223.5',
        'source': 'ESPN',
    }

    def scrape_espn(self):
        self.all_games.extend([game])
        return [game]

    monkeypatch.setattr(LiveOddsScraper, 'scrape_espn_nba_odds', scrape_espn)
    monkeypatch.setattr(LiveOddsScraper, 'scrape_draftkings_odds', lambda self: [])
    monkeypatch.setattr(LiveOddsScraper, 'display_games', lambda *_args: None)

    assert scraper.get_all_games() == [game]
    assert scraper.get_all_games() == [game]


def test_parse_draftkings_games_extracts_spread_moneyline_and_total():
    outcome_cells = [
        FakeElement(
            text='OKC Thunder -2.5\n-110',
            attrs={'aria-label': 'OKC Thunder Spread -2.5 -110'},
        ),
        FakeElement(
            text='OKC Thunder\n-135',
            attrs={'aria-label': 'OKC Thunder Moneyline -135'},
        ),
        FakeElement(
            text='Over 223.5\n-110',
            attrs={'aria-label': 'Over 223.5 Total Points -110'},
        ),
    ]
    game_block = FakeElement(children=outcome_cells)
    team_elements = [
        FakeElement(text='OKC Thunder', parent=game_block),
        FakeElement(text='Boston Celtics', parent=game_block),
    ]
    driver = FakeDriver(team_elements)

    [game] = LiveOddsScraper()._parse_draftkings_games(driver)

    assert game['away_team'] == 'OKC Thunder'
    assert game['home_team'] == 'Boston Celtics'
    assert game['spread'] == '-2.5'
    assert game['moneyline'] == '-135'
    assert game['over_under'] == '223.5'


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
            return {
                'events': [
                    {
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
                                            'away': {'close': {'line': -2.5}},
                                        },
                                        'total': {
                                            'over': {'close': {'line': 223.5}},
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

    [game] = scraper.scrape_espn_nba_odds()

    assert game['matchup'] == 'OKC Thunder @ Boston Celtics'
    assert game['spread'] == '-2.5'
    assert game['moneyline'] == '-135'
    assert game['home_moneyline'] == '+120'
    assert game['over_under'] == '223.5'


def test_parse_espn_header_api_fixture():
    scraper = LiveOddsScraper()
    data = _load_fixture('espn_header_api.json')
    events = data['sports'][0]['leagues'][0]['events']

    games = scraper._parse_espn_events(events)

    assert len(games) == 3

    # DET @ ORL -- away (DET) favored by 3.5
    det_orl = games[0]
    assert det_orl['matchup'] == 'Detroit Pistons @ Orlando Magic'
    assert det_orl['spread'] == '-3.5'
    assert det_orl['moneyline'] == '-162'
    assert det_orl['home_moneyline'] == '+136'
    assert det_orl['over_under'] == '210.5'

    # CLE @ TOR -- away (CLE) favored by 4.5
    cle_tor = games[1]
    assert cle_tor['matchup'] == 'Cleveland Cavaliers @ Toronto Raptors'
    assert cle_tor['spread'] == '-4.5'
    assert cle_tor['moneyline'] == '-198'
    assert cle_tor['home_moneyline'] == '+164'
    assert cle_tor['over_under'] == '218.5'

    # LAL @ HOU -- home (HOU) favored by 5.5, so away is +5.5
    lal_hou = games[2]
    assert lal_hou['matchup'] == 'Los Angeles Lakers @ Houston Rockets'
    assert lal_hou['spread'] == '+5.5'
    assert lal_hou['moneyline'] == '+160'
    assert lal_hou['home_moneyline'] == '-192'
    assert lal_hou['over_under'] == '203.5'

    for game in games:
        assert game['source'] == 'ESPN'
        assert game['date']
        assert game['home_team']
        assert game['away_team']


def test_parse_espn_scoreboard_api_fixture():
    scraper = LiveOddsScraper()
    data = _load_fixture('espn_scoreboard_api.json')
    events = data.get('events', [])

    games = scraper._parse_espn_scoreboard_events(events)

    assert len(games) == 1

    game = games[0]
    assert game['matchup'] == 'Philadelphia 76ers @ Boston Celtics'
    assert game['spread'] == '+7.5'
    assert game['over_under'] == '205.5'
    assert game['moneyline'] != 'N/A'
    assert game['home_moneyline'] != 'N/A'
    assert game['source'] == 'ESPN'
    assert game['away_team'] == 'Philadelphia 76ers'
    assert game['home_team'] == 'Boston Celtics'


def test_draftkings_fixture_no_odds_table_fails_gracefully():
    fixture_path = Path(__file__).parent.parent / 'fixtures' / 'dk-game-lines.html'
    with open(fixture_path, encoding='utf-8') as f:
        html = f.read()

    assert len(html) > 10000
    assert 'DraftKings' in html
    assert 'NBA' in html
    # event-cell__name-text (what the Selenium scraper looks for) is NOT present
    assert 'event-cell__name-text' not in html


def test_select_scoreboard_odds_prefers_draftkings():
    scraper = LiveOddsScraper()
    odds_list = [
        {'provider': {'displayName': 'Caesars'}, 'id': '1'},
        {'provider': {'name': 'Draft Kings'}, 'id': '2'},
        {'provider': {'displayName': 'FanDuel'}, 'id': '3'},
    ]
    selected = scraper._select_scoreboard_odds(odds_list)
    assert selected is not None
    assert selected['id'] == '2'


def test_select_scoreboard_odds_falls_back_to_first():
    scraper = LiveOddsScraper()
    odds_list = [
        {'provider': {'displayName': 'Caesars'}, 'id': '1'},
        {'provider': {'displayName': 'FanDuel'}, 'id': '2'},
    ]
    selected = scraper._select_scoreboard_odds(odds_list)
    assert selected is not None
    assert selected['id'] == '1'


# ============ cb-market (component-builder) structure tests ============


class FakeWebElement:
    """Mock Selenium WebElement for testing cb-market structure."""
    def __init__(self, text='', attrs=None, children=None):
        self._text = text
        self._attrs = attrs or {}
        self._children = children or []

    @property
    def text(self):
        return self._text

    def get_attribute(self, name):
        return self._attrs.get(name)

    def find_element(self, *_args):
        # Parse CSS selector args to find matching child
        for arg in _args:
            arg_str = str(arg)
            # Match data-testid attribute selector: [data-testid='...']
            match = re.search(r"data-testid='([^']+)'", arg_str)
            if match:
                child = self._find_child_by_testid(match.group(1))
                if child:
                    return child

        return self._children[0] if self._children else self

    def _find_child_by_testid(self, testid):
        for child in self._children:
            child_attrs = getattr(child, '_attrs', {})
            if child_attrs.get('data-testid') == testid:
                return child
            # Recursively search children
            result = child._find_child_by_testid(testid)
            if result:
                return result
        return None
        return self

    def find_elements(self, *_args):
        return self._children


class FakeSeleniumDriver:
    """Mock Selenium driver with find_elements support."""
    def __init__(self, elements):
        self._elements = elements

    def find_elements(self, *_args):
        return self._elements


def test_parse_draftkings_cb_market_structure():
    """Test parsing DraftKings cb-market template (component-builder layout)."""
    away_spread_btn = FakeWebElement(
        text='+7.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0HC84578437P750_1'}
    )
    away_spread_btn._children = [
        FakeWebElement(text='+7.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeWebElement(text='-102', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    home_spread_btn = FakeWebElement(
        text='-7.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0HC84578437N750_3'}
    )
    home_spread_btn._children = [
        FakeWebElement(text='-7.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeWebElement(text='-118', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    over_btn = FakeWebElement(
        text='O 205.5',
        attrs={'data-testid': 'component-builder-market-button-34077039-0OU84578437O20550_1'}
    )
    over_btn._children = [
        FakeWebElement(text='O', attrs={'data-testid': 'button-title-market-board'}),
        FakeWebElement(text='205.5', attrs={'data-testid': 'button-points-market-board'}),
        FakeWebElement(text='-110', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    away_ml_btn = FakeWebElement(
        text='+215',
        attrs={'data-testid': 'component-builder-market-button-34077039-0ML84578437_1'}
    )
    away_ml_btn._children = [
        FakeWebElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    home_ml_btn = FakeWebElement(
        text='-265',
        attrs={'data-testid': 'component-builder-market-button-34077039-0ML84578437_3'}
    )
    home_ml_btn._children = [
        FakeWebElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    away_team = FakeWebElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team = FakeWebElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )

    game_template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[
            away_team, home_team,
            away_spread_btn, home_spread_btn,
            over_btn,
            away_ml_btn, home_ml_btn,
        ],
    )

    driver = FakeSeleniumDriver([game_template])
    games = LiveOddsScraper()._parse_draftkings_cb_market(driver)

    assert len(games) == 1
    game = games[0]
    assert game['away_team'] == 'PHI 76ers'
    assert game['home_team'] == 'BOS Celtics'
    assert game['matchup'] == 'PHI 76ers @ BOS Celtics'
    assert game['spread'] == '+7.5'
    assert game['moneyline'] == '+215'
    assert game['home_moneyline'] == '-265'
    assert game['over_under'] == '205.5'
    assert game['source'] == 'DraftKings'


def test_parse_draftkings_games_prefers_cb_market():
    """Test _parse_draftkings_games tries cb-market first, then falls back."""
    away_team = FakeWebElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team = FakeWebElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_ml_btn = FakeWebElement(
        text='+215',
        attrs={'data-testid': 'component-builder-market-button-0ML_1'}
    )
    away_ml_btn._children = [
        FakeWebElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    home_ml_btn = FakeWebElement(
        text='-265',
        attrs={'data-testid': 'component-builder-market-button-0ML_3'}
    )
    home_ml_btn._children = [
        FakeWebElement(text='-265', attrs={'data-testid': 'button-odds-market-board'}),
    ]

    game_template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team, home_team, away_ml_btn, home_ml_btn],
    )

    driver = FakeSeleniumDriver([game_template])
    games = LiveOddsScraper()._parse_draftkings_games(driver)

    assert len(games) == 1
    assert games[0]['away_team'] == 'PHI 76ers'
    assert games[0]['home_team'] == 'BOS Celtics'


def test_parse_draftkings_cb_market_skips_incomplete_games():
    """Games with fewer than 2 teams are skipped."""
    away_team = FakeWebElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    game_template = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team],
    )

    driver = FakeSeleniumDriver([game_template])
    games = LiveOddsScraper()._parse_draftkings_cb_market(driver)
    assert len(games) == 0


def test_parse_draftkings_cb_market_multiple_games():
    """Parse multiple games from cb-market templates."""
    away_team1 = FakeWebElement(
        text='PHI 76ers', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team1 = FakeWebElement(
        text='BOS Celtics', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_ml1 = FakeWebElement(
        text='+215',
        attrs={'data-testid': 'component-builder-market-button-game1-0ML_1'}
    )
    away_ml1._children = [
        FakeWebElement(text='+215', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    template1 = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team1, home_team1, away_ml1],
    )

    away_team2 = FakeWebElement(
        text='ORL Magic', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    home_team2 = FakeWebElement(
        text='DET Pistons', attrs={'class': 'cb-market__label-inner--parlay'}
    )
    away_ml2 = FakeWebElement(
        text='+280',
        attrs={'data-testid': 'component-builder-market-button-game2-0ML_1'}
    )
    away_ml2._children = [
        FakeWebElement(text='+280', attrs={'data-testid': 'button-odds-market-board'}),
    ]
    template2 = FakeWebElement(
        attrs={'class': 'cb-market__template--2-columns'},
        children=[away_team2, home_team2, away_ml2],
    )

    driver = FakeSeleniumDriver([template1, template2])
    games = LiveOddsScraper()._parse_draftkings_cb_market(driver)

    assert len(games) == 2
    assert games[0]['matchup'] == 'PHI 76ers @ BOS Celtics'
    assert games[1]['matchup'] == 'ORL Magic @ DET Pistons'
