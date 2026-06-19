"""
PREDIKTA — Extra official-source scrapers
Some states truly run 3 daily Pick3 draws (Midday/Evening/Night) but
lotteryusa.com doesn't publish all of them. For those states we fetch
directly from the official state-lottery API.

Each function returns a list of {date, tod, d1, d2, d3} — same shape as
scraper.parse_draws — so it can be merged via scraper.save_csv().
"""

import requests
import urllib3
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GA draws are in Eastern Time — use ET to avoid the UTC+1 day bug
# (e.g. Night draw at 11:34 PM ET = 03:34 UTC next day → wrong date if UTC used)
_EASTERN = ZoneInfo("America/New_York")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.galottery.com/en-us/games/draw-games/cash-3/winning-numbers.html",
}

GA_API = "https://www.galottery.com/api/v2/draw-games/draws/"


def _get_json(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=20, verify=False)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ── Georgia — galottery.com official API ──────────────────────────────────
# lotteryusa.com n'a pas GA Cash 3 Midday.
# lotterypost.com est bloqué par Cloudflare sur Render.
# L'API galottery.com (/api/v2/draw-games/draws/) fonctionne sans restriction.
# Elle retourne max ~50 tirages par appel (paramètre previous-draws).
# On pagine en chunks de 45 pour couvrir ~90 jours d'historique récent.
def fetch_ga_cash3(n_chunks: int = 6) -> list[dict]:
    """
    Fetch GA Cash 3 (Midday + Evening + Night) from galottery.com official API.
    Returns list of {date, tod, d1, d2, d3}.
    """
    tod_map = {
        "MIDDAY": "Midday",
        "EVENING": "Evening",
        "NIGHT": "Night",
        "DAY": "Day",
        "MORNING": "Morning",
    }

    draws = []
    seen = set()

    # Page par offset: previous-draws=0→45→90→...
    for chunk in range(n_chunks):
        offset = chunk * 45
        data = _get_json(GA_API, params={"game-names": "CASH 3", "previous-draws": offset + 30})
        if not data:
            break

        raw_draws = data.get("draws", [])
        new_this_chunk = 0

        for d in raw_draws:
            if d.get("status") not in ("CLOSED", "PAYABLE", "RESULTS_AVAILABLE"):
                continue
            results = d.get("results", [])
            if not results:
                continue
            primary = results[0].get("primary", [])
            if len(primary) < 3:
                continue

            ts = d.get("drawTime", 0) / 1000
            dt = datetime.fromtimestamp(ts, tz=_EASTERN)
            iso_date = dt.strftime("%Y-%m-%d")
            tod = tod_map.get(d.get("name", "").upper(), "Evening")

            key = f"{iso_date}_{tod}"
            if key not in seen:
                seen.add(key)
                draws.append({
                    "date": iso_date,
                    "tod": tod,
                    "d1": str(primary[0]),
                    "d2": str(primary[1]),
                    "d3": str(primary[2]),
                })
                new_this_chunk += 1

        if new_this_chunk == 0:
            break

    return draws


# ── Registry of states with an official extra-source ──────────────────────
EXTRA_SOURCES = {
    "GA": fetch_ga_cash3,
}


def fetch_extra(state_code: str) -> list[dict]:
    """Return extra draws for a state from its official source, or [] if none."""
    fn = EXTRA_SOURCES.get(state_code.upper())
    if not fn:
        return []
    try:
        return fn()
    except Exception as e:
        print(f"  [extra:{state_code}] error: {e}")
        return []


if __name__ == "__main__":
    print("Testing GA Cash 3 galottery.com API...")
    draws = fetch_ga_cash3()
    print(f"  {len(draws)} draws fetched")
    for d in draws[-5:]:
        print(f"  {d['date']} {d['tod']:8s} {d['d1']}-{d['d2']}-{d['d3']}")
