from __future__ import annotations

# =============================================================================
# DRAFTKINGS NBA BETTING CATEGORIES — TO BE SCRAPED
# =============================================================================
# Audited: 2026-05-02 from https://sportsbook.draftkings.com/leagues/basketball/nba
#
# URL pattern: /leagues/basketball/nba?category={category}&subcategory={subcategory}
#
# TOP-LEVEL TABS:
# ┌──────────┬──────────┬──────────┐
# │ Games    │ Futures  │ Quick SGP│
# └──────────┴──────────┴──────────┘
#
# =============================================================================
# 1. GAMES TAB (category=games) — DEFAULT
# =============================================================================
#
#  1a. GAME LINES (subcategory=game-lines) — DEFAULT [IMPLEMENTED ✓]
#      URL: ?category=games&subcategory=game-lines
#      Layout per game (cb-market__template--2-columns):
#        cb-market__label-inner--parlay = team names (away, home)
#        Spread column: button[data-testid*='0HC'] > [data-testid='button-points-market-board'] + [data-testid='button-odds-market-board']
#        Total  column: button[data-testid*='0OU'] > [data-testid='button-title-market-board'] + [data-testid='button-points-market-board'] + [data-testid='button-odds-market-board']
#        Moneyline col: button[data-testid*='0ML'] > [data-testid='button-odds-market-board']
#      Current status: _parse_draftkings_cb_market() handles this
#
#  1b. PLAYER PROPS (subcategory=player-props) [PENDING_IMPLEMENTATION]
#      URL: ?category=games&subcategory=player-props&nav_1={prop_type}
#      Second-level nav (nav_1):
#        • POINTS           — Over/Under points scored per player
#        • THREES           — Over/Under 3-pointers made
#        • REBOUNDS         — Over/Under rebounds
#        • ASSISTS          — Over/Under assists
#        • PTS+REB+AST      — Combined points+rebounds+assists
#        • DOUBLE-DOUBLE    — Player to record a double-double (Yes/No)
#        • TRIPLE-DOUBLE    — Player to record a triple-double (Yes/No)
#      Data structure per player row:
#        Player name + image (linked to /players/basketball/{slug}-odds/{id})
#        PPG/AST/RPG stat label
#        Horizontal scrollable threshold buttons with odds (e.g., "25+ -120", "30+ +150")
#        Buttons use class*='cb-market__button'
#      TODO: Implement _parse_draftkings_player_props(driver, prop_type)
#            - Find all player rows per game
#            - Extract player name, stat type, threshold, odds
#            - Handle scrollable threshold strip (horizontal scroll buttons)
#
#  1c. ALT LINES (subcategory=alt-lines) [PENDING_IMPLEMENTATION]
#      URL: ?category=games&subcategory=alt-lines&nav_1={alt_type}
#      Second-level nav (nav_1):
#        • ALTERNATE SPREAD  — Slider from ±0.5 to ±30.5 with odds per increment
#        • ALTERNATE TOTAL   — Slider for alternate over/under totals
#        • MONEYLINE (3-WAY) — Win/Draw/Loss moneyline (includes tie)
#        • HALFTIME/FULLTIME — Half-time result + Full-time result combo
#        • QUARTER/FULLTIME  — Quarter result + Full-time result combo
#      Data structure (Alternate Spread):
#        Two-column layout per game: away team | home team
#        Horizontal scrollable slider with half-point increments
#        Each increment has two buttons: away spread odds + home spread odds
#        CSS: class*='cb-market__button'
#        Center slider shows the current spread value
#      TODO: Implement _parse_draftkings_alt_lines(driver, alt_type)
#            - Parse the scrollable slider values
#            - Map each spread/total increment to away/home odds
#
#  1d. QUICK HITS (subcategory=quick-hits) [PENDING_IMPLEMENTATION]
#      URL: ?category=games&subcategory=quick-hits
#  1d. QUICK HITS (subcategory=quick-hits) [PENDING_IMPLEMENTATION]
#      URL: ?category=games&subcategory=quick-hits&nav_1={hit_type}
#      "First occurrence" props — who/what happens FIRST in the game.
#      Data structure per game:
#        "1st Points Scorer" header + player rows (image, name, moneyline odds button)
#        No spread/total/moneyline — just player name + odds for that event
#      Second-level nav (nav_1):
#        • 1ST POINT            — First player to score any point
#        • 1ST MADE THREE       — First player to make a 3-pointer
#        • 1ST REBOUND          — First player to get a rebound
#        • 1ST ASSIST           — First player to get an assist
#        • 1ST BLOCK            — First player to get a block
#        • 1ST STEAL            — First player to get a steal
#        • 1ST TEAM FG          — First team to make a field goal
#        • 1ST TEAM FG - EXACT  — Exact player + team for first FG
#        • 1ST SCORER - EXACT   — Exact first scorer (player)
#        • 1ST FG MADE - TYPE   — Type of first FG (dunk/layup/jumper/3pt)
#        • 1ST THREE - RESULT   — Result of first 3-pt attempt (make/miss)
#        • 1ST TEAM THREE       — First team to make a 3-pointer
#        • 1ST MINUTE           — Events in the 1st minute
#        • POINTS 1ST 3 MINS    — Points scored in first 3 minutes
#        • TEAM THREES IN 1ST 3 MINS — Team 3-pters in first 3 mins
#        • THREES IN 1ST 3 MINS      — Total 3-pters in first 3 mins
#        • TEAM TO SCORE 1ST FG — Which team scores first field goal
#        • 1ST FG TYPE          — Type of first field goal
#        • 1ST FG EXACT - TEAM  — Exact team for first FG
#        • 1ST POSSESSION       — Which team has first possession
#        • 1ST POSSESSION-EXACT — Exact first possession outcome
#        • TIME OF 1ST POINT    — Time elapsed before first point
#      TODO: Implement _parse_draftkings_quick_hits(driver, hit_type)
#            - Parse game sections (same as other tabs)
#            - Extract player name, image URL, odds for each event type
#      Quick single-click bets like "Team to win by 1-10 points"
#      Fixture (dk-quick-hits-*.html): cb-market__template per game,
#      player rows with name + image + moneyline odds button per event.
#
# =============================================================================
# 2. FUTURES TAB (category=futures)
# =============================================================================
#
#  2a. CHAMPION (subcategory=champion) [PENDING_IMPLEMENTATION]
#      URL: ?category=futures&subcategory=champion
#      "Finals Winner" section with team buttons: "OKC Thunder -130", "BOS Celtics +650"
#      Each button = American odds for that team to win championship
#      TODO: Implement _parse_draftkings_futures_champion(driver)
#
#  2b. PLAYOFFS (subcategory=playoffs) [PENDING_IMPLEMENTATION]
#      URL: ?category=futures&subcategory=playoffs
#      Fixture (dk-futures-playoffs.html): team buttons with odds labels.
#
#  2c. CONFERENCE (subcategory=conference) [PENDING_IMPLEMENTATION]
#      URL: ?category=futures&subcategory=conference
#      Fixture (dk-futures-conference.html): team buttons grouped by East/West.
#
#  2d. SERIES PROPS (subcategory=series-props) [PENDING_IMPLEMENTATION]
#      URL: ?category=futures&subcategory=series-props
#      Fixture (dk-futures-series-props.html): series outcome buttons with odds.
#
#  2e. SERIES PLAYER PROPS (subcategory=series-player-props) [PENDING_IMPLEMENTATION]
#      URL: ?category=futures&subcategory=series-player-props
#      Fixture (dk-futures-series-player-props.html): player stat leader odds.
#
#  2f. SEED TO WIN (subcategory=seed-to-win) [PENDING_IMPLEMENTATION]
#      URL: ?category=futures&subcategory=seed-to-win
#      Fixture (dk-futures-seed-to-win.html): seed-number buttons (1-8) + odds.
#
# =============================================================================
# 3. QUICK SGP TAB — Same Game Parlay
# =============================================================================
#
#  URL: ?category=games&subcategory=game-lines (then SGP toggle)
#  Each game has a Quick SGP link: /event/{slug}/{id}?sgpmode=true
#  [PENDING_IMPLEMENTATION] No fixture exists; requires live DK with sgpmode=true.
#      TODO: Implement _parse_draftkings_sgp(driver)
#
# =============================================================================
# 4. PER-GAME DATA TO EXTRACT (across all categories)
# =============================================================================
#
#  For each game listing, we can extract:
#    • away_team (name, logo URL, team page link)
#    • home_team (name, logo URL, team page link)
#    • event_id (numeric, e.g., 34077039)
#    • event_slug (e.g., "phi-76ers-%40-bos-celtics")
#    • game_date/time (Today/Tomorrow/Mon May 4th + time)
#    • spread (points + odds for away and home)
#    • total (over/under + odds)
#    • moneyline (away + home odds)
#    • more_bets_link (full event page)
#    • sgp_link (same-game parlay quick link)
#
# ==============================================================================
#
# =============================================================================
# FIXTURE AVAILABILITY SUMMARY
# =============================================================================
#
#   fixtures/ directory contains HTML snapshots for offline parser development:
#
#   Games tab:
#     1a. Game Lines         ✓ dk-game-lines.html
#     1b. Player Props       ✓ dk-player-props-*.html (points, threes, rebounds,
#                               assists, pts-reb-ast, double-double, triple-double)
#     1c. Alt Lines          ✓ dk-alt-lines-*.html (spread, total, ml-3way,
#                               halftime, quarter)
#     1d. Quick Hits         ✓ dk-quick-hits-*.html (1st-point, 1st-scorer-exact,
#                               1st-three; remaining hit_types share same structure)
#
#   Futures tab:
#     2a. Champion           ✓ dk-futures-champion.html
#     2b. Playoffs           ✓ dk-futures-playoffs.html
#     2c. Conference         ✓ dk-futures-conference.html
#     2d. Series Props       ✓ dk-futures-series-props.html
#     2e. Series Player Props ✓ dk-futures-series-player-props.html
#     2f. Seed To Win        ✓ dk-futures-seed-to-win.html
#
#   Quick SGP tab:
#     3.  Same Game Parlay   ✗ No fixture — requires live DK with sgpmode=true
#
#   All fixtures embed window.__INITIAL_STATE__ JSON containing eventGroups,
#   outcomes, and sports data. Parsers should extract this JSON block first.
# ==============================================================================
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from ..shared.parsers import (
    GameOdds,
    extract_first_american_odds,
    extract_first_signed_number,
    extract_first_total,
)
from .config import (
    BUTTON_ODDS_DATA_TESTID,
    BUTTON_POINTS_DATA_TESTID,
    BUTTON_TITLE_DATA_TESTID,
    DK_BASE_URL,
    DK_FUTURES_CHAMPION_URL,
    EVENT_CELL_NAME_SELECTOR,
    EVENT_CELL_TEAM_SELECTOR,
    FUTURES_ACCORDION_SELECTOR,
    FUTURES_LOAD_SELECTOR,
    FUTURES_TEAM_ROW_SELECTOR,
    FUTURES_TEMPLATE_SELECTOR,
    MARKET_BUTTON_SELECTOR,
    PAGE_LOAD_SELECTOR,
    PARLAY_LABEL_SELECTOR,
    TEMPLATE_SELECTOR,
)

