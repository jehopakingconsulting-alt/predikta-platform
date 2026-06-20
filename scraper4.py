"""
ZYNORIQ — Pick 4 / Cash 4 / Win 4 / Daily 4 Scraper
Mirrors scraper.py but for 4-digit draw games.
CSV format: date, tod, d1, d2, d3, d4
"""

import requests
import urllib3
import csv
import os
import re
import time
from datetime import datetime, date
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR4 = os.path.join(os.path.dirname(__file__), "data", "pick4")
os.makedirs(DATA_DIR4, exist_ok=True)

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

# ── State → Pick4 game slug mapping (lotterypost.com) ─────────────────────
STATES4 = {
    "CA": {"slug": "daily4",  "name": "California Daily 4",       "dpd": 2},
    "CT": {"slug": "play4",   "name": "Connecticut Play 4",       "dpd": 2},
    "DC": {"slug": "dc4",     "name": "DC Pick 4",                "dpd": 2},
    "DE": {"slug": "play4",   "name": "Delaware Play 4",          "dpd": 2},
    "FL": {"slug": "pick4",   "name": "Florida Pick 4",           "dpd": 2},
    "GA": {"slug": "cash4",   "name": "Georgia Cash 4",           "dpd": 3},
    "IL": {"slug": "pick4",   "name": "Illinois Pick 4",          "dpd": 2},
    "IN": {"slug": "daily4",  "name": "Indiana Daily 4",          "dpd": 2},
    "KY": {"slug": "pick4",   "name": "Kentucky Pick 4",          "dpd": 2},
    "MD": {"slug": "pick4",   "name": "Maryland Pick 4",          "dpd": 2},
    "MI": {"slug": "daily4",  "name": "Michigan Daily 4",         "dpd": 2},
    "MO": {"slug": "pick4",   "name": "Missouri Pick 4",          "dpd": 2},
    "NC": {"slug": "pick4",   "name": "North Carolina Pick 4",    "dpd": 2},
    "NJ": {"slug": "pick4",   "name": "New Jersey Pick 4",        "dpd": 2},
    "NY": {"slug": "win4",    "name": "New York Win 4",           "dpd": 2},
    "OH": {"slug": "pick4",   "name": "Ohio Pick 4",              "dpd": 2},
    "PA": {"slug": "pick4",   "name": "Pennsylvania Pick 4",      "dpd": 2},
    "SC": {"slug": "pick4",   "name": "South Carolina Pick 4",    "dpd": 2},
    "TN": {"slug": "cash4",   "name": "Tennessee Cash 4",         "dpd": 2},
    "TX": {"slug": "daily4",  "name": "Texas Daily 4",            "dpd": 4},
    "VA": {"slug": "pick4",   "name": "Virginia Pick 4",          "dpd": 2},
    "WI": {"slug": "pick4",   "name": "Wisconsin Pick 4",         "dpd": 2},
}

HOT_PICK4_STATES = ["NY", "FL", "GA", "TX", "NJ", "PA"]

MIN_HISTORY_DRAWS = 100


def _do_get(url: str):
    if cffi_requests is not None:
        return cffi_requests.get(url, impersonate="chrome124", timeout=30, verify=False)
    return requests.get(url, headers=HEADERS, timeout=20, verify=False)


def fetch_url(url: str) -> str | None:
    for attempt in range(3):
        try:
            resp = _do_get(url)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1)
    return None


def parse_draws4(html: str) -> list[dict]:
    """
    Parse lotterypost.com past results page for Pick 4 games.
    Returns list of {date, tod, d1, d2, d3, d4}
    """
    soup = BeautifulSoup(html, "html.parser")
    draws = []

    for game_div in soup.select("div.resultsgame"):
        current_date = ""
        for drawing in game_div.select("div.resultsdrawing"):
            time_el = drawing.find("time")
            if time_el and time_el.get("datetime"):
                current_date = time_el["datetime"][:10]

            if not current_date:
                continue

            tod_i = drawing.find("i", class_=re.compile(r"TOD"))
            tod = "Evening"
            if tod_i:
                label_txt = ""
                tod_box = tod_i.find_parent(class_=re.compile(r"\bTOD\b"))
                if tod_box:
                    label_txt = tod_box.get_text(strip=True).lower()
                classes = " ".join(tod_i.get("class", [])).lower()
                tmatch = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', label_txt)
                if tmatch:
                    h = int(tmatch.group(1)) % 12
                    if tmatch.group(3) == "pm": h += 12
                    if h < 12: tod = "Morning"
                    elif h < 17: tod = "Midday"
                    elif h < 21: tod = "Evening"
                    else: tod = "Night"
                else:
                    hay = label_txt or classes
                    if "mid" in hay:
                        tod = "Midday"
                    elif "morn" in hay:
                        tod = "Morning"
                    elif "nite" in hay or "night" in hay or "noche" in hay:
                        tod = "Night"
                    elif "eve" in hay:
                        tod = "Evening"
                    elif "daytime" in hay:
                        tod = "Midday"
                    elif "day" in hay or "día" in hay or "dia" in hay:
                        tod = "Midday"

            # Take only the first ul.resultsnums, expect exactly 4 digits
            first_ul = drawing.select_one("ul.resultsnums")
            if not first_ul:
                continue
            nums = [
                li.get_text(strip=True)
                for li in first_ul.find_all("li")
                if "orange" not in " ".join(li.get("class", []))
                and li.get_text(strip=True).isdigit()
            ]

            if len(nums) == 4:
                draws.append({
                    "date": current_date,
                    "tod": tod,
                    "d1": nums[0],
                    "d2": nums[1],
                    "d3": nums[2],
                    "d4": nums[3],
                })

    return draws


