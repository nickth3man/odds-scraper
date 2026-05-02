# 🏀 NBA Odds Scraper & Expected Value Calculator

A Python project for scraping NBA odds from multiple sportsbooks and calculating expected value for sports bets.

## 📊 Features

- **Sample Odds Scraper** — Multi-sportsbook odds collection (ESPN, DraftKings, FanDuel)
- **Live Odds Scraper** — Real-time scraping from ESPN & DraftKings (HTML/Selenium)
- **Odds Comparison** — Find the best lines across sportsbooks
- **Expected Value Calculator** — Identify profitable betting opportunities using American odds math
- **Kelly Criterion** — Optimal bet sizing for bankroll management
- **CSV Export** — Power BI-ready data files

## 🛠️ Tech Stack

| Tool              | Purpose                    |
| ----------------- | -------------------------- |
| Python **3.12+**  | Runtime                    |
| **uv**            | Package manager            |
| **ruff**          | Linter + formatter         |
| **ty**            | Type checker               |
| selenium          | Browser automation (DraftKings) |
| pandas            | Data manipulation & CSV    |
| requests          | HTTP client                |
| pytest            | Testing framework          |

## 📁 Project Structure

```
odds-scraper/
├── odds_scraping/
│   ├── __init__.py
│   ├── odds_scraper.py          # Sample odds data provider
│   ├── odds_comparison.py       # Cross-sportsbook comparison
│   └── live_odds_scraper.py     # Live ESPN & DraftKings scraper
├── models/
│   └── ev_calculator.py         # Expected Value & Kelly Criterion
├── data/
│   ├── sample_odds_data.csv
│   ├── odds_comparison_results.csv
│   └── nba_standings_2025_26.csv
├── example_usage.py             # Sample scraper demo
├── live_example.py              # Live odds demo
├── config.json                  # Sportsbook configuration
├── pyproject.toml               # Project metadata & tool config
├── uv.lock                      # Dependency lock file
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)

### Setup

```bash
# Clone and enter the project
git clone https://github.com/yourusername/odds-scraper.git
cd odds-scraper

# Install all dependencies (creates .venv + uv.lock)
uv sync

# Run the sample demo
uv run python example_usage.py

# Run live scraping (requires Chrome + working selectors)
uv run python live_example.py
```

### Quality Checks

```bash
uv run ruff check .      # Lint
uv run ruff check --fix  # Auto-fix
uv run ty check          # Type check
uv run pytest            # Run tests
```

## 📊 Usage

### Sample Odds Demo

```bash
uv run python example_usage.py
```

Output:
```
OKC Thunder vs Boston Celtics
  Date: 2026-04-30
  Best: DraftKings (-175)
    ESPN: -180
    DraftKings: -175
    FanDuel: -178

TEAM: OKC Thunder
  Model Probability:     78.0%
  Sportsbook Probability: 63.6%
  EV per $100:           $22.57
  Recommendation:        ✅ BET (Positive EV)
```

### Expected Value Analysis

```python
from odds_scraping.live_odds_scraper import LiveOddsScraper
from models.ev_calculator import EVCalculator

# Scrape live odds
scraper = LiveOddsScraper()
games = scraper.get_all_games()

# Calculate expected value
ev_calc = EVCalculator()
result = ev_calc.evaluate_bet(
    team='OKC Thunder',
    model_prob=0.78,       # Your win probability prediction
    american_odds=-175,    # Sportsbook odds
    stake=100              # Wager amount
)

print(result)
# {
#   'team': 'OKC Thunder',
#   'model_prob': '78.0%',
#   'book_prob': '63.6%',
#   'ev_per_stake': '$22.57',
#   'recommendation': '✅ BET (Positive EV)'
# }
```

## ⚙️ Configuration

```json
{
  "sportsbooks": {
    "espn": { "enabled": true },
    "draftkings": { "enabled": true },
    "fanduel": { "enabled": true }
  }
}
```

## 🧪 Development

### Toolchain

| Command                | What it does                 |
| ---------------------- | ---------------------------- |
| `uv sync`              | Install all dependencies     |
| `uv run ruff check .`  | Lint the codebase            |
| `uv run ruff format .` | Auto-format code             |
| `uv run ty check`      | Type check                   |
| `uv run pytest`        | Run tests with coverage      |
| `uv lock --upgrade`    | Update all deps to latest    |

Dependencies use `>=` constraints in `pyproject.toml`. Exact versions are pinned in `uv.lock` (commit this file).

### External Data Caveats

- **Sportsbook pages can change**: DraftKings selectors are parsed defensively and fall back to `'N/A'` per market, but sportsbook DOM changes or geo/bot gating can still hide odds
- **ESPN odds endpoints are unofficial**: The live scraper uses ESPN's header API first and falls back to ESPN's scoreboard API with the same normalized output schema, but both endpoints can change without public notice

## 📈 Future Enhancements

- [ ] Add more sportsbooks (BetMGM, PointsBet)
- [ ] Multi-sport support (NFL, MLB, NHL)
- [ ] Backtesting framework
- [ ] Web dashboard
- [ ] Machine learning win probability model
- [ ] Automated daily scraping schedule

## ⚠️ Important Notes

- **Legal**: Web scraping odds is legal in most jurisdictions — check local laws
- **Rate Limiting**: Don't make too many requests in short succession
- **Terms of Service**: Review each site's ToS before scraping
- **Not Gambling Advice**: This is an analytical tool, not betting recommendations

## 🤝 Contributing

Found a bug or want to improve it? PRs welcome — just make sure `ruff check .` and `ty check` pass.

---

Built with ❤️ for sports analytics enthusiasts
