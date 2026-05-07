from __future__ import annotations

from collections.abc import Sequence

from backend.enrichment import TeamEnrichmentService, compute_model_probability
from backend.models.domain import Market, MarketType
from backend.models.ev_calculator import EVCalculator, devig_market


def format_expected_value_per_100(
    calculator: EVCalculator, american_odds: int | float, model_probability: float
) -> str:
    """
    Format the expected value for a $100 stake using the provided EV calculator.
    
    Parameters:
        calculator (EVCalculator): Calculator used to compute expected value.
        american_odds (int | float): American-style odds (e.g., -150, +200).
        model_probability (float): Probability of the outcome as a decimal between 0 and 1.
    
    Returns:
        str: Expected value formatted as US dollars with two decimal places (e.g., '$12.34').
    """
    expected_value = calculator.calculate_expected_value(
        model_probability, american_odds, stake=100
    )
    return f'${expected_value:.2f}'


def enrich_live_odds_rows(
    markets: Sequence[Market],
    enrichment_service: TeamEnrichmentService | None = None,
    source: str = '',
) -> list[dict]:
    """
    Produce flattened rows of enriched outcome data for the given markets, including a computed true probability and expected value per $100 stake.
    
    Parameters:
        markets (Sequence[Market]): Sequence of Market objects whose outcomes will be converted into rows.
        enrichment_service (TeamEnrichmentService | None): Optional service used to compute model probabilities for head-to-head markets; when provided and both teams' stats are available, the row probability will be sourced from the model.
        source (str): Identifier for the data source included in each row's `source` and `id` fields.
    
    Returns:
        list[dict]: A list of dictionaries, one per outcome, containing the following keys:
            - id: Unique identifier composed of market key, outcome name, and source.
            - event_id: Market event identifier.
            - market_name: Human-readable market name.
            - market_type: Market type value.
            - bet_name: Outcome name.
            - point: Outcome point or 'N/A' when not present.
            - odds: American odds for the outcome.
            - true_prob: Probability as a percentage string formatted to one decimal place (e.g., '52.3%').
            - true_prob_raw: Numeric probability in [0.0, 1.0].
            - ev_per_100: Expected value formatted as dollars per $100 stake (e.g., '$12.34').
            - prob_source: Source of the probability ('devig' or 'nba_api').
            - source: The provided source identifier.
    
    Notes:
        - For head-to-head markets (exactly two outcomes), the enrichment_service may replace devig-derived probabilities with model probabilities when both teams' stats are available.
        - Rows whose devig-derived probability is 0.0 are omitted unless replaced by a model probability.
    """
    calculator = EVCalculator()
    rows: list[dict] = []

    for market in markets:
        true_probs = devig_market(market)
        h2h_home_probability: float | None = None

        if (
            market.market_type == MarketType.H2H
            and enrichment_service is not None
            and len(market.outcomes) == 2
        ):
            away_stats = enrichment_service.get_team_stats(market.outcomes[0].name)
            home_stats = enrichment_service.get_team_stats(market.outcomes[1].name)
            if away_stats and home_stats:
                h2h_home_probability = compute_model_probability(home_stats, away_stats)

        for i, outcome in enumerate(market.outcomes):
            row_prob = true_probs[i] if i < len(true_probs) else 0.0
            prob_source = 'devig'

            if h2h_home_probability is not None:
                row_prob = 1.0 - h2h_home_probability if i == 0 else h2h_home_probability
                prob_source = 'nba_api'

            if row_prob == 0.0 and prob_source == 'devig':
                continue

            row = {
                'id': f'{market.key}-{outcome.name}-{source}',
                'event_id': market.event_id,
                'market_name': market.name,
                'market_type': market.market_type.value,
                'bet_name': outcome.name,
                'point': outcome.point if outcome.point is not None else 'N/A',
                'odds': outcome.price.american,
                'true_prob': f'{row_prob * 100:.1f}%',
                'true_prob_raw': row_prob,
                'ev_per_100': format_expected_value_per_100(
                    calculator, outcome.price.american, row_prob
                ),
                'prob_source': prob_source,
                'source': source,
            }
            rows.append(row)

    return rows


def merge_source_rows(
    existing_rows: list[dict],
    markets: Sequence[Market],
    source: str,
    enrichment_service: TeamEnrichmentService | None = None,
) -> list[dict]:
    """
    Merge new rows produced from the given markets for a specific source with the existing rows, replacing any existing rows that belong to that source.
    
    Parameters:
        existing_rows (list[dict]): Current table rows. Each row is expected to include a 'source' key.
        markets (Sequence[Market]): Markets to convert into new rows for the provided source.
        source (str): Identifier of the source whose old rows should be replaced by rows derived from `markets`.
        enrichment_service (TeamEnrichmentService | None): Optional service used to enrich head-to-head markets; if omitted, enrichment using external team statistics is skipped.
    
    Returns:
        list[dict]: A combined list containing a shallow copy of all rows from `existing_rows` whose 'source' differs from `source`, followed by newly generated rows for `markets` associated with `source`.
    """
    rows_from_other_sources = [dict(row) for row in existing_rows if row.get('source') != source]
    return rows_from_other_sources + enrich_live_odds_rows(markets, enrichment_service, source)
