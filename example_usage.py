#!/usr/bin/env python3
"""
Example usage of the Sports Analytics tools
Run this to test everything works!
"""

from models.ev_calculator import EVCalculator
from odds_scraping.odds_comparison import OddsComparison
from odds_scraping.odds_scraper import OddsScraper


def main():
    print('\n' + '=' * 80)
    print('NBA ODDS SCRAPER & COMPARISON TOOL')
    print('=' * 80 + '\n')

    # ===== STEP 1: Scrape Odds =====
    print('STEP 1: Scraping odds from all sportsbooks...\n')
    scraper = OddsScraper(config_file='config.json')

    # Get odds from all books
    all_odds = scraper.get_all_odds()
    print(f'Total odds collected: {len(all_odds)}\n')

    # Export to CSV
    scraper.scraped_odds = all_odds
    scraper.export_to_csv('data/sample_odds_data.csv')

    # ===== STEP 2: Compare Odds =====
    print('\n' + '=' * 80)
    print('STEP 2: Comparing odds across sportsbooks...\n')

    comparator = OddsComparison()

    # Add odds from each sportsbook
    espn_odds = scraper.scrape_espn_odds()
    dk_odds = scraper.scrape_draftkings_odds()
    fd_odds = scraper.scrape_fanduel_odds()

    comparator.add_odds('ESPN', espn_odds)
    comparator.add_odds('DraftKings', dk_odds)
    comparator.add_odds('FanDuel', fd_odds)

    # Display comparison
    comparator.display_comparison('moneyline')

    # Export comparison to CSV
    comparator.find_best_odds('moneyline')
    comparator.export_to_csv('data/odds_comparison_results.csv')

    # ===== STEP 3: Calculate Expected Value =====
    print('=' * 80)
    print('STEP 3: Calculating Expected Value for sample bets...\n')

    ev_calc = EVCalculator()

    # Example bets (using your model predictions)
    sample_bets: list[dict[str, str | float | int]] = [
        {
            'team': 'OKC Thunder',
            'model_prob': 0.78,  # You think Thunder have 78% win prob
            'odds': -175,  # DraftKings is offering -175
        },
        {
            'team': 'Denver Nuggets',
            'model_prob': 0.62,
            'odds': 155,
        },
        {
            'team': 'Boston Celtics',
            'model_prob': 0.55,
            'odds': 155,
        },
    ]

    results = []
    for bet in sample_bets:
        result = ev_calc.evaluate_bet(
            team=str(bet['team']),
            model_prob=float(bet['model_prob']),
            american_odds=int(bet['odds']),
            stake=100,
        )
        results.append(result)

    # Display analysis
    ev_calc.display_bet_analysis(results)

    # ===== SUMMARY =====
    print('=' * 80)
    print('[DONE] ALL ANALYSIS COMPLETE!')
    print('=' * 80)
    print('\nFiles created:')
    print('  1. data/sample_odds_data.csv - All scraped odds')
    print('  2. data/odds_comparison_results.csv - Best odds comparison')
    print('\nNext steps:')
    print('  - Open Power BI Desktop')
    print('  - Get Data -> CSV')
    print('  - Select: data/odds_comparison_results.csv')
    print('  - Create visualizations!')
    print()


if __name__ == '__main__':
    main()
