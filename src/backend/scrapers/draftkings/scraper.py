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
from typing import TYPE_CHECKING

from loguru import logger
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

from ...models.domain import Market, MarketType, NormalizedOdds, Outcome
from ..shared.parsers import (
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


def _parse_american(raw: str) -> float | None:
    """
    Parse an American-style odds string into a numeric value.
    
    Accepts strings like "+150" or "-110" and attempts to normalize them; returns None for empty input, the literal "N/A", or when no parsable odds can be extracted.
    
    Returns:
        float | None: The parsed odds as a float (e.g., '+150' -> 150.0, '-110' -> -110.0), or `None` if parsing failed.
    """
    cleaned = raw.strip()
    if not cleaned or cleaned == 'N/A':
        return None
    try:
        return float(cleaned)
    except ValueError:
        extracted = extract_first_american_odds(cleaned)
        return float(extracted) if extracted else None


def _draftkings_event_id_from_text(value: str) -> str | None:
    match = re.search(r'market-button-(\d+)-', value)
    return match.group(1) if match else None


def _fallback_event_id(away_team: str, home_team: str) -> str:
    matchup = f'{away_team}-{home_team}'.lower()
    return re.sub(r'[^a-z0-9]+', '-', matchup).strip('-')


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
        """
        Close and release Playwright resources associated with the session and stop the Playwright driver.
        
        If `session` is `None`, this function does nothing. It attempts to close the page, context, and browser in that order; failures closing individual resources are logged as warnings. After attempting to close resources, the Playwright driver is stopped.
        Parameters:
            session (_BrowserSession | None): Playwright resources to clean up.
        """
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
                logger.warning('Failed to close DraftKings Playwright {}: {}', resource_name, error)
        session.playwright.stop()

    @logger.catch
    def scrape_odds(self) -> list[Market]:
        """
        Fetch current NBA game odds from DraftKings and parse them into Market objects.

        Returns:
            list[Market]: A list of Market objects (H2H, SPREADS, TOTALS) for each found game,
            or an empty list if no games were found or if an error/timeout occurred.
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
                logger.warning('DraftKings timeout. Page title: {}', page.title())
                logger.warning(
                    'Page source preview: {:.500s}',
                    page.content()[:500] if page else '',
                )
                return []

            logger.info('DraftKings page title: {}', page.title())
            games = self.parse_games(page)
            logger.info('DraftKings parse_games returned {} games', len(games))

            if games:
                logger.info(
                    'Scrape complete', source='DraftKings', game_count=len(games), action='complete'
                )
            else:
                logger.warning('No games found', source='DraftKings')

            return games

        except Exception as error:
            logger.error('DraftKings scrape failed: {}', error)
            return []

        finally:
            self._cleanup(session)

    @logger.catch
    def scrape_futures_champion(self) -> list[dict]:
        """
        Fetches DraftKings champion futures odds and returns them as structured rows.

        Navigates to the DraftKings champion futures page and parses available entries into
        a list of dictionaries containing team names and their American odds. On page-load
        timeout or other failures this function returns an empty list.

        Returns:
            results (list[dict]): A list of rows with keys `team` (str), `odds` (str, American odds or 'N/A'),
                `bet_type` (str, 'champion'), and `source` (str, 'DraftKings').
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
            logger.error('DraftKings futures champion scrape failed: {}', error)
            return []

        finally:
            self._cleanup(session)

    def parse_games(self, page) -> list[Market]:
        """
        Parse a DraftKings page and produce a list of Market objects representing the scraped games.
        
        Prefers a single-pass HTML parse using `parsel` when available, falling back to the component-builder (`parse_cb_market`) layout parser and then to the legacy event-cell parser (`parse_event_cells`) if needed.
        
        Parameters:
            page: Playwright Page instance to parse.
        
        Returns:
            markets (list[Market]): List of parsed Market objects; empty list if no games were found.
        """
        if _PARSEL_AVAILABLE and _HtmlSelector is not None:
            html = page.content()
            markets = self.parse_html(html)
            if markets:
                return markets

        # Try new cb-market structure first (component-builder layout)
        markets = self.parse_cb_market(page)
        if markets:
            return markets

        # Fallback to old event-cell structure
        return self.parse_event_cells(page)

    @staticmethod
    def _build_markets(
        away_team: str,
        home_team: str,
        event_id: str | None,
        away_spread_raw: str,
        away_spread_odds_raw: str,
        home_spread_raw: str,
        home_spread_odds_raw: str,
        away_moneyline_raw: str,
        home_moneyline_raw: str,
        over_total_raw: str,
        over_odds_raw: str,
        under_total_raw: str,
        under_odds_raw: str,
    ) -> list[Market]:
        """
        Constructs Market objects (moneyline, spread, and total) for a single game from raw parsed fields.
        
        Parses the provided raw strings and builds zero or more Market instances:
        - Moneyline (H2H): includes an outcome for each side with a parsable American odd.
        - Spread: includes away and home outcomes with point values if a spread can be parsed.
        - Total: includes Over and Under outcomes with the parsed total points if available.
        
        Parameters:
            away_team (str): Away team name.
            home_team (str): Home team name.
            away_spread_raw (str): Raw away spread text (signed number or other text); may be 'N/A' or unparsable.
            away_moneyline_raw (str): Raw away moneyline/american odds text; may be 'N/A' or unparsable.
            home_moneyline_raw (str): Raw home moneyline/american odds text; may be 'N/A' or unparsable.
            over_total_raw (str): Raw over/total points text; may be 'N/A' or unparsable.
        
        Returns:
            list[Market]: A list of Market objects for the game. Markets are omitted when their corresponding raw input cannot be parsed; moneyline outcomes are included only for sides with parsable odds.
        """
        markets: list[Market] = []
        resolved_event_id = event_id or _fallback_event_id(away_team, home_team)

        # H2H (moneyline) market
        away_ml = _parse_american(away_moneyline_raw)
        home_ml = _parse_american(home_moneyline_raw)
        if away_ml is not None and home_ml is not None:
            outcomes = [
                Outcome(name=away_team, price=NormalizedOdds.from_american(away_ml)),
                Outcome(name=home_team, price=NormalizedOdds.from_american(home_ml)),
            ]
            markets.append(
                Market(
                    key=f'draftkings_h2h_{resolved_event_id}',
                    name='Moneyline',
                    sport='nba',
                    event_id=resolved_event_id,
                    market_type=MarketType.H2H,
                    outcomes=outcomes,
                )
            )

        # SPREADS market
        away_spread_val = None
        if away_spread_raw and away_spread_raw != 'N/A':
            try:
                away_spread_val = float(away_spread_raw)
            except ValueError:
                signed = extract_first_signed_number(away_spread_raw)
                if signed:
                    away_spread_val = float(signed)
        home_spread_val = None
        if home_spread_raw and home_spread_raw != 'N/A':
            try:
                home_spread_val = float(home_spread_raw)
            except ValueError:
                signed = extract_first_signed_number(home_spread_raw)
                if signed:
                    home_spread_val = float(signed)
        away_spread_odds = _parse_american(away_spread_odds_raw)
        home_spread_odds = _parse_american(home_spread_odds_raw)
        if (
            away_spread_val is not None
            and home_spread_val is not None
            and away_spread_odds is not None
            and home_spread_odds is not None
        ):
            spread_outcomes = [
                Outcome(
                    name=away_team,
                    price=NormalizedOdds.from_american(away_spread_odds),
                    point=away_spread_val,
                ),
                Outcome(
                    name=home_team,
                    price=NormalizedOdds.from_american(home_spread_odds),
                    point=home_spread_val,
                ),
            ]
            markets.append(
                Market(
                    key=f'draftkings_spread_{resolved_event_id}',
                    name='Spread',
                    sport='nba',
                    event_id=resolved_event_id,
                    market_type=MarketType.SPREADS,
                    outcomes=spread_outcomes,
                )
            )

        # TOTALS market
        total_val = None
        if over_total_raw and over_total_raw != 'N/A':
            try:
                total_val = float(over_total_raw)
            except ValueError:
                extracted = extract_first_total(over_total_raw)
                if extracted:
                    total_val = float(extracted)
        under_total_val = None
        if under_total_raw and under_total_raw != 'N/A':
            try:
                under_total_val = float(under_total_raw)
            except ValueError:
                extracted = extract_first_total(under_total_raw)
                if extracted:
                    under_total_val = float(extracted)
        over_odds = _parse_american(over_odds_raw)
        under_odds = _parse_american(under_odds_raw)
        if total_val is not None and under_total_val is not None and over_odds and under_odds:
            totals_outcomes = [
                Outcome(
                    name='Over',
                    price=NormalizedOdds.from_american(over_odds),
                    point=total_val,
                ),
                Outcome(
                    name='Under',
                    price=NormalizedOdds.from_american(under_odds),
                    point=under_total_val,
                ),
            ]
            markets.append(
                Market(
                    key=f'draftkings_total_{resolved_event_id}',
                    name='Total',
                    sport='nba',
                    event_id=resolved_event_id,
                    market_type=MarketType.TOTALS,
                    outcomes=totals_outcomes,
                )
            )

        return markets

    @staticmethod
    def parse_html(html: str) -> list[Market]:
        """
        Extract DraftKings NBA markets from a page HTML string into Market objects.
        
        Parses the provided full page HTML (as returned by page.content()) and returns a list of Market instances representing parsed moneyline (H2H), spread, and total markets for each detected game. Templates that cannot be parsed are silently skipped. If the `parsel` library is not available, this function returns an empty list.
        
        Parameters:
            html (str): Full HTML of a DraftKings NBA page.
        
        Returns:
            list[Market]: A list of Market objects for parsed games; empty if none found or if `parsel` is unavailable.
        """
        if not _PARSEL_AVAILABLE or _HtmlSelector is None:
            return []

        selector = _HtmlSelector(text=html)
        markets: list[Market] = []

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

                event_id = _draftkings_event_id_from_text(
                    template.css("button[data-testid*='market-button']::attr(data-testid)").get() or ''
                )
                spread_points = [
                    value.strip()
                    for value in template.css(
                        f"button[data-testid*='0HC'] [data-testid='{BUTTON_POINTS_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                spread_odds = [
                    value.strip()
                    for value in template.css(
                        f"button[data-testid*='0HC'] [data-testid='{BUTTON_ODDS_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                away_spread = spread_points[0] if spread_points else 'N/A'
                home_spread = spread_points[1] if len(spread_points) > 1 else 'N/A'
                away_spread_odds = spread_odds[0] if spread_odds else 'N/A'
                home_spread_odds = spread_odds[1] if len(spread_odds) > 1 else 'N/A'
                moneyline_values = [
                    value.strip()
                    for value in template.css(
                        f"button[data-testid*='0ML'] [data-testid='{BUTTON_ODDS_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                away_moneyline = moneyline_values[0] if moneyline_values else 'N/A'
                home_moneyline = moneyline_values[1] if len(moneyline_values) > 1 else 'N/A'
                total_titles = [
                    value.strip().upper()
                    for value in template.css(
                        f"button[data-testid*='0OU'] [data-testid='{BUTTON_TITLE_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                total_points = [
                    value.strip()
                    for value in template.css(
                        f"button[data-testid*='0OU'] [data-testid='{BUTTON_POINTS_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                total_odds = [
                    value.strip()
                    for value in template.css(
                        f"button[data-testid*='0OU'] [data-testid='{BUTTON_ODDS_DATA_TESTID}']::text"
                    ).getall()
                    if value and value.strip()
                ]
                over_total = 'N/A'
                over_odds = 'N/A'
                under_total = 'N/A'
                under_odds = 'N/A'
                for index, title in enumerate(total_titles):
                    if title == 'O' and index < len(total_points):
                        over_total = total_points[index]
                        over_odds = total_odds[index] if index < len(total_odds) else 'N/A'
                    elif title == 'U' and index < len(total_points):
                        under_total = total_points[index]
                        under_odds = total_odds[index] if index < len(total_odds) else 'N/A'

                markets.extend(
                    DraftKingsScraper._build_markets(
                        away_team,
                        home_team,
                        event_id,
                        away_spread,
                        away_spread_odds,
                        home_spread,
                        home_spread_odds,
                        away_moneyline,
                        home_moneyline,
                        over_total,
                        over_odds,
                        under_total,
                        under_odds,
                    )
                )
            except (AttributeError, ValueError, IndexError):
                continue

        return markets

    def parse_cb_market(self, page) -> list[Market]:
        """
        Parse DraftKings game templates rendered with the `cb-market__template` layout into Market objects.
        
        Iterates each market template on the provided Playwright page, extracts away/home team names and the first available spread, moneyline, and over total values from market buttons, and converts each game into one or more Market entries via the scraper's internal market builder.
        
        Parameters:
            page (playwright.sync_api.Page): Playwright page positioned on a DraftKings listings page containing `cb-market__template` elements.
        
        Returns:
            list[Market]: A list of parsed Market objects for all successfully read games; returns an empty list when no templates are found or parsing fails.
        """
        markets: list[Market] = []

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
                    away_spread_odds = 'N/A'
                    home_spread = 'N/A'
                    home_spread_odds = 'N/A'
                    away_moneyline = 'N/A'
                    home_moneyline = 'N/A'
                    over_total = 'N/A'
                    over_odds = 'N/A'
                    under_total = 'N/A'
                    under_odds = 'N/A'
                    event_id: str | None = None

                    for button in buttons:
                        try:
                            testid = button.get_attribute('data-testid') or ''
                            event_id = event_id or _draftkings_event_id_from_text(testid)

                            if '0HC' in testid:
                                points_element = button.query_selector(
                                    f"[data-testid='{BUTTON_POINTS_DATA_TESTID}']"
                                )
                                points = (
                                    points_element.inner_text().strip() if points_element else ''
                                )
                                odds_element = button.query_selector(
                                    f"[data-testid='{BUTTON_ODDS_DATA_TESTID}']"
                                )
                                odds = odds_element.inner_text().strip() if odds_element else ''
                                if away_spread == 'N/A':
                                    away_spread = points
                                    away_spread_odds = odds
                                elif home_spread == 'N/A':
                                    home_spread = points
                                    home_spread_odds = odds
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
                                odds_element = button.query_selector(
                                    f"[data-testid='{BUTTON_ODDS_DATA_TESTID}']"
                                )
                                odds = odds_element.inner_text().strip() if odds_element else ''
                                if over_total == 'N/A' and title.upper() == 'O':
                                    over_total = points
                                    over_odds = odds
                                elif under_total == 'N/A' and title.upper() == 'U':
                                    under_total = points
                                    under_odds = odds
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

                    markets.extend(
                        self._build_markets(
                            away_team,
                            home_team,
                            event_id,
                            away_spread,
                            away_spread_odds,
                            home_spread,
                            home_spread_odds,
                            away_moneyline,
                            home_moneyline,
                            over_total,
                            over_odds,
                            under_total,
                            under_odds,
                        )
                    )

                except Exception as error:
                    logger.warning('Failed to parse DraftKings cb-market game: {}', error)
                    continue

            return markets

        except Exception as error:
            logger.warning('Error parsing DraftKings cb-market structure: {}', error)
            return []

    def parse_event_cells(self, page) -> list[Market]:
        """
        Parse the legacy DraftKings "event-cell" DOM and convert found game rows into Market objects.
        
        Attempts to locate team name elements in pairs (away, home), extracts nearby outcome cells for moneyline, spread, and totals, and builds corresponding Market entries. Returns an empty list if no games are found or if parsing fails.
        
        Returns:
            list[Market]: Parsed markets for each detected game; empty list when none are found or on parse errors.
        """
        markets: list[Market] = []

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
                    home_moneyline = 'N/A'
                    spread = 'N/A'
                    spread_odds = 'N/A'
                    home_spread = 'N/A'
                    home_spread_odds = 'N/A'
                    over_under = 'N/A'
                    over_odds = 'N/A'
                    under_total = 'N/A'
                    under_odds = 'N/A'

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
                        (
                            spread,
                            spread_odds,
                            home_spread,
                            home_spread_odds,
                            moneyline,
                            home_moneyline,
                            over_under,
                            over_odds,
                            under_total,
                            under_odds,
                        ) = self._extract_raw_markets(
                            outcome_cells, away_team, home_team
                        )

                    markets.extend(
                        self._build_markets(
                            away_team,
                            home_team,
                            None,
                            spread,
                            spread_odds,
                            home_spread,
                            home_spread_odds,
                            moneyline,
                            home_moneyline,
                            over_under,
                            over_odds,
                            under_total,
                            under_odds,
                        )
                    )

                except Exception as error:
                    logger.warning('Failed to parse DraftKings game row: {}', error)
                    continue

            return markets

        except Exception as error:
            logger.warning('Error parsing DraftKings event cells: {}', error)
            return []

    def _extract_raw_markets(self, outcome_cells, team_name: str) -> tuple[str, str, str]:
        """
        Extract raw spread, moneyline, and total values from a sequence of outcome cells for a specific team.
        
        Parameters:
        	outcome_cells (iterable): Iterable of DOM element-like objects supporting .inner_text() and .get_attribute().
        	team_name (str): Team name used to disambiguate spread rows that reference a team.
        
        Returns:
        	tuple[str, str, str]: A 3-tuple (spread, moneyline, over_under) where each value is the extracted string or `'N/A'` if not found.
        """
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
        """
        Parse futures betting entries from a DraftKings futures category page.
        
        Extracts team names and their American odds from accordion-style futures listings. Each result is a dict with the team's display name, the extracted American odds (or 'N/A' when none found), the provided bet_type, and the source identifier.
        
        Parameters:
            page: Playwright Page representing the loaded futures category.
            bet_type (str): Category label to assign to each returned entry (e.g., 'champion').
        
        Returns:
            list[dict]: A list of dictionaries with keys:
                - 'team' (str): Team name as displayed on the page.
                - 'odds' (str): American odds string if found, otherwise 'N/A'.
                - 'bet_type' (str): The provided bet_type value.
                - 'source' (str): Fixed string 'DraftKings'.
            If no entries are parsed from the accordion structure, an alternative button-based extraction is attempted and its results are returned.
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
                        logger.warning('Failed to parse futures team row: {}', error)
                        continue

        except Exception as error:
            logger.warning('Failed to parse DraftKings futures {}: {}', bet_type, error)

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
