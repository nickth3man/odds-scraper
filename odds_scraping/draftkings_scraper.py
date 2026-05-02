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
#  1b. PLAYER PROPS (subcategory=player-props) [TODO]
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
#  1c. ALT LINES (subcategory=alt-lines) [TODO]
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
#  1d. QUICK HITS (subcategory=quick-hits) [TODO]
#      URL: ?category=games&subcategory=quick-hits
#  1d. QUICK HITS (subcategory=quick-hits) [TODO]
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
#      TODO: Investigate and implement
#      URL: ?category=games&subcategory=quick-hits
#      Quick single-click bets like "Team to win by 1-10 points"
#      TODO: Investigate and implement
#
# =============================================================================
# 2. FUTURES TAB (category=futures)
# =============================================================================
#
#  2a. CHAMPION (subcategory=champion) [TODO]
#      URL: ?category=futures&subcategory=champion
#      "Finals Winner" section with team buttons: "OKC Thunder -130", "BOS Celtics +650"
#      Each button = American odds for that team to win championship
#      TODO: Implement _parse_draftkings_futures_champion(driver)
#
#  2b. PLAYOFFS (subcategory=playoffs) [TODO]
#      URL: ?category=futures&subcategory=playoffs
#      TODO: Investigate and implement
#
#  2c. CONFERENCE (subcategory=conference) [TODO]
#      URL: ?category=futures&subcategory=conference
#      TODO: Investigate and implement
#
#  2d. SERIES PROPS (subcategory=series-props) [TODO]
#      URL: ?category=futures&subcategory=series-props
#      TODO: Investigate and implement
#
#  2e. SERIES PLAYER PROPS (subcategory=series-player-props) [TODO]
#      URL: ?category=futures&subcategory=series-player-props
#      TODO: Investigate and implement
#
#  2f. SEED TO WIN (subcategory=seed-to-win) [TODO]
#      URL: ?category=futures&subcategory=seed-to-win
#      TODO: Investigate and implement
#
# =============================================================================
# 3. QUICK SGP TAB — Same Game Parlay
# =============================================================================
#
#  URL: ?category=games&subcategory=game-lines (then SGP toggle)
#  Each game has a Quick SGP link: /event/{slug}/{id}?sgpmode=true
#  TODO: Implement _parse_draftkings_sgp(driver)
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

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING

from .parsers import first_american_odds, first_signed_number, first_total

if TYPE_CHECKING:
    from parsel import Selector as HtmlSelector
else:
    HtmlSelector = object

try:
    from parsel import Selector as _HtmlSelector

    _PARSEL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HtmlSelector: type[HtmlSelector] | None = None
    _PARSEL_AVAILABLE = False


class _ByFallback:
    CSS_SELECTOR = 'css selector'
    XPATH = 'xpath'


By = _ByFallback

try:
    from selenium.webdriver.common.by import By

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


logger = logging.getLogger(__name__)


