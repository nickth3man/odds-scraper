import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import json
import time

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class LiveOddsScraper:
    """Scrape live odds from ESPN and DraftKings for real games"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.all_games = []
    
    # ============ ESPN SCRAPING ============
    
    def scrape_espn_nba_odds(self):
        """
        Scrape live NBA odds from ESPN
        Works for regular season and playoffs
        """
        print("🔄 Fetching live NBA odds from ESPN...\n")
        
        try:
            url = "https://www.espn.com/nba/odds"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for game data in the page
            games = self.parse_espn_games(soup)
            
            if games:
                print(f"✅ ESPN: Found {len(games)} games\n")
                self.all_games.extend(games)
                return games
            else:
                print("⚠️ ESPN: No games found (page structure may have changed)\n")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ESPN Error: {e}\n")
            return []
    
    def parse_espn_games(self, soup):
        """Parse game data from ESPN HTML"""
        games = []
        
        try:
            # Look for all game containers
            game_rows = soup.find_all('tr', class_='Table__TR')
            
            if not game_rows:
                # Try alternative selectors
                game_rows = soup.find_all('tr')
            
            for row in game_rows:
                try:
                    cells = row.find_all('td')
                    
                    if len(cells) < 3:
                        continue
                    
                    # Get team text
                    team_text = cells[0].get_text(strip=True)
                    
                    # Get odds text
                    odds_text = ' '.join([cell.get_text(strip=True) for cell in cells[1:]])
                    
                    if not team_text or len(team_text) < 3:
                        continue
                    
                    # Parse teams
                    teams = self.parse_teams(team_text)
                    if not teams:
                        continue
                    
                    team1, team2 = teams
                    
                    game = {
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'home_team': team2,
                        'away_team': team1,
                        'matchup': f"{team1} @ {team2}",
                        'spread': self.extract_spread(odds_text),
                        'moneyline': self.extract_moneyline(odds_text),
                        'over_under': self.extract_ou(odds_text),
                        'source': 'ESPN'
                    }
                    
                    games.append(game)
                    
                except Exception as e:
                    continue
            
            return games
            
        except Exception as e:
            print(f"Error parsing ESPN: {e}")
            return []
    
    def parse_teams(self, team_text):
        """Extract team names from text"""
        if ' vs ' in team_text:
            teams = team_text.split(' vs ')
        elif ' @ ' in team_text:
            teams = team_text.split(' @ ')
        elif '@' in team_text:
            teams = team_text.split('@')
        else:
            return None
        
        if len(teams) == 2:
            return [t.strip() for t in teams]
        return None
    
    def extract_spread(self, text):
        """Extract spread from odds text"""
        import re
        match = re.search(r'([+-]\d+\.?\d*)\s*\(', text)
        return match.group(1) if match else "N/A"
    
    def extract_moneyline(self, text):
        """Extract moneyline from odds text"""
        import re
        match = re.search(r'\(([+-]\d+)\)', text)
        return match.group(1) if match else "N/A"
    
    def extract_ou(self, text):
        """Extract over/under from odds text"""
        import re
        match = re.search(r'o/u\s*(\d+\.?\d*)', text, re.IGNORECASE)
        return match.group(1) if match else "N/A"
    
    # ============ DRAFTKINGS SCRAPING (Selenium) ============
    
    def scrape_draftkings_odds(self):
        """
        Scrape live odds from DraftKings using Selenium
        DraftKings loads odds dynamically with JavaScript
        """
        if not SELENIUM_AVAILABLE:
            print("⚠️ Selenium not available. Install with: pip install selenium")
            return []
        
        print("🔄 Fetching live odds from DraftKings (this takes 10-15 seconds)...\n")
        
        driver = None
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Navigate to DraftKings
            driver.get("https://sportsbook.draftkings.com/leagues/basketball/nba")
            
            print("⏳ Waiting for DraftKings to load (15 seconds)...")
            
            # Wait for games to load
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "event-cell"))
                )
                print("✅ Page loaded!\n")
            except:
                print("⚠️ Page took too long to load\n")
                driver.quit()
                return []
            
            # Parse games
            games = self.parse_draftkings_games(driver)
            
            if games:
                print(f"✅ DraftKings: Found {len(games)} games\n")
                self.all_games.extend(games)
            else:
                print("⚠️ DraftKings: No games found\n")
            
            return games
            
        except Exception as e:
            print(f"❌ DraftKings Error: {e}\n")
            return []
        
        finally:
            if driver:
                driver.quit()
    
    def parse_draftkings_games(self, driver):
        """Parse games from DraftKings using Selenium"""
        games = []
        
        try:
            # Get all game elements
            game_elements = driver.find_elements(By.CLASS_NAME, "event-cell")
            
            for game_elem in game_elements:
                try:
                    # Get team names
                    team_elements = game_elem.find_elements(By.CLASS_NAME, "event-cell__team")
                    
                    if len(team_elements) < 2:
                        continue
                    
                    away_team = team_elements[0].text.strip()
                    home_team = team_elements[1].text.strip()
                    
                    if not away_team or not home_team:
                        continue
                    
                    # Get odds
                    odds_elements = game_elem.find_elements(By.CLASS_NAME, "event-cell__moneyline")
                    
                    spread = "N/A"
                    moneyline = "N/A"
                    ou = "N/A"
                    
                    if len(odds_elements) >= 2:
                        moneyline = odds_elements[0].text.strip()
                    
                    game = {
                        'date': datetime.now().strftime("%Y-%m-%d"),
                        'home_team': home_team,
                        'away_team': away_team,
                        'matchup': f"{away_team} @ {home_team}",
                        'spread': spread,
                        'moneyline': moneyline,
                        'over_under': ou,
                        'source': 'DraftKings'
                    }
                    
                    games.append(game)
                    
                except Exception as e:
                    continue
            
            return games
            
        except Exception as e:
            print(f"Error parsing DraftKings: {e}")
            return []
    
    # ============ EXPORT & DISPLAY ============
    
    def export_to_csv(self, games, filename='data/live_odds.csv'):
        """Export live odds to CSV"""
        if not games:
            print("No games to export")
            return None
        
        df = pd.DataFrame(games)
        df.to_csv(filename, index=False)
        print(f"✅ Live odds exported to {filename}")
        print(f"   Total games: {len(df)}\n")
        
        return df
    
    def display_games(self, games, source=""):
        """Display games in a formatted table"""
        if not games:
            return
        
        df = pd.DataFrame(games)
        
        print("="*100)
        print(f"LIVE {source} GAMES")
        print("="*100)
        print(df.to_string(index=False))
        print()
    
    def get_all_games(self):
        """Scrape both ESPN and DraftKings"""
        print("🏀 FETCHING LIVE NBA ODDS FROM ALL SOURCES\n")
        
        # ESPN
        espn_games = self.scrape_espn_nba_odds()
        if espn_games:
            self.display_games(espn_games, "ESPN")
        
        # DraftKings
        dk_games = self.scrape_draftkings_odds()
        if dk_games:
            self.display_games(dk_games, "DRAFTKINGS")
        
        return self.all_games