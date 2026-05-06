from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from math import exp, log
from pathlib import Path
from typing import cast

import pandas as pd

DEFAULT_DATABASE_PATH = Path('raw/nba/sportsdata/sqlite/nba_stats.sqlite')

TEAM_FEATURE_COLUMNS = [
    'pts',
    'plus_minus',
    'off_rating',
    'def_rating',
    'net_rating',
    'efg_pct',
    'tm_tov_pct',
    'pace',
]


class NbaDatasetLoader:
    """Load canonical NBA historical data from the Sportsdata SQLite database."""

    def __init__(self, database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = Path(database_path)

    def load_moneyline_games(self) -> pd.DataFrame:
        """Load completed games that include moneyline odds and a known winner."""
        return _read_sql(
            self.database_path,
            """
            SELECT
                game_id,
                game_date,
                season_year,
                home AS home_team,
                away AS away_team,
                winner,
                pts_home,
                pts_away,
                margin,
                odds_home,
                odds_away
            FROM games_index
            WHERE odds_home > 0
              AND odds_away > 0
              AND winner IS NOT NULL
              AND pts_home IS NOT NULL
              AND pts_away IS NOT NULL
            ORDER BY game_date, game_id
            """,
            parse_dates=['game_date'],
        )

    def load_team_boxscores(self) -> pd.DataFrame:
        """Load the team-level boxscore columns needed for pre-game rolling features."""
        return _read_sql(
            self.database_path,
            """
            SELECT
                season_year,
                team_abbreviation,
                game_id,
                game_date,
                is_home,
                wl,
                pts,
                plus_minus,
                off_rating,
                def_rating,
                net_rating,
                efg_pct,
                tm_tov_pct,
                pace
            FROM team_boxscores
            ORDER BY game_date, game_id
            """,
            parse_dates=['game_date'],
        )

    def load_game_odds(self, snapshot: str = 'close') -> pd.DataFrame:
        """Load one historical odds snapshot per game for EV backtesting."""
        if snapshot not in {'open', 'close'}:
            raise ValueError("snapshot must be 'open' or 'close'")

        return _read_sql(
            self.database_path,
            """
            SELECT
                game_id,
                game_date,
                odds_date,
                decimal_home,
                decimal_away,
                moneyline_home,
                moneyline_away
            FROM game_odds
            WHERE odds_date = ?
              AND decimal_home > 1
              AND decimal_away > 1
            ORDER BY game_date, game_id
            """,
            parse_dates=['game_date'],
            params=[snapshot],
        )


def _read_sql(
    database_path: Path,
    query: str,
    parse_dates: list[str],
    params: list[object] | None = None,
) -> pd.DataFrame:
    connection = sqlite3.connect(database_path)
    try:
        frame = pd.read_sql_query(query, connection, parse_dates=parse_dates, params=params)
        return frame.copy(deep=True)
    finally:
        connection.close()


def build_moneyline_training_frame(
    loader: NbaDatasetLoader, windows: Sequence[int] = (5, 10, 20)
) -> pd.DataFrame:
    """Build one ML-ready row per game using only team games played before that game."""
    if not windows:
        raise ValueError('windows must contain at least one value')
    invalid_windows = [window for window in windows if window < 1]
    if invalid_windows:
        raise ValueError('windows must be at least 1')

    games = loader.load_moneyline_games()
    boxscores = loader.load_team_boxscores()
    rolling = _build_team_rolling_features(boxscores, windows)
    baseline_window = 10 if 10 in windows else windows[0]

    home_features = _prefix_team_features(rolling, 'home')
    away_features = _prefix_team_features(rolling, 'away')

    training = games.merge(
        home_features,
        left_on=['game_id', 'home_team'],
        right_on=['game_id', 'home_team'],
        how='left',
    ).merge(
        away_features,
        left_on=['game_id', 'away_team'],
        right_on=['game_id', 'away_team'],
        how='left',
    )

    required_columns = [
        f'home_net_rating_roll{baseline_window}',
        f'away_net_rating_roll{baseline_window}',
        f'home_off_rating_roll{baseline_window}',
        f'away_off_rating_roll{baseline_window}',
        f'home_def_rating_roll{baseline_window}',
        f'away_def_rating_roll{baseline_window}',
    ]
    training = training.dropna(subset=required_columns).copy()
    training['home_win'] = (training['winner'] == training['home_team']).astype('int64')
    training['net_rating_diff'] = (
        training[f'home_net_rating_roll{baseline_window}']
        - training[f'away_net_rating_roll{baseline_window}']
    )
    training['off_rating_diff'] = (
        training[f'home_off_rating_roll{baseline_window}']
        - training[f'away_off_rating_roll{baseline_window}']
    )
    training['def_rating_diff'] = (
        training[f'home_def_rating_roll{baseline_window}']
        - training[f'away_def_rating_roll{baseline_window}']
    )
    training['efg_pct_diff'] = (
        training[f'home_efg_pct_roll{baseline_window}']
        - training[f'away_efg_pct_roll{baseline_window}']
    )
    training['turnover_pct_diff'] = (
        training[f'home_tm_tov_pct_roll{baseline_window}']
        - training[f'away_tm_tov_pct_roll{baseline_window}']
    )
    training['pace_diff'] = (
        training[f'home_pace_roll{baseline_window}'] - training[f'away_pace_roll{baseline_window}']
    )

    feature_columns = [
        f'{side}_{column}_roll{window}'
        for side in ('home', 'away')
        for window in windows
        for column in TEAM_FEATURE_COLUMNS
    ]

    frame = training[
        [
            'game_id',
            'game_date',
            'season_year',
            'home_team',
            'away_team',
            'home_win',
            'odds_home',
            'odds_away',
            *feature_columns,
            'net_rating_diff',
            'off_rating_diff',
            'def_rating_diff',
            'efg_pct_diff',
            'turnover_pct_diff',
            'pace_diff',
        ]
    ].reset_index(drop=True)
    return cast(pd.DataFrame, frame)


@dataclass(frozen=True)
class HistoricalMoneylineModel:
    """Lightweight historical home-win probability model for moneyline bets."""

    base_logit: float
    net_rating_weight: float
    team_net_ratings: dict[str, float]

    @classmethod
    def fit(cls, training_frame: pd.DataFrame) -> HistoricalMoneylineModel:
        """Fit a simple calibrated model from a moneyline training frame."""
        if training_frame.empty:
            raise ValueError('training_frame must contain at least one row')

        home_win_rate = _clip_probability(cast(float, training_frame['home_win'].mean()))
        base_logit = _logit(home_win_rate)
        net_rating_weight = _fit_net_rating_weight(training_frame)
        team_net_ratings = _latest_team_net_ratings(training_frame)
        return cls(
            base_logit=base_logit,
            net_rating_weight=net_rating_weight,
            team_net_ratings=team_net_ratings,
        )

    def predict_home_win_probability(self, home_team: str, away_team: str) -> float:
        """Predict the home team's win probability from latest rolling team ratings."""
        if home_team not in self.team_net_ratings:
            raise ValueError(f'No historical rating available for home team: {home_team}')
        if away_team not in self.team_net_ratings:
            raise ValueError(f'No historical rating available for away team: {away_team}')

        rating_diff = self.team_net_ratings[home_team] - self.team_net_ratings[away_team]
        return self.predict_home_win_probability_from_diff(rating_diff)

    def predict_home_win_probability_from_diff(self, net_rating_diff: float) -> float:
        """Predict home-win probability from a pre-game net-rating differential."""
        return _sigmoid(self.base_logit + self.net_rating_weight * net_rating_diff)


@dataclass(frozen=True)
class EloMoneylineModel:
    """Simple NBA Elo baseline with home-court advantage."""

    ratings: dict[str, float]
    home_advantage: float = 100.0

    @classmethod
    def fit(cls, games: pd.DataFrame, k_factor: float = 20.0) -> EloMoneylineModel:
        """Fit final Elo ratings from chronological game results."""
        ratings: dict[str, float] = {}
        for row in games.sort_values('game_date').to_dict(orient='records'):
            home_team = str(row['home_team'])
            away_team = str(row['away_team'])
            home_rating = ratings.get(home_team, 1500.0)
            away_rating = ratings.get(away_team, 1500.0)
            expected_home = _elo_expected_score(home_rating + 100.0, away_rating)
            actual_home = 1.0 if row['winner'] == home_team else 0.0
            margin = abs(float(row['pts_home']) - float(row['pts_away']))
            multiplier = ((margin + 3.0) ** 0.8) / 7.5
            change = k_factor * multiplier * (actual_home - expected_home)
            ratings[home_team] = home_rating + change
            ratings[away_team] = away_rating - change
        return cls(ratings=ratings)

    def predict_home_win_probability(self, home_team: str, away_team: str) -> float:
        """Predict home-win probability from fitted Elo ratings."""
        home_rating = self.ratings.get(home_team, 1500.0) + self.home_advantage
        away_rating = self.ratings.get(away_team, 1500.0)
        return _elo_expected_score(home_rating, away_rating)


@dataclass(frozen=True)
class EvaluationResult:
    """Temporal holdout metrics for a probability model."""

    train_rows: int
    test_rows: int
    brier_score: float
    log_loss: float


@dataclass(frozen=True)
class BacktestResult:
    """Historical flat-stake moneyline backtest result."""

    evaluated_games: int
    bet_count: int
    total_staked: float
    profit: float
    roi: float
    average_edge: float


def devig_decimal_moneyline(home_decimal: float, away_decimal: float) -> tuple[float, float]:
    """Convert two decimal moneyline prices to fair probabilities by removing overround."""
    home_implied = 1.0 / home_decimal
    away_implied = 1.0 / away_decimal
    total_implied = home_implied + away_implied
    if total_implied == 0.0:
        return 0.0, 0.0
    return home_implied / total_implied, away_implied / total_implied


def calculate_brier_score(actual: Sequence[int], predicted: Sequence[float]) -> float:
    """Calculate binary Brier score for calibrated probability evaluation."""
    pairs = list(zip(actual, predicted, strict=True))
    if not pairs:
        raise ValueError('actual and predicted must contain at least one value')
    return sum((truth - probability) ** 2 for truth, probability in pairs) / len(pairs)


def calculate_log_loss(actual: Sequence[int], predicted: Sequence[float]) -> float:
    """Calculate binary log-loss with clipping for numerical stability."""
    pairs = list(zip(actual, predicted, strict=True))
    if not pairs:
        raise ValueError('actual and predicted must contain at least one value')

    total = 0.0
    for truth, probability in pairs:
        clipped = _clip_probability(probability)
        total += truth * log(clipped) + (1 - truth) * log(1.0 - clipped)
    return -total / len(pairs)


def evaluate_temporal_split(
    training_frame: pd.DataFrame, train_fraction: float = 0.8
) -> EvaluationResult:
    """Train on older games and evaluate probability quality on later games."""
    if not 0.0 < train_fraction < 1.0:
        raise ValueError('train_fraction must be between 0 and 1')

    ordered = training_frame.sort_values('game_date').reset_index(drop=True)
    split_index = int(len(ordered) * train_fraction)
    if split_index < 1 or split_index >= len(ordered):
        raise ValueError('training_frame must have enough rows for a temporal split')

    train = ordered.iloc[:split_index]
    test = ordered.iloc[split_index:]
    model = HistoricalMoneylineModel.fit(train)
    actual = [int(value) for value in test['home_win'].tolist()]
    predicted = [
        model.predict_home_win_probability_from_diff(float(value))
        for value in test['net_rating_diff'].tolist()
    ]
    return EvaluationResult(
        train_rows=len(train),
        test_rows=len(test),
        brier_score=calculate_brier_score(actual, predicted),
        log_loss=calculate_log_loss(actual, predicted),
    )


def evaluate_market_baseline(
    training_frame: pd.DataFrame, odds_frame: pd.DataFrame
) -> EvaluationResult:
    """Evaluate de-vigged market-implied probabilities against actual outcomes."""
    merged = training_frame.merge(odds_frame, on='game_id', how='inner', suffixes=('', '_odds'))
    actual = [int(value) for value in merged['home_win'].tolist()]
    predicted = [
        devig_decimal_moneyline(float(row['decimal_home']), float(row['decimal_away']))[0]
        for row in merged.to_dict(orient='records')
    ]
    return EvaluationResult(
        train_rows=0,
        test_rows=len(merged),
        brier_score=calculate_brier_score(actual, predicted),
        log_loss=calculate_log_loss(actual, predicted),
    )


def run_moneyline_backtest(
    training_frame: pd.DataFrame,
    odds_frame: pd.DataFrame,
    model: HistoricalMoneylineModel,
    stake: float = 100.0,
    min_edge: float = 0.0,
) -> BacktestResult:
    """Backtest flat-stake bets where model probability beats de-vigged market probability."""
    merged = training_frame.merge(odds_frame, on='game_id', how='inner', suffixes=('', '_odds'))
    profit = 0.0
    bet_count = 0
    total_edge = 0.0

    for row in merged.to_dict(orient='records'):
        model_home = model.predict_home_win_probability_from_diff(float(row['net_rating_diff']))
        model_away = 1.0 - model_home
        market_home, market_away = devig_decimal_moneyline(
            float(row['decimal_home']), float(row['decimal_away'])
        )
        home_edge = model_home - market_home
        away_edge = model_away - market_away

        if home_edge > min_edge and home_edge >= away_edge:
            bet_count += 1
            total_edge += home_edge
            profit += _settle_decimal_bet(
                won=bool(row['home_win']), decimal_odds=float(row['decimal_home']), stake=stake
            )
        elif away_edge > min_edge:
            bet_count += 1
            total_edge += away_edge
            profit += _settle_decimal_bet(
                won=not bool(row['home_win']), decimal_odds=float(row['decimal_away']), stake=stake
            )

    total_staked = bet_count * stake
    roi = profit / total_staked if total_staked else 0.0
    average_edge = total_edge / bet_count if bet_count else 0.0
    return BacktestResult(
        evaluated_games=len(merged),
        bet_count=bet_count,
        total_staked=total_staked,
        profit=profit,
        roi=roi,
        average_edge=average_edge,
    )


def _build_team_rolling_features(boxscores: pd.DataFrame, windows: Sequence[int]) -> pd.DataFrame:
    sorted_boxscores = boxscores.sort_values(
        ['season_year', 'team_abbreviation', 'game_date', 'game_id']
    ).copy()
    grouped = sorted_boxscores.groupby(['season_year', 'team_abbreviation'])
    for window in windows:
        for column in TEAM_FEATURE_COLUMNS:
            sorted_boxscores[f'{column}_roll{window}'] = grouped[column].transform(
                lambda values, rolling_window=window: (
                    values.shift(1).rolling(window=rolling_window, min_periods=1).mean()
                )
            )

    frame = sorted_boxscores[
        [
            'game_id',
            'team_abbreviation',
            *[f'{column}_roll{window}' for window in windows for column in TEAM_FEATURE_COLUMNS],
        ]
    ]
    return cast(pd.DataFrame, frame)


def _prefix_team_features(features: pd.DataFrame, side: str) -> pd.DataFrame:
    return features.rename(
        columns={
            'team_abbreviation': f'{side}_team',
            **{
                column: f'{side}_{column}'
                for column in features.columns
                if column not in {'game_id', 'team_abbreviation'}
            },
        }
    )


def _fit_net_rating_weight(training_frame: pd.DataFrame) -> float:
    winners = training_frame.loc[training_frame['home_win'] == 1, 'net_rating_diff']
    losers = training_frame.loc[training_frame['home_win'] == 0, 'net_rating_diff']
    if winners.empty or losers.empty:
        return 0.04

    separation = float(winners.mean() - losers.mean())
    if separation == 0.0:
        return 0.04

    sign = 1.0 if separation > 0.0 else -1.0
    return sign * min(abs(separation) / 400.0, 0.08)


def _latest_team_net_ratings(training_frame: pd.DataFrame) -> dict[str, float]:
    ratings: dict[str, float] = {}
    home_rating_column = _first_existing_column(training_frame, 'home_net_rating_roll')
    away_rating_column = _first_existing_column(training_frame, 'away_net_rating_roll')
    rows = cast(
        list[list[object]],
        training_frame.sort_values('game_date')[
            ['home_team', 'away_team', home_rating_column, away_rating_column]
        ]
        .to_numpy()
        .tolist(),
    )
    for home_team, away_team, home_rating, away_rating in rows:
        ratings[str(home_team)] = float(cast(float, home_rating))
        ratings[str(away_team)] = float(cast(float, away_rating))
    return ratings


def _first_existing_column(frame: pd.DataFrame, prefix: str) -> str:
    preferred = f'{prefix}10'
    if preferred in frame.columns:
        return preferred
    for column in frame.columns:
        if column.startswith(prefix):
            return str(column)
    raise ValueError(f'Missing expected feature column with prefix: {prefix}')


def _settle_decimal_bet(won: bool, decimal_odds: float, stake: float) -> float:
    if won:
        return stake * (decimal_odds - 1.0)
    return -stake


def _elo_expected_score(rating: float, opponent_rating: float) -> float:
    return 1.0 / (1.0 + 10 ** ((opponent_rating - rating) / 400.0))


def _clip_probability(probability: float) -> float:
    return min(max(probability, 0.001), 0.999)


def _logit(probability: float) -> float:
    clipped = _clip_probability(probability)
    return log(clipped / (1.0 - clipped))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))
