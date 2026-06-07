"""
Supprime toutes les références "AI/IA" des fichiers publics de PREDIKTA.
Remplace par des termes neutres et professionnels.
"""
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = "C:/Users/PC/Downloads/lottery-analyzer/static"

REPLACEMENTS = [
    # Titre principal
    ("PREDIKTA AI",                    "PREDIKTA"),
    ("PREDIKTA — AI",                  "PREDIKTA"),

    # Business AI → Business Intelligence
    ("Business AI",                    "Business Intelligence"),
    ("business AI",                    "Business Intelligence"),
    ("PREDIKTA Business AI",           "PREDIKTA Business"),
    ("predikta-business-ai",           "predikta-business"),
    ("bizai.html",                     "bizai.html"),  # garder l'URL technique

    # IA/AI en français
    ("Intelligence Artificielle",      "Analyse Prédictive"),
    ("intelligence artificielle",      "analyse prédictive"),
    ("par Intelligence Artificielle",  "par Algorithmes Avancés"),
    ("Prédictions par Inteligencia Artificial", "Predicciones por Algoritmos Avanzados"),
    ("Previsões por Inteligência Artificial",   "Previsões por Algoritmos Avançados"),
    ("Prediksyon pa Entèlijans Atifisyèl",      "Prediksyon pa Algoritm Avanse"),

    # Badges et labels
    ("🤖 XGBoost + Random Forest",     "⚡ XGBoost + Random Forest"),
    ("modèles IA",                     "algorithmes"),
    ("Modèles IA",                     "Algorithmes"),
    ("7 Modèles IA",                   "7 Algorithmes"),
    ("7 modèles IA",                   "7 algorithmes"),
    ("modèles indépendants",           "algorithmes indépendants"),
    ("ML actif",                       "Actif"),
    ("ML: Actif",                      "Actif"),
    ("ML trained",                     "Analyseur actif"),
    ("ML:True",                        "Actif"),
    ("Analyser par IA",                "Analyser"),
    ("Analyse IA",                     "Analyse"),

    # Taglines
    ("Loterie & Business Intelligence", "Loterie & Analyse Prédictive"),
    ("Lottery & Business Intelligence", "Lottery & Predictive Analysis"),
    ("Lotería & Inteligencia de Negocios", "Lotería & Análisis Predictivo"),
    ("Loteria & Inteligência de Negócios", "Loteria & Análise Preditiva"),
    ("Lotri & Entèlijans Biznis",          "Lotri & Analiz Biznis"),

    # World Lottery & Business Intelligence
    ("World Lottery Intelligence",     "World Lottery Analytics"),
    ("AI · WORLD LOTTERY INTELLIGENCE","WORLD LOTTERY ANALYTICS"),

    # Meta descriptions
    ("par intelligence artificielle",  "par algorithmes avancés"),
    ("Powered by AI",                  "Powered by Advanced Analytics"),

    # Assistant
    ("Assistant IA",                   "Assistant PREDIKTA"),
    ("assistant IA",                   "assistant PREDIKTA"),

    # Descriptions techniques (garder termes neutres)
    ("algorithmes IA",                 "algorithmes"),
    ("Algorithmes IA",                 "Algorithmes"),
    ("IA intégrée",                    "Algorithmes intégrés"),

    # Titres de pages
    ("Prédictions par Intelligence Artificielle", "Prédictions par Algorithmes Avancés"),
    ("Artificial Intelligence Predictions",       "Advanced Algorithm Predictions"),
    ("Predicciones por Inteligencia Artificial",  "Predicciones por Algoritmos Avanzados"),

    # Tags / badges visibles
    ("hb-ai\">🤖",                    "hb-ai\">⚡"),
    ("XGBoost + Random Forest",        "XGBoost + Random Forest"),  # garder

    # Business page
    ("Analyse Complète de Projet par Intelligence Artificielle",
     "Analyse Complète de Projet par Algorithmes Avancés"),
    ("Notre IA génère",                "Nos algorithmes génèrent"),
    ("notre IA",                       "nos algorithmes"),
    ("Notre IA",                       "Nos algorithmes"),
    ("l'IA génère",                    "les algorithmes génèrent"),
    ("votre analyse avec l'IA",        "votre analyse"),
]

# Fichiers à traiter
FILES = [
    "index.html", "results.html", "bizai.html", "pro.html",
    "about.html", "faq.html", "contact.html", "privacy.html",
    "terms.html", "404.html", "offline.html", "home.html",
    "all_results.html", "presentation.html", "nav.js", "sw.js", "manifest.json",
]

print("=== Suppression des références IA/AI ===\n")

total_changes = 0
for fname in FILES:
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        print(f"  SKIP (introuvable): {fname}")
        continue

    content = open(path, encoding='utf-8').read()
    original = content
    changes = 0

    for old, new in REPLACEMENTS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            changes += count

    if changes:
        open(path, 'w', encoding='utf-8').write(content)
        print(f"  [OK] {fname} — {changes} remplacement(s)")
        total_changes += changes
    else:
        print(f"  [--] {fname} — aucun changement")

# Traiter aussi app.py et nav.js à la racine
for fname in ["../app.py", "../scraper.py", "../biz_engine.py"]:
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        continue
    content = open(path, encoding='utf-8').read()
    changes = 0
    for old, new in REPLACEMENTS:
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            changes += count
    if changes:
        open(path, 'w', encoding='utf-8').write(content)
        print(f"  [OK] {os.path.basename(fname)} — {changes} remplacement(s)")
        total_changes += changes

print(f"\nTotal: {total_changes} remplacements effectués.")
print("\n=== Vérification résiduelle ===")

# Check for remaining AI/IA occurrences that might be visible to users
for fname in FILES:
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        continue
    content = open(path, encoding='utf-8').read()
    # Find visible AI references (not in URLs, comments, or technical code)
    lines_with_ai = []
    for i, line in enumerate(content.split('\n'), 1):
        stripped = line.strip()
        # Skip URLs, code comments, JS variable names, CSS classes
        if any(skip in stripped for skip in ['//', '/*', '*/', 'class=', 'id=', 'href=', 'src=', 'url(', 'api/', 'bizai', 'function ', 'var ', 'const ', 'let ']):
            continue
        # Check for AI/IA in visible text
        if re.search(r'\bIA\b|\bAI\b', stripped, re.IGNORECASE):
            lines_with_ai.append(f"    L{i}: {stripped[:80]}")
    if lines_with_ai:
        print(f"\n  {fname} — occurrences restantes:")
        for l in lines_with_ai[:5]:
            print(l)

print("\nDone.")