class DraftKingsScraper:
    """Scrape and parse DraftKings NBA odds."""

    def scrape_odds(self) -> list[dict]:
        """
        Scrape live odds from DraftKings using Selenium.

        DraftKings loads odds dynamically with JavaScript. Selenium Manager
        (built into Selenium 4.6+) automatically downloads the correct
        ChromeDriver — no webdriver-manager package required.
        """
        if not SELENIUM_AVAILABLE:
            print('[WARN] Selenium not available. Install with: pip install selenium')
            return []

        from selenium import webdriver
        from selenium.common.exceptions import TimeoutException
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.support import expected_conditions as EC  # noqa: N812
        from selenium.webdriver.support.ui import WebDriverWait

        print('[Fetching] Live odds from DraftKings (this takes 10-15 seconds)...\n')

        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Selenium Manager (built into Selenium 4.6+) handles ChromeDriver automatically
            driver = webdriver.Chrome(options=chrome_options)

            driver.get('https://sportsbook.draftkings.com/leagues/basketball/nba')

            print('Waiting for DraftKings to load (15 seconds)...')

            # Wait for the game table — DraftKings uses sportsbook-table or event-cell classes
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[class*='sportsbook-table'], [class*='event-cell']")
                    )
                )
                print('[OK] Page loaded!\n')
            except TimeoutException:
                print('[WARN] Page took too long to load\n')
                driver.quit()
                return []

            games = self.parse_games(driver)

            if games:
                print(f'[OK] DraftKings: Found {len(games)} games\n')
            else:
                print('[WARN] DraftKings: No games found\n')

            return games

        except Exception as e:
            logger.error('DraftKings scrape failed: %s', e)
            return []

        finally:
            if driver:
                driver.quit()

    def parse_games(self, driver) -> list[dict]:
        """Parse games from DraftKings page using Selenium.

        When parsel is available, HTML is extracted once from the driver and
        parsed with CSS selectors — no repeated Selenium element queries.
        The Selenium paths remain as a fallback.
        """
        if _PARSEL_AVAILABLE and _HtmlSelector is not None and hasattr(driver, 'page_source'):
            html = driver.page_source
            games = self.parse_html(html)
            if games:
                return games

        # Try new cb-market structure first (component-builder layout)
        games = self.parse_cb_market(driver)
        if games:
            return games

        # Fallback to old event-cell structure
        return self.parse_event_cells(driver)

    @staticmethod
    def parse_html(html: str) -> list[dict]:
        """Parse DraftKings NBA page HTML using parsel CSS selectors.

        Accepts raw HTML string (e.g. from ``driver.page_source``) and returns
        a list of game dicts with the same schema as the Selenium paths.
        Returns an empty list when parsel is not installed.
        """
        if not _PARSEL_AVAILABLE or _HtmlSelector is None:
            return []

        sel = _HtmlSelector(text=html)
        games = []

        for template in sel.css(
            "[class*='cb-market__template--2-columns'], [class*='cb-market__template--4-columns']"
        ):
            try:
                # Team names
                team_labels = template.css(
                    "[class*='cb-market__label-inner--parlay']::text"
                ).getall()
                if len(team_labels) < 2:
                    continue
                away_team, home_team = team_labels[0].strip(), team_labels[1].strip()

                def _get_btn(sel_scope, testid_fragment: str, attr: str) -> str:
                    return (
                        sel_scope.css(
                            f"button[data-testid*='{testid_fragment}'] [data-testid='{attr}']::text"
                        ).get()
                        or 'N/A'
                    ).strip() or 'N/A'

                away_spread = _get_btn(template, '0HC', 'button-points-market-board')
                away_ml = _get_btn(template, '0ML', 'button-odds-market-board')
                ou_title = _get_btn(template, '0OU', 'button-title-market-board')
                ou_points = _get_btn(template, '0OU', 'button-points-market-board')
                over_total = ou_points if ou_title.upper() == 'O' else 'N/A'

                games.append(
                    {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'matchup': f'{away_team} @ {home_team}',
                        'spread': away_spread,
                        'moneyline': away_ml,
                        'home_moneyline': 'N/A',
                        'over_under': over_total,
                        'source': 'DraftKings',
                    }
                )
            except (AttributeError, ValueError, IndexError):
                continue

        return games

    def parse_cb_market(self, driver) -> list[dict]:
        """Parse DraftKings games using cb-market__template structure."""
        games = []

        try:
            # Find game templates — DraftKings uses both 2-column and 4-column layouts
            templates = driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='cb-market__template--2-columns'], [class*='cb-market__template--4-columns']",
            )

            if not templates:
                return []

            for template in templates:
                try:
                    # Team names are in cb-market__label-inner--parlay elements
                    team_elems = template.find_elements(
                        By.CSS_SELECTOR, "[class*='cb-market__label-inner--parlay']"
                    )

                    if len(team_elems) < 2:
                        continue

                    away_team = team_elems[0].text.strip()
                    home_team = team_elems[1].text.strip()

                    if not away_team or not home_team:
                        continue

                    # Find all market buttons in this template
                    buttons = template.find_elements(
                        By.CSS_SELECTOR, "button[data-testid*='component-builder-market-button']"
                    )

                    spread = 'N/A'
                    moneyline = 'N/A'
                    ou = 'N/A'

                    away_spread = 'N/A'
                    home_spread = 'N/A'
                    away_ml = 'N/A'
                    home_ml = 'N/A'
                    over_total = 'N/A'

                    for button in buttons:
                        try:
                            testid = button.get_attribute('data-testid') or ''
                            points_elem = button.find_element(
                                By.CSS_SELECTOR, "[data-testid='button-points-market-board']"
                            )
                            points = points_elem.text.strip() if points_elem else ''

                            odds_elem = button.find_element(
                                By.CSS_SELECTOR, "[data-testid='button-odds-market-board']"
                            )
                            odds = odds_elem.text.strip() if odds_elem else ''

                            title_elem = button.find_element(
                                By.CSS_SELECTOR, "[data-testid='button-title-market-board']"
                            )
                            title = title_elem.text.strip() if title_elem else ''

                            if '0HC' in testid:
                                # Spread — first is away, second is home
                                if away_spread == 'N/A':
                                    away_spread = points
                                elif home_spread == 'N/A':
                                    home_spread = points
                            elif '0OU' in testid:
                                # Total — extract the number
                                if over_total == 'N/A' and title.upper() == 'O':
                                    over_total = points
                            elif '0ML' in testid:
                                # Moneyline — first is away, second is home
                                if away_ml == 'N/A':
                                    away_ml = odds
                                elif home_ml == 'N/A':
                                    home_ml = odds

                        except (AttributeError, ValueError):
                            continue

                    # Use away team perspective for consistency
                    spread = away_spread if away_spread != 'N/A' else 'N/A'
                    moneyline = away_ml if away_ml != 'N/A' else 'N/A'
                    ou = over_total if over_total != 'N/A' else 'N/A'

                    games.append(
                        {
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'matchup': f'{away_team} @ {home_team}',
                            'spread': spread,
                            'moneyline': moneyline,
                            'home_moneyline': home_ml,
                            'over_under': ou,
                            'source': 'DraftKings',
                        }
                    )

                except Exception as e:
                    logger.warning('Failed to parse DraftKings cb-market game: %s', e)
                    continue

            return games

        except Exception as e:
            logger.warning('Error parsing DraftKings cb-market structure: %s', e)
            return []

    def parse_event_cells(self, driver) -> list[dict]:
        """Parse DraftKings games using legacy event-cell structure."""
        games = []

        try:
            # Team name elements — DraftKings uses event-cell__name-text (stable partial class)
            team_elements = driver.find_elements(
                By.CSS_SELECTOR, "[class*='event-cell__name-text']"
            )

            if not team_elements:
                # Fallback: try broader event-cell selector
                team_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='event-cell__team']")

            if not team_elements:
                logger.warning('DraftKings: no team elements found — selectors may be stale')
                return []

            # Teams come in pairs: away, home, away, home, ...
            for i in range(0, len(team_elements) - 1, 2):
                try:
                    away_team = team_elements[i].text.strip()
                    home_team = team_elements[i + 1].text.strip()

                    if not away_team or not home_team:
                        continue

                    # Odds: try aria-label on outcome buttons (stable semantic attribute)
                    moneyline = 'N/A'
                    spread = 'N/A'
                    ou = 'N/A'

                    # Find outcome cells near these team elements
                    game_block = (
                        team_elements[i].find_element(
                            By.XPATH,
                            "./ancestor::*[contains(@class,'sportsbook-table__body') or "
                            "contains(@class,'event-cell') or "
                            "contains(@class,'sportsbook-event-accordion')]",
                        )
                        if team_elements
                        else None
                    )

                    if game_block:
                        outcome_cells = game_block.find_elements(
                            By.CSS_SELECTOR,
                            "button[aria-label*='Moneyline'], [class*='sportsbook-outcome-cell__body']",
                        )
                        spread, moneyline, ou = self.parse_markets(outcome_cells, away_team)

                    games.append(
                        {
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'matchup': f'{away_team} @ {home_team}',
                            'spread': spread,
                            'moneyline': moneyline,
                            'over_under': ou,
                            'source': 'DraftKings',
                        }
                    )

                except Exception as e:
                    logger.warning('Failed to parse DraftKings game row: %s', e)
                    continue

            return games

        except Exception as e:
            logger.warning('Error parsing DraftKings event cells: %s', e)
            return []

    def parse_markets(self, outcome_cells, team_name: str) -> tuple[str, str, str]:
        spread = 'N/A'
        moneyline = 'N/A'
        ou = 'N/A'

        for cell in outcome_cells:
            text = cell.text.strip()
            label = cell.get_attribute('aria-label') or ''
            market_text = f'{label} {text}'
            market_text_lower = market_text.lower()

            if moneyline == 'N/A' and 'moneyline' in market_text_lower:
                odds = first_american_odds(market_text)
                if odds:
                    moneyline = odds

            if (
                spread == 'N/A'
                and 'spread' in market_text_lower
                and team_name.lower() in market_text_lower
            ):
                value = first_signed_number(market_text)
                if value:
                    spread = value

            if ou == 'N/A' and (
                'total' in market_text_lower
                or re.search(r'\b(over|under|o|u)\b', market_text_lower)
            ):
                value = first_total(market_text)
                if value:
                    ou = value

        return spread, moneyline, ou
