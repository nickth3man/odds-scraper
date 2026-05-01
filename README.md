# 🏀 Sports Analytics - NBA Odds Scraper & Expected Value Calculator

A complete Python project for scraping real NBA odds from multiple sportsbooks and calculating expected value for sports bets.

## 📊 Features

- **Odds Scraper**: Collects live odds from ESPN and DraftKings
- **Odds Comparison**: Finds the best lines across multiple sportsbooks
- **Expected Value Calculator**: Identifies profitable betting opportunities
- **Power BI Integration**: Export data for visualization and analysis
- **Real-time Data**: Scrapes current playoff and regular season games

## 🛠️ Technologies Used

- **Python 3.9+**
- **BeautifulSoup4** - Web scraping
- **Selenium** - Browser automation for DraftKings
- **Pandas** - Data manipulation
- **Requests** - HTTP requests

## 📁 Project Structure

sports-analytics/ ├── odds_scraping/ │ ├── odds_scraper.py # Scrapes sample odds │ ├── odds_comparison.py # Compares odds across books │ └── live_odds_scraper.py # Scrapes LIVE ESPN & DraftKings ├── models/ │ └── ev_calculator.py # Expected Value calculations ├── data/ │ ├── sample_odds_data.csv │ └── nba_standings_2025_26.csv ├── example_usage.py # Sample scraper example ├── live_example.py # Live odds example ├── config.json # Configuration ├── requirements.txt # Dependencies └── README.md # This file

## 🚀 Quick Start

### Installation

1. Clone the repository

```bash
git clone https://github.com/yourusername/python-projects-.git
cd sports-analytics

2. Create Virtual Envirnoment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

Usages:
 Run sample odds scrapper
python3 example_usage.py

Scrape LIVE odds from ESPN & DraftKings:
python3 live_example.py

Sample Output:
OKC Thunder @ Boston Celtics
  Spread: -7.5
  Moneyline: -175
  Over/Under: 214.5

Expected Value Calculation:
Team: OKC Thunder
Model Probability: 78.0%
Sportsbook Probability: 72.0%
EV per $100: $12.50
Recommendation: ✅ BET (Positive EV)

How It Works

1. Scrape Odds

Collects odds from ESPN using BeautifulSoup
Scrapes DraftKings using Selenium (JavaScript rendering)
Supports moneyline, spread, and over/under
2. Compare Odds

Finds best odds across all sportsbooks
Identifies line discrepancies
Exports to CSV
3. Calculate Expected Value

Converts American odds to implied probability
Compares model predictions to sportsbook odds
Calculates EV and ROI
Applies Kelly Criterion for bankroll management
4. Export to Power BI

CSV files ready for visualization
Create dashboards of odds comparisons
Track ROI over time
💡 Use Cases

Identify +EV Bets: Find bets where your model gives better probability than the sportsbook
Line Shopping: Compare odds across multiple books to get the best value
Portfolio Tracking: Monitor your betting performance over time
Data Analysis: Analyze historical odds and outcomes
📈 Power BI Integration

Open Power BI Desktop
Click Get Data → Text/CSV
Select data/live_odds_all_sources.csv
Create visualizations:
Best odds by sportsbook
Spread comparison charts
Over/under trends

Example Analysis
from odds_scraping.live_odds_scraper import LiveOddsScraper
from models.ev_calculator import EVCalculator

# Scrape live odds
scraper = LiveOddsScraper()
games = scraper.get_all_games()

# Calculate expected value
ev_calc = EVCalculator()
result = ev_calc.evaluate_bet(
    team="OKC Thunder",
    model_prob=0.78,  # Your prediction
    american_odds=-175,  # Sportsbook odds
    stake=100
)

print(result)
# Output:
# {
#   'team': 'OKC Thunder',
#   'model_prob': '78.0%',
#   'book_prob': '71.4%',
#   'ev_per_stake': '$12.50',
#   'recommendation': '✅ BET'
# }
Configuration:
{
  "sportsbooks": {
    "espn": {"enabled": true},
    "draftkings": {"enabled": true},
    "fanduel": {"enabled": true}
  }
Important Notes:
Legal: Web scraping odds is legal in most jurisdictions
Rate Limiting: Don't make too many requests in short time
Terms of Service: Check each site's ToS before scraping
No Betting Required: This is analytical, not gambling advice

Future Enhancements:
Add more sportsbooks (FanDuel, BetMGM, etc.)
 Implement multi-sport support (NFL, MLB, NHL)
 Add backtesting framework
 Create web dashboard
 Machine learning win probability model
 Automated daily scraping schedule

Contributing:
Found a bug or want to improve it? Feel free to:

Fork the repo
Create a feature branch
Submit a pull request

Questions or suggestions? Reach out!

Built with ❤️ for sports analytics enthusiasts

```
