from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.data.nba_dataset import (
    BacktestResult,
    EloMoneylineModel,
    HistoricalMoneylineModel,
    NbaDatasetLoader,
    build_moneyline_training_frame,
    calculate_brier_score,
    calculate_log_loss,
    devig_decimal_moneyline,
    evaluate_market_baseline,
    evaluate_temporal_split,
    run_moneyline_backtest,
)


def create_fixture_database(path: Path) -> None:
    """
    Create a SQLite fixture database at the given path with pre-populated tables and sample data.

    The function creates a SQLite database file at `path` and populates it with three tables and deterministic fixture rows useful for tests:
    - games_index: game-level metadata (game_id, game_date, season_year, home, away, winner, pts_home, pts_away, margin, odds_home, odds_away).
    - game_odds: odds snapshots per game (including decimal and moneyline fields, snapshot marker such as 'open'/'close', and source_url).
    - team_boxscores: team-level boxscore and team-strength metrics per game (including off/def/net ratings and other boxscore stats).

    Inserts three fixture games (g1–g3), multiple odds snapshots (open and close) for each game, and two team boxscore rows per game (home and away for teams 'AAA' and 'BBB'). The database is committed before the connection is closed.

    Parameters:
        path (Path): Filesystem path where the SQLite database file will be created or overwritten.
    """
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE games_index (
                game_id TEXT,
                game_date TEXT,
                season_year INTEGER,
                home TEXT,
                away TEXT,
                winner TEXT,
                pts_home INTEGER,
                pts_away INTEGER,
                margin INTEGER,
                odds_home REAL,
                odds_away REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE game_odds (
                game_id TEXT,
                game_date TEXT,
                odds_date TEXT,
                last_fetched TEXT,
                decimal_home REAL,
                decimal_away REAL,
                moneyline_home INTEGER,
                moneyline_away INTEGER,
                source_url TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE team_boxscores (
                season_year INTEGER,
                team_abbreviation TEXT,
                game_id TEXT,
                game_date TEXT,
                is_home INTEGER,
                wl INTEGER,
                pts INTEGER,
                plus_minus INTEGER,
                off_rating REAL,
                def_rating REAL,
                net_rating REAL,
                efg_pct REAL,
                tm_tov_pct REAL,
                pace REAL
            )
            """
        )

        games = [
            ('g1', '2024-01-01T00:00:00', 2024, 'AAA', 'BBB', 'AAA', 110, 100, 10, 1.80, 2.10),
            ('g2', '2024-01-02T00:00:00', 2024, 'BBB', 'AAA', 'AAA', 99, 105, -6, 2.20, 1.70),
            ('g3', '2024-01-03T00:00:00', 2024, 'AAA', 'BBB', 'AAA', 112, 90, 22, 1.60, 2.50),
        ]
        conn.executemany('INSERT INTO games_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', games)

        odds_rows = [
            ('g1', '2024-01-01T00:00:00', 'open', '2024-01-01', 1.80, 2.10, -125, 110, 'fixture'),
            ('g1', '2024-01-01T00:00:00', 'close', '2024-01-01', 1.70, 2.20, -143, 120, 'fixture'),
            ('g2', '2024-01-02T00:00:00', 'open', '2024-01-02', 2.20, 1.70, 120, -143, 'fixture'),
            ('g2', '2024-01-02T00:00:00', 'close', '2024-01-02', 2.40, 1.60, 140, -167, 'fixture'),
            ('g3', '2024-01-03T00:00:00', 'open', '2024-01-03', 1.60, 2.50, -167, 150, 'fixture'),
            ('g3', '2024-01-03T00:00:00', 'close', '2024-01-03', 1.50, 2.70, -200, 170, 'fixture'),
        ]
        conn.executemany('INSERT INTO game_odds VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', odds_rows)

        team_rows = [
            (
                2024,
                'AAA',
                'g1',
                '2024-01-01T00:00:00',
                1,
                1,
                110,
                10,
                112.0,
                102.0,
                10.0,
                0.55,
                0.11,
                98.0,
            ),
            (
                2024,
                'BBB',
                'g1',
                '2024-01-01T00:00:00',
                0,
                0,
                100,
                -10,
                102.0,
                112.0,
                -10.0,
                0.50,
                0.14,
                98.0,
            ),
            (
                2024,
                'BBB',
                'g2',
                '2024-01-02T00:00:00',
                1,
                0,
                99,
                -6,
                99.0,
                105.0,
                -6.0,
                0.49,
                0.16,
                97.0,
            ),
            (
                2024,
                'AAA',
                'g2',
                '2024-01-02T00:00:00',
                0,
                1,
                105,
                6,
                105.0,
                99.0,
                6.0,
                0.54,
                0.10,
                97.0,
            ),
            (
                2024,
                'AAA',
                'g3',
                '2024-01-03T00:00:00',
                1,
                1,
                112,
                22,
                120.0,
                98.0,
                22.0,
                0.60,
                0.09,
                101.0,
            ),
            (
                2024,
                'BBB',
                'g3',
                '2024-01-03T00:00:00',
                0,
                0,
                90,
                -22,
                98.0,
                120.0,
                -22.0,
                0.45,
                0.18,
                101.0,
            ),
        ]
        conn.executemany(
            'INSERT INTO team_boxscores VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            team_rows,
        )
        conn.commit()
    finally:
        conn.close()


def test_loader_reads_moneyline_games_and_team_boxscores(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)

    loader = NbaDatasetLoader(database_path)

    games = loader.load_moneyline_games()
    boxscores = loader.load_team_boxscores()

    assert list(games['game_id']) == ['g1', 'g2', 'g3']
    assert list(boxscores['team_abbreviation'])[:2] == ['AAA', 'BBB']


def test_loader_reads_closing_odds_snapshots(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)

    odds = NbaDatasetLoader(database_path).load_game_odds(snapshot='close')

    assert list(odds['game_id']) == ['g1', 'g2', 'g3']
    assert list(odds['decimal_home']) == [1.70, 2.40, 1.50]


def test_devig_decimal_moneyline_returns_fair_probabilities() -> None:
    home_probability, away_probability = devig_decimal_moneyline(1.80, 2.10)

    assert home_probability + away_probability == pytest.approx(1.0)
    assert home_probability == pytest.approx(0.5384615385)


def test_build_moneyline_training_frame_uses_only_prior_team_games(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)
    loader = NbaDatasetLoader(database_path)

    frame = build_moneyline_training_frame(loader, windows=(2,))

    assert list(frame['game_id']) == ['g2', 'g3']
    first_row = frame.iloc[0]
    assert first_row['home_team'] == 'BBB'
    assert first_row['away_team'] == 'AAA'
    assert first_row['home_win'] == 0
    assert first_row['home_net_rating_roll2'] == pytest.approx(-10.0)
    assert first_row['away_net_rating_roll2'] == pytest.approx(10.0)
    assert first_row['net_rating_diff'] == pytest.approx(-20.0)


def test_historical_moneyline_model_predicts_probability_from_training_frame(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)
    loader = NbaDatasetLoader(database_path)
    frame = build_moneyline_training_frame(loader, windows=(2, 10))

    model = HistoricalMoneylineModel.fit(frame)

    probability = model.predict_home_win_probability(home_team='AAA', away_team='BBB')

    assert 0.5 < probability < 1.0


def test_temporal_split_evaluation_reports_probability_metrics(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)
    loader = NbaDatasetLoader(database_path)
    frame = build_moneyline_training_frame(loader, windows=(2, 10))

    result = evaluate_temporal_split(frame, train_fraction=0.5)

    assert 0.0 <= result.brier_score <= 1.0
    assert result.log_loss > 0.0
    assert result.train_rows == 1
    assert result.test_rows == 1


def test_market_baseline_evaluates_devigged_closing_odds(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)
    loader = NbaDatasetLoader(database_path)
    frame = build_moneyline_training_frame(loader, windows=(2, 10))

    result = evaluate_market_baseline(frame, loader.load_game_odds(snapshot='close'))

    assert result.train_rows == 0
    assert result.test_rows == 2
    assert 0.0 <= result.brier_score <= 1.0
    assert result.log_loss > 0.0


def test_elo_moneyline_model_predicts_from_game_history(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)
    games = NbaDatasetLoader(database_path).load_moneyline_games()

    model = EloMoneylineModel.fit(games)
    probability = model.predict_home_win_probability('AAA', 'BBB')

    assert 0.5 < probability < 1.0


def test_metric_helpers_match_known_values() -> None:
    actual = [1, 0]
    predicted = [0.75, 0.25]

    assert calculate_brier_score(actual, predicted) == pytest.approx(0.0625)
    assert calculate_log_loss(actual, predicted) == pytest.approx(0.287682, abs=1e-6)


def test_moneyline_backtest_flags_positive_ev_bets(tmp_path: Path) -> None:
    database_path = tmp_path / 'nba_stats.sqlite'
    create_fixture_database(database_path)
    loader = NbaDatasetLoader(database_path)
    frame = build_moneyline_training_frame(loader, windows=(2, 10))
    model = HistoricalMoneylineModel.fit(frame)

    result = run_moneyline_backtest(frame, loader.load_game_odds(snapshot='close'), model)

    assert isinstance(result, BacktestResult)
    assert result.evaluated_games == 2
    assert result.bet_count >= 1
    assert result.total_staked == result.bet_count * 100.0
