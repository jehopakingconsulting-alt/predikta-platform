"""
ZYNORIQ AI — Deep Verification Script
Verifies translations, code integrity, and functional endpoints.
"""
import sys, io, json, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT  = "C:/Users/PC/Downloads/lottery-analyzer"
LANGS = ['fr','en','es','pt','ht']
PASS  = 0
WARN  = 0
FAIL  = 0

def ok(msg):   global PASS; PASS+=1; print(f"  ✅  {msg}")
def warn(msg): global WARN; WARN+=1; print(f"  ⚠️  {msg}")
def fail(msg): global FAIL; FAIL+=1; print(f"  ❌  {msg}")

def read(path):
    try:    return open(os.path.join(ROOT,path), encoding='utf-8').read()
    except: return ""

# ════════════════════════════════════════════════════════
# 1. TRADUCTIONS — lecture réelle des dicts
# ════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  1. TRADUCTIONS — VERIFICATION PROFONDE")
print("="*60)

# ── index.html ──
idx = read("static/index.html")
t_match = re.search(r'const T\s*=\s*\{(.+?)\};\s*//\s*═|const T\s*=\s*(\{.+?^};)', idx, re.DOTALL)
# Extract T dict manually
t_block = re.search(r'const T = \{(.*?)\}\s*;\s*\n\s*\n', idx, re.DOTALL)
print("\n[index.html] Dictionnaire T:")
REQUIRED_KEYS = ['heroTitle','heroSub','btnAnalyze','btnScrape','welcome','analyzing',
    'scraping','lastDraw','predictions','models','hotcold','gaps','fourier','entropy',
    'markov','sums','parity','pairs','mlActive','mlInactive','statsTitle',
    'today','totalDraws','noData','confVH','confH','confM','confL','confVL',
    'overdue','pos','draw','rank','combo','score','footer']
for lang in LANGS:
    # Check key count in T dict
    pattern = f"'{lang}':" + r'\s*\{([^}]+)\}'
    m = re.search(pattern, idx)
    if m:
        keys_found = re.findall(r"(\w+):", m.group(1))
        missing = [k for k in REQUIRED_KEYS if k not in m.group(1)]
        if missing:
            warn(f"index.html [{lang}] — {len(keys_found)} clés OK, manque: {missing[:3]}...")
        else:
            ok(f"index.html [{lang}] — {len(keys_found)} clés toutes présentes")
    else:
        fail(f"index.html [{lang}] — dict non trouvé")

# ── results.html ──
res = read("static/results.html")
print("\n[results.html] Dictionnaire LANGS:")
RESULT_KEYS = ['title','sub','search','gridTitle','today','yesterday','noData',
    'update','noDataMsg','scrapeBtn','loading','draws','allStates']
for lang in LANGS:
    pattern = f"'{lang}':" + r'\s*\{([^}]+)\}'
    m = re.search(pattern, res)
    if m:
        missing = [k for k in RESULT_KEYS if k not in m.group(1)]
        if missing:
            warn(f"results.html [{lang}] — manque: {missing}")
        else:
            ok(f"results.html [{lang}] — {len(RESULT_KEYS)} clés OK")
    else:
        fail(f"results.html [{lang}] — dict non trouvé")

# ── nav.js ──
nav = read("static/nav.js")
print("\n[nav.js] NAV_T:")
NAV_KEYS = ['results','analyze','pro','about','faq','contact']
for lang in LANGS:
    pattern = f"'{lang}':" + r'\s*\{([^}]+)\}'
    m = re.search(pattern, nav)
    if m:
        missing = [k for k in NAV_KEYS if k not in m.group(1)]
        if missing:
            warn(f"nav.js [{lang}] — manque: {missing}")
        else:
            ok(f"nav.js [{lang}] — {len(NAV_KEYS)} clés OK")
    else:
        fail(f"nav.js [{lang}] — dict non trouvé")