if TYPE_CHECKING:
    from parsel import Selector as HtmlSelector
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright
else:
    HtmlSelector = object

try:
    from parsel import Selector as _HtmlSelector

    _PARSEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HtmlSelector: type[HtmlSelector] | None = None
    _PARSEL_AVAILABLE = False


USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)


@dataclass(frozen=True)
class _BrowserSession:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page


def _close_resource(resource: Page | BrowserContext | Browser | None) -> None:
    if resource is None:
        return
    resource.close()


class DraftKingsScraper:
    """Scrape and parse DraftKings NBA odds."""

    @staticmethod
    def _create_page() -> _BrowserSession:
        """Create a stealth-configured Playwright browser page."""
        playwright = sync_playwright().start()
        browser: Browser | None = None
        context: BrowserContext | None = None
        page: Page | None = None
        try:
            browser = playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--window-size=1920,1080',
                ],
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=USER_AGENT,
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()
            Stealth().apply_stealth_sync(page)
            return _BrowserSession(
                playwright=playwright, browser=browser, context=context, page=page
            )
        except Exception:
            _close_resource(page)
            _close_resource(context)
            _close_resource(browser)
            playwright.stop()
            raise

    @staticmethod
    def _cleanup(session: _BrowserSession | None) -> None:
        """Clean up Playwright resources from leaf objects back to the driver."""
        if session is None:
            return
        for resource_name, resource in (
            ('page', session.page),
            ('context', session.context),
            ('browser', session.browser),
        ):
            try:
                _close_resource(resource)
            except Exception as error:
                logger.warning('Failed to close DraftKings Playwright %s: %s', resource_name, error)
        session.playwright.stop()

    @logger.catch
    def scrape_odds(self) -> list[GameOdds]:
        """Scrape live odds from DraftKings using Playwright.

        Playwright launches a stealth-configured Chromium browser, navigates
        to DraftKings, waits for the game table to load, then passes the page
        to parse_games() for HTML extraction.
        """
        logger.info('Fetching live odds', source='DraftKings', action='fetch')

        session = None
        try:
            session = self._create_page()
            page = session.page

            page.goto(DK_BASE_URL, wait_until='domcontentloaded')

            logger.info('Waiting for page load', source='DraftKings', timeout=20, action='wait')

            try:
                page.wait_for_selector(
                    PAGE_LOAD_SELECTOR,
                    timeout=20000,
                )
                logger.info('Page loaded', source='DraftKings', action='complete')
            except PlaywrightTimeoutError:
                logger.warning('Page load timeout, saving debug snapshot', source='DraftKings')
                logger.warning('DraftKings timeout. Page title: %s', page.title())
                logger.warning(
                    'Page source preview: %.500s',
                    page.content()[:500] if page else '',
                )
                return []

            logger.info('DraftKings page title: %s', page.title())
            games = self.parse_games(page)
            logger.info('DraftKings parse_games returned %d games', len(games))

            if games:
                logger.info(
                    'Scrape complete', source='DraftKings', game_count=len(games), action='complete'
                )
            else:
                logger.warning('No games found', source='DraftKings')

            return games

        except Exception as error:
            logger.error('DraftKings scrape failed: %s', error)
            return []

        finally:
            self._cleanup(session)

    @logger.catch
    def scrape_futures_champion(self) -> list[dict]:
        """Scrape DraftKings futures champion odds using Playwright.

        Navigates to ?category=futures&subcategory=champion and parses
        team names with American championship odds.
        """
        logger.info('Fetching futures champion odds', source='DraftKings', action='fetch')

        session = None
        try:
            session = self._create_page()
            page = session.page
            page.goto(DK_FUTURES_CHAMPION_URL, wait_until='domcontentloaded')

            logger.info(
                'Waiting for futures page load', source='DraftKings', timeout=15, action='wait'
            )

            try:
                page.wait_for_selector(
                    FUTURES_LOAD_SELECTOR,
                    timeout=15000,
                )
                logger.info('Futures champion page loaded', source='DraftKings', action='complete')
            except PlaywrightTimeoutError:
                logger.warning('Futures champion page load timeout', source='DraftKings')
                return []

            results = self.parse_futures_champion(page)

            if results:
                logger.info(
                    'Futures champion scrape complete',
                    source='DraftKings',
                    team_count=len(results),
                    action='complete',
                )
            else:
                logger.warning('No champion teams found', source='DraftKings')

            return results

        except Exception as error:
            logger.error('DraftKings futures champion scrape failed: %s', error)
            return []

        finally:
            self._cleanup(session)

    def parse_games(self, page) -> list[GameOdds]:
        """Parse games from DraftKings page using Playwright.

        When parsel is available, HTML is extracted once from the page and
        parsed with CSS selectors — no repeated element queries.
        The Playwright paths remain as a fallback.
        """
        if _PARSEL_AVAILABLE and _HtmlSelector is not None:
            html = page.content()
            games = self.parse_html(html)
            if games:
                return games

        # Try new cb-market structure first (component-builder layout)
        games = self.parse_cb_market(page)
        if games:
            return games

        # Fallback to old event-cell structure
        return self.parse_event_cells(page)

    @staticmethod
    def parse_html(html: str) -> list[GameOdds]:
        """Parse DraftKings NBA page HTML using parsel CSS selectors.

        Accepts raw HTML string (e.g. from page.content()) and returns
        a list of game dicts with the same schema as the Playwright paths.
        Returns an empty list when parsel is not installed.
        """
        if not _PARSEL_AVAILABLE or _HtmlSelector is None:
            return []

        selector = _HtmlSelector(text=html)
        games = []

        for template in selector.css(TEMPLATE_SELECTOR):
            try:
                # Team names
                team_labels = template.css(f'{PARLAY_LABEL_SELECTOR}::text').getall()
                if len(team_labels) < 2:
                    continue
                away_team, home_team = team_labels[0].strip(), team_labels[1].strip()

                def get_button_text(selector_scope, testid_fragment: str, data_testid: str) -> str:
                    return (
                        selector_scope.css(
                            f"button[data-testid*='{testid_fragment}'] [data-testid='{data_testid}']::text"
                        ).get()
                        or 'N/A'
                    ).strip() or 'N/A'

                away_spread = get_button_text(template, '0HC', BUTTON_POINTS_DATA_TESTID)
                moneyline_values = [
                    value.strip()
                    for value in template.css(
                        f"button[data-testid*='0ML'] [data-testid='{BUTTON_ODDS_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                away_moneyline = moneyline_values[0] if moneyline_values else 'N/A'
                home_moneyline = moneyline_values[1] if len(moneyline_values) > 1 else 'N/A'
                over_under_title = get_button_text(template, '0OU', BUTTON_TITLE_DATA_TESTID)
                over_under_points = get_button_text(template, '0OU', BUTTON_POINTS_DATA_TESTID)
                over_total = over_under_points if over_under_title.upper() == 'O' else 'N/A'

                games.append(
                    {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'matchup': f'{away_team} @ {home_team}',
                        'spread': away_spread,
                        'moneyline': away_moneyline,
                        'home_moneyline': home_moneyline,
                        'over_under': over_total,
                        'source': 'DraftKings',
                    }
                )
            except (AttributeError, ValueError, IndexError):
                continue

        return games

    def parse_cb_market(self, page) -> list[GameOdds]:
        """Parse DraftKings games using cb-market__template structure."""
        games = []

        try:
            # Find game templates — DraftKings uses both 2-column and 4-column layouts
            templates = page.query_selector_all(TEMPLATE_SELECTOR)

            if not templates:
                return []

            for template in templates:
                try:
                    # Team names are in cb-market__label-inner--parlay elements
                    team_elements = template.query_selector_all(PARLAY_LABEL_SELECTOR)

                    if len(team_elements) < 2:
                        continue

                    away_team = team_elements[0].inner_text().strip()
                    home_team = team_elements[1].inner_text().strip()

                    if not away_team or not home_team:
                        continue

                    # Find all market buttons in this template
                    buttons = template.query_selector_all(MARKET_BUTTON_SELECTOR)

                    away_spread = 'N/A'
                    away_moneyline = 'N/A'
                    home_moneyline = 'N/A'
                    over_total = 'N/A'

                    for button in buttons:
                        try:
                            testid = button.get_attribute('data-testid') or ''

                            if '0HC' in testid:
                                points_element = button.query_selector(
                                    f"[data-testid='{BUTTON_POINTS_DATA_TESTID}']"
                                )
                                points = (
                                    points_element.inner_text().strip() if points_element else ''
                                )
                                if away_spread == 'N/A':
                                    away_spread = points
                            elif '0OU' in testid:
                                title_element = button.query_selector(
                                    f"[data-testid='{BUTTON_TITLE_DATA_TESTID}']"
                                )
                                title = title_element.inner_text().strip() if title_element else ''
                                points_element = button.query_selector(
                                    f"[data-testid='{BUTTON_POINTS_DATA_TESTID}']"
                                )
                                points = (
                                    points_element.inner_text().strip() if points_element else ''
                                )
                                if over_total == 'N/A' and title.upper() == 'O':
                                    over_total = points
                            elif '0ML' in testid:
                                odds_element = button.query_selector(
                                    f"[data-testid='{BUTTON_ODDS_DATA_TESTID}']"
                                )
                                odds = odds_element.inner_text().strip() if odds_element else ''
                                if away_moneyline == 'N/A':
                                    away_moneyline = odds
                                elif home_moneyline == 'N/A':
                                    home_moneyline = odds

                        except (AttributeError, ValueError):
                            continue

                    games.append(
                        {
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'matchup': f'{away_team} @ {home_team}',
                            'spread': away_spread,
                            'moneyline': away_moneyline,
                            'home_moneyline': home_moneyline,
                            'over_under': over_total,
                            'source': 'DraftKings',
                        }
                    )

                except Exception as error:
                    logger.warning('Failed to parse DraftKings cb-market game: %s', error)
                    continue

            return games

        except Exception as error:
            logger.warning('Error parsing DraftKings cb-market structure: %s', error)
            return []

    def parse_event_cells(self, page) -> list[GameOdds]:
        """Parse DraftKings games using legacy event-cell structure."""
        games = []

        try:
            # Team name elements — DraftKings uses event-cell__name-text (stable partial class)
            team_elements = page.query_selector_all(EVENT_CELL_NAME_SELECTOR)

            if not team_elements:
                # Fallback: try broader event-cell selector
                team_elements = page.query_selector_all(EVENT_CELL_TEAM_SELECTOR)

            if not team_elements:
                logger.warning('DraftKings: no team elements found — selectors may be stale')
                return []

            # Teams come in pairs: away, home, away, home, ...
            for team_index in range(0, len(team_elements) - 1, 2):
                try:
                    away_team = team_elements[team_index].inner_text().strip()
                    home_team = team_elements[team_index + 1].inner_text().strip()

                    if not away_team or not home_team:
                        continue

                    # Odds: try aria-label on outcome buttons (stable semantic attribute)
                    moneyline = 'N/A'
                    spread = 'N/A'
                    over_under = 'N/A'

                    # Find outcome cells near these team elements
                    game_block = team_elements[team_index].query_selector(
                        "xpath=./ancestor::*[contains(@class,'sportsbook-table__body') or "
                        "contains(@class,'event-cell') or "
                        "contains(@class,'sportsbook-event-accordion')]"
                    )

                    if game_block:
                        outcome_cells = game_block.query_selector_all(
                            "button[aria-label*='Moneyline'], "
                            "[class*='sportsbook-outcome-cell__body']"
                        )
                        spread, moneyline, over_under = self.parse_markets(outcome_cells, away_team)

                    games.append(
                        {
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'matchup': f'{away_team} @ {home_team}',
                            'spread': spread,
                            'moneyline': moneyline,
                            'home_moneyline': 'N/A',
                            'over_under': over_under,
                            'source': 'DraftKings',
                        }
                    )

                except Exception as error:
                    logger.warning('Failed to parse DraftKings game row: %s', error)
                    continue

            return games

        except Exception as error:
            logger.warning('Error parsing DraftKings event cells: %s', error)
            return []

    def parse_markets(self, outcome_cells, team_name: str) -> tuple[str, str, str]:
        spread = 'N/A'
        moneyline = 'N/A'
        over_under = 'N/A'

        for cell in outcome_cells:
            text = cell.inner_text().strip()
            label = cell.get_attribute('aria-label') or ''
            market_text = f'{label} {text}'
            market_text_lower = market_text.lower()

            if moneyline == 'N/A' and 'moneyline' in market_text_lower:
                odds = extract_first_american_odds(market_text)
                if odds:
                    moneyline = odds

            if (
                spread == 'N/A'
                and 'spread' in market_text_lower
                and team_name.lower() in market_text_lower
            ):
                value = extract_first_signed_number(market_text)
                if value:
                    spread = value

            if over_under == 'N/A' and (
                'total' in market_text_lower
                or re.search(r'\b(over|under|o|u)\b', market_text_lower)
            ):
                value = extract_first_total(market_text)
                if value:
                    over_under = value

        return spread, moneyline, over_under

    def _parse_futures_buttons(self, page, bet_type: str) -> list[dict]:
        results: list[dict] = []
        templates = page.query_selector_all(FUTURES_TEMPLATE_SELECTOR)

        for template in templates:
            buttons = template.query_selector_all(f'{FUTURES_LOAD_SELECTOR}, button')
            for button in buttons:
                title = button.query_selector(f"[data-testid='{BUTTON_TITLE_DATA_TESTID}']")
                team_name = title.inner_text().strip() if title else ''
                if not team_name:
                    continue

                odds_element = button.query_selector(f"[data-testid='{BUTTON_ODDS_DATA_TESTID}']")
                odds_text = (
                    odds_element.inner_text().strip()
                    if odds_element
                    else button.inner_text().strip()
                )
                odds = extract_first_american_odds(odds_text) or 'N/A'
                results.append(
                    {
                        'team': team_name,
                        'odds': odds,
                        'bet_type': bet_type,
                        'source': 'DraftKings',
                    }
                )

        return results

    def parse_futures_category(self, page, bet_type: str) -> list[dict]:
        """Parse a DraftKings futures betting category.

        HTML structure: sportsbook-accordion__wrapper sections contain
        content-sports-hierarchy-teams__team rows, each with a team name
        <a> tag and an American-odds button.
        """
        results: list[dict] = []

        try:
            wrappers = page.query_selector_all(FUTURES_ACCORDION_SELECTOR)

            for wrapper in wrappers:
                teams = wrapper.query_selector_all(FUTURES_TEAM_ROW_SELECTOR)

                for team in teams:
                    try:
                        # Team name is in an <a> tag
                        name_element = team.query_selector('a')
                        team_name = name_element.inner_text().strip() if name_element else ''

                        if not team_name:
                            continue

                        # American odds in button text within the team row
                        odds = 'N/A'
                        buttons = team.query_selector_all('button')
                        for button in buttons:
                            found = extract_first_american_odds(button.inner_text().strip())
                            if found:
                                odds = found
                                break

                        results.append(
                            {
                                'team': team_name,
                                'odds': odds,
                                'bet_type': bet_type,
                                'source': 'DraftKings',
                            }
                        )
                    except Exception as error:
                        logger.warning('Failed to parse futures team row: %s', error)
                        continue

        except Exception as error:
            logger.warning('Failed to parse DraftKings futures %s: %s', bet_type, error)

        return results or self._parse_futures_buttons(page, bet_type)

    def parse_futures_champion(self, page) -> list[dict]:
        return self._parse_futures_buttons(page, 'champion') or self.parse_futures_category(
            page, 'champion'
        )

    def parse_futures_playoffs(self, page) -> list[dict]:
        return self.parse_futures_category(page, 'playoffs')

    def parse_futures_conference(self, page) -> list[dict]:
        return self.parse_futures_category(page, 'conference')

    def parse_futures_series_props(self, page) -> list[dict]:
        return self.parse_futures_category(page, 'series_props')

    def parse_futures_series_player_props(self, page) -> list[dict]:
        return self.parse_futures_category(page, 'series_player_props')

    def parse_futures_seed_to_win(self, page) -> list[dict]:
        return self.parse_futures_category(page, 'seed_to_win')
