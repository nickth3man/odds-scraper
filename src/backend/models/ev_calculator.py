from loguru import logger


class EVCalculator:
    """Calculate Expected Value for sports bets"""

    def __init__(self):
        """Initialize expected value calculator"""
        self.bets = []

    def convert_american_to_probability(self, american_odds: int | float) -> float:
        """
        Convert American odds to implied probability

        Example:
        -110 odds → 52.4% probability
        +150 odds → 40.0% probability
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
        self, model_probability: float, american_odds: int, stake: float = 100
    ) -> float:
        """
        Calculate Expected Value of a bet

        Expected Value = (Win Probability x Payout) - (Loss Probability x Stake)

        Args:
            model_probability: Your predicted win probability (0.0 - 1.0)
            american_odds: Sportsbook odds (e.g., -110, +150)
            stake: Amount wagered

        Returns:
            Expected value in dollars
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

    def evaluate_bet(
        self, team: str, model_probability: float, american_odds: int, stake: float = 100
    ) -> dict:
        """
        Full evaluation of a potential bet

        Returns a dictionary with:
        - Team
        - Model probability
        - Sportsbook implied probability
        - Expected value and Expected value percentage
        - Recommendation
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
        Calculate optimal bet size using Kelly Criterion

        Prevents overbetting and bankroll ruin

        Kelly % = (Probability x Odds - (1 - Probability)) / Odds
        """
        decimal_odds = 100 / abs(american_odds) if american_odds < 0 else 1 + american_odds / 100

        kelly = (win_probability * decimal_odds - (1 - win_probability)) / decimal_odds

        # Return as percentage of bankroll (cap at 5% for safety)
        kelly_percent = max(0, min(kelly, 0.05))

        return kelly_percent

    def display_bet_analysis(self, bets: list[dict]):
        """
        Log a concise debug summary for a list of bet evaluation dictionaries.
        
        Parameters:
            bets (list[dict]): List of bet result dictionaries as produced by `evaluate_bet`. Each dictionary is expected to contain the keys: 'team', 'model_probability', 'american_odds', 'expected_value_per_stake', and 'recommendation'.
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
