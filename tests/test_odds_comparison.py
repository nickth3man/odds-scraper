"""Unit tests for OddsComparison — cross-sportsbook odds comparison module."""

import pytest

from backend.scrapers import OddsComparison

# ── Test fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def draftkings_odds():
    """DraftKings odds for two games."""
    return [
        {
            'game_id': 1,
            'date': '2026-04-30',
            'team': 'OKC Thunder',
            'opponent': 'Boston Celtics',
            'moneyline': -175,
            'spread': -7.0,
            'over_under': 214.0,
            'sportsbook': 'DraftKings',
        },
        {
            'game_id': 2,
            'date': '2026-04-30',
            'team': 'LA Lakers',
            'opponent': 'GS Warriors',
            'moneyline': -150,
            'spread': -3.5,
            'over_under': 228.5,
            'sportsbook': 'DraftKings',
        },
    ]


@pytest.fixture
def fanduel_odds():
    """FanDuel odds for the same two games with slightly different lines."""
    return [
        {
            'game_id': 1,
            'date': '2026-04-30',
            'team': 'OKC Thunder',
            'opponent': 'Boston Celtics',
            'moneyline': -180,
            'spread': -7.5,
            'over_under': 213.5,
            'sportsbook': 'FanDuel',
        },
        {
            'game_id': 2,
            'date': '2026-04-30',
            'team': 'LA Lakers',
            'opponent': 'GS Warriors',
            'moneyline': -145,
            'spread': -3.0,
            'over_under': 229.0,
            'sportsbook': 'FanDuel',
        },
    ]


@pytest.fixture
def espn_odds():
    """ESPN odds for the same two games."""
    return [
        {
            'game_id': 1,
            'date': '2026-04-30',
            'team': 'OKC Thunder',
            'opponent': 'Boston Celtics',
            'moneyline': -178,
            'spread': -7.0,
            'over_under': 214.5,
            'sportsbook': 'ESPN',
        },
        {
            'game_id': 2,
            'date': '2026-04-30',
            'team': 'LA Lakers',
            'opponent': 'GS Warriors',
            'moneyline': -148,
            'spread': -3.5,
            'over_under': 228.0,
            'sportsbook': 'ESPN',
        },
    ]


# ── add_odds ──────────────────────────────────────────────────────────────────


def test_add_odds_stores_internal_state(draftkings_odds):
    """add_odds stores the odds list keyed by sportsbook name."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)

    assert 'DraftKings' in comparison.odds_by_sportsbook
    assert comparison.odds_by_sportsbook['DraftKings'] == draftkings_odds
    assert len(comparison.odds_by_sportsbook['DraftKings']) == 2


def test_add_odds_multiple_sportsbooks(draftkings_odds, fanduel_odds):
    """Adding multiple sportsbooks stores each under its own key."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)

    assert list(comparison.odds_by_sportsbook.keys()) == ['DraftKings', 'FanDuel']
    assert (
        comparison.odds_by_sportsbook['DraftKings'] is not comparison.odds_by_sportsbook['FanDuel']
    )


# ── find_best_odds — moneyline ────────────────────────────────────────────────


def test_find_best_odds_moneyline(draftkings_odds, fanduel_odds, espn_odds):
    """Higher American odds = better payout. DraftKings has -175 on OKC (highest)."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)
    comparison.add_odds('ESPN', espn_odds)

    results = comparison.find_best_odds('moneyline')

    assert len(results) == 2

    # OKC Thunder: DK -175 > ESPN -178 > FD -180
    okc = next(r for r in results if r['team'] == 'OKC Thunder')
    assert okc['best_sportsbook'] == 'DraftKings'
    assert okc['best_odds'] == -175
    assert okc['bet_type'] == 'moneyline'

    # LA Lakers: FD -145 > ESPN -148 > DK -150
    lakers = next(r for r in results if r['team'] == 'LA Lakers')
    assert lakers['best_sportsbook'] == 'FanDuel'
    assert lakers['best_odds'] == -145


def test_find_best_odds_moneyline_includes_all_book_columns(draftkings_odds, fanduel_odds):
    """Each result row should contain every sportsbook's odds as a column."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)

    results = comparison.find_best_odds('moneyline')

    okc = next(r for r in results if r['team'] == 'OKC Thunder')
    assert okc['DraftKings_odds'] == -175
    assert okc['FanDuel_odds'] == -180


# ── find_best_odds — spread ───────────────────────────────────────────────────


