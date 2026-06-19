"""
PREDIKTA — Official State Lottery Scrapers
Source directe : sites officiels des loteries d'État.

Latence : 1-3 min après tirage (vs 10-20 min pour les agrégateurs).
États couverts : NY, FL, GA, TX, PA, NJ, OH, IL, NC, MD

Ces scrapers sont appelés en SOURCE 0 dans smart_scraper.py,
avant lotteryusa / usamega / lotterypost.
"""

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.5",
}

_TOD_MAP = {
    "midday": "Midday", "mid-day": "Midday", "noon": "Midday",
    "daytime": "Midday", "day": "Midday",
    "evening": "Evening", "eve": "Evening",
    "morning": "Morning", "morn": "Morning",
    "night": "Night", "nite": "Night",
}

def _classify_tod(text: str) -> str:
    low = text.lower()
    for kw, tod in _TOD_MAP.items():
        if kw in low:
            return tod
    return "Evening"

def _get(url: str, json: bool = False, timeout: int = 15):
    """GET avec curl_cffi (TLS impersonation) ou requests classique."""
    try:
        if cffi_requests:
            r = cffi_requests.get(url, impersonate="chrome124", headers=_HEADERS, timeout=timeout, verify=False)
        else:
            r = requests.get(url, headers=_HEADERS, timeout=timeout, verify=False)
        if r.status_code == 200:
            return r.json() if json else r.text
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════════════════
# NEW YORK — nylottery.ny.gov (JSON natif)
# ══════════════════════════════════════════════════════════════════════════

def scrape_ny() -> list[dict]:
    """
    NY Lottery API officielle : JSON avec les derniers résultats Numbers (Pick 3).
    Endpoint : https://nylottery.ny.gov/api/1.0/past-winning-numbers/pick-3
    """
    draws = []

    # Endpoint JSON officiel
    url = "https://nylottery.ny.gov/api/1.0/past-winning-numbers/pick-3"
    data = _get(url, json=True)
    if data and isinstance(data, dict):
        for entry in data.get("data", []):
            try:
                date_str = entry.get("draw_date", "")[:10]
                nums = entry.get("winning_numbers", "").split()
                tod_raw = entry.get("draw_time", "midday")
                if len(nums) >= 3:
                    draws.append({
                        "date": date_str,
                        "tod": _classify_tod(tod_raw),
                        "d1": nums[0], "d2": nums[1], "d3": nums[2],
                    })
            except Exception:
                pass

    if draws:
        return draws

    # Fallback HTML officiel
    url_html = "https://nylottery.ny.gov/games/numbers"
    html = _get(url_html)
    if html:
        draws = _parse_ny_html(html)

    return draws


