"""
PREDIKTA — Smart Multi-Source Scraper
Chaîne de sources avec fallback automatique pour tous les États.

Ordre de priorité :
  1. lotteryusa.com   — aucun Cloudflare, stable, résultats ~15 min après tirage
  2. usamega.com      — backup gratuit, structure HTML simple
  3. lotterypost.com  — dernier recours (curl_cffi TLS impersonation)

Usage :
  from smart_scraper import scrape_state, scrape_states_batch, scrape_all_smart
"""

import csv
import os
import re
import time
import threading
from datetime import datetime, date, timedelta, timezone

import requests
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Résultats de chaque source (suivi de fiabilité) ───────────────────────
_source_stats: dict[str, dict] = {}  # {state: {source: ok_count, fail_count}}
_stats_lock = threading.Lock()

def _record(state: str, source: str, ok: bool):
    with _stats_lock:
        s = _source_stats.setdefault(state, {})
        key = f"{source}_{'ok' if ok else 'fail'}"
        s[key] = s.get(key, 0) + 1

def get_source_stats() -> dict:
    with _stats_lock:
        return dict(_source_stats)


# ══════════════════════════════════════════════════════════════════════════
# SOURCE 1 — lotteryusa.com
# ══════════════════════════════════════════════════════════════════════════

def _scrape_lotteryusa(state: str) -> list[dict]:
    """Délègue à lotteryusa_scraper.fetch_state() déjà éprouvé."""
    try:
        from lotteryusa_scraper import fetch_state
        draws = fetch_state(state)
        _record(state, "lotteryusa", bool(draws))
        return draws
    except Exception as e:
        print(f"  [smart][lotteryusa][{state}] error: {e}")
        _record(state, "lotteryusa", False)
        return []


# ══════════════════════════════════════════════════════════════════════════
# SOURCE 2 — usamega.com
# ══════════════════════════════════════════════════════════════════════════

# Mapping état → slug usamega.com
_USAMEGA_STATE_SLUGS = {
    "AR": "arkansas", "AZ": "arizona",  "CA": "california", "CO": "colorado",
    "CT": "connecticut", "DC": "dc",    "DE": "delaware",   "FL": "florida",
    "GA": "georgia",  "IA": "iowa",     "ID": "idaho",      "IL": "illinois",
    "IN": "indiana",  "KS": "kansas",   "KY": "kentucky",   "LA": "louisiana",
    "MA": "massachusetts", "MD": "maryland", "ME": "maine", "MI": "michigan",
    "MN": "minnesota", "MO": "missouri","MS": "mississippi","NC": "north-carolina",
    "NE": "nebraska", "NH": "new-hampshire", "NJ": "new-jersey", "NM": "new-mexico",
    "NY": "new-york", "OH": "ohio",     "OK": "oklahoma",   "OR": "oregon",
    "PA": "pennsylvania", "PR": "puerto-rico", "SC": "south-carolina",
    "TN": "tennessee","TX": "texas",    "VA": "virginia",   "VT": "vermont",
    "WA": "washington","WI": "wisconsin","WV": "west-virginia",
}

# Mapping état → slug du jeu Pick 3 sur usamega.com
_USAMEGA_GAME_SLUGS = {
    "AR": "cash-3",      "AZ": "pick-3",      "CA": "daily-3",
    "CO": "pick-3",      "CT": "play-3",       "DC": "dc-3",
    "DE": "play-3",      "FL": "pick-3",       "GA": "cash-3",
    "IA": "pick-3",      "ID": "pick-3",       "IL": "pick-3",
    "IN": "daily-3",     "KS": "pick-3",       "KY": "pick-3",
    "LA": "pick-3",      "MA": "the-numbers-game", "MD": "pick-3",
    "ME": "pick-3",      "MI": "daily-3",      "MN": "pick-3",
    "MO": "pick-3",      "MS": "pick-3",       "NC": "pick-3",
    "NE": "pick-3",      "NH": "pick-3",       "NJ": "pick-3",
    "NM": "pick-3",      "NY": "numbers",      "OH": "pick-3",
    "OK": "pick-3",      "OR": "pick-3",       "PA": "pick-3",
    "PR": "pega-3",      "SC": "pick-3",       "TN": "cash-3",
    "TX": "pick-3",      "VA": "pick-3",       "VT": "pick-3",
    "WA": "pick-3",      "WI": "pick-3",       "WV": "daily-3",
}

_USAMEGA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.usamega.com/",
}

_TOD_WORDS = {
    "midday": "Midday", "mid-day": "Midday", "noon": "Midday", "day": "Midday",
    "evening": "Evening", "eve": "Evening",
    "morning": "Morning", "morn": "Morning",
    "night": "Night", "nite": "Night",
}

