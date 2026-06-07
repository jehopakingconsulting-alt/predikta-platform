import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
app.config['TESTING'] = True
c = app.test_client()

# Test /api/results/latest
r = c.get('/api/results/latest')
d = json.loads(r.data)
print(f"Total states: {len(d)}")
print("States with data:")
for code, v in d.items():
    if v['has_data']:
        ld = v['latest'][0] if v['latest'] else {}
        tag = 'TODAY' if v['is_today'] else ('YESTERDAY' if v['is_yesterday'] else v.get('latest_date',''))
        combo = f"{ld.get('d1','-')}-{ld.get('d2','-')}-{ld.get('d3','-')}"
        tod = ld.get('tod','')
        flag = v['flag']
        name = v['name']
        print(f"  {flag} {code}: {combo} [{tod}] — {tag}")

# Test state month
print()
r2 = c.get('/api/results/NY/month/2026/6')
d2 = json.loads(r2.data)
total = d2.get('total', 0)
days = d2.get('days', [])
print(f"NY June 2026: {total} draws, {len(days)} days")
if days:
    first = days[0]
    print(f"  Latest day: {first['date']} — {len(first['draws'])} draws")
    for draw in first['draws']:
        print(f"    {draw['tod']}: {draw['d1']}-{draw['d2']}-{draw['d3']}")

# Test FL Midday
print()
r3 = c.get('/api/results/FL/month/2026/5')
d3 = json.loads(r3.data)
print(f"FL May 2026: {d3.get('total',0)} draws, {len(d3.get('days',[]))} days")

# Test schedule
print()
r4 = c.get('/api/states')
d4 = json.loads(r4.data)
print("Schedule sample:")
for code in ['NY','TX','FL','GA']:
    sched = d4.get(code, {}).get('schedule', [])
    print(f"  {code}: {[s['tod']+' '+s['time'] for s in sched]}")
