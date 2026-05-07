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
        """
        Initialize the loader with the path to the SQLite database.
        
        Parameters:
            database_path (str | Path): Filesystem path to the SQLite database file. Defaults to DEFAULT_DATABASE_PATH. The path is stored on the instance as a pathlib.Path in `self.database_path`.
        """
        self.database_path = Path(database_path)

    def load_moneyline_games(self) -> pd.DataFrame:
        """
        Load completed games that have positive moneyline odds and a recorded winner.
        
        The returned DataFrame contains the columns:
        `game_id`, `game_date`, `season_year`, `home_team`, `away_team`, `winner`,
        `pts_home`, `pts_away`, `margin`, `odds_home`, and `odds_away`. Rows are
        ordered by `game_date` then `game_id`, and `game_date` is parsed as a
        datetime. Only games with `odds_home > 0`, `odds_away > 0`, non-null
        `winner`, and non-null `pts_home`/`pts_away` are included.
        
        Returns:
            pd.DataFrame: Per-game identifiers, scores, margin, and moneyline odds.
        """
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
        """
        Load a single historical odds snapshot per game for expected-value backtesting.
        
        Parameters:
            snapshot (str): Which odds snapshot to load; must be 'open' or 'close'.
        
        Returns:
            pd.DataFrame: Rows ordered by game_date and game_id with columns
                `game_id`, `game_date`, `odds_date`, `decimal_home`, `decimal_away`,
                `moneyline_home`, and `moneyline_away`.
        
        Raises:
            ValueError: If `snapshot` is not 'open' or 'close'.
        """
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
    """
    Execute a SQL query against a SQLite database and return the result as a pandas DataFrame.
    
    Parameters:
        database_path (Path): Path to the SQLite database file.
        query (str): SQL query string to execute.
        parse_dates (list[str]): Column names that should be parsed as datetimes.
        params (list[object] | None): Optional sequence of parameters to bind to the query.
    
    Returns:
        pd.DataFrame: A deep-copied DataFrame containing the query results with specified columns parsed as datetimes.
        
    Notes:
        The database connection is always closed before returning.
    """
    connection = sqlite3.connect(database_path)
    try:
        frame = pd.read_sql_query(query, connection, parse_dates=parse_dates, params=params)
        return frame.copy(deep=True)
    finally:
        connection.close()


def build_moneyline_training_frame(
    loader: NbaDatasetLoader, windows: Sequence[int] = (5, 10, 20)
) -> pd.DataFrame:
    """
    Builds a machine-learning-ready per-game DataFrame with pre-game team rolling features and target/differential columns.
    
    Parameters:
        loader (NbaDatasetLoader): Data loader used to read games, boxscores, and odds from the dataset.
        windows (Sequence[int]): Sequence of positive integers specifying the rolling-window sizes (in prior games) used to compute team-level features; must contain at least one value and all values must be >= 1.
    
    Returns:
        pd.DataFrame: A DataFrame with one row per game containing:
            - identifiers and metadata: `game_id`, `game_date`, `season_year`, `home_team`, `away_team`
            - target: `home_win` (1 if home team won, 0 otherwise)
            - market odds: `odds_home`, `odds_away`
            - rolling features for each side and window using the pattern `{side}_{feature}_roll{window}` for every feature in TEAM_FEATURE_COLUMNS and every requested window
            - baseline-window differential features: `net_rating_diff`, `off_rating_diff`, `def_rating_diff`, `efg_pct_diff`, `turnover_pct_diff`, `pace_diff`
    """
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
        """
        Create a HistoricalMoneylineModel calibrated from a moneyline training frame.
        
        Computes a baseline logit from the mean home win rate, fits a scalar weight for
        net-rating differentials, and extracts the latest per-team net ratings from the
        frame.
        
        Parameters:
        	training_frame (pd.DataFrame): Training rows containing `home_win` and the
        		rolling net-rating features; must contain at least one row.
        
        Returns:
        	HistoricalMoneylineModel: A model populated with `base_logit`, `net_rating_weight`,
        		and `team_net_ratings`.
        
        Raises:
        	ValueError: If `training_frame` is empty.
        """
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
        """
        Predict the probability that the home team wins using the latest available team net ratings.
        
        Parameters:
        	home_team (str): Home team identifier matching keys of the model's `team_net_ratings`.
        	away_team (str): Away team identifier matching keys of the model's `team_net_ratings`.
        
        Returns:
        	probability (float): Probability of a home win as a float between 0.0 and 1.0.
        
        Raises:
        	ValueError: If a rating for `home_team` or `away_team` is not available in `team_net_ratings`.
        """
        if home_team not in self.team_net_ratings:
            raise ValueError(f'No historical rating available for home team: {home_team}')
        if away_team not in self.team_net_ratings:
            raise ValueError(f'No historical rating available for away team: {away_team}')

        rating_diff = self.team_net_ratings[home_team] - self.team_net_ratings[away_team]
        return self.predict_home_win_probability_from_diff(rating_diff)

    def predict_home_win_probability_from_diff(self, net_rating_diff: float) -> float:
        """
        Predict the home team's win probability from a pre-game net-rating differential.
        
        Parameters:
            net_rating_diff (float): Home team's net rating minus away team's net rating prior to the game.
        
        Returns:
            probability (float): Estimated probability (0.0 to 1.0) that the home team wins.
        """
        return _sigmoid(self.base_logit + self.net_rating_weight * net_rating_diff)


