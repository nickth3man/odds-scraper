"""Source-specific URLs and CSS selectors for the DraftKings odds adapter."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

DK_BASE_URL = 'https://sportsbook.draftkings.com/leagues/basketball/nba'
DK_FUTURES_CHAMPION_URL = DK_BASE_URL + '?category=futures&subcategory=champion'

# ---------------------------------------------------------------------------
# Page load wait selectors
# ---------------------------------------------------------------------------

PAGE_LOAD_SELECTOR = "[class*='cb-market'], [class*='event-cell']"
FUTURES_LOAD_SELECTOR = "[class*='cb-market__button']"

# ---------------------------------------------------------------------------
# Template selectors (component-builder layout)
# ---------------------------------------------------------------------------

TEMPLATE_SELECTOR = (
    "[class*='cb-market__template--2-columns'], [class*='cb-market__template--4-columns']"
)
PARLAY_LABEL_SELECTOR = "[class*='cb-market__label-inner--parlay']"
MARKET_BUTTON_SELECTOR = "button[data-testid*='component-builder-market-button']"

# ---------------------------------------------------------------------------
# Market board data-testid fragments (used in selector construction)
# ---------------------------------------------------------------------------

BUTTON_POINTS_DATA_TESTID = 'button-points-market-board'
BUTTON_ODDS_DATA_TESTID = 'button-odds-market-board'
BUTTON_TITLE_DATA_TESTID = 'button-title-market-board'

# ---------------------------------------------------------------------------
# Legacy event-cell selectors (fallback path)
# ---------------------------------------------------------------------------

EVENT_CELL_NAME_SELECTOR = "[class*='event-cell__name-text']"
EVENT_CELL_TEAM_SELECTOR = "[class*='event-cell__team']"

# ---------------------------------------------------------------------------
# Futures / category selectors
# ---------------------------------------------------------------------------

FUTURES_ACCORDION_SELECTOR = "[class*='sportsbook-accordion__wrapper']"
FUTURES_TEAM_ROW_SELECTOR = "[class*='content-sports-hierarchy-teams__team']"
FUTURES_TEMPLATE_SELECTOR = (
    "[class*='cb-market__template'], [class*='sportsbook-accordion__wrapper']"
)
