import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options  
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup
import csv
import time

MAIN_YEARS_URL = "https://www.baseball-almanac.com/yearmenu.shtml"

def clean_champion_text(raw_text):
    if not raw_text:
        return "Not found"
    text = raw_text.strip()
    if not text:
        return "Not found"

    # Extract only letters and spaces up to where team name ends
    match = re.match(r'^([A-Za-z\s]+)', text)
    if match:
        cleaned = match.group(1).strip()
        if cleaned:
            return cleaned
    return text  # fallback if regex fails

def extract_champion_team(line):
    team_suffixes = [
        "Athletics", "Red Stockings", "Wolves", "White Stockings",
        "Browns", "Orioles", "Wolverines", "Blues",
        "Metropolitans", "Alleghenys", "Giants", "Dodgers",
        "Yankees", "Mets", "Cardinals", "Cubs", "Tigers",
        "Phillies", "Indians", "Braves", "Red Sox",
    ]
    suffix_pattern = "|".join(team_suffixes)
    pattern = re.compile(
        rf"champion(?:ship)?(?:\s*[\:\-–]?\s*)([A-Z][a-zA-Z\s]*?(?:{suffix_pattern}))\b", 
        re.IGNORECASE
    )
    match = pattern.search(line)
    if match:
        team_name = clean_champion_text(match.group(1))
        print(f"[DEBUG] Matched champion team: '{team_name}' in line: '{line}'")
        return team_name

    alt_pattern = re.compile(
        rf"(?:champion|pennant winner|league champion)(?:ship)?(?:\s*[\:\-–]?\s*)([A-Z][a-zA-Z\s]*?(?:{suffix_pattern}))\b",
        re.IGNORECASE
    )
    alt_match = alt_pattern.search(line)
    if alt_match:
        team_name = clean_champion_text(alt_match.group(1))
        print(f"[DEBUG] Matched alternate champion team: '{team_name}' in line: '{line}'")
        return team_name

    print(f"[DEBUG] No champion found in line: '{line}'")
    return "Not found"

def get_year_links(driver):
    driver.get(MAIN_YEARS_URL)
    print(f"Loading main page {MAIN_YEARS_URL}")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
    except TimeoutException:
        print("Timeout loading main years page")
        return []

    links = []
    anchor_tags = driver.find_elements(By.TAG_NAME, "a")
    for a in anchor_tags:
        href = a.get_attribute("href")
        if href and "yr" in href and href.endswith("a.shtml"):
            year_part = href.split("/")[-1]
            year_str = year_part[2:6]
            if year_str.isdigit():
                year = int(year_str)
                links.append((year, href))
    print(f"Found {len(links)} year links")
    return sorted(links, key=lambda x: x[0])

