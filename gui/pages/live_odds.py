from nicegui import APIRouter, run, ui

from odds_scraping.espn_scraper import EspnOddsScraper
from odds_scraping.live_odds_scraper import LiveOddsScraper

router = APIRouter()

COLUMNS = [
    {'name': 'date', 'label': 'Date', 'field': 'date', 'sortable': True},
    {'name': 'matchup', 'label': 'Matchup', 'field': 'matchup', 'align': 'left'},
    {'name': 'spread', 'label': 'Spread', 'field': 'spread'},
    {'name': 'moneyline', 'label': 'ML (Away)', 'field': 'moneyline'},
    {'name': 'home_moneyline', 'label': 'ML (Home)', 'field': 'home_moneyline'},
    {'name': 'over_under', 'label': 'O/U', 'field': 'over_under'},
    {'name': 'source', 'label': 'Source', 'field': 'source', 'sortable': True},
]


@router.page('/odds')
def live_odds() -> None:
    with ui.column().classes('w-full p-6 gap-4'):
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
            ui.label('Live Odds').classes('text-2xl font-bold')

        with ui.row().classes('gap-3 items-center'):
            espn_btn = ui.button('Scrape ESPN', icon='refresh')
            dk_btn = ui.button('Scrape DraftKings', icon='refresh').props('outline')
            status = ui.label('').classes('text-gray-500 text-sm')

        table = ui.table(columns=COLUMNS, rows=[], row_key='matchup').classes('w-full')
        table.add_slot(
            'body-cell-source',
            r'<td :props="props"><q-badge :color="props.value === \'ESPN\' ? \'red\' : \'blue\'">'
            r':label="props.value" /></q-badge></td>',
        )
        ui.input('Search').bind_value(table, 'filter').classes('w-64')

        async def scrape_espn() -> None:
            espn_btn.disable()
            status.text = 'Fetching ESPN odds...'
            scraper = EspnOddsScraper()
            games = await run.io_bound(scraper.scrape_nba_odds)
            existing = [r for r in table.rows if r.get('source') != 'ESPN']
            table.rows[:] = existing + games
            table.update()
            status.text = f'Loaded {len(games)} ESPN games.'
            espn_btn.enable()

        async def scrape_dk() -> None:
            dk_btn.disable()
            status.text = 'Fetching DraftKings odds (Selenium)...'
            live = LiveOddsScraper()
            games = await run.io_bound(live.scrape_draftkings_odds)
            existing = [r for r in table.rows if r.get('source') != 'DraftKings']
            table.rows[:] = existing + games
            table.update()
            status.text = f'Loaded {len(games)} DraftKings games.'
            dk_btn.enable()

        espn_btn.on_click(scrape_espn)
        dk_btn.on_click(scrape_dk)
