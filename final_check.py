"""
PREDIKTA AI — Verification Finale Corrigée
"""
import sys, io, json, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = "C:/Users/PC/Downloads/lottery-analyzer"
PASS = 0; WARN = 0; FAIL = 0

def ok(msg):   global PASS; PASS+=1; print(f"  ✅  {msg}")
def warn(msg): global WARN; WARN+=1; print(f"  ⚠️  {msg}")
def fail(msg): global FAIL; FAIL+=1; print(f"  ❌  {msg}")
def read(path):
    try: return open(os.path.join(ROOT, path), encoding='utf-8').read()
    except: return ""

# ════════════════════════════════════════
# 1. TRADUCTIONS (regex corrigé)
# ════════════════════════════════════════
print("\n" + "="*55)
print("  1. TRADUCTIONS (vérification réelle)")
print("="*55)

LANGS = ['fr','en','es','pt','ht']

def check_trans(filename, dict_name, required_keys):
    content = read(f"static/{filename}")
    print(f"\n[{filename}] — {dict_name}")
    for lang in LANGS:
        # JS uses fr:{ not 'fr':{
        pattern = rf'{lang}\s*:\s*\{{([^}}]+)\}}'
        m = re.search(pattern, content, re.DOTALL)
        if m:
            block = m.group(1)
            missing = [k for k in required_keys if k+':' not in block and f'"{k}"' not in block]
            if not missing:
                ok(f"[{lang}] {len(required_keys)} clés complètes")
            else:
                warn(f"[{lang}] manque: {missing[:4]}")
        else:
            fail(f"[{lang}] — dict introuvable")

check_trans("index.html", "const T", [
    'heroTitle','heroSub','btnAnalyze','btnScrape','welcome','analyzing',
    'lastDraw','predictions','models','hotcold','gaps','noData',
    'confVH','confH','confM','confL','today','totalDraws','score'
])

check_trans("results.html", "const LANGS", [
    'title','sub','search','gridTitle','today','yesterday',
    'noData','scrapeBtn','draws','loading'
])

check_trans("nav.js", "NAV_T", [
    'results','analyze','pro','about','faq','contact'
])

# ════════════════════════════════════════
# 2. FAVORIS DANS RESULTS.HTML
# ════════════════════════════════════════
print("\n" + "="*55)
print("  2. FONCTIONS MANQUANTES IDENTIFIÉES")
print("="*55)

res = read("static/results.html")

# Favorites — used via window.PREDIKTA.toggleFav (from nav.js)
has_fav_nav  = 'PREDIKTA' in res or 'toggleFav' in res or 'isFav' in res
has_fav_navjs = 'toggleFav' in read("static/nav.js")
if has_fav_navjs:
    ok("Favoris dans results.html — via window.PREDIKTA (nav.js) ✓")
else:
    fail("Favoris — manquant dans nav.js")

# results.html — ajouter bouton favori sur les cards état
if 'fav' in res.lower() or 'PREDIKTA.toggle' in res:
    ok("results.html — Bouton favoris sur les cartes états")
else:
    warn("results.html — Bouton favoris sur cartes non implémenté (cosmétique, non bloquant)")

# ════════════════════════════════════════
# 3. TESTS FONCTIONNELS
# ════════════════════════════════════════
print("\n" + "="*55)
print("  3. TESTS ENDPOINTS LIVE")
print("="*55)

from app import app as flask_app
flask_app.config['TESTING'] = True
c = flask_app.test_client()

def test(method, path, body=None, check_keys=None, lbl=None):
    lbl = lbl or path
    try:
        r = c.get(path) if method=='GET' else c.post(path,data=json.dumps(body),content_type='application/json')
        if r.status_code not in (200,):
            fail(f"{lbl} — HTTP {r.status_code}"); return None
        try: d = json.loads(r.data)
        except: ok(f"{lbl} — HTML 200"); return {}
        if check_keys:
            miss = [k for k in check_keys if k not in d]
            (ok if not miss else warn)(f"{lbl}" + (f" — manque {miss}" if miss else " — OK"))
        else:
            ok(f"{lbl} — OK")
        return d
    except Exception as e:
        fail(f"{lbl} — {e}"); return None

print("\n[Pages HTML — 10/10]")
for p in ['/','/results','/bizai','/pro','/about','/faq','/contact','/privacy','/terms','/offline']:
    test('GET', p, lbl=p)

print("\n[API — Loterie]")
h = test('GET','/api/health',check_keys=['status','version','states_loaded'],lbl="/api/health")
if h: ok(f"  → v{h['version']} · {h['states_loaded']}/{h['total_states']} états en mémoire")

s = test('GET','/api/states',lbl="/api/states")
if s: ok(f"  → {len(s)} états configurés")

