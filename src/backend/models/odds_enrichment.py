from __future__ import annotations

from collections.abc import Mapping, Sequence

from backend.enrichment import TeamEnrichmentService, compute_model_probability
from backend.models.ev_calculator import EVCalculator


def parse_american_odds(value: object) -> int | None:
    """Parse an American odds string (e.g. '+150', '-110') into an integer.

    Args:
        value: Raw odds value, typically a string like '+150' or '-110'.

    Returns:
        The odds as an integer, or ``None`` when *value* cannot be parsed.
    """
    try:
        return int(str(value).replace('+', ''))
    except (TypeError, ValueError):
        return None


def format_expected_value_per_100(
    calculator: EVCalculator, moneyline: object, model_probability: float
) -> str:
    """Compute the expected value per $100 staked for a single moneyline.

    Args:
        calculator: ``EVCalculator`` instance used for the computation.
        moneyline: Raw moneyline value (e.g. ``'-110'`` or ``'+150'``).
        model_probability: Win probability from the model (0.0-1.0).

    Returns:
        A formatted dollar string such as ``'$5.00'``, or ``'N/A'`` when the
        moneyline cannot be parsed.
    """
    american_odds = parse_american_odds(moneyline)
    if american_odds is None:
        return 'N/A'

    expected_value = calculator.calculate_expected_value(
        model_probability, american_odds, stake=100
    )
    return f'${expected_value:.2f}'


def enrich_live_odds_rows(
    games: Sequence[Mapping[str, object]],
    model_probability: float,
    enrichment_service: TeamEnrichmentService | None = None,
) -> list[dict]:
    """
    Enrich scraper game mappings with expected-value columns and optional model-derived team data.

    When provided, `enrichment_service` is used to fetch team stats; if stats for both teams are available the function derives an effective win probability and adds model-derived fields (home_win_pct, away_win_pct, home_off_rating, home_def_rating, away_off_rating, away_def_rating, home_record, away_record, model_probability_source='nba_api'). If stats are missing for either team the row receives model_probability_source='manual_slider'. If `enrichment_service` is not provided no model-derived fields or probability source are added. In all cases the function adds `expected_value_per_100` and `home_expected_value_per_100` computed using the effective probability.

    Parameters:
        games: Sequence of game mappings produced by a scraper.
        model_probability: Fallback win probability (0.0-1.0) used when model-derived probability is not available.
        enrichment_service: Optional service used to obtain team statistics; when None no enrichment is attempted.

    Returns:
        List[dict]: A list of enriched row dictionaries containing the original game data plus EV columns and, when available, model-derived team fields.
    """
    calculator = EVCalculator()
    rows: list[dict] = []
    for game in games:
        row = dict(game)
        effective_probability = model_probability
        if enrichment_service is not None:
            home_team = str(row.get('home_team', ''))
            away_team = str(row.get('away_team', ''))
            home_stats = enrichment_service.get_team_stats(home_team)
            away_stats = enrichment_service.get_team_stats(away_team)
            if home_stats and away_stats:
                effective_probability = compute_model_probability(home_stats, away_stats)
                row['home_win_pct'] = effective_probability
                row['away_win_pct'] = 1.0 - effective_probability
                row['home_off_rating'] = home_stats.off_rating
                row['home_def_rating'] = home_stats.def_rating
                row['away_off_rating'] = away_stats.off_rating
                row['away_def_rating'] = away_stats.def_rating
                row['home_record'] = f'{home_stats.wins}-{home_stats.losses}'
                row['away_record'] = f'{away_stats.wins}-{away_stats.losses}'
                row['model_probability_source'] = 'nba_api'
            else:
                row['model_probability_source'] = 'manual_slider'
        row['expected_value_per_100'] = format_expected_value_per_100(
            calculator, row.get('moneyline'), 1.0 - effective_probability
        )
        row['home_expected_value_per_100'] = format_expected_value_per_100(
            calculator, row.get('home_moneyline'), effective_probability
        )
        rows.append(row)
    return rows


def recompute_expected_value(
    rows: list[dict],
    model_probability: float,
) -> list[dict]:
    """Re-compute EV columns for existing table rows using per-row or slider probability.

    For rows whose ``model_probability_source`` is ``'nba_api'`` the function retains
    the row's ``home_win_pct`` as the home win probability; all other rows use the
    slider ``model_probability``. The away EV is always computed from
    ``1 - home_probability``.

    Args:
        rows: Current table rows (each must contain ``moneyline`` and
            ``home_moneyline`` keys).
        model_probability: Fallback home win probability (0.0-1.0) used when the
            row does not carry a model-derived probability.

    Returns:
        New list of rows with refreshed ``expected_value_per_100`` and
        ``home_expected_value_per_100`` values.
    """
    calculator = EVCalculator()
    result: list[dict] = []
    for row in rows:
        row_prob = model_probability
        if row.get('model_probability_source') == 'nba_api' and 'home_win_pct' in row:
            row_prob = float(row['home_win_pct'])
        away_prob = 1.0 - row_prob
        result.append(
            {
                **row,
                'expected_value_per_100': format_expected_value_per_100(
                    calculator, row.get('moneyline'), away_prob
                ),
                'home_expected_value_per_100': format_expected_value_per_100(
                    calculator, row.get('home_moneyline'), row_prob
                ),
            }
        )
    return result


def merge_source_rows(
    existing_rows: list[dict],
    games: Sequence[Mapping[str, object]],
    source: str,
    model_probability: float,
    enrichment_service: TeamEnrichmentService | None = None,
) -> list[dict]:
    """
    Merge freshly scraped games for a given source into the existing table rows.

    Preserves rows from other sources (their EV values are recomputed using the provided model_probability) and replaces rows whose `source` matches the given `source` with the newly enriched game rows.

    Parameters:
        existing_rows (list[dict]): Current rows in the odds table.
        games (Sequence[Mapping[str, object]]): Newly scraped game mappings to insert for `source`.
        source (str): Identifier of the sportsbook or feed being refreshed (e.g., "ESPN").
        model_probability (float): Base win probability (0.0-1.0) used to recompute expected value columns for preserved rows and to compute EV for new rows.
        enrichment_service (TeamEnrichmentService | None): Optional service used when enriching newly scraped games; when provided, team stats may be used to derive an effective model probability for those games.

    Returns:
        list[dict]: Combined list of preserved (recomputed) rows from other sources followed by enriched rows for `source`, suitable for table update.
    """
    rows_from_other_sources = [dict(row) for row in existing_rows if row.get('source') != source]
    re_enriched = recompute_expected_value(rows_from_other_sources, model_probability)
    return re_enriched + enrich_live_odds_rows(games, model_probability, enrichment_service)