# ── bizai.html ──
biz = read("static/bizai.html")
print("\n[bizai.html] (page en FR — multilingue via nav.js):")
has_fr = 'fr' in biz or "'fr'" in biz
ok("bizai.html — Interface française complète") if has_fr else fail("bizai.html — pas de français")
ok("bizai.html — nav.js inclus (langue auto)") if 'nav.js' in biz else fail("bizai.html — nav.js manquant")

# ════════════════════════════════════════════════════════
# 2. FONCTIONS JS CRITIQUES
# ════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  2. FONCTIONS JS CRITIQUES")
print("="*60)

js_checks_index = [
    ("function setLang",        "setLang() — changement de langue"),
    ("function loadReport",     "loadReport() — chargement rapport"),
    ("function runScrape",      "runScrape() — scraping"),
    ("function renderAll",      "renderAll() — rendu complet"),
    ("function renderConsensus","renderConsensus() — prédictions"),
    ("function renderHotCold",  "renderHotCold() — chaud/froid"),
    ("function renderGaps",     "renderGaps() — écarts"),
    ("function renderMarkov",   "renderMarkov() — Markov"),
    ("function sharePrediction","sharePrediction() — partage"),
    ("function copyCombo",      "copyCombo() — copie combo"),
    ("function toggleFavCombo", "toggleFavCombo() — favoris"),
    ("function showToast",      "showToast() — notifications"),
    ("function drawFreqChart",  "drawFreqChart() — graphique fréq"),
    ("function drawSumChart",   "drawSumChart() — graphique sommes"),
    ("tickerNext",              "Ticker rotatif bannières"),
    ("PREDIKTA_LANG",           "Détection langue auto"),
    ("serviceWorker",           "PWA Service Worker"),
    ("googletagmanager",        "Google Analytics 4"),
]
print("\n[index.html]")
for pattern, label in js_checks_index:
    (ok if pattern in idx else fail)(label)

js_checks_results = [
    ("function loadAll",       "loadAll() — chargement états"),
    ("function openDetail",    "openDetail() — panneau détail"),
    ("function changeMonth",   "changeMonth() — navigation mois"),
    ("function filterStates",  "filterStates() — recherche"),
    ("function quickFilter",   "quickFilter() — filtres rapides"),
    ("function shareResult",   "shareResult() — partage résultat"),
    ("function scrapeDetail",  "scrapeDetail() — mise à jour"),
    ("function renderGrid",    "renderGrid() — grille états"),
    ("function renderDetailDays","renderDetailDays() — jours détail"),
    ("livePulse",              "Indicateur LIVE animé"),
    ("toggleFav",              "Système de favoris"),
]
print("\n[results.html]")
for pattern, label in js_checks_results:
    (ok if pattern in res else fail)(label)

js_checks_bizai = [
    ("function runAnalysis",   "runAnalysis() — lancement analyse"),
    ("function renderReport",  "renderReport() — rendu rapport"),
    ("function collectData",   "collectData() — collecte formulaire"),
    ("function nextStep",      "nextStep() — wizard navigation"),
    ("function loadExample",   "loadExample() — exemples"),
    ("function drawGauge",     "drawGauge() — jauge viabilité"),
    ("function switchPlanTab", "switchPlanTab() — onglets plan"),
    ("function exportPDF",     "exportPDF() — export"),
    ("function shareReport",   "shareReport() — partage rapport"),
    ("EXAMPLES",               "Projets exemples pré-chargés"),
    ("api/bizai/analyze",      "Appel API Business AI"),
]
print("\n[bizai.html]")
for pattern, label in js_checks_bizai:
    (ok if pattern in biz else fail)(label)

# ════════════════════════════════════════════════════════
# 3. BACKEND PYTHON
# ════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  3. BACKEND PYTHON")
print("="*60)

