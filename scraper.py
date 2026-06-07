"""
PREDIKTA — Universal Lottery Scraper
Source: Sources publiques de résultats de loterie (données factuelles)
Supports 30+ US states · Pick3 / Cash3 / Daily3 / Play3
Fetches years of historical data via monthly pagination.
"""

import requests
import urllib3
import csv
import os
import re
import time
from datetime import datetime, date
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

BASE_URL = "https://www.lotterypost.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# ── State → Pick3 game slug mapping ───────────────────────────────────────
# Format: state_code: {"slug": "...", "name": "...", "draws_per_day": N}
STATES = {
    # ── Tier 1 — High volume states ──────────────────────────────────────
    "NY": {"slug": "numbers",        "name": "New York Numbers",        "dpd": 2},
    "GA": {"slug": "cash3",          "name": "Georgia Cash 3",          "dpd": 2},
    "TX": {"slug": "pick3",          "name": "Texas Pick 3",            "dpd": 4},
    "FL": {"slug": "pick3",          "name": "Florida Pick 3",          "dpd": 2},
    "CA": {"slug": "daily3",         "name": "California Daily 3",      "dpd": 2},
    "PA": {"slug": "pick3",          "name": "Pennsylvania Pick 3",     "dpd": 2},
    "NJ": {"slug": "pick3",          "name": "New Jersey Pick 3",       "dpd": 2},
    "IL": {"slug": "pick3",          "name": "Illinois Pick 3",         "dpd": 2},
    "OH": {"slug": "pick3",          "name": "Ohio Pick 3",             "dpd": 2},
    "NC": {"slug": "pick3",          "name": "North Carolina Pick 3",   "dpd": 2},
    "VA": {"slug": "pick3",          "name": "Virginia Pick 3",         "dpd": 2},
    "MI": {"slug": "pick3",          "name": "Michigan Pick 3",         "dpd": 2},
    # ── Tier 2 — Mid-size states ──────────────────────────────────────────
    "TN": {"slug": "cash3",          "name": "Tennessee Cash 3",        "dpd": 2},
    "SC": {"slug": "pick3",          "name": "South Carolina Pick 3",   "dpd": 2},
    "CT": {"slug": "play3",          "name": "Connecticut Play 3",      "dpd": 2},
    "MD": {"slug": "pick3",          "name": "Maryland Pick 3",         "dpd": 2},
    "IN": {"slug": "daily3",         "name": "Indiana Daily 3",         "dpd": 2},
    "KY": {"slug": "pick3",          "name": "Kentucky Pick 3",         "dpd": 2},
    "MO": {"slug": "pick3",          "name": "Missouri Pick 3",         "dpd": 2},
    "AZ": {"slug": "pick3",          "name": "Arizona Pick 3",          "dpd": 1},
    "CO": {"slug": "pick3",          "name": "Colorado Pick 3",         "dpd": 2},
    "LA": {"slug": "pick3",          "name": "Louisiana Pick 3",        "dpd": 1},
    "MS": {"slug": "pick3",          "name": "Mississippi Pick 3",      "dpd": 2},
    "AR": {"slug": "cash3",          "name": "Arkansas Cash 3",         "dpd": 2},
    "IA": {"slug": "pick3",          "name": "Iowa Pick 3",             "dpd": 2},
    "KS": {"slug": "pick3",          "name": "Kansas Pick 3",           "dpd": 2},
    "OK": {"slug": "pick3",          "name": "Oklahoma Pick 3",         "dpd": 1},
    "DE": {"slug": "play3",          "name": "Delaware Play 3",         "dpd": 2},
    "NM": {"slug": "pick3",          "name": "New Mexico Pick 3",       "dpd": 2},
    "WV": {"slug": "daily3",         "name": "West Virginia Daily 3",   "dpd": 2},
    # ── Tier 3 — Additional states (newly added) ──────────────────────────
    "DC": {"slug": "pick3",          "name": "DC Pick 3",               "dpd": 2},
    "WI": {"slug": "pick3",          "name": "Wisconsin Pick 3",        "dpd": 2},
    "MN": {"slug": "pick3",          "name": "Minnesota Pick 3",        "dpd": 1},
    "NE": {"slug": "pick3",          "name": "Nebraska Pick 3",         "dpd": 1},
    "NH": {"slug": "pick3",          "name": "NH Pick 3",               "dpd": 1},
    "VT": {"slug": "pick3",          "name": "VT Pick 3",               "dpd": 1},
    "ME": {"slug": "pick3",          "name": "ME Pick 3",               "dpd": 1},
    "WA": {"slug": "pick3",          "name": "Washington Pick 3",       "dpd": 1},
    "ID": {"slug": "pick3",          "name": "Idaho Pick 3",            "dpd": 1},
    "PR": {"slug": "pega3",          "name": "Puerto Rico Pega 3",      "dpd": 1},
}


