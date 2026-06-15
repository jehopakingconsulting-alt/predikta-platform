"""
PREDIKTA — lotteryusa.com generic multi-game scraper.

Same c-draw-card structure as lotteryusa_scraper.py (used for Pick3/Cash3),
but generalized to any game: main numbers come from <li class="c-ball ...">,
bonus numbers (Powerball, Mega Ball, Cash Ball, Lotto bonus, ...) come from
<li class="c-result__bonus">PB:14</li> (text after the colon).
"""

import json
import os
import re
import time
from datetime import datetime

from bs4 import BeautifulSoup

from lotteryusa_scraper import BASE_URL, fetch_url, _title_to_tod

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "lotteryusa_games_config.json")
with open(_CONFIG_PATH, encoding="utf-8") as f:
    _GAMES_CONFIG = json.load(f)


def parse_game_draws(html: str, tod: str) -> list[dict]:
    """Parse a lotteryusa.com results page into [{date, tod, nums, extra}, ...]."""
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

        ball_list = tr.select_one("ul.c-result")
        if not ball_list:
            continue

        nums = []
        extra = []
        for li in ball_list.find_all("li"):
            classes = li.get("class", [])
            text = li.get_text(strip=True)
            if "c-ball" in classes:
                if text.isdigit():
                    nums.append(text)
            elif "c-result__bonus" in classes:
                m = re.search(r":\s*(\d+)", text)
                if m:
                    extra.append(m.group(1))

        if not nums:
            continue

        draws.append({
            "date": d.strftime("%Y-%m-%d"),
            "tod": tod,
            "nums": nums,
            "extra": extra,
        })

    return draws


def fetch_game(state: str, lp_slug: str) -> list[dict]:
    """Fetch recent draws for one game via lotteryusa.com.

    Returns [] if this game isn't mapped to a lotteryusa.com slug.
    """
    info = _GAMES_CONFIG.get(state.upper(), {}).get(lp_slug)
    if not info or not info.get("lu_slug"):
        return []

    from discover_lotteryusa import STATE_SLUGS
    state_slug = STATE_SLUGS.get(state.upper())
    if not state_slug:
        return []

    # La page "/year" liste ~50 derniers tirages (vs ~10 sur la page de
    # base) — voir lotteryusa_scraper.fetch_state pour le rationnel.
    url = f"{BASE_URL}/{state_slug}/{info['lu_slug']}/year"
    html = fetch_url(url)
    if not html:
        url = f"{BASE_URL}/{state_slug}/{info['lu_slug']}/"
        html = fetch_url(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    tod = _title_to_tod(h1.get_text(strip=True)) if h1 else "Evening"

    return parse_game_draws(html, tod)


if __name__ == "__main__":
    import sys
    state = sys.argv[1].upper() if len(sys.argv) > 1 else "NY"
    for lp_slug in _GAMES_CONFIG.get(state, {}):
        draws = fetch_game(state, lp_slug)
        print(f"[{state}] {lp_slug}: {len(draws)} draws")
        for d in sorted(draws, key=lambda x: x["date"], reverse=True)[:2]:
            print("   ", d)
        time.sleep(0.2)
