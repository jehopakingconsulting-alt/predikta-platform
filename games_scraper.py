"""
PREDIKTA AI — Multi-Game Scraper
Fetches ALL lottery games per state from lotterypost.com
Handles Pick2, Pick3, Pick4, Pick5, Pick6, Powerball, Mega Millions, etc.
"""

import requests, urllib3, re, time, json, os
from bs4 import BeautifulSoup
from datetime import datetime, date
from games_config import STATE_GAMES, GAME_TYPES

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://www.lotterypost.com"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "games")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.5",
}


def fetch_url(url: str) -> str | None:
    for _ in range(2):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(0.5)
    return None


def parse_game_results(html: str, game_type: str) -> list[dict]:
    """
    Parse lotterypost results page for any game type.
    Returns list of draws with all numbers.
    """
    soup = BeautifulSoup(html, "html.parser")
    draws = []
    gt = GAME_TYPES.get(game_type, GAME_TYPES["pick3"])
    expected_main = gt["num_balls"]
    expected_extra = gt["extra_balls"]

    for game_div in soup.select("div.resultsgame"):
        current_date = ""
        for drawing in game_div.select("div.resultsdrawing"):
            # Date
            time_el = drawing.find("time")
            if time_el and time_el.get("datetime"):
                current_date = time_el["datetime"][:10]
            if not current_date:
                continue

            # TOD
            tod_i = drawing.find("i", class_=re.compile(r"TOD"))
            tod = "Evening"
            if tod_i:
                cls = " ".join(tod_i.get("class", []))
                tod = "Midday" if "mid" in cls.lower() else "Morning" if "morn" in cls.lower() else "Evening"

            # All number groups in this drawing
            num_rows = drawing.select("div.resultsnumsrow")
            all_nums = []
            extra_nums = []

            for row in num_rows:
                ul = row.select_one("ul.resultsnums")
                if not ul:
                    continue
                nums_in_row = [
                    li.get_text(strip=True)
                    for li in ul.find_all("li")
                    if li.get_text(strip=True).isdigit()
                    and "orange" not in " ".join(li.get("class", []))  # exclude Fireball
                ]
                # Determine if this is extra ball row (usually contains fewer numbers)
                is_extra = "fireball" in row.get_text(strip=True).lower() or \
                           "powerball" in row.get_text(strip=True).lower() or \
                           "mega" in row.get_text(strip=True).lower() or \
                           (len(nums_in_row) <= 2 and len(all_nums) > 0)

                if is_extra:
                    extra_nums.extend(nums_in_row[:expected_extra] if expected_extra else [])
                else:
                    all_nums.extend(nums_in_row)

            # Also check for separate extra ball row styling
            extra_divs = drawing.select("div.resultsnumsrow ul.resultsnums li.purple, div.resultsnumsrow ul.resultsnums li.blue")
            if extra_divs:
                extra_nums = [li.get_text(strip=True) for li in extra_divs]
                # Remove extra from all_nums if accidentally included
                all_nums = [n for n in all_nums if n not in extra_nums]

            if not all_nums:
                continue

            draw = {
                "date":  current_date,
                "tod":   tod,
                "nums":  all_nums[:max(expected_main, len(all_nums))],
                "extra": extra_nums[:expected_extra] if expected_extra else [],
            }

            # Validate minimum numbers
            if len(draw["nums"]) >= min(expected_main, 2):
                draws.append(draw)

    return draws


def fetch_game(state: str, game: dict, n_months: int = 3) -> list[dict]:
    """Fetch recent results for one game."""
    slug = game["slug"]
    game_type = game["type"]
    label = game["label"]

    all_draws = []
    seen = set()
    now = datetime.now()
    year, month = now.year, now.month

    for i in range(n_months):
        url = (f"{BASE_URL}/results/{state.lower()}/{slug}/past"
               if i == 0
               else f"{BASE_URL}/results/{state.lower()}/{slug}/past/{year}/{month}")

        html = fetch_url(url)
        if html:
            draws = parse_game_results(html, game_type)
            for d in draws:
                key = f"{d['date']}_{d['tod']}"
                if key not in seen:
                    all_draws.append(d)
                    seen.add(key)

        month -= 1
        if month == 0: month = 12; year -= 1
        time.sleep(0.4)

    return all_draws


def save_game_results(state: str, game: dict, draws: list[dict]):
    """Save game results to JSON (more flexible than CSV for variable ball counts)."""
    state_dir = os.path.join(DATA_DIR, state.upper())
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, f"{game['slug']}.json")

    existing = {}
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            existing = json.load(f)

    for d in draws:
        key = f"{d['date']}_{d['tod']}"
        existing[key] = d

    # Sort newest first
    sorted_draws = sorted(existing.values(), key=lambda x: x["date"], reverse=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(sorted_draws, f, indent=2, ensure_ascii=False)

    return len(sorted_draws)


def load_game_results(state: str, slug: str) -> list[dict]:
    path = os.path.join(DATA_DIR, state.upper(), f"{slug}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def fetch_all_games_for_state(state: str, n_months: int = 2) -> dict:
    """Fetch all games for a state. Returns {slug: draws}."""
    state = state.upper()
    games = STATE_GAMES.get(state, [])
    if not games:
        print(f"  [{state}] No games configured")
        return {}

    results = {}
    for game in games:
        print(f"  [{state}] {game['label']}...")
        draws = fetch_game(state, game, n_months)
        if draws:
            total = save_game_results(state, game, draws)
            print(f"    → {len(draws)} new · {total} total")
        else:
            print(f"    → No data (game may not exist or requires login)")
        results[game["slug"]] = draws
        time.sleep(0.6)

    return results


def get_today_all_games(state: str) -> list[dict]:
    """
    Get today's (or most recent) results for all games in a state.
    Returns list of game results for display.
    """
    state = state.upper()
    games = STATE_GAMES.get(state, [])
    today = date.today().isoformat()
    yesterday = date.today().isoformat()

    results = []
    for game in games:
        draws = load_game_results(state, game["slug"])
        if not draws:
            continue

        # Get the most recent draws (today or yesterday)
        by_date = {}
        for d in draws:
            by_date.setdefault(d["date"], []).append(d)

        if not by_date:
            continue

        latest_date = max(by_date.keys())
        latest_draws = sorted(by_date[latest_date], key=lambda x: x.get("tod", ""))
        is_today = latest_date == today

        gt = GAME_TYPES.get(game["type"], {})
        results.append({
            "slug":      game["slug"],
            "label":     game["label"],
            "game_type": game["type"],
            "icon":      gt.get("icon", "🎰"),
            "num_balls": gt.get("num_balls", 3),
            "extra_balls": gt.get("extra_balls", 0),
            "date":      latest_date,
            "is_today":  is_today,
            "draws":     latest_draws,
        })

    return results


if __name__ == "__main__":
    import sys
    states = sys.argv[1:] if len(sys.argv) > 1 else ["NY", "GA", "TX", "FL"]
    for state in states:
        print(f"\n[{state}] Fetching all games...")
        fetch_all_games_for_state(state, n_months=1)
    print("\nDone.")