def test_find_best_odds_spread(draftkings_odds, fanduel_odds, espn_odds):
    """Higher spread = more favorable. FD has -3.0 on Lakers (best among books)."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)
    comparison.add_odds('ESPN', espn_odds)

    results = comparison.find_best_odds('spread')

    assert len(results) == 2

    # OKC Thunder: -7.0 (DK/ESPN) > -7.5 (FD)
    okc = next(r for r in results if r['team'] == 'OKC Thunder')
    assert okc['best_sportsbook'] in ('DraftKings', 'ESPN')
    assert okc['best_odds'] == -7.0

    # LA Lakers: -3.0 (FD) > -3.5 (DK/ESPN)
    lakers = next(r for r in results if r['team'] == 'LA Lakers')
    assert lakers['best_sportsbook'] == 'FanDuel'
    assert lakers['best_odds'] == -3.0


# ── find_best_odds — over/under ───────────────────────────────────────────────


def test_find_best_odds_over_under(draftkings_odds, fanduel_odds, espn_odds):
    """Higher total = better. ESPN has 214.5 on OKC; FD has 229.0 on Lakers."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)
    comparison.add_odds('ESPN', espn_odds)

    results = comparison.find_best_odds('over_under')

    # OKC Thunder: ESPN 214.5 > DK 214.0 > FD 213.5
    okc = next(r for r in results if r['team'] == 'OKC Thunder')
    assert okc['best_sportsbook'] == 'ESPN'
    assert okc['best_odds'] == 214.5

    # LA Lakers: FD 229.0 > DK 228.5 > ESPN 228.0
    lakers = next(r for r in results if r['team'] == 'LA Lakers')
    assert lakers['best_sportsbook'] == 'FanDuel'
    assert lakers['best_odds'] == 229.0


# ── Sportsbook with missing games ─────────────────────────────────────────────


def test_sportsbook_missing_games(draftkings_odds, fanduel_odds):
    """Sportsbook missing a game only contributes to games it covers."""
    # FanDuel only has the Lakers game — no OKC
    fd_partial = [g for g in fanduel_odds if g['team'] == 'LA Lakers']

    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fd_partial)

    results = comparison.find_best_odds('moneyline')

    assert len(results) == 2

    # OKC Thunder: only DraftKings has it
    okc = next(r for r in results if r['team'] == 'OKC Thunder')
    assert okc['best_sportsbook'] == 'DraftKings'
    assert okc['best_odds'] == -175
    assert okc.get('FanDuel_odds') is None

    # LA Lakers: both books; FD -145 > DK -150
    lakers = next(r for r in results if r['team'] == 'LA Lakers')
    assert lakers['best_sportsbook'] == 'FanDuel'
    assert lakers['best_odds'] == -145


# ── Empty / edge cases ────────────────────────────────────────────────────────


def test_empty_odds_by_sportsbook_returns_empty_list():
    """Calling find_best_odds with no odds added returns an empty list."""
    comparison = OddsComparison()

    result = comparison.find_best_odds('moneyline')
    assert result == []


def test_add_odds_empty_list(draftkings_odds):
    """Adding an empty odds list stores it but produces no comparison rows."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', [])

    results = comparison.find_best_odds('moneyline')
    assert len(results) == 2  # games come from first-sportsbook base


def test_comparison_results_populated_after_find_best_odds(draftkings_odds, fanduel_odds):
    """comparison_results is populated after calling find_best_odds."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)

    assert comparison.comparison_results == []

    results = comparison.find_best_odds('moneyline')
    assert comparison.comparison_results == results
    assert len(comparison.comparison_results) == 2


# ── CSV export ────────────────────────────────────────────────────────────────


def test_export_to_csv_writes_file(draftkings_odds, fanduel_odds, tmp_path):
    """export_to_csv writes comparison results to the filesystem."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)
    comparison.find_best_odds('moneyline')

    csv_path = tmp_path / 'results.csv'
    comparison.export_to_csv(filename=str(csv_path))

    assert csv_path.exists()
    content = csv_path.read_text()
    assert 'team' in content
    assert 'OKC Thunder' in content
    assert 'best_sportsbook' in content
    assert 'DraftKings_odds' in content


def test_export_to_csv_with_no_results(tmp_path):
    """export_to_csv does not write when comparison_results is empty."""
    comparison = OddsComparison()

    csv_path = tmp_path / 'empty.csv'
    comparison.export_to_csv(filename=str(csv_path))

    assert not csv_path.exists()


def test_display_comparison_returns_none(draftkings_odds, fanduel_odds):
    """display_comparison prints and returns None (no crash)."""
    comparison = OddsComparison()
    comparison.add_odds('DraftKings', draftkings_odds)
    comparison.add_odds('FanDuel', fanduel_odds)

    result = comparison.display_comparison('moneyline')
    assert result is None