def get_yearly_stats(url, driver):
    all_teams = []
    try:
        print(f"\nScraping {url}")
        driver.get(url)
        time.sleep(2)  # wait for full load
        print(f"Page title: {driver.title}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        tables = soup.find_all("table")
        print(f"Found {len(tables)} tables on page")

        team_table = None

        # Try to find table by caption or table text containing "standings"
        for i, table in enumerate(tables):
            caption = table.find("caption")
            caption_text = caption.get_text(strip=True).lower() if caption else ""
            table_text = table.get_text(separator=" ").lower()

            if "standings" in caption_text or "team standings" in caption_text:
                team_table = table
                print(f"Selected Table {i} by caption: {caption_text}")
                break
            elif "standings" in table_text or "team standings" in table_text:
                team_table = table
                print(f"Selected Table {i} by table text containing 'standings'")
                break

        # Fallback heuristic if no table found yet
        if not team_table:
            for i, table in enumerate(tables):
                rows = table.find_all("tr")
                if len(rows) < 5:
                    continue
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 3:
                        first_col = cols[0].get_text(strip=True)
                        try:
                            wins = int(cols[1].get_text(strip=True))
                            losses = int(cols[2].get_text(strip=True))
                            team_table = table
                            print(f"Selected Table {i} by heuristic on row: {first_col}")
                            break
                        except ValueError:
                            continue
                if team_table:
                    break

        if not team_table:
            print(f"No suitable team stats table found on {url}")
            return None

        rows = team_table.find_all("tr")[1:]
        print(f"Found {len(rows)} rows in team table")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                team = cols[0].get_text(strip=True)
                try:
                    wins = int(cols[1].get_text(strip=True))
                    losses = int(cols[2].get_text(strip=True))
                    print(f"Parsed wins: {wins}, losses: {losses} for team {team}")
                    all_teams.append({"team": team, "wins": wins, "losses": losses})
                except ValueError as ve:
                    print(f"ValueError parsing wins/losses: {ve} in row: {[c.get_text(strip=True) for c in cols]}")
                    continue

        if not all_teams:
            print(f"No team data found on {url}")
            return None

        most_wins = max(all_teams, key=lambda x: x["wins"])
        most_losses = max(all_teams, key=lambda x: x["losses"])

        # Improved champion line search
        body_text = soup.get_text(separator="\n")
        keywords = ["world series champion", "world champion", "champion", "pennant winner", "league champion"]
        candidate_lines = []

        for line in body_text.splitlines():
            lowered = line.lower()
            if any(kw in lowered for kw in keywords):
                candidate_lines.append(line.strip())

        if candidate_lines:
            # Pick the longest line as champion description
            champion_line = max(candidate_lines, key=len)
            champion_line = extract_champion_team(champion_line)
        else:
            champion_line = "Not found"

        print(f"Champion line: {champion_line}")

        return {
            "most_wins": most_wins["team"],
            "most_losses": most_losses["team"],
            "champion": champion_line
        }

    except Exception as e:
        print(f"Error scraping stats from {url}: {e}")
        return None

def get_yearly_content(url, year, writer, driver):
    try:
        print(f"Scraping content: {url}")
        driver.get(url)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        content_div = soup.find("div", class_="main-content") or soup.find("body")
        if content_div:
            paragraphs = content_div.find_all(["p", "ul", "ol"])
            for para in paragraphs:
                section_text = para.get_text(strip=True)
                if not section_text:
                    continue
                lowered = section_text.lower()
                if (
                    lowered.startswith("copyright") or
                    "preserved today" in lowered or
                    "hosted by" in lowered
                ):
                    continue  # skip footer/junk
                
                tag_name = para.name
                section_type = "Event Summary" if tag_name == "p" else "Event List"

                writer.writerow({
                    "Year": year,
                    "Section": section_type,
                    "Content": section_text
                })
    except Exception as e:
        print(f"Error fetching content for {year}: {e}")

def save_stats_csv(stats_list, filename="mlb_stats_summary.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as statsfile:
        fieldnames = ["Year", "Most Wins", "Most Losses", "Champion"]
        writer = csv.DictWriter(statsfile, fieldnames=fieldnames)
        writer.writeheader()
        for stats in stats_list:
            writer.writerow({
                "Year": stats["year"],
                "Most Wins": stats["most_wins"],
                "Most Losses": stats["most_losses"],
                "Champion": stats["champion"]
            })

def main():
    options = Options()
    options.add_argument("--headless")
    options.set_preference("general.useragent.override", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    )

    driver = webdriver.Firefox(options=options)
    print("Browser opened using:", driver.capabilities["browserName"])

    all_stats = []

    with open("mlb_history_sections.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Year", "Section", "Content"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        try:
            year_links = get_year_links(driver)
            if not year_links:
                print("No year links found. Exiting.")
                return
            
            for year, url in year_links:
                if year > 2025:
                    print(f"Reached year {year}, stopping as requested.")
                    break

                stats = get_yearly_stats(url, driver)
                if stats:
                    stats["year"] = year
                    all_stats.append(stats)
                    print(f"{year}: {stats}")
                else:
                    print(f"Skipping {year} due to missing stats.")

                get_yearly_content(url, year, writer, driver)

        finally:
            driver.quit()

    save_stats_csv(all_stats)

if __name__ == "__main__":
    main()
