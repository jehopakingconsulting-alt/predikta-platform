"""
PREDIKTA — Extra official-source scrapers
Some states truly run 3-4 daily Pick3 draws (Morning/Day/Evening/Night) but
lotterypost.com only republishes Midday/Evening. For those states we fetch
directly from the official state-lottery site so Matin/Jour/Soir/Nuit are
all available for analysis.

Each function returns a list of {date, tod, d1, d2, d3} — same shape as
scraper.parse_draws — so it can be merged via scraper.save_csv().
"""

import re
import requests
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}


def _get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


# ── Texas Lottery — official Pick 3 (Morning / Day / Evening / Night) ─────
def fetch_tx_official():
    url = "https://www.texaslottery.com/export/sites/lottery/Games/Pick_3/Winning_Numbers/index.html"
    html = _get(url)
    if not html:
        return []

    draws = []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    tods = ["Morning", "Day", "Evening", "Night"]

    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) < 8:
            continue
        # cell[0] = date link
        date_m = re.search(r">(\d{2}/\d{2}/\d{4})<", cells[0])
        if not date_m:
            continue
        try:
            iso_date = datetime.strptime(date_m.group(1), "%m/%d/%Y").strftime("%Y-%m-%d")
        except Exception:
            continue

        # numbers are in cells 1, 3, 5, 7 (Fireball is the cell right after each)
        for idx, tod in zip([1, 3, 5, 7], tods):
            if idx >= len(cells):
                continue
            txt = re.sub(r"&nbsp;", " ", cells[idx])
            nums = re.findall(r"\d", txt)
            if len(nums) >= 3:
                draws.append({
                    "date": iso_date,
                    "tod": tod,
                    "d1": nums[0], "d2": nums[1], "d3": nums[2],
                })

    return draws


# ── Registry of states with an official 4-draws/day source ────────────────
EXTRA_SOURCES = {
    "TX": fetch_tx_official,
}


def fetch_extra(state_code: str):
    """Return extra (Morning/Day/Night) draws for a state, or [] if none configured."""
    fn = EXTRA_SOURCES.get(state_code.upper())
    if not fn:
        return []
    try:
        return fn()
    except Exception as e:
        print(f"  [extra:{state_code}] error: {e}")
        return []
