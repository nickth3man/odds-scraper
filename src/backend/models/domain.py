from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class NormalizedOdds(BaseModel):
    """Unified odds representation with American, decimal, and implied probability."""

    american: float = Field(description='American odds (e.g. +150, -110)')
    decimal: float = Field(description='Decimal odds (e.g. 2.5, 1.91)')
    implied_probability: float = Field(
        ge=0.0, le=1.0, description='Implied win probability (0.0 - 1.0)'
    )

    @classmethod
    def from_american(cls, american: float) -> NormalizedOdds:
        """Create ``NormalizedOdds`` from American odds.

        Args:
            american: American odds value (e.g. +150, -110).

        Returns:
            A ``NormalizedOdds`` instance with decimal and implied probability computed.
        """
        if american == 0:
            raise ValueError('american odds must be non-zero')
        if american < 0:
            decimal = 1.0 + (100.0 / abs(american))
            implied_probability = abs(american) / (abs(american) + 100.0)
        else:
            decimal = 1.0 + (american / 100.0)
            implied_probability = 100.0 / (american + 100.0)

        return cls(american=american, decimal=decimal, implied_probability=implied_probability)


class Outcome(BaseModel):
    """A single betting outcome within a market."""

    name: str = Field(description='Outcome label (e.g. "Lakers", "Over", "Yes")')
    price: NormalizedOdds = Field(description='Normalized odds for this outcome')
    point: float | None = Field(default=None, description='Spread or total line (if applicable)')
    description: str | None = Field(
        default=None, description='Additional outcome context (e.g. player name for props)'
    )


class MarketType(StrEnum):
    """Enumeration of supported betting market types."""

    SPREADS = 'spreads'
    TOTALS = 'totals'
    H2H = 'h2h'
    PLAYER_PROP = 'player_prop'
    OUTRIGHTS = 'outrights'
    ALTERNATE_SPREADS = 'alternate_spreads'
    ALTERNATE_TOTALS = 'alternate_totals'


class Market(BaseModel):
    """A betting market containing one or more outcomes."""

    key: str = Field(description='Unique market identifier')
    name: str = Field(description='Human-readable market name (e.g. "Spread", "Moneyline")')
    sport: str = Field(description='Sport key (e.g. "nba", "nfl")')
    event_id: str | None = Field(
        default=None, description='Optional event/game identifier this market belongs to'
    )
    market_type: MarketType = Field(description='Categorization of the market')
    outcomes: list[Outcome] = Field(
        default_factory=list, description='All available outcomes for this market'
    )