def _parse_ny_html(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    draws = []
    # NY publie les tirages dans des blocs avec date + chiffres
    for block in soup.select(".draw-result, .winning-numbers, .results-block, article"):
        date_el = block.find(class_=re.compile(r"date|draw-date"))
        nums_el = block.find(class_=re.compile(r"number|ball|winning"))
        if not date_el or not nums_el:
            continue
        try:
            date_str = _parse_date(date_el.get_text(strip=True))
            digits = re.findall(r'\b\d\b', nums_el.get_text())
            if date_str and len(digits) >= 3:
                tod_raw = block.get_text(" ")
                draws.append({
                    "date": date_str,
                    "tod": _classify_tod(tod_raw),
                    "d1": digits[0], "d2": digits[1], "d3": digits[2],
                })
        except Exception:
            pass
    return draws


# ══════════════════════════════════════════════════════════════════════════
# FLORIDA — flalottery.com (JSON API)
# ══════════════════════════════════════════════════════════════════════════

def scrape_fl() -> list[dict]:
    """FL Lottery : endpoint JSON officiel pour Pick 3."""
    draws = []

    # Endpoint JSON connu
    url = "https://www.flalottery.com/site/winningNumberSearch?searchType=latest&gameNameAlias=PICK3&interfaceType=JSON"
    data = _get(url, json=True)
    if data:
        for entry in (data if isinstance(data, list) else data.get("draws", [])):
            try:
                date_str = _parse_date(str(entry.get("drawDate", "")))
                nums = str(entry.get("winningNumbers", "")).replace("/", " ").split()
                tod_raw = str(entry.get("drawTime", entry.get("drawPeriod", "Evening")))
                if date_str and len(nums) >= 3:
                    draws.append({
                        "date": date_str,
                        "tod": _classify_tod(tod_raw),
                        "d1": nums[0], "d2": nums[1], "d3": nums[2],
                    })
            except Exception:
                pass

    if draws:
        return draws

    # Fallback HTML officiel
    url_html = "https://www.flalottery.com/games/pick3"
    html = _get(url_html)
    if html:
        draws = _parse_generic_html(html, "FL")

    return draws


# ══════════════════════════════════════════════════════════════════════════
# GEORGIA — galottery.com
# ══════════════════════════════════════════════════════════════════════════

def scrape_ga() -> list[dict]:
    """GA Lottery : endpoint JSON ou HTML officiel pour Cash 3."""
    draws = []

    # Tentative JSON
    url_json = "https://www.galottery.com/api/games/cash3/results/latest"
    data = _get(url_json, json=True)
    if data:
        for entry in (data if isinstance(data, list) else [data]):
            try:
                date_str = _parse_date(str(entry.get("drawDate", "")))
                nums = re.findall(r'\d', str(entry.get("winningNumbers", "")))
                tod_raw = str(entry.get("drawTime", entry.get("period", "Evening")))
                if date_str and len(nums) >= 3:
                    draws.append({
                        "date": date_str,
                        "tod": _classify_tod(tod_raw),
                        "d1": nums[0], "d2": nums[1], "d3": nums[2],
                    })
            except Exception:
                pass

    if draws:
        return draws

    # Fallback HTML
    url_html = "https://www.galottery.com/en-us/games/draw-games/cash-3.html"
    html = _get(url_html)
    if html:
        draws = _parse_generic_html(html, "GA")

    return draws


# ══════════════════════════════════════════════════════════════════════════
# TEXAS — txlottery.org (CSV officiel)
# ══════════════════════════════════════════════════════════════════════════

def scrape_tx() -> list[dict]:
    """TX Lottery : fichier CSV officiel Pick 3 (mis à jour en temps réel)."""
    import csv, io

    draws = []

    # TX publie un CSV téléchargeable directement
    url_csv = "https://www.txlottery.org/export/sites/lottery/Games/Pick_3/Winning_Numbers/pick3.csv"
    raw = _get(url_csv)
    if raw:
        try:
            reader = csv.DictReader(io.StringIO(raw))
            for row in reader:
                try:
                    # Colonnes typiques TX: Game Name, Month, Day, Year, Num1, Num2, Num3, ...
                    month = row.get("Month", row.get("month", "")).strip()
                    day   = row.get("Day",   row.get("day",   "")).strip()
                    year  = row.get("Year",  row.get("year",  "")).strip()
                    if not (month and day and year):
                        # Essayer format Date unique
                        date_raw = row.get("Date", row.get("DrawDate", "")).strip()
                        date_str = _parse_date(date_raw)
                    else:
                        date_str = f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
                    if not date_str:
                        continue
                    d1 = row.get("Num1", row.get("Number1", row.get("n1", ""))).strip()
                    d2 = row.get("Num2", row.get("Number2", row.get("n2", ""))).strip()
                    d3 = row.get("Num3", row.get("Number3", row.get("n3", ""))).strip()
                    if not (d1.isdigit() and d2.isdigit() and d3.isdigit()):
                        continue
                    tod_raw = row.get("Game Name", row.get("DrawTime", row.get("Time", "Evening")))
                    draws.append({
                        "date": date_str,
                        "tod": _classify_tod(tod_raw),
                        "d1": d1, "d2": d2, "d3": d3,
                    })
                except Exception:
                    pass
        except Exception:
            pass

    if draws:
        return draws

    # Fallback HTML
    url_html = "https://www.txlottery.org/export/sites/lottery/Games/Pick_3/Winning_Numbers/"
    html = _get(url_html)
    if html:
        draws = _parse_generic_html(html, "TX")

    return draws


# ══════════════════════════════════════════════════════════════════════════
# PENNSYLVANIA — palottery.state.pa.us
# ══════════════════════════════════════════════════════════════════════════

def scrape_pa() -> list[dict]:
    """PA Lottery : résultats officiels Pick 3."""
    draws = []

    url = "https://www.palottery.state.pa.us/Games/Current-Game-Pages/Pick-3.aspx"
    html = _get(url)
    if html:
        draws = _parse_generic_html(html, "PA")

    return draws


# ══════════════════════════════════════════════════════════════════════════
# NEW JERSEY — njlottery.com
# ══════════════════════════════════════════════════════════════════════════

def scrape_nj() -> list[dict]:
    url = "https://www.njlottery.com/api/v1/draw-games/draws/?gameId=1029&pageSize=10"
    data = _get(url, json=True)
    draws = []
    if data:
        for entry in data.get("draws", data if isinstance(data, list) else []):
            try:
                date_str = _parse_date(str(entry.get("drawDate", "")))
                nums = re.findall(r'\d', str(entry.get("winningNumbers", "")))
                tod_raw = str(entry.get("drawTime", "Evening"))
                if date_str and len(nums) >= 3:
                    draws.append({"date": date_str, "tod": _classify_tod(tod_raw),
                                  "d1": nums[0], "d2": nums[1], "d3": nums[2]})
            except Exception:
                pass
    if not draws:
        html = _get("https://www.njlottery.com/en-us/drawgames/pick3.html")
        if html:
            draws = _parse_generic_html(html, "NJ")
    return draws


# ══════════════════════════════════════════════════════════════════════════
# OHIO — ohiolottery.com
# ══════════════════════════════════════════════════════════════════════════

def scrape_oh() -> list[dict]:
    url = "https://www.ohiolottery.com/api/GameResults/ByGame?gameId=3"
    data = _get(url, json=True)
    draws = []
    if data:
        for entry in (data if isinstance(data, list) else data.get("results", [])):
            try:
                date_str = _parse_date(str(entry.get("DrawDate", entry.get("drawDate", ""))))
                nums = re.findall(r'\d', str(entry.get("WinningNumbers", entry.get("winningNumbers", ""))))
                tod_raw = str(entry.get("DrawTime", entry.get("drawTime", "Evening")))
                if date_str and len(nums) >= 3:
                    draws.append({"date": date_str, "tod": _classify_tod(tod_raw),
                                  "d1": nums[0], "d2": nums[1], "d3": nums[2]})
            except Exception:
                pass
    if not draws:
        html = _get("https://www.ohiolottery.com/Games/DrawGames/Pick-3")
        if html:
            draws = _parse_generic_html(html, "OH")
    return draws


# ══════════════════════════════════════════════════════════════════════════
# ILLINOIS — illinoislottery.com
# ══════════════════════════════════════════════════════════════════════════

def scrape_il() -> list[dict]:
    url = "https://www.illinoislottery.com/illinois-lottery/winning-numbers/pick-3"
    html = _get(url)
    return _parse_generic_html(html, "IL") if html else []


# ══════════════════════════════════════════════════════════════════════════
# NORTH CAROLINA — nclottery.com
# ══════════════════════════════════════════════════════════════════════════

def scrape_nc() -> list[dict]:
    url = "https://www.nclottery.com/pick3"
    html = _get(url)
    return _parse_generic_html(html, "NC") if html else []


# ══════════════════════════════════════════════════════════════════════════
# MARYLAND — mdlottery.com
# ══════════════════════════════════════════════════════════════════════════

def scrape_md() -> list[dict]:
    url = "https://www.mdlottery.com/games/pick-3/"
    html = _get(url)
    return _parse_generic_html(html, "MD") if html else []


# ══════════════════════════════════════════════════════════════════════════
# GENERIC HTML PARSER (fallback universel)
# ══════════════════════════════════════════════════════════════════════════

def _parse_generic_html(html: str, state: str) -> list[dict]:
    """
    Parser HTML générique — cherche des patterns de 3 chiffres séparés
    associés à une date sur la page officielle de chaque État.
    """
    soup = BeautifulSoup(html, "html.parser")
    draws = []
    seen = set()

    # Stratégie 1 : chercher des balises <time> + chiffres proches
    for time_el in soup.find_all("time"):
        date_str = _parse_date(time_el.get("datetime", "") or time_el.get_text(strip=True))
        if not date_str:
            continue
        # Chercher les chiffres dans le parent ou les siblings
        container = time_el.find_parent() or time_el
        text = container.get_text(" ", strip=True)
        digits = re.findall(r'\b(\d)\b', text)
        if len(digits) >= 3:
            key = f"{date_str}_{digits[0]}{digits[1]}{digits[2]}"
            if key not in seen:
                seen.add(key)
                tod = _classify_tod(text)
                draws.append({"date": date_str, "tod": tod,
                              "d1": digits[0], "d2": digits[1], "d3": digits[2]})

    if draws:
        return draws

    # Stratégie 2 : chercher des patterns "X-X-X" ou "X X X" avec date voisine
    for line in html.split("\n"):
        m = re.search(r'\b(\d)[\-\s](\d)[\-\s](\d)\b', line)
        if not m:
            continue
        date_m = re.search(
            r'(\d{4}[-/]\d{2}[-/]\d{2})|(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})',
            line
        )
        if not date_m:
            continue
        date_str = _parse_date(date_m.group(0))
        if not date_str:
            continue
        key = f"{date_str}_{m.group(1)}{m.group(2)}{m.group(3)}"
        if key not in seen:
            seen.add(key)
            tod = _classify_tod(line)
            draws.append({"date": date_str, "tod": tod,
                          "d1": m.group(1), "d2": m.group(2), "d3": m.group(3)})

    return draws


# ══════════════════════════════════════════════════════════════════════════
# DATE PARSER UNIVERSEL
# ══════════════════════════════════════════════════════════════════════════

def _parse_date(raw: str) -> str | None:
    """Essaie de parser une date dans plusieurs formats et retourne YYYY-MM-DD."""
    if not raw:
        return None
    raw = raw.strip()
    # ISO déjà formaté
    m = re.match(r'(\d{4})[-/](\d{2})[-/](\d{2})', raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    # MM/DD/YYYY
    m = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', raw)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    # "Jun 19, 2026" or "June 19 2026"
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(raw[:20], fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Timestamp ISO avec T
    m = re.match(r'(\d{4}-\d{2}-\d{2})T', raw)
    if m:
        return m.group(1)
    return None


# ══════════════════════════════════════════════════════════════════════════
# REGISTRY — mapping état → fonction de scraping officiel
# ══════════════════════════════════════════════════════════════════════════

OFFICIAL_SCRAPERS: dict[str, callable] = {
    "NY": scrape_ny,
    "FL": scrape_fl,
    "GA": scrape_ga,
    "TX": scrape_tx,
    "PA": scrape_pa,
    "NJ": scrape_nj,
    "OH": scrape_oh,
    "IL": scrape_il,
    "NC": scrape_nc,
    "MD": scrape_md,
}


def scrape_official(state: str) -> list[dict]:
    """
    Appelle le scraper officiel pour un état donné.
    Retourne [] si l'état n'a pas de scraper officiel ou si ça échoue.
    """
    state = state.upper()
    fn = OFFICIAL_SCRAPERS.get(state)
    if not fn:
        return []
    try:
        draws = fn()
        if draws:
            print(f"  [official][{state}] {len(draws)} tirages")
        return draws or []
    except Exception as e:
        print(f"  [official][{state}] error: {e}")
        return []


if __name__ == "__main__":
    import sys, urllib3
    urllib3.disable_warnings()
    states = [s.upper() for s in sys.argv[1:]] or list(OFFICIAL_SCRAPERS.keys())
    for st in states:
        draws = scrape_official(st)
        print(f"[{st}] {len(draws)} tirages — dernier: {draws[0] if draws else 'aucun'}")