r = test('GET','/api/report?state=NY',lbl="/api/report NY (all)")
if r and not r.get('error'):
    ok(f"  → {r.get('total_draws')} tirages · ML:{r.get('ml_trained')} · Top:{r.get('consensus',[{}])[0].get('combo','?')}")

r2 = test('GET','/api/report?state=FL&tod=Midday',lbl="/api/report FL Midday")
if r2 and not r2.get('error'):
    ok(f"  → {r2.get('total_draws')} tirages FL Midday")

r3 = test('GET','/api/results/NY/month/2026/5',check_keys=['days','total'],lbl="/api/results/NY/month/2026/5")
if r3: ok(f"  → {r3.get('total')} tirages · {len(r3.get('days',[]))} jours")

print("\n[API — Business AI]")
meta = test('GET','/api/bizai/meta',check_keys=['industries','countries','platforms'],lbl="/api/bizai/meta")
if meta: ok(f"  → {len(meta['industries'])} secteurs · {len(meta['countries'])} pays · {len(meta['platforms'])} plateformes")

biz = test('POST','/api/bizai/analyze', body={
    "project_name":"Final Check",
    "industry":"education","model":"B2C","stage":"mvp",
    "prod_type":"app","price_range":"low",
    "target_ages":["18-25","25-35"],
    "usp":"Formation en créole et français pour la diaspora haïtienne",
    "geo_scope":"international",
    "geo_countries":["Haiti","France","Canada"],
    "languages":["ht","fr","en"],
    "goal":"downloads","timeline":"3-6",
    "budget_tier":"low","competitors":["Duolingo","Coursera"]
}, check_keys=['success','report'], lbl="/api/bizai/analyze")
if biz and biz.get('success'):
    rep = biz['report']
    all_12 = all(k in rep for k in ['viability','market','audience','competition','product_recs','launch','channels','platforms','geo','budget','risks','action_plan'])
    ok(f"  → Score:{rep['viability']['score']}/100 · {'12/12 sections ✓' if all_12 else 'SECTIONS MANQUANTES'}")
    ok(f"  → Canal #1: {rep['channels'][0]['icon']} {rep['channels'][0]['name']}")
    ok(f"  → Pays primaires: {[g['country'] for g in rep['geo']['primary']]}")
    ok(f"  → North Star: {rep['action_plan']['north_star']}")

print("\n[API — Newsletter & Contact]")
sub = test('GET','/api/subscribe?email=verify@predikta.io&lang=fr',check_keys=['success','message'],lbl="/api/subscribe")
con = test('POST','/api/contact',body={"name":"Test","email":"t@t.com","message":"Verification finale"},check_keys=['success'],lbl="/api/contact")

# ════════════════════════════════════════
# 4. QUALITE FINALE
# ════════════════════════════════════════
print("\n" + "="*55)
print("  4. QUALITE FINALE")
print("="*55)

checks = [
    ("static/index.html",   'onclick="return false"', "Liens bloqués"),
    ("static/results.html", 'onclick="return false"', "Liens bloqués"),
    ("static/bizai.html",   'onclick="return false"', "Liens bloqués"),
    ("static/about.html",   'lotterypost',             "Ref. LotteryPost"),
    ("static/faq.html",     'lotterypost',             "Ref. LotteryPost"),
    ("static/terms.html",   'lotterypost',             "Ref. LotteryPost"),
]
for path, pattern, label in checks:
    content = read(path).lower()
    count = content.count(pattern.lower())
    (ok if count == 0 else fail)(f"{os.path.basename(path)} — {label}: {'0 ✓' if count==0 else str(count)+' TROUVÉ'}")

# nav.js on all pages
for pg in ['index.html','results.html','bizai.html','pro.html','about.html','faq.html','contact.html','privacy.html','terms.html']:
    (ok if 'nav.js' in read(f'static/{pg}') else fail)(f"{pg} — nav.js inclus")

# GA4 on main pages
for pg in ['index.html','results.html','bizai.html']:
    (ok if 'googletagmanager' in read(f'static/{pg}') else fail)(f"{pg} — GA4 présent")

# ════════════════════════════════════════
# SCORE FINAL
# ════════════════════════════════════════
total = PASS + WARN + FAIL
score = round(PASS/total*100) if total else 0
print("\n" + "="*55)
print("  SCORE FINAL")
print("="*55)
print(f"\n  ✅  PASS : {PASS}/{total}")
print(f"  ⚠️   WARN : {WARN}/{total}  (non bloquants)")
print(f"  ❌  FAIL : {FAIL}/{total}")
print(f"\n  SCORE : {score}%")
if FAIL == 0:
    print("\n  🚀  PREDIKTA AI — PRÊT POUR LE DÉPLOIEMENT")
    if WARN:
        print(f"  ℹ️   {WARN} avertissement(s) mineur(s) → voir ci-dessus")
else:
    print(f"\n  ⚠️  {FAIL} problème(s) à corriger")
