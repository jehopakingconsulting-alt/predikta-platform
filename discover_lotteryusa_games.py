"""
One-time discovery: for every game in games_config.STATE_GAMES (Pick4/5/6,
Powerball, Mega Millions, etc.), find the matching lotteryusa.com URL slug.
Writes lotteryusa_games_config.json: {STATE: {lp_slug: lu_slug_or_null}}
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests as creq
from bs4 import BeautifulSoup

from games_config import STATE_GAMES
from discover_lotteryusa import STATE_SLUGS

BASE = "https://www.lotteryusa.com"


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


SPECIAL = {
    "megamillions": "mega-millions",
    "allornothing": "all-or-nothing",
    "superlottoplus": "super-lotto-plus",
    "luckyforlife": "lucky-for-life",
    "texastwostep": "texas-two-step",
    "win4": "win-4",
    "take5": "take-5",
    "pick10": "pick-10",
    "pick6": "pick-6",
    "cash4": "cash-4",
    "cash5": "cash-5",
    "cash3": "cash-3",
    "daily4": "daily-4",
    "daily3": "daily-3",
    "play3": "play-3",
    "pega3": "pega-3",
    "fantasy5": "fantasy-5",
    "masscash": "mass-cash",
    "lotto47": "lotto-47",
}


def candidates(slug):
    cands = [slug]
    if slug in SPECIAL:
        cands.append(SPECIAL[slug])

    # midday- prefix or -midday suffix: rebuild around the base slug
    m = re.match(r"^(midday-|midday)(.+)$", slug)
    if m:
        base = m.group(2)
        base_h = SPECIAL.get(base, re.sub(r"([a-zA-Z])(\d+)$", r"\1-\2", base))
        cands += [f"midday-{base_h}", f"{base_h}-midday"]

    m = re.match(r"^(.+)-midday$", slug)
    if m:
        base = m.group(1)
        base_h = SPECIAL.get(base, re.sub(r"([a-zA-Z])(\d+)$", r"\1-\2", base))
        cands += [f"midday-{base_h}", f"{base_h}-midday"]

    # generic: insert hyphen before trailing digits
    cands.append(re.sub(r"([a-zA-Z])(\d+)$", r"\1-\2", slug))
    # insert hyphen before any digit anywhere
    cands.append(re.sub(r"([a-zA-Z])(\d)", r"\1-\2", slug))

    seen = set()
    out = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def process_game(state, state_slug, game):
    slug = game["slug"]
    label_words = set(re.findall(r"[a-z0-9]+", game["label"].lower()))
    for cand in candidates(slug):
        title = fetch_title(f"{state_slug}/{cand}")
        if title is None:
            continue
        title_words = set(re.findall(r"[a-z0-9]+", title.lower()))
        # require at least one significant label word (len>=3) to match
        sig = {w for w in label_words if len(w) >= 3}
        if not sig or sig & title_words or any(w in title.lower().replace(" ", "") for w in sig):
            return slug, {"lu_slug": cand, "title": title}
    return slug, {"lu_slug": None, "title": None}


def main():
    results = {}
    jobs = []
    for state, games in STATE_GAMES.items():
        state_slug = STATE_SLUGS.get(state)
        if not state_slug:
            continue
        results[state] = {}
        for game in games:
            jobs.append((state, state_slug, game))

    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(process_game, s, ss, g): (s, g["slug"]) for s, ss, g in jobs}
        for fut in as_completed(futures):
            state, slug = futures[fut]
            lp_slug, info = fut.result()
            results[state][lp_slug] = info
            print(f"[{state}] {lp_slug} -> {info}")

    with open("lotteryusa_games_config.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nSaved lotteryusa_games_config.json")


if __name__ == "__main__":
    main()
