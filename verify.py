"""Verification complete de PREDIKTA AI."""
import os, re, json, sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = "C:/Users/PC/Downloads/lottery-analyzer"

def read(path):
    try:
        return open(os.path.join(ROOT, path), encoding='utf-8').read()
    except:
        return ""

OK   = "[OK]  "
WARN = "[WARN]"
MISS = "[MISS]"

print("=" * 60)
print("  PREDIKTA AI — VERIFICATION FINALE COMPLETE")
print("=" * 60)

# ── TRADUCTIONS ──────────────────────────────────────────────
print("\n--- TRADUCTIONS ---")
langs = ['fr','en','es','pt','ht']

checks = {
    "index.html":   (read("static/index.html"),   "const T = {", ["fr:","en:","es:","pt:","ht:"]),
    "results.html": (read("static/results.html"),  "const LANGS = {", ["fr:{","en:{","es:{","pt:{","ht:{"]),
    "bizai.html":   (read("static/bizai.html"),    "multilingual", ["fr:","en:","es:","pt:","ht:"]),
    "nav.js":       (read("static/nav.js"),         "NAV_T = {", ["fr:","en:","es:","pt:","ht:"]),
}

for fname, (content, marker, patterns) in checks.items():
    found_langs = [l for l in langs if f"'{l}'" in content or f'"{l}"' in content]
    if len(found_langs) >= 5:
        print(f"{OK} {fname} — {len(found_langs)}/5 langues: {found_langs}")
    elif len(found_langs) > 0:
        missing = [l for l in langs if l not in found_langs]
        print(f"{WARN} {fname} — {len(found_langs)}/5 langues (manque: {missing})")
    else:
        print(f"{MISS} {fname} — aucune traduction multi-langue")

# ── LIENS AFFILIES ───────────────────────────────────────────
print("\n--- LIENS AFFILIES & UTM ---")
index_content = read("static/index.html")
nav_content   = read("static/nav.js")
combined = index_content + nav_content

affiliate_checks = [
    ("utm_source=predikta",       "UTM source predikta"),
    ("utm_medium=affiliate",      "UTM medium affiliate"),
    ("utm_campaign=",             "UTM campaign tags"),
    ("thelotter.com",             "TheLotter URL"),
    ("lotterypro.com",            "LotteryPro URL"),
    ("jackpot.com",               "Jackpot.com URL"),
    ("target=\"_blank\"",         "Links → nouvel onglet"),
    ("rel=\"noopener\"",          "rel=noopener securite"),
    ("PREDIKTA_AFFILIATE",        "Objet PREDIKTA_AFFILIATE"),
    ("onclick=\"return false\"",  "Liens bloques (a eviter)"),
]
for pattern, label in affiliate_checks:
    found = pattern in combined
    status = WARN if pattern == "onclick=\"return false\"" and found else (OK if found else MISS)
    note = " ← ENCORE DES LIENS BLOQUES !" if pattern == "onclick=\"return false\"" and found else ""
    print(f"{status} {label}{note}")

# Count remaining blocked links
blocked = index_content.count('onclick="return false"')
if blocked > 0:
    print(f"{WARN}  {blocked} lien(s) encore bloques dans index.html")
else:
    print(f"{OK}  Aucun lien bloque dans index.html")

# ── SECURITE ─────────────────────────────────────────────────
print("\n--- SECURITE & BACKEND ---")
app_content = read("app.py")
sec_checks = [
    ("X-Content-Type-Options",    "Header securite XSS"),
    ("X-Frame-Options",           "Header anti-clickjacking"),
    ("Access-Control-Allow-Origin","CORS header"),
    ("errorhandler(404)",         "Page 404 personnalisee"),
    ("errorhandler(500)",         "Page 500 personnalisee"),
    ("/api/subscribe",            "Endpoint newsletter"),
    ("/api/contact",              "Endpoint contact"),
    ("/api/health",               "Health check"),
    ("/api/bizai/analyze",        "Business AI analyze"),
    ("LotteryPost",               "LotteryPost dans app.py (ok interne)"),
]
for pattern, label in sec_checks:
    found = pattern in app_content
    print(f"{OK if found else MISS} {label}")

# ── PAGES LEGALES ────────────────────────────────────────────
print("\n--- PAGES LEGALES & CONTENU ---")
legal_files = {
    "privacy.html": ["RGPD","confidentialité","données"],
    "terms.html":   ["responsabilité","loterie","jeux"],
    "about.html":   ["PREDIKTA","algorithme","mission"],
    "faq.html":     ["prédictions","données","abonnement"],
    "contact.html": ["/api/contact","email","formulaire"],
}
for fname, keywords in legal_files.items():
    content = read(f"static/{fname}")
    found_kw = [k for k in keywords if k.lower() in content.lower()]
    if len(found_kw) >= 2:
        print(f"{OK} {fname} — contenu OK")
    else:
        print(f"{WARN} {fname} — contenu incomplet")

