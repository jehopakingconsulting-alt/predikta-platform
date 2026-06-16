"""
PREDIKTA — lotteryusa.com scraper pour Pick 4 / Cash 4 / Win 4 / Daily 4
Miroir de lotteryusa_scraper.py mais pour les jeux 4 chiffres.
lotteryusa.com n'est pas derrière Cloudflare — fonctionne depuis Render.
"""

import json
import os
import time
from datetime import datetime

from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

import requests

BASE_URL = "https://www.lotteryusa.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.5",
}

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "lotteryusa4_config.json")
with open(_CONFIG_PATH, encoding="utf-8") as f:
    _CONFIG4 = json.load(f)

_TOD_WORDS = {
    "evening": "Evening",
    "midday":  "Midday",
    "mid-day": "Midday",
    "morning": "Morning",
    "night":   "Night",
    "day":     "Midday",
}


def _title_to_tod(title: str) -> str:
    low = title.lower()
    for word, tod in _TOD_WORDS.items():
        if word in low:
            return tod
    return "Evening"


def fetch_url(url: str) -> str | None:
    for _ in range(3):
        try:
            if cffi_requests is not None:
                r = cffi_requests.get(url, impersonate="chrome124", timeout=20, verify=False)
            else:
                r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            if r.status_code == 200:
                return r.text
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(0.5)
    return None


def parse_draws4(html: str, tod: str) -> list[dict]:
    """Parse a lotteryusa.com results page for 4-digit games."""
    soup = BeautifulSoup(html, "html.parser")
    draws = []

    for tr in soup.select("table.c-results-table tr.c-draw-card"):
        date_sub = tr.select_one("time.c-draw-card__draw-date .c-draw-card__draw-date-sub")
        if not date_sub:
            continue
        try:
            d = datetime.strptime(date_sub.get_text(strip=True), "%b %d, %Y")
        except ValueError:
            continue

        ball_list = tr.select_one("ul.c-result.c-draw-card__ball-list")
        if not ball_list:
            continue
        digits = [li.get_text(strip=True) for li in ball_list.find_all("li")]
        digits = [dg for dg in digits if dg.isdigit()]
        if len(digits) != 4:
            continue

        draws.append({
            "date": d.strftime("%Y-%m-%d"),
            "tod":  tod,
            "d1":   digits[0],
            "d2":   digits[1],
            "d3":   digits[2],
            "d4":   digits[3],
        })

    return draws


def fetch_state4(state_code: str) -> list[dict]:
    """Fetch all Pick 4 TOD pages for a state from lotteryusa.com."""
    cfg = _CONFIG4.get(state_code.upper())
    if not cfg:
        return []

    state_slug = cfg["state_slug"]
    all_draws = []
    seen = set()

    for variant in cfg.get("variants", {}).values():
        slug  = variant["slug"]
        tod   = _title_to_tod(variant["title"])
        url   = f"{BASE_URL}/{state_slug}/{slug}/year"
        html  = fetch_url(url)
        if not html:
            url  = f"{BASE_URL}/{state_slug}/{slug}/"
            html = fetch_url(url)
        if not html:
            print(f"  [{state_code}] lotteryusa4: no data for {slug}")
            continue

        draws = parse_draws4(html, tod)
        print(f"  [{state_code}] lotteryusa4: {len(draws)} draws via {slug} ({tod})")
        for draw in draws:
            key = f"{draw['date']}_{draw['tod']}"
            if key not in seen:
                all_draws.append(draw)
                seen.add(key)
        time.sleep(0.3)

    return all_draws


if __name__ == "__main__":
    import sys
    codes = [s.upper() for s in sys.argv[1:]] or ["NY", "GA", "TX", "FL", "NJ", "PA"]
    for code in codes:
        draws = fetch_state4(code)
        print(f"[{code}] {len(draws)} Pick4 draws total")
        for d in sorted(draws, key=lambda x: (x["date"], x["tod"]), reverse=True)[:3]:
            print("   ", d)
