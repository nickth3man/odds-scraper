# 🏀 NBA Odds Scraper & Expected Value Calculator

A Python project for scraping NBA odds from multiple sportsbooks and calculating expected value for sports bets.

## 📊 Features

- **Sample Odds Scraper** — Multi-sportsbook odds collection (ESPN, DraftKings, FanDuel)
- **Live Odds Scraper** — Real-time scraping from ESPN's JSON API + DraftKings via Selenium
- **TLS Impersonation** — `curl_cffi` browser fingerprinting bypasses bot-detection on protected endpoints
- **Fast JSON Parsing** — `orjson` replaces stdlib `json` for faster response deserialization
- **HTML Parsing** — `parsel` CSS-selector parser extracts DraftKings odds without chained Selenium queries
- **Unified Schema** — `OddsComparison` accepts output from both scrapers transparently
- **Odds Comparison** — Find the best lines across sportsbooks with correct American odds logic
- **Expected Value Calculator** — Identify profitable betting opportunities using American odds math
- **Kelly Criterion** — Optimal bet sizing for bankroll management
- **CSV Export** — Power BI-ready data files

## 🛠️ Tech Stack

| Tool                | Purpose                                          |
| ------------------- | ------------------------------------------------ |
| Python **3.12+**    | Runtime                                          |
| **uv**              | Package manager                                  |
| **ruff**            | Linter + formatter                               |
| **ty**              | Type checker                                     |
| selenium            | Browser automation (DraftKings)                  |
| httpx               | Async-capable HTTP client with retry logic       |
| curl-cffi           | TLS fingerprint impersonation (anti-bot bypass)  |
| orjson              | Fast JSON serialization/deserialization          |
| parsel              | CSS/XPath HTML parsing (Scrapy-style)            |
| tenacity            | Retry logic with exponential backoff             |
| fake-useragent      | Rotating User-Agent strings                      |
| courlan             | Domain extraction for per-domain rate limiting   |
| pandas              | Data manipulation & CSV export                   |
| pytest              | Testing framework                                |

## 📁 Project Structure

```
odds-scraper/
├── odds_scraping/
│   ├── __init__.py
│   ├── odds_scraper.py          # Sample odds data provider
│   ├── odds_comparison.py       # Cross-sportsbook comparison (unified schema)
│   ├── http_client.py           # Resilient HTTP client (retry, rate-limit, UA rotation)
│   └── live_odds_scraper.py     # Live ESPN & DraftKings scraper
├── models/
│   └── ev_calculator.py         # Expected Value & Kelly Criterion
├── data/
│   ├── sample_odds_data.csv
│   ├── odds_comparison_results.csv
│   └── nba_standings_2025_26.csv
├── fixtures/                    # HTML/JSON fixtures for offline tests
├── tests/                       # pytest test suite (62 tests)
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
- Chrome (for DraftKings live scraping — Selenium Manager auto-downloads ChromeDriver)

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
uv run pytest            # Run tests (62 tests)
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
  Recommendation:        [BET] Positive EV
```

### Expected Value Analysis

```python
from odds_scraping.live_odds_scraper import LiveOddsScraper
from odds_scraping.odds_comparison import OddsComparison
from models.ev_calculator import EVCalculator

# Scrape live odds from ESPN (no browser needed)
scraper = LiveOddsScraper()
games = scraper.scrape_espn_nba_odds()

# Compare odds across sportsbooks
# OddsComparison accepts output from both OddsScraper and LiveOddsScraper
comparison = OddsComparison()
comparison.add_odds('ESPN', games)
best = comparison.find_best_odds('moneyline')

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
#   'recommendation': '[BET] Positive EV'
# }
```

### Fast JSON + TLS Impersonation

```python
from odds_scraping.http_client import HttpClient

http = HttpClient()

# Standard request — uses orjson for fast parsing
data = http.get_json('https://site.api.espn.com/apis/v2/sports/basketball/nba/odds')

# TLS impersonation — presents a real Chrome fingerprint (requires curl_cffi)
data = http.get_json(
    'https://sportsbook.draftkings.com/api/odds/v2/odds',
    impersonate='chrome110',
)

http.close()
```

### Parse DraftKings HTML with parsel (no browser)

```python
from odds_scraping.live_odds_scraper import LiveOddsScraper

# Works with any saved HTML — useful for testing or offline processing
with open('fixtures/dk-game-lines.html') as f:
    html = f.read()

games = LiveOddsScraper.parse_draftkings_html(html)
# Returns list of game dicts with home_team, away_team, spread, moneyline, over_under
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
| `uv run pytest`        | Run 62 tests                 |
| `uv lock --upgrade`    | Update all deps to latest    |

Dependencies use `>=` constraints in `pyproject.toml`. Exact versions are pinned in `uv.lock` (commit this file).

### Architecture

```
LiveOddsScraper
├── scrape_espn_nba_odds()          ESPN header API → JSON
│   └── _scrape_espn_scoreboard_fallback()   scoreboard API fallback
└── scrape_draftkings_nba_odds()    Selenium → page_source
    └── _parse_draftkings_games()
        ├── parse_draftkings_html() parsel path (fast, testable)  ← preferred
        ├── _parse_draftkings_cb_market()   Selenium cb-market path
        └── _parse_draftkings_event_cells() Selenium legacy fallback

HttpClient
├── get()         httpx + tenacity retry + per-domain rate limiting + UA rotation
└── get_json()    orjson fast parse; curl_cffi impersonation when impersonate= set

OddsComparison
└── find_best_odds()   _normalize_game() maps both scraper schemas → unified view
```

### External Data Caveats

- **Sportsbook pages can change**: DraftKings selectors are parsed defensively with three fallback layers (parsel → cb-market Selenium → event-cell Selenium), but DOM changes or geo/bot gating can still hide odds
- **ESPN odds endpoints are unofficial**: The live scraper calls ESPN's header API first and falls back to the scoreboard API with the same normalized output schema; both endpoints can change without notice
- **curl_cffi impersonation**: Effective against TLS fingerprint checks, not against login walls or account-based rate limits

## 📈 Future Enhancements

- [ ] Add more sportsbooks (BetMGM, PointsBet)
- [ ] Multi-sport support (NFL, MLB, NHL)
- [ ] Backtesting framework
- [ ] Web dashboard
- [ ] Machine learning win probability model
- [ ] Automated daily scraping schedule
- [ ] Playwright network interception replacing Selenium

## ⚠️ Important Notes

- **Legal**: Web scraping odds is legal in most jurisdictions — check local laws
- **Rate Limiting**: The `HttpClient` enforces per-domain minimum delays automatically
- **Terms of Service**: Review each site's ToS before scraping
- **Not Gambling Advice**: This is an analytical tool, not betting recommendations

## 🤝 Contributing

Found a bug or want to improve it? PRs welcome — just make sure `ruff check .` and `uv run pytest` pass.

---

Built with ❤️ for sports analytics enthusiasts