def fetch_months4(state_code: str, slug: str, n_months: int = 12) -> list[dict]:
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
            draws = parse_draws4(html)
            for d in draws:
                key = f"{d['date']}_{d['tod']}"
                if key not in seen:
                    all_draws.append(d)
                    seen.add(key)

        month -= 1
        if month == 0:
            month = 12
            year -= 1

        time.sleep(0.6)

    return all_draws


_CSV4_CACHE: dict[str, tuple[float, list[dict]]] = {}


def save_csv4(state_code: str, draws: list[dict]):
    path = os.path.join(DATA_DIR4, f"{state_code.lower()}.csv")
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
        writer = csv.DictWriter(f, fieldnames=["date", "tod", "d1", "d2", "d3", "d4"])
        writer.writeheader()
        writer.writerows(sorted_rows)

    _CSV4_CACHE.pop(state_code, None)
    return len(existing)


def load_csv4(state_code: str) -> list[dict]:
    path = os.path.join(DATA_DIR4, f"{state_code.lower()}.csv")
    if not os.path.exists(path):
        return []
    mtime = os.path.getmtime(path)
    cached = _CSV4_CACHE.get(state_code)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    _CSV4_CACHE[state_code] = (mtime, rows)
    return rows


def _existing_draw_count4(state_code: str) -> int:
    path = os.path.join(DATA_DIR4, f"{state_code.lower()}.csv")
    if not os.path.exists(path):
        return 0
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


def fetch_state4(state_code: str, n_months: int = 12) -> list[dict]:
    state_code = state_code.upper()
    if state_code not in STATES4:
        print(f"  [{state_code}] Unknown Pick4 state")
        return []

    cfg = STATES4[state_code]
    print(f"  [{state_code}] {cfg['name']} (Pick4) — fetching...")

    # Essayer lotteryusa.com en priorité (pas de Cloudflare, fonctionne sur Render)
    draws = []
    try:
        import lotteryusa4_scraper
        draws = lotteryusa4_scraper.fetch_state4(state_code)
        if draws:
            print(f"  [{state_code}] {len(draws)} Pick4 draws via lotteryusa.com")
    except Exception as e:
        print(f"  [{state_code}] lotteryusa4 failed: {e}")

    # Repli sur lotterypost.com si nécessaire
    if not draws:
        print(f"  [{state_code}] fallback: lotterypost.com")
        draws = fetch_months4(state_code, cfg["slug"], max(n_months, 12))

    # Compléter si historique insuffisant
    if draws:
        existing = _existing_draw_count4(state_code)
        seen = {f"{d['date']}_{d['tod']}" for d in draws}
        if existing + len(seen) < MIN_HISTORY_DRAWS:
            print(f"  [{state_code}] historique insuffisant — backfill lotterypost.com")
            backfill = fetch_months4(state_code, cfg["slug"], max(n_months, 12))
            added = 0
            for d in backfill:
                key = f"{d['date']}_{d['tod']}"
                if key not in seen:
                    draws.append(d)
                    seen.add(key)
                    added += 1
            if added:
                print(f"  [{state_code}] +{added} draws ajoutés via lotterypost.com")

    if not draws:
        print(f"  [{state_code}] No Pick4 draws found")
        return []

    print(f"  [{state_code}] {len(draws)} Pick4 draws fetched total")
    return draws


def scrape_all4(states: list[str] = None, n_months: int = 12):
    targets = states or list(STATES4.keys())
    for code in targets:
        draws = fetch_state4(code, n_months)
        if draws:
            total = save_csv4(code, draws)
            print(f"  [{code}] {total} Pick4 records saved")
        time.sleep(1)
    print("\nDone (Pick4).")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        codes = [s.upper() for s in sys.argv[1:]]
    else:
        codes = ["NY", "GA", "TX", "FL"]
    scrape_all4(codes, n_months=24)