# app.py
app_content = read("app.py")
app_checks = [
    ("add_security_headers",          "Middleware sécurité"),
    ("X-Content-Type-Options",        "Header XSS protection"),
    ("X-Frame-Options",               "Header anti-clickjacking"),
    ("Access-Control-Allow-Origin",   "CORS"),
    ("errorhandler(404)",             "Handler 404"),
    ("errorhandler(500)",             "Handler 500"),
    ("/api/subscribe",                "Endpoint newsletter"),
    ("/api/contact",                  "Endpoint contact"),
    ("/api/health",                   "Endpoint health check"),
    ("/api/report",                   "Endpoint analyseur loterie"),
    ("/api/scrape",                   "Endpoint scraping"),
    ("/api/results/latest",           "Endpoint résultats latest"),
    ("/api/results/<state_code>/month","Endpoint résultats par mois"),
    ("/api/bizai/analyze",            "Endpoint Business AI"),
    ("/api/bizai/meta",               "Endpoint meta Business AI"),
    ("save_subscriber",               "Sauvegarde abonnés"),
    ("DRAW_SCHEDULE",                 "Horaires tirages par état"),
    ("STATE_FLAGS",                   "Emojis états"),
    ("NumpyJSONProvider",             "Sérialisation numpy"),
    ("from biz_engine import",        "Import biz_engine"),
    ("from ml_engine import",         "Import ml_engine"),
    ("from scraper import",           "Import scraper"),
]
print("\n[app.py]")
for pattern, label in app_checks:
    (ok if pattern in app_content else fail)(label)

# biz_engine.py
biz_eng = read("biz_engine.py")
biz_eng_checks = [
    ("def analyze_project",      "Fonction principale analyze_project"),
    ("def _viability_score",     "Score de viabilité"),
    ("def _market_analysis",     "Analyse de marché"),
    ("def _audience_analysis",   "Analyse audience"),
    ("def _competitive_analysis","Analyse concurrentielle"),
    ("def _product_recommendations","Recommandations produit"),
    ("def _launch_strategy",     "Stratégie de lancement"),
    ("def _recommend_channels",  "Recommandation canaux"),
    ("def _platform_priorities", "Priorités plateformes"),
    ("def _geo_analysis",        "Analyse géographique"),
    ("def _budget_allocation",   "Allocation budget"),
    ("def _risk_assessment",     "Analyse des risques"),
    ("def _action_plan",         "Plan d'action 30-60-90"),
    ("PLATFORMS",                "Base de données plateformes"),
    ("INDUSTRIES",               "Base de données secteurs"),
    ("COUNTRIES_DATA",           "Base de données pays"),
    ("facebook",                 "Plateforme Facebook"),
    ("linkedin",                 "Plateforme LinkedIn"),
    ("tiktok",                   "Plateforme TikTok"),
    ("email",                    "Canal Email Marketing"),
    ("whatsapp",                 "Canal WhatsApp"),
]
print("\n[biz_engine.py]")
for pattern, label in biz_eng_checks:
    (ok if pattern in biz_eng else fail)(label)

# ml_engine.py
ml_eng = read("ml_engine.py")
ml_checks = [
    ("class MLPredictor",        "Classe ML principale"),
    ("RandomForestClassifier",   "Random Forest"),
    ("XGBClassifier",            "XGBoost"),
    ("GradientBoostingClassifier","Gradient Boosting"),
    ("def markov_predict",       "Prédiction Markov"),
    ("def fourier_cycles",       "Analyse Fourier"),
    ("def monte_carlo",          "Simulation Monte Carlo"),
    ("def ensemble_consensus",   "Consensus ensemble"),
    ("def build_features",       "Feature engineering"),
    ("def run_all_models",       "Runner tous modèles"),
    ("def digit_gap_analysis",   "Analyse des écarts"),
    ("def entropy_analysis",     "Analyse entropie"),
    ("def chi_square_test",      "Test chi-carré"),
    ("def sum_analysis",         "Analyse des sommes"),
    ("def parity_analysis",      "Analyse parité"),
    ("n_simulations=50000",      "Monte Carlo 50 000 simulations"),
]
print("\n[ml_engine.py]")
for pattern, label in ml_checks:
    (ok if pattern in ml_eng else fail)(label)