@dataclass(frozen=True)
class EloMoneylineModel:
    """Simple NBA Elo baseline with home-court advantage."""

    ratings: dict[str, float]
    home_advantage: float = 100.0

    @classmethod
    def fit(
        cls, games: pd.DataFrame, k_factor: float = 20.0, home_advantage: float = 100.0
    ) -> EloMoneylineModel:
        """
        Estimate Elo ratings by processing games in chronological order.
        
        Parameters:
            games (pd.DataFrame): Game records containing the columns 'game_date', 'home_team', 'away_team', 'winner', 'pts_home', and 'pts_away'. Rows need not be pre-sorted; they will be processed in ascending 'game_date' order.
            k_factor (float): Base Elo update scale applied to each game (default 20.0). Larger values produce larger rating changes per game.
        
        Returns:
            EloMoneylineModel: A model instance whose `ratings` map each team to its final Elo rating after processing all games.
        """
        ratings: dict[str, float] = {}
        for row in games.sort_values('game_date').to_dict(orient='records'):
            home_team = str(row['home_team'])
            away_team = str(row['away_team'])
            home_rating = ratings.get(home_team, 1500.0)
            away_rating = ratings.get(away_team, 1500.0)
            expected_home = _elo_expected_score(home_rating + home_advantage, away_rating)
            actual_home = 1.0 if row['winner'] == home_team else 0.0
            margin = abs(float(row['pts_home']) - float(row['pts_away']))
            multiplier = ((margin + 3.0) ** 0.8) / 7.5
            change = k_factor * multiplier * (actual_home - expected_home)
            ratings[home_team] = home_rating + change
            ratings[away_team] = away_rating - change
        return cls(ratings=ratings, home_advantage=home_advantage)

    def predict_home_win_probability(self, home_team: str, away_team: str) -> float:
        """
        Compute the home team's probability of winning using the model's fitted Elo ratings.
        
        Returns:
            probability (float): Probability in [0.0, 1.0] that the home team wins.
        """
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
    """
    Convert two decimal moneyline prices into normalized (fair) probabilities by removing the bookmaker's overround.
    
    Parameters:
        home_decimal (float): Decimal odds for the home team.
        away_decimal (float): Decimal odds for the away team.
    
    Returns:
        (home_prob, away_prob): Tuple of probabilities where each probability equals its implied probability (1/decimal) normalized so the two sum to 1. Returns (0.0, 0.0) if both decimals imply zero total probability.
    """
    home_implied = 1.0 / home_decimal
    away_implied = 1.0 / away_decimal
    total_implied = home_implied + away_implied
    if total_implied == 0.0:
        return 0.0, 0.0
    return home_implied / total_implied, away_implied / total_implied


def calculate_brier_score(actual: Sequence[int], predicted: Sequence[float]) -> float:
    """
    Compute the Brier score for binary outcomes.
    
    Calculates the mean squared error between actual binary outcomes (0 or 1) and predicted probabilities.
    
    Parameters:
        actual (Sequence[int]): Sequence of binary outcomes (0 or 1).
        predicted (Sequence[float]): Sequence of predicted probabilities (expected in [0, 1]).
    
    Returns:
        float: Mean squared error between actual outcomes and predicted probabilities.
    
    Raises:
        ValueError: If the input sequences are empty or have differing lengths.
    """
    pairs = list(zip(actual, predicted, strict=True))
    if not pairs:
        raise ValueError('actual and predicted must contain at least one value')
    return sum((truth - probability) ** 2 for truth, probability in pairs) / len(pairs)


