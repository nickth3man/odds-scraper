#!/usr/bin/env python3
"""
Live Odds Scraper Example
Fetches REAL, LIVE odds from ESPN and DraftKings
Great for playoffs!
"""

from odds_scraping.live_odds_scraper import LiveOddsScraper


def main():
    print('\n' + '=' * 100)
    print('LIVE NBA ODDS SCRAPER - ESPN & DRAFTKINGS')
    print('=' * 100 + '\n')

    scraper = LiveOddsScraper()

    # Get all games from both sources
    all_games = scraper.get_all_games()

    # Export combined results
    if all_games:
        df = scraper.export_to_csv(all_games, 'data/live_odds_all_sources.csv')

        print('=' * 100)
        print('SUMMARY')
        print('=' * 100)
        print(f'Total games found: {len(df)}')
        print(f'Sources: {df["source"].unique().tolist()}')
        print('\nFile saved: data/live_odds_all_sources.csv')
        print('\nYou can now:')
        print('  1. Open in Power BI')
        print('  2. Compare odds across sportsbooks')
        print('  3. Calculate Expected Value')
        print('=' * 100 + '\n')
    else:
        print('[ERROR] No games found from any source')
        print('\nTroubleshooting:')
        print('  - Check if there are live games today')
        print('  - Check your internet connection')
        print('  - ESPN/DraftKings may have changed their website structure')
        print()


if __name__ == '__main__':
    main()
