from odds_scraping import live_odds_scraper
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

    responses = iter([HeaderResponse(), ScoreboardResponse()])
    monkeypatch.setattr(live_odds_scraper.requests, 'get', lambda *_args, **_kwargs: next(responses))

    [game] = LiveOddsScraper().scrape_espn_nba_odds()

    assert game['matchup'] == 'OKC Thunder @ Boston Celtics'
    assert game['spread'] == '-2.5'
    assert game['moneyline'] == '-135'
    assert game['over_under'] == '223.5'