def calculate_log_loss(actual: Sequence[int], predicted: Sequence[float]) -> float:
    """
    Compute the binary log loss between true labels and predicted probabilities with clipping for numerical stability.
    
    Parameters:
        actual (Sequence[int]): Sequence of true binary labels (0 or 1). Length must match `predicted`.
        predicted (Sequence[float]): Sequence of predicted probabilities (expected in [0, 1]). Length must match `actual`.
    
    Returns:
        float: Mean binary log loss (negative average log-likelihood).
    
    Raises:
        ValueError: If `actual` and `predicted` are empty or have differing lengths.
    """
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
    """
    Train a HistoricalMoneylineModel on earlier games and evaluate its probability predictions on later games.
    
    Parameters:
        training_frame (pd.DataFrame): DataFrame of per-game training rows ordered by `game_date` containing at least the columns `game_date`, `home_win`, and `net_rating_diff`.
        train_fraction (float): Fraction of rows to use for training (must be greater than 0 and less than 1).
    
    Returns:
        EvaluationResult: Object containing `train_rows`, `test_rows`, `brier_score`, and `log_loss` computed on the holdout (later) portion.
    
    Raises:
        ValueError: If `train_fraction` is not in (0, 1) or if the split yields an empty train or test set.
    """
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
    """
    Evaluate the market baseline by comparing de-vigged decimal odds to actual home-win outcomes.
    
    Parameters:
        training_frame (pd.DataFrame): DataFrame containing game identifiers and actual outcomes; must include a `game_id` column and a `home_win` column (0/1).
        odds_frame (pd.DataFrame): DataFrame containing market decimal odds; must include `game_id`, `decimal_home`, and `decimal_away` columns.
    
    Returns:
        EvaluationResult: EvaluationResult with `train_rows` set to 0, `test_rows` equal to the number of merged games, `brier_score` computed between actual home-win labels and de-vigged market probabilities, and `log_loss` computed likewise.
    """
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
    """
    Run a flat-stake backtest comparing a model's probabilities to de-vigged market probabilities and settle bets when the model shows sufficient edge.
    
    Parameters:
        training_frame (pd.DataFrame): Per-game feature frame containing `game_id`, `home_win`, and `net_rating_diff`.
        odds_frame (pd.DataFrame): Odds frame containing `game_id`, `decimal_home`, and `decimal_away`.
        model (HistoricalMoneylineModel): Probability model used to produce home win probabilities from `net_rating_diff`.
        stake (float): Fixed stake placed on each bet when an edge is taken.
        min_edge (float): Minimum positive edge (model probability minus market probability) required to place a bet.
    
    Returns:
        BacktestResult: Aggregated backtest metrics including number of evaluated games, bets placed, total staked, profit, ROI, and average edge.
    """
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
    """
    Compute prior-game rolling means of team statistics for specified window sizes.
    
    Parameters:
        boxscores (pd.DataFrame): Team boxscore rows ordered by game with columns at minimum
            'season_year', 'team_abbreviation', 'game_date', 'game_id' and all names listed in
            TEAM_FEATURE_COLUMNS.
        windows (Sequence[int]): Sequence of positive integer window sizes (number of prior games)
            for which to compute rolling means.
    
    Returns:
        pd.DataFrame: A frame with columns:
            - 'game_id'
            - 'team_abbreviation'
            - one column per feature and window named '{feature}_roll{window}',
              containing the mean of that feature over the specified number of prior games
              (the current game's value is excluded).
    """
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
    """
    Prefix team feature columns with the given side.
    
    Rename `team_abbreviation` to `{side}_team` and prepend `{side}_` to every column except `game_id` and `team_abbreviation`.
    
    Parameters:
        features (pd.DataFrame): DataFrame containing team-level features including `team_abbreviation` and `game_id`.
        side (str): Prefix to apply to team feature columns (e.g., `"home"` or `"away"`).
    
    Returns:
        pd.DataFrame: A new DataFrame with `team_abbreviation` renamed to `{side}_team` and other feature columns (except `game_id`) renamed with the `{side}_` prefix.
    """
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
    """
    Estimate a scalar weight for the net-rating differential based on the mean separation
    between games won by the home team and games lost by the home team.
    
    If there are no winners or no losers in the frame, or if the mean separation is zero,
    this returns a default weight of 0.04. Otherwise the weight is the sign of the
    separation multiplied by min(|separation| / 400.0, 0.08).
    
    Returns:
        float: Weight to apply to `net_rating_diff` (positive when higher net-rating favors
        home wins, negative when it disfavors them).
    """
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
    """
    Extract the most recent net rating value for each team from a chronological training frame.
    
    Parameters:
        training_frame (pd.DataFrame): DataFrame sorted by `game_date` (or containing `game_date`) and containing columns
            `home_team`, `away_team`, and at least one pair of net rating columns whose names start with
            `home_net_rating_roll` and `away_net_rating_roll` (e.g., `home_net_rating_roll10` / `away_net_rating_roll10`).
    
    Returns:
        dict[str, float]: Mapping from team identifier (string) to the team's latest net rating (float). For teams
        that appear multiple times, the value from the last (most recent) game in chronological order is used.
    
    Raises:
        ValueError: If no matching `home_net_rating_roll*` or `away_net_rating_roll*` column exists in `training_frame`.
    """
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
    """
    Find the first column name in `frame` that begins with `prefix`, preferring the `{prefix}10` variant.
    
    Parameters:
        frame (pd.DataFrame): DataFrame whose columns will be searched.
        prefix (str): Column name prefix to match.
    
    Returns:
        str: The name of the preferred matching column (returns `f"{prefix}10"` if present), otherwise the first column that starts with `prefix`.
    
    Raises:
        ValueError: If no column in `frame` starts with `prefix`.
    """
    preferred = f'{prefix}10'
    if preferred in frame.columns:
        return preferred
    for column in frame.columns:
        if column.startswith(prefix):
            return str(column)
    raise ValueError(f'Missing expected feature column with prefix: {prefix}')


