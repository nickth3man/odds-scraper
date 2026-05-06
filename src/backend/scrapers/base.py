from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.domain import Market


class BaseScraper(ABC):
    """Abstract base class for sportsbook odds scrapers.

    Subclasses must implement :meth:`scrape` to return a list of normalized
    :class:`Market` objects.  The interface is intentionally minimal so
    that new sportsbooks can be added without changing orchestrator code.
    """

    @abstractmethod
    def scrape(self) -> list[Market]:
        """Fetch and return normalized odds for the current slate.

        Returns:
            list[Market]: A list of normalized market objects following the
            canonical ``Market`` schema.  An empty list is returned when no
            games are available or the fetch fails.
        """
        ...
