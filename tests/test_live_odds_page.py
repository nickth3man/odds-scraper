from backend.models.domain import Market, MarketType, NormalizedOdds, Outcome
from backend.models.odds_enrichment import (
    enrich_live_odds_rows,
    merge_source_rows,
)
from frontend.gui.pages.live_odds import SOURCE_BADGE_SLOT


def test_source_badge_slot_uses_valid_quasar_table_cell_template():
    assert '<q-td :props="props">' in SOURCE_BADGE_SLOT
    assert "props.value === 'ESPN' ? 'red' : 'blue'" in SOURCE_BADGE_SLOT
    assert '\\' not in SOURCE_BADGE_SLOT


def make_h2h_market(
    event_id: str = 'evt-1',
    away_name: str = 'OKC Thunder',
    away_odds: float | int = -110,
    home_name: str = 'Boston Celtics',
    home_odds: float | int = 120,
) -> Market:
    return Market(
        key=f'{event_id}-h2h',
        name='Moneyline',
        sport='nba',
        event_id=event_id,
        market_type=MarketType.H2H,
        outcomes=[
            Outcome(name=away_name, price=NormalizedOdds.from_american(away_odds)),
            Outcome(name=home_name, price=NormalizedOdds.from_american(home_odds)),
        ],
    )


def test_enrich_live_odds_rows_flattens_market_and_adds_ev_columns():
    market = make_h2h_market(away_odds=-110, home_odds=120)
    rows = enrich_live_odds_rows([market], source='ESPN')

    assert len(rows) == 2

    # Away team row (first outcome)
    away_row = rows[0]
    assert away_row['bet_name'] == 'OKC Thunder'
    assert away_row['odds'] == -110
    assert away_row['source'] == 'ESPN'
    assert away_row['prob_source'] == 'devig'
    # devig for -110 / +120
    # Implied: 110/210 = 0.5238, 100/220 = 0.4545
    # Total = 0.9783. True prob: 0.5238 / 0.9783 = ~0.535
    assert away_row['true_prob'] == '53.5%'
    assert 'ev_per_100' in away_row

    # Home team row (second outcome)
    home_row = rows[1]
    assert home_row['bet_name'] == 'Boston Celtics'
    assert home_row['odds'] == 120
    assert home_row['source'] == 'ESPN'
    assert home_row['prob_source'] == 'devig'
    assert home_row['true_prob'] == '46.5%'


def test_enrich_live_odds_skips_outcomes_when_devig_fails():
    # A market where implied probabilities sum to 0 (degenerate case)
    market = Market(
        key='evt-2-h2h',
        name='Moneyline',
        sport='nba',
        event_id='evt-2',
        market_type=MarketType.H2H,
        outcomes=[
            Outcome(
                name='Team A',
                price=NormalizedOdds(american=0, decimal=1.0, implied_probability=0.0),
            ),
            Outcome(
                name='Team B',
                price=NormalizedOdds(american=0, decimal=1.0, implied_probability=0.0),
            ),
        ],
    )
    rows = enrich_live_odds_rows([market], source='ESPN')

    assert len(rows) == 0


def test_merge_source_rows_replaces_only_refreshed_sportsbook_rows():
    existing_rows = [
        {
            'id': 'evt-old-h2h-Team X-ESPN',
            'source': 'ESPN',
            'odds': -110,
            'ev_per_100': '$5.00',
            'true_prob_raw': 0.50,
            'prob_source': 'devig',
        },
        {
            'id': 'evt-dk-h2h-Team Y-DraftKings',
            'source': 'DraftKings',
            'odds': 150,
            'ev_per_100': '$0.00',
            'true_prob_raw': 0.40,
            'prob_source': 'devig',
        },
    ]

    new_espn_markets = [make_h2h_market(event_id='evt-new')]

    rows = merge_source_rows(existing_rows, new_espn_markets, 'ESPN')

    assert len(rows) == 3  # 1 DK row preserved + 2 ESPN outcomes (Away + Home)
    sources = [row['source'] for row in rows]
    assert sources.count('DraftKings') == 1
    assert sources.count('ESPN') == 2

    event_ids = [row.get('event_id') for row in rows if row['source'] == 'ESPN']
    assert event_ids == ['evt-new', 'evt-new']
