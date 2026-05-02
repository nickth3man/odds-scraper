import logging

from nicegui import app, ui

logging.basicConfig(level=logging.INFO)

from gui.pages import ev_calc, home, live_odds

app.include_router(home.router)
app.include_router(live_odds.router)
app.include_router(ev_calc.router)


def start() -> None:
    ui.run(title='Odds Scraper', port=8080, reload=False)


if __name__ in {'__main__', '__mp_main__'}:
    start()
