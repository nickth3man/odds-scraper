from __future__ import annotations

from collections.abc import Sequence

from backend.enrichment import TeamEnrichmentService, compute_model_probability
from backend.models.ev_calculator import EVCalculator, devig_market
from backend.models.domain import Market, MarketType


def format_expected_value_per_100(
    calculator: EVCalculator, american_odds: int | float, model_probability: float
) -> str:
    """Compute the expected value per $100 staked for a single odds value."""
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
    Enrich scraper Market mappings with expected-value columns and optional model-derived team data.
    Returns flattened rows for each outcome.
    """
    calculator = EVCalculator()
    rows: list[dict] = []
    
    for market in markets:
        true_probs = devig_market(market)
        
        for i, outcome in enumerate(market.outcomes):
            row_prob = true_probs[i] if i < len(true_probs) else 0.0
            prob_source = 'devig'
            
            if market.market_type == MarketType.H2H and enrichment_service is not None:
                if len(market.outcomes) == 2:
                    team_name = outcome.name
                    opp_idx = 1 if i == 0 else 0
                    opp_name = market.outcomes[opp_idx].name
                    
                    team_stats = enrichment_service.get_team_stats(team_name)
                    opp_stats = enrichment_service.get_team_stats(opp_name)
                    
                    if team_stats and opp_stats:
                        row_prob = compute_model_probability(team_stats, opp_stats)
                        prob_source = 'nba_api'
            
            if row_prob == 0.0 and prob_source == 'devig':
                row_prob = model_probability
                prob_source = 'manual_slider'
            
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
    Merge freshly scraped markets for a given source into the existing table rows.
    """
    rows_from_other_sources = [dict(row) for row in existing_rows if row.get('source') != source]
    return rows_from_other_sources + enrich_live_odds_rows(markets, enrichment_service, source)
