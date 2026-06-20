"""Corrige les dernières occurrences visibles de IA/AI."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

fixes = [
    # home.html meta description
    ("static/home.html",
     'ZYNORIQ — Plateforme mondiale : prédictions loterie IA, résultats en direct 44 États, analyse Business complète.',
     'ZYNORIQ — Plateforme mondiale : prédictions avancées, résultats en direct 44 États, analyse Business complète.'),
    # bizai.html meta
    ("static/bizai.html",
     "avec l'IA :",
     "par algorithmes :"),
    # terms.html
    ("static/terms.html",
     "générées par des algorithmes d'IA",
     "générées par nos algorithmes avancés"),
    # manifest.json
    ("static/manifest.json",
     "Lancer l'analyse IA",
     "Lancer l'analyse"),
    # presentation.html tagline
    ("static/presentation.html",
     "prédictions de loterie par IA",
     "prédictions de loterie avancées"),
    # presentation.html comment
    ("static/presentation.html",
     "AI MODELS SHOWCASE",
     "ALGORITHM SHOWCASE"),
    # manifest description
    ("static/manifest.json",
     "Loterie & Analyse Prédictive",
     "Loterie & Analyse Prédictive"),
]

import os
ROOT = "C:/Users/PC/Downloads/lottery-analyzer"

for fname, old, new in fixes:
    path = os.path.join(ROOT, fname)
    if not os.path.exists(path):
        print(f"  SKIP: {fname}")
        continue
    content = open(path, encoding='utf-8').read()
    if old in content:
        content = content.replace(old, new)
        open(path, 'w', encoding='utf-8').write(content)
        print(f"  [OK] {fname}")
    else:
        # Try without special chars (encoding issue)
        print(f"  [--] {fname} - pattern not found (may already be fixed)")

print("\nDone.")