# ── Parser ────────────────────────────────────────────────────────────────

def parse_draws(html: str) -> list[dict]:
    """
    Parse lotterypost.com /past results page.
    Handles Fireball (TX/FL), multiple TODs per day.
    Returns list of {date, tod, d1, d2, d3}
    """
    soup = BeautifulSoup(html, "html.parser")
    draws = []

    for game_div in soup.select("div.resultsgame"):
        current_date = ""
        for drawing in game_div.select("div.resultsdrawing"):
            # Date: may only appear on first drawing of the day
            time_el = drawing.find("time")
            if time_el and time_el.get("datetime"):
                current_date = time_el["datetime"][:10]

            if not current_date:
                continue

            # Time of day
            tod_i = drawing.find("i", class_=re.compile(r"TOD"))
            tod = "Evening"
            if tod_i:
                classes = " ".join(tod_i.get("class", []))
                if "mid" in classes.lower():
                    tod = "Midday"
                elif "morn" in classes.lower():
                    tod = "Morning"
                elif "day" in classes.lower() and "mid" not in classes.lower():
                    tod = "Day"
                elif "nite" in classes.lower() or "night" in classes.lower():
                    tod = "Night"

            # Main numbers: take ONLY the first ul.resultsnums (ignore Fireball)
            first_ul = drawing.select_one("ul.resultsnums")
            if not first_ul:
                continue
            # Exclude orange (Fireball) li elements
            nums = [
                li.get_text(strip=True)
                for li in first_ul.find_all("li")
                if "orange" not in " ".join(li.get("class", []))
                and li.get_text(strip=True).isdigit()
            ]

            if len(nums) == 3:
                draws.append({
                    "date": current_date,
                    "tod": tod,
                    "d1": nums[0],
                    "d2": nums[1],
                    "d3": nums[2],
                })

    return draws


# ── HTTP Fetch ────────────────────────────────────────────────────────────

def fetch_url(url: str) -> str | None:
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1)
    return None


# ── Month-by-month fetcher ────────────────────────────────────────────────

def fetch_months(state_code: str, slug: str, n_months: int = 12) -> list[dict]:
    """
    Fetch up to n_months of data for a state/game, newest first.
    URL pattern: /results/{state}/{slug}/past[/{year}/{month}]
    """
    all_draws = []
    seen = set()

    now = datetime.now()
    year, month = now.year, now.month

    for i in range(n_months):
        if i == 0:
            url = f"{BASE_URL}/results/{state_code.lower()}/{slug}/past"
        else:
            url = f"{BASE_URL}/results/{state_code.lower()}/{slug}/past/{year}/{month}"

        html = fetch_url(url)
        if html:
            draws = parse_draws(html)
            new = 0
            for d in draws:
                key = f"{d['date']}_{d['tod']}"
                if key not in seen:
                    all_draws.append(d)
                    seen.add(key)
                    new += 1

        # Go back one month
        month -= 1
        if month == 0:
            month = 12
            year -= 1

        time.sleep(0.6)

    return all_draws


# ── CSV helpers ───────────────────────────────────────────────────────────

def save_csv(state_code: str, draws: list[dict]):
    path = os.path.join(DATA_DIR, f"{state_code.lower()}.csv")
    existing = {}

    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row.setdefault("tod", "Evening")
                key = f"{row['date']}_{row['tod']}"
                existing[key] = row

    for d in draws:
        key = f"{d['date']}_{d['tod']}"
        existing[key] = d

    sorted_rows = sorted(
        existing.values(),
        key=lambda r: (r["date"], r["tod"]),
        reverse=True
    )

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "tod", "d1", "d2", "d3"])
        writer.writeheader()
        writer.writerows(sorted_rows)

    return len(existing)


def load_csv(state_code: str) -> list[dict]:
    path = os.path.join(DATA_DIR, f"{state_code.lower()}.csv")
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Public API ────────────────────────────────────────────────────────────

def fetch_state(state_code: str, n_months: int = 12) -> list[dict]:
    state_code = state_code.upper()
    if state_code not in STATES:
        print(f"  [{state_code}] Unknown state")
        return []

    cfg = STATES[state_code]
    print(f"  [{state_code}] {cfg['name']} — fetching {n_months} months...")
    draws = fetch_months(state_code, cfg["slug"], n_months)
    print(f"  [{state_code}] {len(draws)} draws fetched")
    return draws


def scrape_all(states: list[str] = None, n_months: int = 12):
    targets = states or list(STATES.keys())
    for code in targets:
        draws = fetch_state(code, n_months)
        if draws:
            total = save_csv(code, draws)
            print(f"  [{code}] {total} total records saved")
        time.sleep(1)
    print("\nDone.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        codes = [s.upper() for s in sys.argv[1:]]
    else:
        codes = ["NY", "GA", "TX", "FL"]
    scrape_all(codes, n_months=24)