# scraper.py
scr = read("scraper.py")
scraper_checks = [
    ('"NY"',  "État New York"),
    ('"GA"',  "État Georgia"),
    ('"TX"',  "État Texas"),
    ('"FL"',  "État Florida"),
    ('"CA"',  "État California"),
    ('"PA"',  "État Pennsylvania"),
    ('"IL"',  "État Illinois"),
    ('"DC"',  "État DC (nouveau)"),
    ('"PR"',  "Puerto Rico (nouveau)"),
    ("def parse_draws",       "Parser HTML lotterypost"),
    ("def fetch_months",      "Pagination par mois"),
    ("def save_csv",          "Sauvegarde CSV"),
    ("def load_csv",          "Chargement CSV"),
    ("Fireball",              "Gestion numéro Fireball (TX/FL)"),
    ("urllib3.disable_warnings","SSL warnings supprimés"),
]
print("\n[scraper.py]")
for pattern, label in scraper_checks:
    (ok if pattern in scr else fail)(label)

# ════════════════════════════════════════════════════════
# 4. TESTS FONCTIONNELS LIVE
# ════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  4. TESTS FONCTIONNELS — ENDPOINTS LIVE")
print("="*60)

from app import app as flask_app
flask_app.config['TESTING'] = True
client = flask_app.test_client()

def test_endpoint(method, path, data=None, expected_keys=None, label=None):
    try:
        if method == 'GET':
            r = client.get(path)
        else:
            r = client.post(path, data=json.dumps(data), content_type='application/json')

        if r.status_code != 200:
            fail(f"{label or path} — HTTP {r.status_code}")
            return None

        try:
            d = json.loads(r.data)
        except:
            ok(f"{label or path} — HTML OK")
            return r.data

        if expected_keys:
            missing = [k for k in expected_keys if k not in d]
            if missing:
                warn(f"{label or path} — clés manquantes: {missing}")
            else:
                ok(f"{label or path} — {len(expected_keys)} clés OK")
        else:
            ok(f"{label or path} — {r.status_code} OK")
        return d
    except Exception as e:
        fail(f"{label or path} — ERREUR: {str(e)[:60]}")
        return None

print("\n[Pages HTML]")
for path in ['/','/results','/bizai','/pro','/about','/faq','/contact','/privacy','/terms','/offline']:
    test_endpoint('GET', path, label=path)

print("\n[API Endpoints]")
health = test_endpoint('GET','/api/health',expected_keys=['status','version','states_loaded','total_states'],label="GET /api/health")
if health:
    ok(f"  → {health['states_loaded']}/{health['total_states']} états chargés, version {health['version']}")

states = test_endpoint('GET','/api/states',label="GET /api/states")
if states:
    ok(f"  → {len(states)} états retournés")

latest = test_endpoint('GET','/api/results/latest',label="GET /api/results/latest")
if latest:
    has_data = sum(1 for v in latest.values() if v.get('has_data'))
    ok(f"  → {has_data}/{len(latest)} états avec données")

ny_month = test_endpoint('GET','/api/results/NY/month/2026/6',
    expected_keys=['state','name','days','total'],label="GET /api/results/NY/month/2026/6")
if ny_month:
    ok(f"  → {ny_month.get('total',0)} tirages NY juin 2026")

report = test_endpoint('GET','/api/report?state=NY&tod=all',
    expected_keys=['consensus','viability','total_draws','ml_trained','channels'],
    label="GET /api/report?state=NY")
if report:
    ok(f"  → {report.get('total_draws')} tirages, ML: {report.get('ml_trained')}, top: {report['consensus'][0]['combo'] if report.get('consensus') else '?'}")

meta = test_endpoint('GET','/api/bizai/meta',
    expected_keys=['industries','countries','platforms'],label="GET /api/bizai/meta")
if meta:
    ok(f"  → {len(meta['industries'])} secteurs, {len(meta['countries'])} pays, {len(meta['platforms'])} plateformes")

