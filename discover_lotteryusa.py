"""
One-time discovery script: figure out, for each state in scraper.STATES,
the correct lotteryusa.com state-path slug + game slug(s) for each
time-of-day draw. Writes results to lotteryusa_config.json.
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as creq
from bs4 import BeautifulSoup

from scraper import STATES

BASE = "https://www.lotteryusa.com"

STATE_SLUGS = {
    "AR": "arkansas", "AZ": "arizona", "CA": "california", "CO": "colorado",
    "CT": "connecticut", "DC": "washington-dc", "DE": "delaware", "FL": "florida",
    "GA": "georgia", "IA": "iowa", "ID": "idaho", "IL": "illinois", "IN": "indiana",
    "KS": "kansas", "KY": "kentucky", "LA": "louisiana", "MD": "maryland",
    "ME": "maine", "MI": "michigan", "MN": "minnesota", "MO": "missouri",
    "MS": "mississippi", "NC": "north-carolina", "NE": "nebraska",
    "NH": "new-hampshire", "NJ": "new-jersey", "NM": "new-mexico", "NY": "new-york",
    "OH": "ohio", "OK": "oklahoma", "PA": "pennsylvania", "PR": "puerto-rico",
    "SC": "south-carolina", "TN": "tennessee", "TX": "texas", "VA": "virginia",
    "VT": "vermont", "WA": "washington", "WI": "wisconsin", "WV": "west-virginia",
}

# Candidate base game slugs to try (lotterypost slug first, then common variants)
def candidate_base_slugs(lp_slug):
    cands = [lp_slug]
    m = re.match(r"([a-z]+)(\d)", lp_slug)
    if m:
        cands.append(f"{m.group(1)}-{m.group(2)}")
    cands += ["pick-3", "cash-3", "daily-3", "play-3", "numbers", "pega-3", "dc-3"]
    seen = set()
    out = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out

TOD_PREFIXES = ["midday-", "morning-", "evening-", "day-", "night-"]
TOD_SUFFIXES = ["-midday", "-morning", "-evening", "-day", "-night"]


def fetch_title(path):
    url = f"{BASE}/{path}/"
    try:
        r = creq.get(url, impersonate="chrome124", timeout=15, verify=False)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        h1 = soup.find("h1")
        return h1.get_text(strip=True) if h1 else ""
    except Exception:
        return None


def find_base_slug(state_slug, lp_slug):
    for cand in candidate_base_slugs(lp_slug):
        title = fetch_title(f"{state_slug}/{cand}")
        if title:
            return cand, title
    return None, None


def find_tod_variants(state_slug, base_slug):
    variants = {}
    base_title = fetch_title(f"{state_slug}/{base_slug}")
    if base_title:
        variants["base"] = {"slug": base_slug, "title": base_title}

    for pfx in TOD_PREFIXES:
        cand = f"{pfx}{base_slug}"
        title = fetch_title(f"{state_slug}/{cand}")
        if title:
            variants[cand] = {"slug": cand, "title": title}

    for sfx in TOD_SUFFIXES:
        cand = f"{base_slug}{sfx}"
        title = fetch_title(f"{state_slug}/{cand}")
        if title:
            variants[cand] = {"slug": cand, "title": title}

    return variants


def process_state(code, cfg):
    state_slug = STATE_SLUGS.get(code)
    if not state_slug:
        return code, {"error": "no state slug"}

    base_slug, base_title = find_base_slug(state_slug, cfg["slug"])
    if not base_slug:
        return code, {"error": "no working base slug", "state_slug": state_slug}

    variants = find_tod_variants(state_slug, base_slug)
    return code, {
        "state_slug": state_slug,
        "base_slug": base_slug,
        "base_title": base_title,
        "variants": variants,
    }


def main():
    results = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(process_state, code, cfg): code for code, cfg in STATES.items()}
        for fut in as_completed(futures):
            code, info = fut.result()
            results[code] = info
            print(f"[{code}] {info}")

    with open("lotteryusa_config.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nSaved lotteryusa_config.json")


if __name__ == "__main__":
    main()
