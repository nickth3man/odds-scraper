from __future__ import annotations

from nicegui import APIRouter, run, ui

from backend.enrichment import TeamEnrichmentService
from backend.models.odds_enrichment import merge_source_rows, recompute_expected_value
from backend.scrapers import LiveOddsScraper
from backend.scrapers.espn import EspnOddsScraper

router = APIRouter()

COLUMNS = [
    {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
    {'name': 'matchup', 'label': 'Matchup', 'field': 'matchup', 'align': 'left'},
    {'name': 'spread', 'label': 'Spread', 'field': 'spread'},
    {'name': 'moneyline', 'label': 'ML (Away)', 'field': 'moneyline'},
    {'name': 'home_moneyline', 'label': 'ML (Home)', 'field': 'home_moneyline'},
    {'name': 'over_under', 'label': 'O/U', 'field': 'over_under'},
    {
        'name': 'expected_value_per_100',
        'label': 'EV / $100 (Away)',
        'field': 'expected_value_per_100',
    },
    {
        'name': 'home_expected_value_per_100',
        'label': 'EV / $100 (Home)',
        'field': 'home_expected_value_per_100',
    },
    {'name': 'source', 'label': 'Source', 'field': 'source', 'sortable': True},
    {'name': 'home_record', 'label': 'Record (H)', 'field': 'home_record'},
    {'name': 'away_record', 'label': 'Record (A)', 'field': 'away_record'},
    {'name': 'home_win_pct', 'label': 'Win% (Model)', 'field': 'home_win_pct'},
]

SOURCE_BADGE_SLOT = """
<q-td :props="props">
    <q-badge :color="props.value === 'ESPN' ? 'red' : 'blue'" :label="props.value" />
</q-td>
"""


@router.page('/odds')
def live_odds() -> None:
    """Render the Live Odds page with multi-source scraping and EV analysis.

    Provides buttons to scrape ESPN and DraftKings odds, a probability slider
    for EV computation, and a searchable table with per-row expected-value
    enrichment for both away and home moneylines.
    """
    enrichment = TeamEnrichmentService()

    with ui.column().classes('w-full p-6 gap-4'):
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
            ui.label('Live Odds').classes('text-2xl font-bold')

        with ui.row().classes('gap-3 items-center'):
            espn_button = ui.button('Scrape ESPN', icon='refresh')
            draftkings_button = ui.button('Scrape DraftKings', icon='refresh').props('outline')
            model_probability = ui.number(
                'Model win probability (%)', value=55.0, min=1, max=99, step=0.5
            ).classes('w-56')
            status = ui.label('').classes('text-gray-500 text-sm')

        table = ui.table(columns=COLUMNS, rows=[], row_key='matchup').classes('w-full')
        table.add_slot('body-cell-source', SOURCE_BADGE_SLOT)
        ui.input('Search').bind_value(table, 'filter').classes('w-64')

        def current_model_probability() -> float:
            """Read the current model probability slider value, clamped to [1, 99]%.

            Returns:
                Win probability as a float between 0.0 and 1.0.
            """
            try:
                value = float(model_probability.value or 55.0)
            except (TypeError, ValueError):
                value = 55.0
            return min(max(value, 1.0), 99.0) / 100

        async def scrape_espn() -> None:
            """Scrape ESPN odds and merge them into the live table."""
            espn_button.disable()
            status.text = 'Fetching ESPN odds...'
            try:
                scraper = EspnOddsScraper()
                games = await run.io_bound(scraper.scrape_nba_odds)
                prob = current_model_probability()
                rows = await run.io_bound(
                    merge_source_rows, list(table.rows), games, 'ESPN', prob, enrichment
                )
                table.update_rows(rows)
                status.text = f'Loaded {len(games)} ESPN games.'
            except Exception:
                status.text = 'Error fetching ESPN odds.'
            finally:
                espn_button.enable()

        async def scrape_draftkings() -> None:
            """
            Scrape live DraftKings odds and merge the results into the page's table using the current model probability and enrichment.

            This updates the UI state: disables the DraftKings button while running, sets the status text to indicate progress or error, and replaces the table rows with the merged/enriched rows on success. No value is returned.
            """
            draftkings_button.disable()
            status.text = 'Fetching DraftKings odds (Playwright)...'
            try:
                scraper = LiveOddsScraper()
                games = await run.io_bound(scraper.scrape_draftkings_odds)
                prob = current_model_probability()
                rows = await run.io_bound(
                    merge_source_rows, list(table.rows), games, 'DraftKings', prob, enrichment
                )
                table.update_rows(rows)
                status.text = f'Loaded {len(games)} DraftKings games.'
            except Exception:
                status.text = 'Error fetching DraftKings odds.'
            finally:
                draftkings_button.enable()

        async def on_probability_change(_e: object) -> None:
            if table.rows:
                updated = await run.io_bound(
                    recompute_expected_value, list(table.rows), current_model_probability()
                )
                table.update_rows(updated)

        model_probability.on_value_change(on_probability_change)

        espn_button.on_click(scrape_espn)
        draftkings_button.on_click(scrape_draftkings)
