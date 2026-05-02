from nicegui import APIRouter, ui

from models.ev_calculator import EVCalculator

router = APIRouter()

RESULT_COLUMNS = [
    {'name': 'team', 'label': 'Team', 'field': 'team', 'align': 'left'},
    {'name': 'model_prob', 'label': 'Model Prob', 'field': 'model_prob'},
    {'name': 'book_prob', 'label': 'Book Prob', 'field': 'book_prob'},
    {'name': 'american_odds', 'label': 'Odds', 'field': 'american_odds'},
    {'name': 'ev_per_stake', 'label': 'EV / $100', 'field': 'ev_per_stake'},
    {'name': 'ev_percent', 'label': 'EV %', 'field': 'ev_percent'},
    {'name': 'kelly', 'label': 'Kelly %', 'field': 'kelly'},
    {'name': 'recommendation', 'label': 'Recommendation', 'field': 'recommendation', 'align': 'left'},
]


@router.page('/ev')
def ev_calculator() -> None:
    calc = EVCalculator()

    with ui.column().classes('w-full p-6 gap-6'):
        with ui.row().classes('items-center gap-2'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/')).props('flat round')
            ui.label('EV Calculator').classes('text-2xl font-bold')

        with ui.card().classes('w-full max-w-lg'):
            ui.label('Bet Parameters').classes('text-lg font-semibold mb-2')

            team_input = ui.input('Team Name', placeholder='e.g. OKC Thunder').classes('w-full')
            prob_input = ui.number('Model Win Probability (%)', value=55.0, min=1, max=99, step=0.5).classes('w-full')
            odds_input = ui.number('American Odds', value=-110, step=1).classes('w-full')
            stake_input = ui.number('Stake ($)', value=100, min=1, step=10).classes('w-full')

            error_label = ui.label('').classes('text-red-500 text-sm')
            calc_btn = ui.button('Calculate EV', icon='calculate').classes('mt-2')

        table = ui.table(columns=RESULT_COLUMNS, rows=[], row_key='team').classes('w-full')

        def calculate() -> None:
            team = team_input.value or 'Unknown'
            try:
                model_prob = float(prob_input.value) / 100
                american_odds = int(odds_input.value)
                stake = float(stake_input.value)
            except (TypeError, ValueError):
                error_label.text = 'Please fill in all fields with valid numbers.'
                return

            error_label.text = ''
            result = calc.evaluate_bet(team, model_prob, american_odds, stake)
            kelly_pct = calc.kelly_criterion(model_prob, american_odds)
            row = {**result, 'kelly': f'{kelly_pct * 100:.2f}%'}
            table.add_row(row)

        calc_btn.on_click(calculate)
        ui.button('Clear', on_click=lambda: table.update_rows([])).props('flat')
