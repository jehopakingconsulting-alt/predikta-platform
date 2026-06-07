"""Research script: map all lotterypost.com states and game URLs."""
import requests, urllib3, re, time
from bs4 import BeautifulSoup
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.5',
}

BASE = "https://www.lotterypost.com"

# All states on lotterypost
STATES_CODES = [
    'al','ar','az','ca','co','ct','dc','de','fl','ga',
    'ia','id','il','in','ks','ky','la','ma','md','me',
    'mi','mn','mo','ms','mt','nc','nd','ne','nh','nj',
    'nm','ny','oh','ok','or','pa','pr','ri','sc','sd',
    'tn','tx','va','vt','wa','wi','wv','wy',
]

# Pick3 game slugs by state (known)
PICK3_GAMES = {
    'ny': 'numbers',
    'ga': 'cash3',
    'tx': 'pick3',
    'fl': 'pick3',
    'ca': 'daily3',
    'il': 'pick3',
    'pa': 'pick3',
    'nj': 'pick3',
    'nc': 'pick3',
    'va': 'pick3',
    'oh': 'pick3',
    'mi': 'pick3',
    'tn': 'cash3',
    'sc': 'pick3',
    'ct': 'play3',
    'md': 'pick3',
    'ma': 'numbers',
    'in': 'daily3',
    'ky': 'pick3',
    'mo': 'pick3',
    'az': 'pick3',
    'co': 'pick3',
    'wa': 'daily-game',
    'la': 'pick3',
    'ms': 'pick3',
    'ar': 'cash3',
    'ia': 'pick3',
    'ks': 'pick3',
    'ok': 'pick3',
    'wv': 'daily3',
    'de': 'play3',
    'ri': 'numbers',
    'nh': 'tri-state-pick3',
    'vt': 'tri-state-pick3',
    'me': 'tri-state-pick3',
    'nm': 'pick3',
    'id': 'pick3',
}

def parse_draws(html):
    soup = BeautifulSoup(html, 'html.parser')
    draws = []
    for game in soup.select('div.resultsgame'):
        date = ''
        for drawing in game.select('div.resultsdrawing'):
            time_el = drawing.find('time')
            if time_el and time_el.get('datetime'):
                date = time_el['datetime'][:10]
            tod_i = drawing.find('i', class_=re.compile('TOD'))
            tod = ''
            if tod_i:
                cls = ' '.join(tod_i.get('class', []))
                tod = 'Midday' if 'mid' in cls.lower() else 'Evening'
            nums = [li.get_text(strip=True) for li in drawing.select('ul.resultsnums li')]
            if date and len(nums) == 3:
                draws.append({'date': date, 'tod': tod, 'd1': nums[0], 'd2': nums[1], 'd3': nums[2]})
    return draws


def find_pick3_slug(state_code):
    """Discover Pick3 game slug for a state."""
    url = f"{BASE}/results/{state_code}"
    try:
        r = requests.get(url, headers=headers, timeout=12, verify=False)
        if r.status_code != 200:
            return None, 0
        soup = BeautifulSoup(r.text, 'html.parser')
        # Look for Pick3-like game links
        pick3_keywords = ['pick3','pick-3','cash3','cash-3','daily3','daily-3',
                          'numbers','play3','play-3','daily-game','tri-state-pick3','win3']
        for a in soup.select('a[href]'):
            href = a['href'].lower()
            for kw in pick3_keywords:
                if f'/{state_code}/{kw}' in href or f'/{state_code.upper()}/{kw}' in href:
                    game_name = a.get_text(strip=True)
                    return kw, game_name
        return None, 0
    except Exception as e:
        return None, str(e)


def test_game(state_code, slug):
    url = f"{BASE}/results/{state_code}/{slug}/past"
    try:
        r = requests.get(url, headers=headers, timeout=12, verify=False)
        if r.status_code != 200:
            return 0, r.status_code
        draws = parse_draws(r.text)
        return len(draws), 200
    except Exception as e:
        return 0, str(e)


if __name__ == '__main__':
    print("=" * 70)
    print("LOTTERYPOST.COM — FULL STATE RESEARCH")
    print("=" * 70)

    confirmed = {}

    # Test priority states first
    priority = ['ny','ga','tx','fl','ca','il','pa','nj','nc','va','oh','mi',
                'tn','sc','ct','md','ma','in','ky','mo','az','co','la','ms',
                'ar','ia','ks','ok','de','ri','nm','wv']

    for code in priority:
        slug = PICK3_GAMES.get(code)
        if not slug:
            slug, _ = find_pick3_slug(code)
        if not slug:
            print(f"[{code.upper():3}] No Pick3 slug found")
            continue

        n_draws, status = test_game(code, slug)
        if n_draws > 0:
            confirmed[code] = slug
            print(f"[{code.upper():3}] /{slug:25} -> {n_draws:3} draws  OK")
        else:
            print(f"[{code.upper():3}] /{slug:25} -> {status}")
        time.sleep(0.5)

    print()
    print("=" * 70)
    print(f"CONFIRMED: {len(confirmed)} states with Pick3 data")
    print("=" * 70)
    for code, slug in confirmed.items():
        print(f"  '{code}': '{slug}',")