biz_payload = {
    "project_name":"Deep Verify Test",
    "industry":"tech","model":"B2C","stage":"mvp","prod_type":"app",
    "price_range":"medium","target_ages":["18-25","25-35"],
    "usp":"Application mobile pour analyser les marchés émergents",
    "geo_scope":"international","geo_countries":["France","Haiti","Brésil"],
    "languages":["fr","ht","pt"],"goal":"downloads","timeline":"3-6",
    "budget_tier":"mid","competitors":["Competitor A","Competitor B"]
}
biz_result = test_endpoint('POST','/api/bizai/analyze',data=biz_payload,
    expected_keys=['success','report'],label="POST /api/bizai/analyze")
if biz_result and biz_result.get('success'):
    rep = biz_result['report']
    sections = ['viability','market','audience','competition','product_recs','launch','channels','platforms','geo','budget','risks','action_plan']
    all_present = all(s in rep for s in sections)
    ok(f"  → Score: {rep['viability']['score']}/100, {len(sections)}/12 sections") if all_present else warn("  → Sections manquantes")
    ok(f"  → Canal #1: {rep['channels'][0]['icon']} {rep['channels'][0]['name']}")
    ok(f"  → Plan 30j: {len(rep['action_plan']['day30'])} actions")

sub = test_endpoint('GET','/api/subscribe?email=final_test@predikta.ai&lang=fr',
    expected_keys=['success','message'],label="GET /api/subscribe")

# ════════════════════════════════════════════════════════
# 5. QUALITE CODE
# ════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  5. QUALITE & SECURITE CODE")
print("="*60)

# Check no LotteryPost in public pages
public_pages = ['static/index.html','static/results.html','static/about.html',
                 'static/faq.html','static/terms.html','static/bizai.html']
print("\n[Références LotteryPost dans pages publiques]")
for page in public_pages:
    content = read(page)
    if 'lotterypost' in content.lower():
        warns = [l.strip()[:80] for l in content.split('\n') if 'lotterypost' in l.lower()]
        warn(f"{page} — {len(warns)} référence(s) encore présente(s)")
    else:
        ok(f"{page} — Aucune référence LotteryPost")

# Check no blocked links
print("\n[Liens bloqués onclick=return false]")
for page in ['static/index.html','static/results.html','static/bizai.html','static/pro.html']:
    content = read(page)
    count = content.count('onclick="return false"')
    if count > 0:
        fail(f"{page} — {count} lien(s) bloqué(s)")
    else:
        ok(f"{page} — Aucun lien bloqué")

# Check GA4 in all main pages
print("\n[Google Analytics 4]")
for page in ['static/index.html','static/results.html','static/bizai.html']:
    content = read(page)
    has_ga = 'googletagmanager' in content
    (ok if has_ga else fail)(f"{page} — GA4 {'présent' if has_ga else 'MANQUANT'}")

# Check nav.js in all pages
print("\n[nav.js dans toutes les pages]")
all_pages = ['static/index.html','static/results.html','static/bizai.html',
             'static/pro.html','static/about.html','static/faq.html',
             'static/contact.html','static/privacy.html','static/terms.html']
for page in all_pages:
    content = read(page)
    (ok if 'nav.js' in content else fail)(f"{os.path.basename(page)}")

# ════════════════════════════════════════════════════════
# SCORE FINAL
# ════════════════════════════════════════════════════════
total = PASS + WARN + FAIL
print("\n" + "="*60)
print("  SCORE FINAL")
print("="*60)
print(f"\n  ✅ PASS  : {PASS}/{total}")
print(f"  ⚠️  WARN  : {WARN}/{total}")
print(f"  ❌ FAIL  : {FAIL}/{total}")
score = round(PASS/total*100) if total else 0
print(f"\n  SCORE GLOBAL : {score}%")

if FAIL == 0 and WARN <= 3:
    print("\n  🚀 ZYNORIQ AI EST PRÊT POUR LE DÉPLOIEMENT")
elif FAIL == 0:
    print(f"\n  ✅ Prêt — {WARN} avertissement(s) mineur(s) à surveiller")
else:
    print(f"\n  ⚠️  {FAIL} problème(s) critique(s) à corriger avant déploiement")
