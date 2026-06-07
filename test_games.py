import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
app.config['TESTING'] = True
c = app.test_client()

r = c.get('/api/games/config')
d = json.loads(r.data)
print("États configurés:", list(d['states'].keys()))
print()
for state, games in d['states'].items():
    labels = [g['label'] for g in games]
    print(f"{state} ({len(games)} jeux): {', '.join(labels)}")

print()
print("=== Test scraping NY (1 mois) ===")
# Test scraping a few games for NY
from games_scraper import fetch_game, save_game_results
from games_config import STATE_GAMES

ny_games = STATE_GAMES['NY'][:3]  # first 3 games
for game in ny_games:
    print(f"Fetching {game['label']}...")
    draws = fetch_game('NY', game, n_months=1)
    print(f"  -> {len(draws)} draws")
    if draws:
        d0 = draws[0]
        nums_str = '-'.join(d0['nums'])
        extra_str = f" +{'-'.join(d0['extra'])}" if d0.get('extra') else ''
        print(f"  Latest: {d0['date']} {d0['tod']}: {nums_str}{extra_str}")
        save_game_results('NY', game, draws)

print()
print("=== Today's NY games ===")
r2 = c.get('/api/games/today/NY')
d2 = json.loads(r2.data)
print(f"Has data: {d2['has_data']} | Games with data: {len(d2['games'])}")
for g in d2['games']:
    draws_info = ', '.join([f"{draw['tod']}: {'-'.join(draw['nums'])}" for draw in g['draws'][:2]])
    print(f"  {g['icon']} {g['label']}: {draws_info}")
