from loguru import logger

from backend.models.domain import Market, NormalizedOdds


class EVCalculator:
    """Calculate Expected Value for sports bets"""

    def __init__(self):
        """Initialize expected value calculator"""
        self.bets = []

    def convert_american_to_probability(self, american_odds: int | float) -> float:
        """
        Convert American-style betting odds to an implied probability between 0 and 1.
        
        Parameters:
            american_odds (int | float): American odds (negative for favorites, positive for underdogs). A value of 0 is treated as a guaranteed outcome.
        
        Returns:
            float: Implied probability in the range [0.0, 1.0].
        
        Raises:
            TypeError: If `american_odds` is not an int or float.
        """
        if not isinstance(american_odds, (int, float)):
            raise TypeError(f'american_odds must be numeric, got {type(american_odds).__name__}')
        if american_odds == 0:
            return 1.0
        if american_odds < 0:
            probability = abs(american_odds) / (abs(american_odds) + 100)
        else:
            probability = 100 / (american_odds + 100)

        return probability

    def calculate_expected_value(
        self, model_probability: float, american_odds: int | float, stake: float = 100
    ) -> float:
        """
        Compute the expected monetary value of a single bet.
        
        Calculates expected value as (model_probability * payout) - ((1 - model_probability) * stake),
        where `payout` is the profit on a winning bet derived from American odds.
        
        Args:
            model_probability (float): Predicted probability of winning, between 0.0 and 1.0.
            american_odds (int | float): Sportsbook American odds (e.g., -110, 150).
            stake (float): Amount wagered in dollars.
        
        Returns:
            float: Expected value in dollars (positive means expected profit, negative means expected loss).
        """
        # Convert odds to payout
        if american_odds < 0:
            payout = stake * (100 / abs(american_odds))
        else:
            payout = stake * (american_odds / 100)

        # Calculate expected value
        win_value = model_probability * payout
        loss_value = (1 - model_probability) * stake
        expected_value = win_value - loss_value

        return expected_value

    def calculate_expected_value_from_odds(
        self, model_probability: float, odds: NormalizedOdds, stake: float = 100
    ) -> float:
        """
        Calculate the expected monetary value of placing a stake on an outcome described by a NormalizedOdds object.
        
        Parameters:
            model_probability (float): The model's estimated probability of the outcome occurring (0.0–1.0).
            odds (NormalizedOdds): An object providing market odds; the method uses the `american` field from this object.
            stake (float): The wager amount in dollars (default is 100).
        
        Returns:
            float: Expected value in dollars (positive indicates an expected profit, negative indicates an expected loss).
        """
        return self.calculate_expected_value(model_probability, odds.american, stake)

    def evaluate_bet(
        self, team: str, model_probability: float, american_odds: int, stake: float = 100
    ) -> dict:
        """
        Evaluate a proposed bet, append the formatted analysis to self.bets, and return the analysis dictionary.
        
        The returned dictionary contains human-readable, formatted fields suitable for reporting.
        
        Returns:
            dict: Analysis with keys:
                - team (str): Team identifier passed to the function.
                - model_probability (str): Model probability formatted as a percentage (e.g., "42.5%").
                - sportsbook_probability (str): Sportsbook implied probability formatted as a percentage.
                - american_odds (int): The American odds used for the evaluation.
                - expected_value_per_stake (str): Expected value per provided stake formatted as dollars (e.g., "$12.34").
                - expected_value_percent (str): Expected value expressed as a percentage of the stake.
                - recommendation (str): One of:
                    "[BET] Positive Expected Value",
                    "[PASS] Neutral Expected Value",
                    "[PASS] Slight Negative Expected Value",
                    "[AVOID] Strong Negative Expected Value".
        """
        sportsbook_probability = self.convert_american_to_probability(american_odds)
        expected_value = self.calculate_expected_value(model_probability, american_odds, stake)
        expected_value_percent = (expected_value / stake) * 100 if stake != 0 else 0.0

        # Determine recommendation
        if expected_value > 0:
            recommendation = '[BET] Positive Expected Value'
        elif expected_value == 0.0:
            recommendation = '[PASS] Neutral Expected Value'
        elif expected_value < -5:
            recommendation = '[AVOID] Strong Negative Expected Value'
        else:
            recommendation = '[PASS] Slight Negative Expected Value'

        result = {
            'team': team,
            'model_probability': f'{model_probability * 100:.1f}%',
            'sportsbook_probability': f'{sportsbook_probability * 100:.1f}%',
            'american_odds': american_odds,
            'expected_value_per_stake': f'${expected_value:.2f}',
            'expected_value_percent': f'{expected_value_percent:.1f}%',
            'recommendation': recommendation,
        }

        self.bets.append(result)
        return result

    def calculate_kelly_criterion(self, win_probability: float, american_odds: int) -> float:
        """
        Compute the recommended Kelly fraction of bankroll to wager for a given win probability and American odds, capped at 5%.
        
        Parameters:
            win_probability (float): Probability of winning expressed as a decimal between 0 and 1.
            american_odds (int): American-format odds (negative for favorites, positive for underdogs).
        
        Returns:
            float: Fraction of bankroll to stake (e.g., 0.02 for 2%). Returns 0.0 if the formula yields a negative fraction; otherwise the value is capped at 0.05 (5%).
        """
        decimal_odds = 100 / abs(american_odds) if american_odds < 0 else 1 + american_odds / 100

        kelly = (win_probability * decimal_odds - (1 - win_probability)) / decimal_odds

        # Return as percentage of bankroll (cap at 5% for safety)
        kelly_percent = max(0, min(kelly, 0.05))

        return kelly_percent

    def display_bet_analysis(self, bets: list[dict]):
        """
        Log a concise debug summary for each bet in the provided list.
        
        Parameters:
            bets (list[dict]): List of bet result dictionaries. Each dictionary must contain the keys:
                'team', 'model_probability', 'american_odds', 'expected_value_per_stake', and 'recommendation'.
        """
        logger.debug('Bet analysis', bet_count=len(bets))

        for bet in bets:
            logger.debug(
                'Bet: {team}',
                team=bet['team'],
                model_prob=bet['model_probability'],
                odds=bet['american_odds'],
                ev=bet['expected_value_per_stake'],
                recommendation=bet['recommendation'],
            )


def devig_market(market: Market) -> list[float]:
    """
    Compute de-vigged ("true") probabilities for a market by normalizing each outcome's implied probability so the probabilities sum to 1.
    
    Parameters:
        market (Market): Market object whose outcomes expose `price.implied_probability` for each outcome.
    
    Returns:
        list[float]: A list of de-vigged probabilities corresponding to market.outcomes.
            - Returns an empty list if `market.outcomes` is empty.
            - If the sum of implied probabilities is 0, returns a list of `0.0` values with the same length as `market.outcomes`.
    """
    if not market.outcomes:
        return []

    implied_probs = [outcome.price.implied_probability for outcome in market.outcomes]
    total_implied = sum(implied_probs)

    if total_implied == 0:
        return [0.0] * len(market.outcomes)

    return [p / total_implied for p in implied_probs]