def _parse_usamega_tod(text: str) -> str:
    low = text.lower()
    for word, tod in _TOD_WORDS.items():
        if word in low:
            return tod
    return "Evening"


def _parse_usamega_html(html: str, default_tod: str = "Evening") -> list[dict]:
    """Parse usamega.com results page for Pick 3 draws."""
    soup = BeautifulSoup(html, "html.parser")
    draws = []

    # usamega.com uses <table> with rows containing date + numbers
    for row in soup.select("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        date_cell = cells[0].get_text(strip=True)
        # Try to parse date — formats: "Jun 19, 2026" or "06/19/2026"
        draw_date = None
        for fmt in ("%b %d, %Y", "%m/%d/%Y", "%B %d, %Y"):
            try:
                draw_date = datetime.strptime(date_cell[:15], fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                pass
        if not draw_date:
            # Try extracting date from raw text
            m = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', date_cell)
            if m:
                try:
                    draw_date = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
                except Exception:
                    pass
        if not draw_date:
            continue

        # Find 3 single digits in the row
        all_text = " ".join(c.get_text(strip=True) for c in cells[1:])
        digits = re.findall(r'\b(\d)\b', all_text)
        if len(digits) < 3:
            # Try splitting numbers like "1-2-3" or "123"
            nums_raw = re.findall(r'\d[\-\s]?\d[\-\s]?\d', all_text)
            if nums_raw:
                clean = re.sub(r'[\-\s]', '', nums_raw[0])
                if len(clean) == 3:
                    digits = list(clean)
        if len(digits) < 3:
            continue

        # TOD from row class or sibling text
        tod = default_tod
        row_class = " ".join(row.get("class", []))
        row_text = row.get_text(" ", strip=True)
        for word, t in _TOD_WORDS.items():
            if word in row_class.lower() or word in row_text.lower():
                tod = t
                break

        draws.append({
            "date": draw_date,
            "tod": tod,
            "d1": digits[0],
            "d2": digits[1],
            "d3": digits[2],
        })

    return draws


def _scrape_usamega(state: str) -> list[dict]:
    """Scrape usamega.com pour un état donné (Pick 3)."""
    state_slug = _USAMEGA_STATE_SLUGS.get(state)
    game_slug  = _USAMEGA_GAME_SLUGS.get(state)
    if not state_slug or not game_slug:
        return []

    draws = []
    base = f"https://www.usamega.com/{state_slug}/{game_slug}"
    urls = [f"{base}/results", f"{base}-results", base]

    for url in urls:
        try:
            r = requests.get(url, headers=_USAMEGA_HEADERS, timeout=20, verify=False)
            if r.status_code == 200 and len(r.text) > 500:
                d = _parse_usamega_html(r.text)
                if d:
                    draws = d
                    break
        except Exception:
            pass
        time.sleep(0.3)

    _record(state, "usamega", bool(draws))
    return draws


# ══════════════════════════════════════════════════════════════════════════
# SOURCE 3 — lotterypost.com (curl_cffi TLS impersonation)
# ══════════════════════════════════════════════════════════════════════════

def _scrape_lotterypost(state: str) -> list[dict]:
    """Délègue à scraper.fetch_months() avec curl_cffi pour passer Cloudflare."""
    try:
        from scraper import fetch_months, STATES
        info = STATES.get(state)
        if not info:
            _record(state, "lotterypost", False)
            return []
        draws = fetch_months(state, info["slug"], n_months=1)
        _record(state, "lotterypost", bool(draws))
        return draws
    except Exception as e:
        print(f"  [smart][lotterypost][{state}] error: {e}")
        _record(state, "lotterypost", False)
        return []


# ══════════════════════════════════════════════════════════════════════════
# MERGE + SAVE
# ══════════════════════════════════════════════════════════════════════════

def _merge_draws(existing: list[dict], new_draws: list[dict]) -> tuple[list[dict], int]:
    """Fusionne new_draws dans existing, déduplique par (date, tod). Retourne (merged, added_count)."""
    seen = {(d["date"], d.get("tod", "Evening")) for d in existing}
    added = 0
    merged = list(existing)
    for draw in new_draws:
        key = (draw["date"], draw.get("tod", "Evening"))
        if key not in seen:
            merged.append(draw)
            seen.add(key)
            added += 1
    merged.sort(key=lambda d: (d["date"], d.get("tod", "")))
    return merged, added


def _load_csv(state: str) -> list[dict]:
    path = os.path.join(DATA_DIR, f"{state.lower()}.csv")
    if not os.path.exists(path):
        return []
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
    except Exception:
        pass
    return rows


def _save_csv(state: str, draws: list[dict]):
    path = os.path.join(DATA_DIR, f"{state.lower()}.csv")
    if not draws:
        return
    fieldnames = ["date", "tod", "d1", "d2", "d3"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(draws)


# ══════════════════════════════════════════════════════════════════════════
# MAIN API
# ══════════════════════════════════════════════════════════════════════════

def scrape_state(state: str, sources: list[str] | None = None) -> dict:
    """
    Scrape un état via la chaîne de sources (fallback automatique).

    sources: liste ordonnée parmi ["lotteryusa", "usamega", "lotterypost"]
             (None = ordre par défaut)

    Retourne: {"state": str, "added": int, "source": str, "total": int, "ok": bool}
    """
    state = state.upper()
    if sources is None:
        sources = ["lotteryusa", "usamega", "lotterypost"]

    existing = _load_csv(state)
    new_draws: list[dict] = []
    used_source = "none"

    for src in sources:
        if src == "lotteryusa":
            new_draws = _scrape_lotteryusa(state)
        elif src == "usamega":
            new_draws = _scrape_usamega(state)
        elif src == "lotterypost":
            new_draws = _scrape_lotterypost(state)

        if new_draws:
            used_source = src
            break
        print(f"  [smart][{state}] {src} → 0 résultats, essai suivant...")
        time.sleep(0.5)

    if not new_draws:
        print(f"  [smart][{state}] ⚠️ Toutes les sources ont échoué")
        return {"state": state, "added": 0, "source": "none", "total": len(existing), "ok": False}

    merged, added = _merge_draws(existing, new_draws)
    if added > 0:
        _save_csv(state, merged)

    print(f"  [smart][{state}] +{added} nouveaux tirages via {used_source} (total: {len(merged)})")
    return {"state": state, "added": added, "source": used_source, "total": len(merged), "ok": True}


def scrape_states_batch(states: list[str], delay: float = 0.5) -> list[dict]:
    """Scrape plusieurs états en série (Render = 1 worker — pas de parallélisme)."""
    results = []
    for state in states:
        try:
            r = scrape_state(state)
            results.append(r)
        except Exception as e:
            print(f"  [smart][{state}] exception: {e}")
            results.append({"state": state, "added": 0, "source": "error", "ok": False})
        time.sleep(delay)
    return results


def scrape_all_smart(delay: float = 0.5) -> list[dict]:
    """Scrape tous les états connus (Pick 3)."""
    from scraper import STATES
    all_states = list(STATES.keys())
    print(f"[smart] scrape_all_smart — {len(all_states)} états")
    return scrape_states_batch(all_states, delay=delay)


# ══════════════════════════════════════════════════════════════════════════
# DRAW-TIME WATCHER — pour app.py
# ══════════════════════════════════════════════════════════════════════════

# Délai après le tirage avant de scraper (minutes)
POST_DRAW_DELAY_MIN = 15

def get_states_due_now(buffer_min: int = POST_DRAW_DELAY_MIN,
                       window_min: int = 30) -> list[tuple[str, str]]:
    """
    Retourne la liste des (state, tod) dont le tirage vient de se terminer
    dans la fenêtre [now - (buffer_min + window_min), now - buffer_min].

    buffer_min : délai minimum après le tirage (résultats pas encore publiés)
    window_min : fenêtre glissante pour ne pas rater un tirage
    """
    try:
        from draw_schedule import DRAW_SCHEDULE, _parse_schedule_time
        from zoneinfo import ZoneInfo
    except ImportError:
        return []

    now_utc = datetime.now(timezone.utc)
    due = []

    for state, sessions in DRAW_SCHEDULE.items():
        for session in sessions:
            try:
                hour, minute, tz_name = _parse_schedule_time(session["time"])
                tz = ZoneInfo(tz_name)
                now_local = now_utc.astimezone(tz)
                # Construire le datetime du dernier tirage dans ce fuseau
                draw_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
                # Si dans le futur → prendre hier
                if draw_local > now_local:
                    draw_local -= timedelta(days=1)
                draw_utc = draw_local.astimezone(timezone.utc)
                delta_min = (now_utc - draw_utc).total_seconds() / 60
                if buffer_min <= delta_min <= (buffer_min + window_min):
                    due.append((state, session["tod"]))
            except Exception:
                continue

    return due


if __name__ == "__main__":
    import sys
    import urllib3
    urllib3.disable_warnings()

    codes = [s.upper() for s in sys.argv[1:]]
    if not codes:
        codes = ["NY", "FL", "GA", "TX", "PA"]

    for code in codes:
        res = scrape_state(code)
        print(f"  → {res}")
