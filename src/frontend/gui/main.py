from nicegui import app, ui

from backend.logging_config import configure_logging
from frontend.gui.pages import home, live_odds

configure_logging(level='INFO')

app.include_router(home.router)
app.include_router(live_odds.router)


def start() -> None:
    ui.run(title='Odds Scraper', port=8080, reload=False)


if __name__ in {'__main__', '__mp_main__'}:
    start()
