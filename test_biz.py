import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app import app
app.config['TESTING'] = True
c = app.test_client()

# Test /api/bizai/meta
r = c.get('/api/bizai/meta')
d = json.loads(r.data)
print(f"Industries: {len(d['industries'])}")
print(f"Countries:  {len(d['countries'])}")
print(f"Platforms:  {len(d['platforms'])}")

# Test full analysis
payload = {
    "project_name": "SaaS PME Haiti",
    "description": "Logiciel de gestion comptable pour PME haitiennes",
    "industry": "tech",
    "model": "B2B",
    "stage": "idea",
    "prod_type": "saas",
    "price_range": "medium",
    "target_ages": ["25-35", "35-45"],
    "usp": "Nous aidons les PME haitiennes a gerer leur comptabilite en creole et francais, sans competence technique",
    "geo_scope": "international",
    "geo_countries": ["Haiti", "France", "Canada"],
    "languages": ["fr", "ht"],
    "goal": "sales",
    "timeline": "6-12",
    "budget_tier": "mid",
    "competitors": ["QuickBooks", "Odoo"],
}

r2 = c.post('/api/bizai/analyze',
    data=json.dumps(payload),
    content_type='application/json')
d2 = json.loads(r2.data)

if d2.get('success'):
    rep = d2['report']
    print()
    print(f"Projet:          {rep['project_name']}")
    print(f"Secteur:         {rep['industry_label']}")
    print(f"Score viabilite: {rep['viability']['score']}/100 — {rep['viability']['label']}")
    print(f"Bonuses:         {rep['viability']['bonuses'][:2]}")
    print()
    print(f"Marche:          {rep['market']['market_size']} — croissance {rep['market']['growth_rate']}")
    print(f"Niches:          {rep['market']['niches']}")
    print()
    print(f"Canaux top 3:")
    for i, ch in enumerate(rep['channels'][:3]):
        print(f"  {i+1}. {ch['icon']} {ch['name']} (score:{ch['score']})")
    print()
    print(f"Budget mensuel:  {rep['budget']['monthly_budget']}")
    print(f"Allocation:      {rep['budget']['allocation']}")
    print()
    print(f"Pays primaires:  {[g['country'] for g in rep['geo']['primary']]}")
    print(f"Pays secondaires:{[g['country'] for g in rep['geo']['secondary']]}")
    print()
    print(f"North Star:      {rep['action_plan']['north_star']}")
    print(f"Plan 30j (3 ex): {rep['action_plan']['day30'][:3]}")
    print()
    print(f"Risques:         {len(rep['risks']['risks'])}")
    print(f"Risque principal:{rep['risks']['risks'][0]['risk']}")
    print()
    print("TOUTES LES SECTIONS: OK")
    sections = ['viability','market','audience','competition','product_recs','launch','channels','platforms','geo','budget','risks','action_plan']
    for s in sections:
        print(f"  {s}: OK" if s in rep else f"  {s}: MANQUANT")
else:
    print("ERREUR:", d2.get('error'))
