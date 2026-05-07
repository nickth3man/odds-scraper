from __future__ import annotations

from nicegui import APIRouter, run, ui

from backend.enrichment import TeamEnrichmentService
from backend.models.odds_enrichment import merge_source_rows
from backend.scrapers import LiveOddsScraper
from backend.scrapers.espn import EspnOddsScraper

router = APIRouter()

COLUMNS = [
    {'name': 'event_id', 'label': 'Event ID', 'field': 'event_id', 'sortable': True},
    {'name': 'market_name', 'label': 'Market', 'field': 'market_name', 'sortable': True},
    {'name': 'bet_name', 'label': 'Bet', 'field': 'bet_name', 'align': 'left'},
    {'name': 'point', 'label': 'Line', 'field': 'point'},
    {'name': 'odds', 'label': 'Odds', 'field': 'odds'},
    {'name': 'true_prob', 'label': 'True Prob (%)', 'field': 'true_prob'},
    {'name': 'ev_per_100', 'label': 'EV / $100', 'field': 'ev_per_100'},
    {'name': 'source', 'label': 'Source', 'field': 'source', 'sortable': True},
]

SOURCE_BADGE_SLOT = """
<q-td :props="props">
    <q-badge :color="props.value === 'ESPN' ? 'red' : 'blue'" :label="props.value" />
</q-td>
"""


@router.page('/odds')
def live_odds() -> None:
    """Render the Live Odds page with multi-source scraping and EV analysis.

    Provides buttons to scrape ESPN and DraftKings odds and a searchable table
    with per-row expected-value enrichment for bet outcomes with valid data.
    """
    enrichment = TeamEnrichmentService()

    with ui.column().classes('w-full p-6 gap-4'):
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
            ui.label('Live Odds').classes('text-2xl font-bold')

        with ui.row().classes('gap-3 items-center'):
            espn_button = ui.button('Scrape ESPN', icon='refresh')
            draftkings_button = ui.button('Scrape DraftKings', icon='refresh').props('outline')
            status = ui.label('').classes('text-gray-500 text-sm')

        table = ui.table(columns=COLUMNS, rows=[], row_key='id').classes('w-full')
        ui.input('Search').bind_value(table, 'filter').classes('w-64')

        async def scrape_espn() -> None:
            """Scrape ESPN odds and merge them into the live table."""
            espn_button.disable()
            status.text = 'Fetching ESPN odds...'
            try:
                scraper = EspnOddsScraper()
                games = await run.io_bound(scraper.scrape_nba_odds)
                rows = await run.io_bound(
                    merge_source_rows, list(table.rows), games, 'ESPN', enrichment
                )
                table.update_rows(rows)
                status.text = f'Loaded {len(games)} ESPN games.'
            except Exception:
                status.text = 'Error fetching ESPN odds.'
            finally:
                espn_button.enable()

        async def scrape_draftkings() -> None:
            """
            Scrape live DraftKings odds and merge the enriched rows into the page table.
            
            Disables the DraftKings button while running, updates the status text to indicate progress or error, performs the DraftKings scrape and enrichment, replaces the table rows with the merged results on success, and re-enables the button when finished.
            """
            draftkings_button.disable()
            status.text = 'Fetching DraftKings odds (Playwright)...'
            try:
                scraper = LiveOddsScraper()
                games = await run.io_bound(scraper.scrape_draftkings_odds)
                rows = await run.io_bound(
                    merge_source_rows, list(table.rows), games, 'DraftKings', enrichment
                )
                table.update_rows(rows)
                status.text = f'Loaded {len(games)} DraftKings games.'
            except Exception:
                status.text = 'Error fetching DraftKings odds.'
            finally:
                draftkings_button.enable()

        espn_button.on_click(scrape_espn)
        draftkings_button.on_click(scrape_draftkings)
