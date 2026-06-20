"""
ZYNORIQ — Official State Lottery Scrapers
Source directe : sites officiels des loteries d'État.

Latence : 1-3 min après tirage (vs 10-20 min pour les agrégateurs).
États couverts : NY, FL, GA, TX, PA, NJ, OH, IL, NC, MD,
                 TN, VA, SC, KY, IN, MI, CT, WI, MN, LA,
                 MO, CO, AR, WV, DE, MS, KS, OK, NM, ID,
                 IA, NE, ME, VT, NH, WA, AZ, CA, DC, PR (40 états)

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

# ══════════════════════════════════════════════════════════════════════════
# HELPER — JSON + HTML fallback en une ligne
# ══════════════════════════════════════════════════════════════════════════

def _scrape(state: str, html_urls: list[str], json_urls: list[str] = None,
            json_key: str = None, date_field: str = "drawDate",
            nums_field: str = "winningNumbers", tod_field: str = "drawTime") -> list[dict]:
    """
    Helper générique : essaie chaque URL JSON puis chaque URL HTML.
    Retourne dès qu'on a au moins un tirage.
    """
    draws = []

    # 1. JSON endpoints
    for url in (json_urls or []):
        data = _get(url, json=True)
        if not data:
            continue
        entries = data
        if json_key:
            entries = data.get(json_key, []) if isinstance(data, dict) else data
        elif isinstance(data, dict):
            # Cherche la première clé liste
            for v in data.values():
                if isinstance(v, list):
                    entries = v
                    break
        for entry in (entries if isinstance(entries, list) else [entries]):
            try:
                date_str = _parse_date(str(entry.get(date_field, entry.get("DrawDate", entry.get("date", "")))))
                raw_nums = str(entry.get(nums_field, entry.get("WinningNumbers", entry.get("numbers", ""))))
                nums = re.findall(r'\b\d\b', raw_nums) or re.findall(r'\d', raw_nums)
                tod_raw = str(entry.get(tod_field, entry.get("DrawTime", entry.get("period", "Evening"))))
                if date_str and len(nums) >= 3:
                    draws.append({"date": date_str, "tod": _classify_tod(tod_raw),
                                  "d1": nums[0], "d2": nums[1], "d3": nums[2]})
            except Exception:
                pass
        if draws:
            return draws

    # 2. HTML pages
    for url in html_urls:
        html = _get(url)
        if html:
            draws = _parse_generic_html(html, state)
            if draws:
                return draws

    return draws


# ══════════════════════════════════════════════════════════════════════════
# TENNESSEE — tnlottery.com (Cash 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_tn() -> list[dict]:
    return _scrape("TN",
        html_urls=["https://tnlottery.com/winningnumbers/",
                   "https://tnlottery.com/games/cash-3/"],
        json_urls=["https://tnlottery.com/api/games/cash3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# VIRGINIA — valottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_va() -> list[dict]:
    return _scrape("VA",
        html_urls=["https://www.valottery.com/data/winning-numbers",
                   "https://www.valottery.com/games/pick3"],
        json_urls=["https://www.valottery.com/api/Numbers/GetDrawingsByGame?gameTypeId=pick3&count=20"])


# ══════════════════════════════════════════════════════════════════════════
# SOUTH CAROLINA — sceducationlottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_sc() -> list[dict]:
    return _scrape("SC",
        html_urls=["https://www.sceducationlottery.com/play/draw-games/pick-3",
                   "https://www.sceducationlottery.com/winning-numbers/pick-3"])


# ══════════════════════════════════════════════════════════════════════════
# KENTUCKY — kylottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ky() -> list[dict]:
    return _scrape("KY",
        html_urls=["https://www.kylottery.com/apps/draw_games/pick3/",
                   "https://www.kylottery.com/winning-numbers/pick-3"],
        json_urls=["https://www.kylottery.com/api/games/pick3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# INDIANA — hoosierlottery.com (Daily 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_in() -> list[dict]:
    return _scrape("IN",
        html_urls=["https://www.hoosierlottery.com/games/daily3",
                   "https://www.hoosierlottery.com/winning-numbers/"],
        json_urls=["https://www.hoosierlottery.com/api/games/daily3/results"])


# ══════════════════════════════════════════════════════════════════════════
# MICHIGAN — michiganlottery.com (Daily 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_mi() -> list[dict]:
    return _scrape("MI",
        html_urls=["https://www.michiganlottery.com/games/daily-3",
                   "https://www.michiganlottery.com/winning-numbers/"],
        json_urls=["https://www.michiganlottery.com/api/game/results?gameName=daily-3&count=10"])


# ══════════════════════════════════════════════════════════════════════════
# CONNECTICUT — ctlottery.org (Play3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ct() -> list[dict]:
    return _scrape("CT",
        html_urls=["https://www.ctlottery.org/winning-numbers/",
                   "https://www.ctlottery.org/games/play3/"])


# ══════════════════════════════════════════════════════════════════════════
# WISCONSIN — wilottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_wi() -> list[dict]:
    return _scrape("WI",
        html_urls=["https://www.wilottery.com/lotto-games/pick3.aspx",
                   "https://www.wilottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# MINNESOTA — mnlottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_mn() -> list[dict]:
    return _scrape("MN",
        html_urls=["https://www.mnlottery.com/games/pick3/",
                   "https://www.mnlottery.com/winning_numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# LOUISIANA — louisianalottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_la() -> list[dict]:
    return _scrape("LA",
        html_urls=["https://www.louisianalottery.com/games/pick-3",
                   "https://www.louisianalottery.com/winning-numbers/"],
        json_urls=["https://www.louisianalottery.com/api/games/pick3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# MISSOURI — molottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_mo() -> list[dict]:
    return _scrape("MO",
        html_urls=["https://www.molottery.com/drawgames/pick3.do",
                   "https://www.molottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# COLORADO — coloradolottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_co() -> list[dict]:
    return _scrape("CO",
        html_urls=["https://www.coloradolottery.com/en/games/pick-3/",
                   "https://www.coloradolottery.com/en/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# ARKANSAS — myarkansaslottery.com (Cash 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ar() -> list[dict]:
    return _scrape("AR",
        html_urls=["https://www.myarkansaslottery.com/games/cash-3",
                   "https://www.myarkansaslottery.com/winning-numbers/"],
        json_urls=["https://www.myarkansaslottery.com/api/games/cash3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# WEST VIRGINIA — wvlottery.com (Daily 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_wv() -> list[dict]:
    return _scrape("WV",
        html_urls=["https://www.wvlottery.com/game/daily-3/",
                   "https://www.wvlottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# DELAWARE — delottery.com (Play 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_de() -> list[dict]:
    return _scrape("DE",
        html_urls=["https://www.delottery.com/winning-numbers",
                   "https://www.delottery.com/games/play3"])


# ══════════════════════════════════════════════════════════════════════════
# MISSISSIPPI — mslottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ms() -> list[dict]:
    return _scrape("MS",
        html_urls=["https://www.mslottery.com/en-us/games/drawgames/pick-3.html",
                   "https://www.mslottery.com/en-us/winning-numbers.html"])


# ══════════════════════════════════════════════════════════════════════════
# KANSAS — kslottery.net (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ks() -> list[dict]:
    return _scrape("KS",
        html_urls=["https://www.kslottery.net/Games/Pick3",
                   "https://www.kslottery.net/winningnumbers/"],
        json_urls=["https://www.kslottery.net/api/games/pick3/results"])


# ══════════════════════════════════════════════════════════════════════════
# OKLAHOMA — lottery.ok.gov (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ok() -> list[dict]:
    return _scrape("OK",
        html_urls=["https://www.lottery.ok.gov/games/pick3.html",
                   "https://www.lottery.ok.gov/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# NEW MEXICO — nmlottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_nm() -> list[dict]:
    return _scrape("NM",
        html_urls=["https://www.nmlottery.com/games/pick-3",
                   "https://www.nmlottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# IDAHO — idaholottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_id() -> list[dict]:
    return _scrape("ID",
        html_urls=["https://www.idaholottery.com/games/idaho-pick-3/",
                   "https://www.idaholottery.com/results/"])


# ══════════════════════════════════════════════════════════════════════════
# IOWA — ialottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ia() -> list[dict]:
    return _scrape("IA",
        html_urls=["https://ialottery.com/games/pick3",
                   "https://ialottery.com/winning-numbers/"],
        json_urls=["https://ialottery.com/api/games/pick3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# NEBRASKA — nelottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ne() -> list[dict]:
    return _scrape("NE",
        html_urls=["https://www.nelottery.com/lotto/results/?game=12",
                   "https://www.nelottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# MAINE — mainelottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_me() -> list[dict]:
    return _scrape("ME",
        html_urls=["https://www.mainelottery.com/games/pick3",
                   "https://www.mainelottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# VERMONT — vtlottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_vt() -> list[dict]:
    return _scrape("VT",
        html_urls=["https://www.vtlottery.com/games/pick3",
                   "https://www.vtlottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# NEW HAMPSHIRE — nhlottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_nh() -> list[dict]:
    return _scrape("NH",
        html_urls=["https://www.nhlottery.com/Games/Pick3",
                   "https://www.nhlottery.com/winning-numbers/"])


# ══════════════════════════════════════════════════════════════════════════
# WASHINGTON — walottery.com (Daily Game)
# ══════════════════════════════════════════════════════════════════════════
def scrape_wa() -> list[dict]:
    return _scrape("WA",
        html_urls=["https://www.walottery.com/WinningNumbers/DailyGame.aspx",
                   "https://www.walottery.com/WinningNumbers/"],
        json_urls=["https://www.walottery.com/api/WinningNumbers/DailyGame"])


# ══════════════════════════════════════════════════════════════════════════
# ARIZONA — arizonalottery.com (Pick 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_az() -> list[dict]:
    return _scrape("AZ",
        html_urls=["https://www.arizonalottery.com/play/draw-games/pick/",
                   "https://www.arizonalottery.com/winning-numbers/"],
        json_urls=["https://www.arizonalottery.com/api/games/pick3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# CALIFORNIA — calottery.com (Daily 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_ca() -> list[dict]:
    draws = _scrape("CA",
        html_urls=[],
        json_urls=["https://www.calottery.com/api/DrawGameApi/DrawGamePastDrawResults/9/1/20"])
    if not draws:
        draws = _scrape("CA",
            html_urls=["https://www.calottery.com/draw-games/daily-3"])
    return draws


# ══════════════════════════════════════════════════════════════════════════
# WASHINGTON DC — dclottery.com (DC-3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_dc() -> list[dict]:
    return _scrape("DC",
        html_urls=["https://dclottery.com/games/dc3",
                   "https://dclottery.com/winning-numbers/"],
        json_urls=["https://dclottery.com/api/games/dc3/results/latest"])


# ══════════════════════════════════════════════════════════════════════════
# PUERTO RICO — puertoricololottery.com (Pega 3)
# ══════════════════════════════════════════════════════════════════════════
def scrape_pr() -> list[dict]:
    return _scrape("PR",
        html_urls=["https://www.puertoricololottery.com/pega3",
                   "https://loteriapr.com/pega3/",
                   "https://www.loteriapr.com/resultados/"])


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
    # Nouveaux scrapers officiels
    "TN": scrape_tn,
    "VA": scrape_va,
    "SC": scrape_sc,
    "KY": scrape_ky,
    "IN": scrape_in,
    "MI": scrape_mi,
    "CT": scrape_ct,
    "WI": scrape_wi,
    "MN": scrape_mn,
    "LA": scrape_la,
    "MO": scrape_mo,
    "CO": scrape_co,
    "AR": scrape_ar,
    "WV": scrape_wv,
    "DE": scrape_de,
    "MS": scrape_ms,
    "KS": scrape_ks,
    "OK": scrape_ok,
    "NM": scrape_nm,
    "ID": scrape_id,
    "IA": scrape_ia,
    "NE": scrape_ne,
    "ME": scrape_me,
    "VT": scrape_vt,
    "NH": scrape_nh,
    "WA": scrape_wa,
    "AZ": scrape_az,
    "CA": scrape_ca,
    "DC": scrape_dc,
    "PR": scrape_pr,
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
