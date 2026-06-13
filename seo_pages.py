"""
PREDIKTA — Public SEO pages ("Pick 3 [State] Predictions Today").

Server-rendered (no auth, no JS required for content) so search engines can
index the daily hot/cold digits & suggested combinations for each state.
Reuses the lightweight analyzer.py engine (no Monte Carlo / ML — fast enough
to compute on every request).
"""

from datetime import date
from scraper import STATES, load_csv
from analyzer import full_report

BALL_COLORS = [
    '#ff4444', '#ff7722', '#ffcc22', '#88cc22', '#22cc66',
    '#22ccbb', '#2288ff', '#7744ff', '#cc44ff', '#ff44aa',
]

STATE_FLAGS = {
    "AR": "💎", "AZ": "🌵", "CA": "☀️", "CO": "🏔️", "CT": "⚓", "DC": "🏛️",
    "DE": "🦆", "FL": "🌴", "GA": "🍑", "IA": "🌽", "ID": "🥔", "IL": "🏙️", "IN": "🏁",
    "KS": "🌾", "KY": "🐎", "LA": "🎷", "MA": "🦞", "MD": "🦀", "ME": "🦞", "MI": "🚗",
    "MN": "🌨️", "MO": "⛵", "MS": "🎶", "NC": "🌲", "NE": "🌾", "NH": "🏔️", "NJ": "🌊",
    "NM": "🌶️", "NY": "🗽", "OH": "🌻", "OK": "🛢️", "PA": "🔔", "PR": "🌺", "SC": "🌴",
    "TN": "🎸", "TX": "⭐", "VA": "🦅", "VT": "🍁", "WA": "🌧️", "WI": "🧀", "WV": "⛰️",
}

T = {
    "fr": {
        "title": lambda name, d: f"Pick 3 {name} — Prédictions du jour {d} | PREDIKTA",
        "desc": lambda name, d: f"Numéros chauds, froids et combinaisons suggérées pour {name} Pick 3, mis à jour le {d}. Analyse statistique gratuite par PREDIKTA.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Prédictions du jour",
        "lastDraw": "Dernier tirage", "hot": "🔥 Chiffres chauds (30 derniers tirages)",
        "cold": "❄️ Chiffres froids (30 derniers tirages)", "overdue": "⏳ Chiffres en retard",
        "suggestions": "Combinaisons suggérées", "confidence": "Confiance",
        "noData": "Données non disponibles pour cet État pour le moment.",
        "ctaTitle": "Aller plus loin avec PREDIKTA", "ctaDesc": "Markov, Monte Carlo, Machine Learning (XGBoost/Random Forest), analyse de Fourier, archives illimitées et plus pour tous les États.",
        "ctaBtn": "🔮 Lancer l'analyse complète →", "backToIndex": "← Tous les États",
        "indexTitle": "Pick 3 — Prédictions du jour, tous les États | PREDIKTA",
        "indexDesc": "Numéros chauds, froids et combinaisons suggérées Pick 3 pour tous les États américains, mis à jour quotidiennement.",
        "indexH1": "🎯 Pick 3 — Prédictions du jour par État",
        "totalDraws": "tirages analysés",
        "drawn": "tiré",
    },
    "en": {
        "title": lambda name, d: f"Pick 3 {name} Predictions Today {d} | PREDIKTA",
        "desc": lambda name, d: f"Hot, cold numbers and suggested combinations for {name} Pick 3, updated {d}. Free statistical analysis by PREDIKTA.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Today's Predictions",
        "lastDraw": "Last draw", "hot": "🔥 Hot digits (last 30 draws)",
        "cold": "❄️ Cold digits (last 30 draws)", "overdue": "⏳ Overdue digits",
        "suggestions": "Suggested combinations", "confidence": "Confidence",
        "noData": "No data available for this state yet.",
        "ctaTitle": "Go further with PREDIKTA", "ctaDesc": "Markov chains, Monte Carlo, Machine Learning (XGBoost/Random Forest), Fourier analysis, unlimited archives and more for every state.",
        "ctaBtn": "🔮 Run the full analysis →", "backToIndex": "← All states",
        "indexTitle": "Pick 3 — Today's Predictions for Every State | PREDIKTA",
        "indexDesc": "Hot, cold numbers and suggested Pick 3 combinations for every US state, updated daily.",
        "indexH1": "🎯 Pick 3 — Today's Predictions by State",
        "totalDraws": "draws analyzed",
        "drawn": "drawn",
    },
}

