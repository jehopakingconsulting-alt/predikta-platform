import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
app.config['TESTING'] = True
c = app.test_client()

# Test NY all draws
r = c.get('/api/report?state=NY&tod=all')
d = json.loads(r.data)
print('NY all:', r.status_code, '| draws:', d.get('total_draws'), '| ML:', d.get('ml_trained'))
print('Top 5 consensus:')
for s in d.get('consensus', [])[:5]:
    print(' ', s['combo'], '|', round(s['confidence_pct'],1), '%')

# Test FL Midday only
r2 = c.get('/api/report?state=FL&tod=Midday')
d2 = json.loads(r2.data)
print()
print('FL Midday:', r2.status_code, '| draws:', d2.get('total_draws'))
for s in d2.get('consensus', [])[:3]:
    print(' ', s['combo'], '|', round(s['confidence_pct'],1), '%')

# Test TX Morning only
r3 = c.get('/api/report?state=TX&tod=Morning')
d3 = json.loads(r3.data)
print()
print('TX Morning:', r3.status_code, '| draws:', d3.get('total_draws'))
for s in d3.get('consensus', [])[:3]:
    print(' ', s['combo'], '|', round(s['confidence_pct'],1), '%')

# Test /api/states
r4 = c.get('/api/states')
d4 = json.loads(r4.data)
print()
print('States with data:')
for code, info in d4.items():
    if info['draws'] > 0:
        print(f"  {code}: {info['draws']} draws — {info['name']}")
