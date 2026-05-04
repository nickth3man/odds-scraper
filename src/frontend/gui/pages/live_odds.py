from nicegui import APIRouter, run, ui

from backend.models.ev_calculator import EVCalculator
from backend.odds_scraping.espn_scraper import EspnOddsScraper
from backend.odds_scraping.live_odds_scraper import LiveOddsScraper

router = APIRouter()

COLUMNS = [
    {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
    {'name': 'matchup', 'label': 'Matchup', 'field': 'matchup', 'align': 'left'},
    {'name': 'spread', 'label': 'Spread', 'field': 'spread'},
    {'name': 'moneyline', 'label': 'ML (Away)', 'field': 'moneyline'},
    {'name': 'home_moneyline', 'label': 'ML (Home)', 'field': 'home_moneyline'},
    {'name': 'over_under', 'label': 'O/U', 'field': 'over_under'},
    {'name': 'ev_per_100', 'label': 'EV / $100 (Away)', 'field': 'ev_per_100'},
    {'name': 'source', 'label': 'Source', 'field': 'source', 'sortable': True},
]

SOURCE_BADGE_SLOT = """
<q-td :props="props">
    <q-badge :color="props.value === 'ESPN' ? 'red' : 'blue'" :label="props.value" />
</q-td>
"""


def _parse_american_odds(value: object) -> int | None:
    try:
        return int(str(value).replace('+', ''))
    except (TypeError, ValueError):
        return None


def _format_ev_per_100(
    calculator: EVCalculator, moneyline: object, model_probability: float
) -> str:
    american_odds = _parse_american_odds(moneyline)
    if american_odds is None:
        return 'N/A'

    ev = calculator.calculate_ev(model_probability, american_odds, stake=100)
    return f'${ev:.2f}'


def enrich_live_odds_rows(games: list[dict], model_probability: float) -> list[dict]:
    calculator = EVCalculator()
    rows = []
    for game in games:
        row = dict(game)
        row['ev_per_100'] = _format_ev_per_100(calculator, row.get('moneyline'), model_probability)
        rows.append(row)
    return rows


def _recompute_ev(rows: list[dict], model_probability: float) -> list[dict]:
    calculator = EVCalculator()
    return [
        {
            **row,
            'ev_per_100': _format_ev_per_100(calculator, row.get('moneyline'), model_probability),
        }
        for row in rows
    ]


def merge_source_rows(
    existing_rows: list[dict], games: list[dict], source: str, model_probability: float
) -> list[dict]:
    rows_from_other_sources = [dict(row) for row in existing_rows if row.get('source') != source]
    re_enriched = _recompute_ev(rows_from_other_sources, model_probability)
    return re_enriched + enrich_live_odds_rows(games, model_probability)


@router.page('/odds')
def live_odds() -> None:
    with ui.column().classes('w-full p-6 gap-4'):
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
            ui.label('Live Odds').classes('text-2xl font-bold')

        with ui.row().classes('gap-3 items-center'):
            espn_btn = ui.button('Scrape ESPN', icon='refresh')
            dk_btn = ui.button('Scrape DraftKings', icon='refresh').props('outline')
            model_probability = ui.number(
                'Model win probability (%)', value=55.0, min=1, max=99, step=0.5
            ).classes('w-56')
            status = ui.label('').classes('text-gray-500 text-sm')

        table = ui.table(columns=COLUMNS, rows=[], row_key='matchup').classes('w-full')
        table.add_slot('body-cell-source', SOURCE_BADGE_SLOT)
        ui.input('Search').bind_value(table, 'filter').classes('w-64')

        def current_model_probability() -> float:
            try:
                value = float(model_probability.value or 55.0)
            except (TypeError, ValueError):
                value = 55.0
            return min(max(value, 1.0), 99.0) / 100

        async def scrape_espn() -> None:
            espn_btn.disable()
            status.text = 'Fetching ESPN odds...'
            try:
                scraper = EspnOddsScraper()
                games = await run.io_bound(scraper.scrape_nba_odds)
                rows = merge_source_rows(table.rows, games, 'ESPN', current_model_probability())
                table.update_rows(rows)
                status.text = f'Loaded {len(games)} ESPN games.'
            except Exception:
                status.text = 'Error fetching ESPN odds.'
            finally:
                espn_btn.enable()

        async def scrape_dk() -> None:
            dk_btn.disable()
            status.text = 'Fetching DraftKings odds (Selenium)...'
            try:
                live = LiveOddsScraper()
                games = await run.io_bound(live.scrape_draftkings_odds)
                rows = merge_source_rows(
                    table.rows, games, 'DraftKings', current_model_probability()
                )
                table.update_rows(rows)
                status.text = f'Loaded {len(games)} DraftKings games.'
            except Exception:
                status.text = 'Error fetching DraftKings odds.'
            finally:
                dk_btn.enable()

        espn_btn.on_click(scrape_espn)
        dk_btn.on_click(scrape_dk)
