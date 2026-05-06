import pandas as pd
from loguru import logger


def _normalize_game(game: dict) -> dict:
    """
    Produce a normalized game record that always contains `team` and `opponent` keys.

    Accepts game records using either a canonical schema (`team`, `opponent`, `sportsbook`)
    or alternate scraper schemas that use `home_team`, `away_team`, and `source`.
    If `sportsbook` is missing but `source` exists, `source` is copied to `sportsbook`.

    Parameters:
        game (dict): A game record from a scraper; may use keys like `team`/`opponent`
            or `home_team`/`away_team` and optionally `source`.

    Returns:
        dict: A copy of the input record with guaranteed `team` and `opponent` keys
            and `sportsbook` set when `source` was provided and `sportsbook` was not.
    """
    if 'team' in game and 'opponent' in game:
        return game  # already canonical
    normalized = dict(game)
    normalized['team'] = game.get('away_team', game.get('home_team', 'Unknown'))
    normalized['opponent'] = game.get('home_team', 'Unknown')
    # Map 'source' -> 'sportsbook' if present
    if 'source' in normalized and 'sportsbook' not in normalized:
        normalized['sportsbook'] = normalized['source']
    return normalized


class OddsComparison:
    """Compare odds across multiple sportsbooks"""

    def __init__(self):
        """Initialize the odds comparison tool"""
        self.odds_by_sportsbook = {}
        self.comparison_results = []

    def add_odds(self, sportsbook: str, odds_list: list[dict]):
        """
        Store odds for a sportsbook, replacing any previously stored odds for that sportsbook.

        Parameters:
            sportsbook (str): Identifier for the sportsbook.
            odds_list (list[dict]): List of odds entry dictionaries to associate with the sportsbook.
        """
        self.odds_by_sportsbook[sportsbook] = odds_list
        logger.info('Odds added', sportsbook=sportsbook, count=len(odds_list))

    def find_best_odds(self, bet_type: str = 'moneyline'):
        """
        Compute the best odds for each matchup across all stored sportsbooks.

        For each matchup the method returns a dict containing:
        - `date`: matchup date from the normalized game record
        - `team`: home/away team designated as `team` in the normalized record
        - `opponent`: opponent team from the normalized record
        - `best_sportsbook`: sportsbook offering the best numeric odds for the requested `bet_type`
        - `best_odds`: numeric odds value from `best_sportsbook`
        - `bet_type`: the odds type used to compare (the `bet_type` parameter)
        - additional keys of the form `"{sportsbook}_odds"` containing each sportsbook's numeric odds for the matchup

        The method also updates `self.comparison_results` with the computed list.

        Parameters:
            bet_type (str): The odds field name to compare (e.g., `'moneyline'`).

        Returns:
            list[dict]: A list of result dictionaries described above; an empty list if no odds have been added.
        """
        results = []

        if not self.odds_by_sportsbook:
            return results

        # Get all games
        first_sportsbook_odds = next(iter(self.odds_by_sportsbook.values()))
        games = {}

        for raw_game in first_sportsbook_odds:
            game = _normalize_game(raw_game)
            game_key = f'{game["team"]} vs {game["opponent"]}'
            if game_key not in games:
                games[game_key] = {
                    'date': game['date'],
                    'team': game['team'],
                    'opponent': game['opponent'],
                    'odds': {},
                }

        # Collect odds from all sportsbooks
        for sportsbook, odds_list in self.odds_by_sportsbook.items():
            for raw_game in odds_list:
                game = _normalize_game(raw_game)
                game_key = f'{game["team"]} vs {game["opponent"]}'
                if game_key in games:
                    games[game_key]['odds'][sportsbook] = game[bet_type]

        # Find best odds for each game
        for _game_key, game_data in games.items():
            best_sportsbook = None
            best_value = None

            for sportsbook, odds in game_data['odds'].items():
                if best_value is None:
                    best_sportsbook = sportsbook
                    best_value = odds
                else:
                    # American odds: less-negative beats more-negative (e.g. -105 > -110);
                    # among positives, higher is better (e.g. +150 > +120).
                    # Sorting by numeric value handles both cases correctly.
                    if odds > best_value:
                        best_sportsbook = sportsbook
                        best_value = odds
            result = {
                'date': game_data['date'],
                'team': game_data['team'],
                'opponent': game_data['opponent'],
                'best_sportsbook': best_sportsbook,
                'best_odds': best_value,
                'bet_type': bet_type,
            }

            # Add all sportsbook odds to result
            for sportsbook, odds in game_data['odds'].items():
                result[f'{sportsbook}_odds'] = odds

            results.append(result)

        self.comparison_results = results
        return results

    def display_comparison(self, bet_type: str = 'moneyline'):
        """
        Compute the best-odds comparison for the specified bet type, store the results on the instance, and emit a debug log with summary information.

        This calls find_best_odds(bet_type) to build and assign comparison results to self.comparison_results, then logs a debug event containing the bet type and the number of matchups produced.

        Parameters:
            bet_type (str): The betting market to compare (e.g., 'moneyline').
        """
        results = self.find_best_odds(bet_type)

        logger.debug('Comparison display', bet_type=bet_type, game_count=len(results))

    def export_to_csv(self, filename='data/odds_comparison_results.csv'):
        """
        Write the stored comparison results to a CSV file.

        If there are no comparison results, the method does nothing. When results exist, they are converted into a table and written to `filename` with no row index.

        Parameters:
            filename (str): Path to the output CSV file. Defaults to 'data/odds_comparison_results.csv'.
        """
        if not self.comparison_results:
            logger.warning('No comparison results to display')
            return

        comparison_table = pd.DataFrame(self.comparison_results)
        comparison_table.to_csv(filename, index=False)
        logger.info(
            'Comparison exported',
            filename=filename,
            game_count=len(comparison_table),
            action='export',
        )