# ── DONNEES ──────────────────────────────────────────────────
print("\n--- DONNEES & ETATS ---")
import glob
csvs = glob.glob(os.path.join(ROOT, "data/*.csv"))
total_draws = 0
for csv in sorted(csvs):
    with open(csv, encoding='utf-8') as f:
        lines = len(f.readlines()) - 1
    total_draws += lines
    print(f"{OK} {os.path.basename(csv)}: {lines} tirages")

scraper = read("scraper.py")
states_count = scraper.count('"slug":')
print(f"{OK} Total tirages: {total_draws}")
print(f"{OK} Etats configures dans scraper: {states_count}")
states_without_data = states_count - len(csvs)
print(f"{WARN if states_without_data>0 else OK} Etats sans donnees encore: {states_without_data} (a scraper)")

# ── PWA ──────────────────────────────────────────────────────
print("\n--- PWA & SEO ---")
manifest = read("static/manifest.json")
sw       = read("static/sw.js")
robots   = read("static/robots.txt")
sitemap  = read("static/sitemap.xml")
print(f"{OK if 'predikta' in manifest.lower() else MISS} manifest.json valide")
print(f"{OK if 'install' in sw else MISS} Service Worker install")
print(f"{OK if 'fetch' in sw else MISS} Service Worker offline cache")
print(f"{OK if 'Sitemap' in robots else MISS} robots.txt avec Sitemap")
print(f"{OK if '<url>' in sitemap else MISS} sitemap.xml avec URLs")
sitemap_count = sitemap.count('<url>')
print(f"{OK} sitemap.xml: {sitemap_count} URLs indexees")

# Check GA4 in main pages
for fname in ["index.html","results.html","bizai.html"]:
    content = read(f"static/{fname}")
    has_ga = "googletagmanager" in content or "G-XXXXXXXXXX" in content
    print(f"{OK if has_ga else MISS} Google Analytics dans {fname}")

# ── NAVIGATION ───────────────────────────────────────────────
print("\n--- NAVIGATION PARTAGEE (nav.js) ---")
nav = read("static/nav.js")
nav_checks = [
    ("bizai",              "Lien Business AI dans nav"),
    ("results",            "Lien Resultats dans nav"),
    ("toggleTheme",        "Dark/Light toggle"),
    ("toggleMobileMenu",   "Menu hamburger mobile"),
    ("predikta-btt",       "Bouton back-to-top"),
    ("localStorage",       "Favoris localStorage"),
    ("saveLang",           "Sauvegarde langue"),
    ("PREDIKTA_AFFILIATE", "Liens affilies UTM"),
]
for pattern, label in nav_checks:
    print(f"{OK if pattern in nav else MISS} {label}")

# Check nav.js included in all pages
print("\n--- nav.js INCLUS DANS LES PAGES ---")
for fname in ["index.html","results.html","bizai.html","pro.html","about.html","faq.html","contact.html","privacy.html","terms.html"]:
    content = read(f"static/{fname}")
    has_nav = "nav.js" in content
    print(f"{OK if has_nav else MISS} {fname}")

# ── SUMMARY ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  ELEMENTS A COMPLETER AVANT DEPLOIEMENT")
print("=" * 60)

todo = []
for fname in ["index.html","results.html"]:
    content = read(f"static/{fname}")
    if 'onclick="return false"' in content:
        todo.append(f"Liens bloques encore dans {fname}")

if "bizai.html" in [f for f in ["bizai.html"] if not any(f"'{l}'" in read(f"static/{f}") for l in langs)]:
    todo.append("bizai.html — traductions EN/ES/PT/HT non implementees")

todo += [
    "Remplacer G-XXXXXXXXXX par votre vrai ID Google Analytics 4",
    "Remplacer les URLs affilies par vos VRAIS IDs d'affilie (TheLotter, LotteryPro, Jackpot)",
    "Scraper les 39 etats sans donnees (python scraper.py dans terminal)",
    "Integrer Stripe/PayPal pour les paiements PRO/ELITE",
    "Configurer SMTP pour l'envoi reel des emails newsletter",
    "Acheter le domaine (predikta.io recommande) et deployer",
    "Mettre les vraies videos dans le lecteur PREDIKTA TV",
    "Remplacer localhost:5000 par votre vrai domaine dans sitemap.xml et robots.txt",
]

for i, item in enumerate(todo, 1):
    print(f"  {i:2}. {'[CODE]' if i<=2 else '[BUSI]'} {item}")

print(f"\nTotal taches restantes: {len(todo)}")
print(f"  {2} necessitent du code")
print(f"  {len(todo)-2} necessitent des comptes/services externes")