CONF_EN = {
    "Très élevée": "Very high", "Élevée": "High", "Moyenne": "Medium", "Faible": "Low",
}


def _bc(n):
    return BALL_COLORS[int(n) % 10]


def _ball(n, size=34):
    color = _bc(n)
    return (f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:{size}px;height:{size}px;border-radius:50%;font-size:.95rem;font-weight:800;'
            f'background:{color}22;border:2px solid {color};color:{color};margin:2px">{n}</span>')


def _digit_chip(n, color):
    return (f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:30px;height:30px;border-radius:50%;font-size:.85rem;font-weight:800;'
            f'background:{color}1a;border:2px solid {color};color:{color};margin:3px">{n}</span>')


def _page_shell(title, desc, canonical, lang, body, alt_links=""):
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<meta name="description" content="{desc}"/>
<link rel="canonical" href="{canonical}"/>
{alt_links}
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet"/>
<style>
:root{{--bg:#04040f;--card:#0b0b22;--border:#1a1a45;--accent:#4f6eff;--accent2:#8855ff;--gold:#ffd700;--green:#22e87a;--text:#e8eeff;--muted:#4d5a8a;--muted2:#7888bb;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6}}
a{{color:var(--accent)}}
.wrap{{max-width:760px;margin:0 auto;padding:24px 18px 60px}}
h1{{font-family:'Orbitron',monospace;font-size:clamp(1.3rem,5vw,1.9rem);font-weight:900;
  background:linear-gradient(135deg,#6688ff,#aa66ff,#ffd700);-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px;line-height:1.3}}
.sub{{color:var(--muted2);font-size:.85rem;margin-bottom:24px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:18px 20px;margin-bottom:16px}}
.card h2{{font-size:.95rem;font-weight:800;color:var(--text);margin-bottom:10px}}
.combo-chip{{display:inline-flex;align-items:center;gap:8px;padding:8px 14px;margin:4px;border-radius:10px;
  background:rgba(255,215,0,.08);border:1px solid rgba(255,215,0,.3);font-weight:800;font-size:1.1rem;
  letter-spacing:2px;color:var(--gold)}}
.combo-conf{{font-size:.62rem;font-weight:600;color:var(--muted2);letter-spacing:0;text-transform:none}}
.cta{{background:linear-gradient(135deg,rgba(79,110,255,.12),rgba(136,85,255,.1));border:1px solid var(--accent);
  border-radius:14px;padding:20px;text-align:center;margin-top:20px}}
.cta h2{{font-size:1.1rem;margin-bottom:6px}}
.cta p{{font-size:.8rem;color:var(--muted2);margin-bottom:14px}}
.cta-btn{{display:inline-block;padding:12px 26px;border-radius:10px;background:linear-gradient(135deg,var(--accent),var(--accent2));
  color:#fff;font-weight:800;text-decoration:none;font-size:.85rem}}
.back{{display:inline-block;margin-bottom:18px;font-size:.8rem;color:var(--muted2);text-decoration:none}}
.state-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}}
.state-card{{display:flex;align-items:center;gap:8px;padding:12px 14px;background:var(--card);
  border:1px solid var(--border);border-radius:10px;text-decoration:none;color:var(--text);font-weight:700;font-size:.8rem;transition:border-color .15s}}
.state-card:hover{{border-color:var(--accent)}}
</style>
</head>
<body>
<script src="/nav.js"></script>
<div class="wrap">
{body}
</div>
<footer data-pfooter></footer>
</body>
</html>"""


def render_prediction_page(state_code: str, base_url: str, lang: str = "fr") -> str:
    lang = lang if lang in T else "fr"
    t = T[lang]
    state_code = state_code.upper()
    cfg = STATES.get(state_code, {})
    name = cfg.get("name", state_code)
    today = date.today().isoformat()
    flag = STATE_FLAGS.get(state_code, "🎰")

    draws = load_csv(state_code)
    canonical = f"{base_url}/predictions/{state_code.lower()}" + ("?lang=en" if lang == "en" else "")
    alt = (f'<link rel="alternate" hreflang="fr" href="{base_url}/predictions/{state_code.lower()}"/>'
           f'<link rel="alternate" hreflang="en" href="{base_url}/predictions/{state_code.lower()}?lang=en"/>')

    if not draws:
        body = (f'<a class="back" href="/predictions{"?lang=en" if lang=="en" else ""}">{t["backToIndex"]}</a>'
                f'<h1>{flag} {t["h1"](name)}</h1>'
                f'<div class="card">{t["noData"]}</div>')
        return _page_shell(t["title"](name, today), t["desc"](name, today), canonical, lang, body, alt)

    report = full_report(state_code)
    last = report["last_draw"]
    balls = "".join(_ball(last[p]) for p in ["d1", "d2", "d3"])

    hot = [d for d, v in report["hot_cold_30"].items() if v["status"] == "HOT"]
    cold = [d for d, v in report["hot_cold_30"].items() if v["status"] == "COLD"]
    overdue = [d for d, v in report["gaps"].items() if v["overdue"]]

    hot_html = "".join(_digit_chip(d, "#ff4444") for d in hot) or "—"
    cold_html = "".join(_digit_chip(d, "#4499ff") for d in cold) or "—"
    overdue_html = "".join(_digit_chip(d, "#ffcc22") for d in overdue) or "—"

    sugg_html = ""
    for s in report["suggestions"][:5]:
        conf = s["confidence"]
        if lang == "en":
            conf = CONF_EN.get(conf, conf)
        sugg_html += f'<span class="combo-chip">{s["combo"]} <span class="combo-conf">{conf}</span></span>'

    body = f"""<a class="back" href="/predictions{'?lang=en' if lang=='en' else ''}">{t['backToIndex']}</a>
<h1>{flag} {t['h1'](name)}</h1>
<div class="sub">{today} · {report['total_draws']} {t['totalDraws']}</div>

<div class="card">
  <h2>{t['lastDraw']} — {last['date']} ({last.get('tod','')})</h2>
  <div>{balls}</div>
</div>

<div class="card">
  <h2>{t['suggestions']}</h2>
  <div>{sugg_html}</div>
</div>

<div class="card">
  <h2>{t['hot']}</h2>
  <div>{hot_html}</div>
</div>

<div class="card">
  <h2>{t['cold']}</h2>
  <div>{cold_html}</div>
</div>

<div class="card">
  <h2>{t['overdue']}</h2>
  <div>{overdue_html}</div>
</div>

<div class="cta">
  <h2>{t['ctaTitle']}</h2>
  <p>{t['ctaDesc']}</p>
  <a class="cta-btn" href="/?state={state_code}">{t['ctaBtn']}</a>
</div>"""

    return _page_shell(t["title"](name, today), t["desc"](name, today), canonical, lang, body, alt)


def render_predictions_index(base_url: str, lang: str = "fr") -> str:
    lang = lang if lang in T else "fr"
    t = T[lang]
    canonical = f"{base_url}/predictions" + ("?lang=en" if lang == "en" else "")
    alt = (f'<link rel="alternate" hreflang="fr" href="{base_url}/predictions"/>'
           f'<link rel="alternate" hreflang="en" href="{base_url}/predictions?lang=en"/>')

    qs = "?lang=en" if lang == "en" else ""
    cards = "".join(
        f'<a class="state-card" href="/predictions/{code.lower()}{qs}">'
        f'{STATE_FLAGS.get(code,"🎰")} {cfg["name"]}</a>'
        for code, cfg in sorted(STATES.items(), key=lambda kv: kv[1]["name"])
    )

    body = f"""<h1>{t['indexH1']}</h1>
<div class="sub">{date.today().isoformat()}</div>
<div class="state-grid">{cards}</div>
<div class="cta">
  <h2>{t['ctaTitle']}</h2>
  <p>{t['ctaDesc']}</p>
  <a class="cta-btn" href="/pro">{t['ctaBtn']}</a>
</div>"""

    return _page_shell(t["indexTitle"], t["indexDesc"], canonical, lang, body, alt)
