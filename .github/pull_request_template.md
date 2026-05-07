## Summary

-

## Testing

- [ ] `uv run ruff format --check .`
- [ ] `uv run ruff check .`
- [ ] `uv run ty check`
- [ ] `uv run pyright`
- [ ] `uv run pytest`

## Scraper and UX impact

- [ ] No scraper behavior changed
- [ ] ESPN behavior changed
- [ ] DraftKings behavior changed
- [ ] NiceGUI behavior changed
- [ ] I updated or added offline fixtures for parser changes

## Data/modeling impact

- [ ] No historical data/modeling behavior changed
- [ ] Rolling features are leak-free and use only prior-game data
- [ ] Validation is chronological or walk-forward
- [ ] Backtests use odds snapshots available at the simulated bet time
- [ ] Metrics include Brier score/log-loss when probability models changed
- [ ] No raw datasets or generated model artifacts are included

## Notes for reviewers

-