def _settle_decimal_bet(won: bool, decimal_odds: float, stake: float) -> float:
    """
    Compute the profit for a settled decimal-odds bet.
    
    Parameters:
        won (bool): True if the bet was successful (won), False otherwise.
        decimal_odds (float): The decimal odds offered for the bet (e.g., 2.5).
        stake (float): The amount staked on the bet.
    
    Returns:
        float: Profit amount: `stake * (decimal_odds - 1.0)` if `won` is True, `-stake` if `won` is False.
    """
    if won:
        return stake * (decimal_odds - 1.0)
    return -stake


def _elo_expected_score(rating: float, opponent_rating: float) -> float:
    """
    Compute the expected score (win probability) for a team given its Elo rating and an opponent's rating.
    
    Parameters:
        rating (float): Elo rating of the team.
        opponent_rating (float): Elo rating of the opponent.
    
    Returns:
        float: Expected score as a probability between 0 and 1.
    """
    return 1.0 / (1.0 + 10 ** ((opponent_rating - rating) / 400.0))


def _clip_probability(probability: float) -> float:
    """
    Clamp a probability value to the inclusive range 0.001 through 0.999.
    
    Returns:
        float: The input probability constrained to be at least 0.001 and at most 0.999.
    """
    return min(max(probability, 0.001), 0.999)


def _logit(probability: float) -> float:
    """
    Compute the logit (log-odds) of a probability with clipping for numerical stability.
    
    The input probability is clipped to the interval [0.001, 0.999] before computing the log-odds to avoid infinite values.
    
    Parameters:
        probability (float): A probability value, typically between 0 and 1.
    
    Returns:
        float: The log-odds value computed as log(p / (1 - p)) after clipping.
    """
    clipped = _clip_probability(probability)
    return log(clipped / (1.0 - clipped))


def _sigmoid(value: float) -> float:
    """
    Compute the logistic sigmoid of a real-valued input.
    
    Parameters:
        value (float): Input value (e.g., log-odds or score difference).
    
    Returns:
        probability (float): A value strictly between 0 and 1 computed as 1 / (1 + exp(-value)).
    """
    return 1.0 / (1.0 + exp(-value))
