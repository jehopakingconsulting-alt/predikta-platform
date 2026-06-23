"""
ZYNORIQ — Public SEO pages ("Pick 3 [State] Predictions Today").

Server-rendered (no auth, no JS required for content) so search engines can
index the daily hot/cold digits & suggested combinations for each state.
Reuses the lightweight analyzer.py engine (no Monte Carlo / ML — fast enough
to compute on every request).
"""

from datetime import date
from scraper import STATES, load_csv
from analyzer import full_report
from draw_schedule import next_draw_session

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
        "title": lambda name, d: f"Pick 3 {name} — Prédictions du jour {d} | ZYNORIQ",
        "desc": lambda name, d: f"Numéros chauds, froids et combinaisons suggérées pour {name} Pick 3, mis à jour le {d}. Analyse statistique gratuite par ZYNORIQ.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Prédictions du jour",
        "lastDraw": "Dernier tirage", "hot": "🔥 Chiffres chauds (30 derniers tirages)",
        "cold": "❄️ Chiffres froids (30 derniers tirages)", "overdue": "⏳ Chiffres en retard",
        "suggestions": "Combinaisons suggérées", "confidence": "Tendance statistique",
        "noData": "Données non disponibles pour cet État pour le moment.",
        "ctaTitle": "Aller plus loin avec ZYNORIQ", "ctaDesc": "Markov, Monte Carlo, Machine Learning (XGBoost/Random Forest), analyse de Fourier, archives illimitées et plus pour tous les États.",
        "ctaBtn": "🔮 Lancer l'analyse complète →", "backToIndex": "← Tous les États",
        "indexTitle": "Pick 3 — Prédictions du jour, tous les États | ZYNORIQ",
        "indexDesc": "Numéros chauds, froids et combinaisons suggérées Pick 3 pour tous les États américains, mis à jour quotidiennement.",
        "indexH1": "🎯 Pick 3 — Prédictions du jour par État",
        "totalDraws": "tirages analysés",
        "drawn": "tiré",
        "transBtn": "🔍 Mode Transparence — pourquoi ces suggestions ?",
        "transFreq": "Fréquence", "transGap": "Écart actuel/moyen", "transHotCold": "Tendance",
        "transOverdue": "en retard", "transHot": "CHAUD", "transCold": "FROID", "transNeutral": "NEUTRE",
        "transMarkov": "Markov (vs dernier tirage)",
        "transDisclaimer": "Ces signaux décrivent l'historique des tirages — ils n'augmentent pas vos chances de gagner et ne garantissent aucun résultat futur.",
        "nextDraw": "⏰ Prochain tirage", "today": "aujourd'hui", "tomorrow": "demain",
    },
    "en": {
        "title": lambda name, d: f"Pick 3 {name} Predictions Today {d} | ZYNORIQ",
        "desc": lambda name, d: f"Hot, cold numbers and suggested combinations for {name} Pick 3, updated {d}. Free statistical analysis by ZYNORIQ.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Today's Predictions",
        "lastDraw": "Last draw", "hot": "🔥 Hot digits (last 30 draws)",
        "cold": "❄️ Cold digits (last 30 draws)", "overdue": "⏳ Overdue digits",
        "suggestions": "Suggested combinations", "confidence": "Statistical trend",
        "noData": "No data available for this state yet.",
        "ctaTitle": "Go further with ZYNORIQ", "ctaDesc": "Markov chains, Monte Carlo, Machine Learning (XGBoost/Random Forest), Fourier analysis, unlimited archives and more for every state.",
        "ctaBtn": "🔮 Run the full analysis →", "backToIndex": "← All states",
        "indexTitle": "Pick 3 — Today's Predictions for Every State | ZYNORIQ",
        "indexDesc": "Hot, cold numbers and suggested Pick 3 combinations for every US state, updated daily.",
        "indexH1": "🎯 Pick 3 — Today's Predictions by State",
        "totalDraws": "draws analyzed",
        "drawn": "drawn",
        "transBtn": "🔍 Transparency Mode — why these suggestions?",
        "transFreq": "Frequency", "transGap": "Current/avg gap", "transHotCold": "Trend",
        "transOverdue": "overdue", "transHot": "HOT", "transCold": "COLD", "transNeutral": "NEUTRAL",
        "transMarkov": "Markov (vs last draw)",
        "transDisclaimer": "These signals describe historical draw patterns — they do not increase your odds of winning or guarantee any future outcome.",
        "nextDraw": "⏰ Next draw", "today": "today", "tomorrow": "tomorrow",
    },
    "es": {
        "title": lambda name, d: f"Pick 3 {name} — Predicciones de hoy {d} | ZYNORIQ",
        "desc": lambda name, d: f"Números calientes, fríos y combinaciones sugeridas para {name} Pick 3, actualizado el {d}. Análisis estadístico gratuito de ZYNORIQ.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Predicciones de hoy",
        "lastDraw": "Último sorteo", "hot": "🔥 Números calientes (últimos 30 sorteos)",
        "cold": "❄️ Números fríos (últimos 30 sorteos)", "overdue": "⏳ Números atrasados",
        "suggestions": "Combinaciones sugeridas", "confidence": "Tendencia estadística",
        "noData": "Datos no disponibles para este estado por el momento.",
        "ctaTitle": "Ve más allá con ZYNORIQ", "ctaDesc": "Cadenas de Markov, Monte Carlo, Machine Learning (XGBoost/Random Forest), análisis de Fourier, archivos ilimitados y más para todos los estados.",
        "ctaBtn": "🔮 Iniciar el análisis completo →", "backToIndex": "← Todos los estados",
        "indexTitle": "Pick 3 — Predicciones de hoy para todos los estados | ZYNORIQ",
        "indexDesc": "Números calientes, fríos y combinaciones sugeridas Pick 3 para todos los estados de EE.UU., actualizado diariamente.",
        "indexH1": "🎯 Pick 3 — Predicciones de hoy por estado",
        "totalDraws": "sorteos analizados",
        "drawn": "sorteado",
        "transBtn": "🔍 Modo Transparencia — ¿por qué estas sugerencias?",
        "transFreq": "Frecuencia", "transGap": "Brecha actual/promedio", "transHotCold": "Tendencia",
        "transOverdue": "atrasado", "transHot": "CALIENTE", "transCold": "FRÍO", "transNeutral": "NEUTRAL",
        "transMarkov": "Markov (vs último sorteo)",
        "transDisclaimer": "Estas señales describen patrones históricos de los sorteos — no aumentan sus posibilidades de ganar ni garantizan ningún resultado futuro.",
        "nextDraw": "⏰ Próximo sorteo", "today": "hoy", "tomorrow": "mañana",
    },
    "pt": {
        "title": lambda name, d: f"Pick 3 {name} — Previsões de hoje {d} | ZYNORIQ",
        "desc": lambda name, d: f"Números quentes, frios e combinações sugeridas para {name} Pick 3, atualizado em {d}. Análise estatística gratuita da ZYNORIQ.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Previsões de hoje",
        "lastDraw": "Último sorteio", "hot": "🔥 Números quentes (últimos 30 sorteios)",
        "cold": "❄️ Números frios (últimos 30 sorteios)", "overdue": "⏳ Números atrasados",
        "suggestions": "Combinações sugeridas", "confidence": "Tendência estatística",
        "noData": "Dados não disponíveis para este estado no momento.",
        "ctaTitle": "Vá mais longe com a ZYNORIQ", "ctaDesc": "Cadeias de Markov, Monte Carlo, Machine Learning (XGBoost/Random Forest), análise de Fourier, arquivos ilimitados e mais para todos os estados.",
        "ctaBtn": "🔮 Iniciar a análise completa →", "backToIndex": "← Todos os estados",
        "indexTitle": "Pick 3 — Previsões de hoje para todos os estados | ZYNORIQ",
        "indexDesc": "Números quentes, frios e combinações sugeridas Pick 3 para todos os estados dos EUA, atualizado diariamente.",
        "indexH1": "🎯 Pick 3 — Previsões de hoje por estado",
        "totalDraws": "sorteios analisados",
        "drawn": "sorteado",
        "transBtn": "🔍 Modo Transparência — por que essas sugestões?",
        "transFreq": "Frequência", "transGap": "Lacuna atual/média", "transHotCold": "Tendência",
        "transOverdue": "em atraso", "transHot": "QUENTE", "transCold": "FRIO", "transNeutral": "NEUTRO",
        "transMarkov": "Markov (vs último sorteio)",
        "transDisclaimer": "Esses sinais descrevem padrões históricos dos sorteios — eles não aumentam suas chances de ganhar nem garantem qualquer resultado futuro.",
        "nextDraw": "⏰ Próximo sorteio", "today": "hoje", "tomorrow": "amanhã",
    },
    "ht": {
        "title": lambda name, d: f"Pick 3 {name} — Prediksyon jodi a {d} | ZYNORIQ",
        "desc": lambda name, d: f"Chif cho, frèt ak konbinezon ki sijere pou {name} Pick 3, mizajou {d}. Analiz statistik gratis pa ZYNORIQ.",
        "h1": lambda name: f"🎯 Pick 3 {name} — Prediksyon jodi a",
        "lastDraw": "Dènye tiraj", "hot": "🔥 Chif cho yo (30 dènye tiraj)",
        "cold": "❄️ Chif frèt yo (30 dènye tiraj)", "overdue": "⏳ Chif an reta",
        "suggestions": "Konbinezon ki sijere", "confidence": "Tandans statistik",
        "noData": "Pa gen done disponib pou eta sa a kounye a.",
        "ctaTitle": "Ale pi lwen ak ZYNORIQ", "ctaDesc": "Markov, Monte Carlo, Machine Learning (XGBoost/Random Forest), analiz Fourier, achiv san limit ak plis pou tout eta.",
        "ctaBtn": "🔮 Lanse analiz konplè →", "backToIndex": "← Tout eta yo",
        "indexTitle": "Pick 3 — Prediksyon jodi a pou tout eta | ZYNORIQ",
        "indexDesc": "Chif cho, frèt ak konbinezon Pick 3 ki sijere pou tout eta Ozetazini, mizajou chak jou.",
        "indexH1": "🎯 Pick 3 — Prediksyon jodi a pa eta",
        "totalDraws": "tiraj analize",
        "drawn": "tire",
        "transBtn": "🔍 Mòd Transparans — poukisa sigjesyon sa yo?",
        "transFreq": "Frekans", "transGap": "Espas aktyèl/mwayèn", "transHotCold": "Tandans",
        "transOverdue": "an reta", "transHot": "CHO", "transCold": "FRÈT", "transNeutral": "NÈITRAL",
        "transMarkov": "Markov (vs dènye tiraj)",
        "transDisclaimer": "Siyal sa yo dekri modèl istorik tiraj yo — yo pa ogmante chans ou pou genyen ni garanti okenn rezilta nan lavni.",
        "nextDraw": "⏰ Pwochen tiraj", "today": "jodi a", "tomorrow": "demen",
    },
}

SUPPORTED_LANGS = ["fr", "en", "es", "pt", "ht"]

CONF_BY_LANG = {
    "en": {"Tendance très forte": "Very strong trend", "Tendance forte": "Strong trend", "Tendance moyenne": "Medium trend", "Tendance faible": "Weak trend"},
    "es": {"Tendance très forte": "Tendencia muy fuerte", "Tendance forte": "Tendencia fuerte", "Tendance moyenne": "Tendencia media", "Tendance faible": "Tendencia débil"},
    "pt": {"Tendance très forte": "Tendência muito forte", "Tendance forte": "Tendência forte", "Tendance moyenne": "Tendência média", "Tendance faible": "Tendência fraca"},
    "ht": {"Tendance très forte": "Tandans trè fò", "Tendance forte": "Tandans fò", "Tendance moyenne": "Tandans mwayen", "Tendance faible": "Tandans fèb"},
}

TOD_T = {
    "fr": {"Morning": "Matin", "Midday": "Midi", "Day": "Jour", "Evening": "Soir", "Night": "Nuit"},
    "en": {"Morning": "Morning", "Midday": "Midday", "Day": "Day", "Evening": "Evening", "Night": "Night"},
    "es": {"Morning": "Mañana", "Midday": "Mediodía", "Day": "Día", "Evening": "Tarde", "Night": "Noche"},
    "pt": {"Morning": "Manhã", "Midday": "Meio-dia", "Day": "Dia", "Evening": "Tarde", "Night": "Noite"},
    "ht": {"Morning": "Maten", "Midday": "Midi", "Day": "Jounen", "Evening": "Aswè", "Night": "Nuit"},
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
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{desc}"/>
<meta property="og:type" content="website"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:image" content="https://www.zynoriq.com/og-image.png"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:image" content="https://www.zynoriq.com/og-image.png"/>
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
.trans-toggle{{margin-top:12px;border-top:1px solid var(--border);padding-top:10px}}
.trans-toggle>summary{{cursor:pointer;font-size:.78rem;font-weight:700;color:var(--muted2)}}
.trans-wrap{{margin-top:10px}}
.trans-details{{margin-bottom:6px;border:1px solid var(--border);border-radius:8px;padding:6px 10px}}
.trans-details>summary{{cursor:pointer;font-size:.85rem;font-weight:700;letter-spacing:1px}}
.trans-body{{margin-top:6px;font-size:.72rem;color:var(--muted2);line-height:1.7}}
.trans-row{{padding:3px 0}}
.trans-disclaimer{{font-size:.68rem;color:var(--muted);line-height:1.6;margin-top:8px}}
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
    base_path = f"{base_url}/predictions/{state_code.lower()}"
    canonical = base_path + (f"?lang={lang}" if lang != "fr" else "")
    alt = "".join(
        f'<link rel="alternate" hreflang="{ll}" href="{base_path}{"?lang=" + ll if ll != "fr" else ""}"/>'
        for ll in SUPPORTED_LANGS
    )

    if not draws:
        body = (f'<a class="back" href="/predictions{"?lang=" + lang if lang != "fr" else ""}">{t["backToIndex"]}</a>'
                f'<h1>{flag} {t["h1"](name)}</h1>'
                f'<div class="card">{t["noData"]}</div>')
        return _page_shell(t["title"](name, today), t["desc"](name, today), canonical, lang, body, alt)

    # Base the "last draw" / suggestions on the session that's coming up
    # next (e.g. if it's 6:15 PM and tonight's "Soir" draw is at 6:59 PM,
    # use the history of "Soir" draws — not just the most recent draw
    # overall, which could be an earlier "Nuit"/"Matin" session).
    nxt = next_draw_session(state_code)
    draws_for_report = draws
    if nxt:
        tdraws = [d for d in draws if d.get("tod") == nxt["tod"]]
        if tdraws:
            latest_tod_date = max(d["date"] for d in tdraws)
            days_old = (date.today() - date.fromisoformat(latest_tod_date)).days
            draws_for_report = tdraws if days_old <= 7 else draws

    report = full_report(state_code, draws_for_report)
    last = report["last_draw"]
    last_date_age = (date.today() - date.fromisoformat(last["date"])).days
    stale_warning = ""
    if last_date_age > 3:
        stale_warning = (
            '<div class="card" style="border-color:#aa6600;color:#ffcc66;padding:12px;margin-bottom:16px;font-size:.85rem">'
            f'⚠️ Données non à jour (dernier tirage : {last["date"]}). '
            f'Rendez-vous sur <a href="/analyze" style="color:#44aaff">Analyser</a> et cliquez Scraper pour rafraîchir.'
            '</div>'
        )
    balls = "".join(_ball(last[p]) for p in ["d1", "d2", "d3"])

    hot = [d for d, v in report["hot_cold_30"].items() if v["status"] == "HOT"]
    cold = [d for d, v in report["hot_cold_30"].items() if v["status"] == "COLD"]
    overdue = [d for d, v in report["gaps"].items() if v["overdue"]]

    hot_html = "".join(_digit_chip(d, "#ff4444") for d in hot) or "—"
    cold_html = "".join(_digit_chip(d, "#4499ff") for d in cold) or "—"
    overdue_html = "".join(_digit_chip(d, "#ffcc22") for d in overdue) or "—"

    sugg_html = ""
    for s in report["suggestions"][:5]:
        conf = CONF_BY_LANG.get(lang, {}).get(s["confidence"], s["confidence"])
        sugg_html += f'<span class="combo-chip">{s["combo"]} <span class="combo-conf">{conf}</span></span>'

    trans_html = ""
    hc_status_label = {"HOT": t["transHot"], "COLD": t["transCold"], "NEUTRAL": t["transNeutral"]}
    for s in report["suggestions"][:5]:
        combo_conf = CONF_BY_LANG.get(lang, {}).get(s["confidence"], s["confidence"])
        rows = ""
        for di in s.get("breakdown", []):
            gap_txt = f'{di["current_gap"]}/{di["avg_gap"]}' if di["avg_gap"] else str(di["current_gap"])
            overdue_txt = f' ⏰ {t["transOverdue"]}' if di["overdue"] else ""
            rows += (
                f'<div class="trans-row">'
                f'<b>{di["position"].upper()} = {di["digit"]}</b> · '
                f'{t["transFreq"]}: {di["freq_pct"]}% · '
                f'{t["transHotCold"]}: {hc_status_label.get(di["hot_cold"], di["hot_cold"])} · '
                f'{t["transGap"]}: {gap_txt}{overdue_txt} · '
                f'{t["transMarkov"]}: {di["markov_pct"]}%'
                f'</div>'
            )
        trans_html += (
            f'<details class="trans-details">'
            f'<summary>{s["combo"]} — {combo_conf}</summary>'
            f'<div class="trans-body">{rows}</div>'
            f'</details>'
        )
    trans_html += f'<p class="trans-disclaimer">{t["transDisclaimer"]}</p>'

    tod = last.get("tod", "")
    tod_label = TOD_T.get(lang, {}).get(tod, tod)

    next_html = ""
    if nxt:
        next_tod_label = TOD_T.get(lang, {}).get(nxt["tod"], nxt["tod"])
        when = t["today"] if nxt["date"] == today else t["tomorrow"]
        next_html = f'<div class="sub">{t["nextDraw"]}: {next_tod_label} — {when} {nxt["time"]}</div>'

    body = f"""<a class="back" href="/predictions{'?lang=' + lang if lang != 'fr' else ''}">{t['backToIndex']}</a>
<h1>{flag} {t['h1'](name)}</h1>
<div class="sub">{today} · {report['total_draws']} {t['totalDraws']}</div>
{next_html}
{stale_warning}
<div class="card">
  <h2>{t['lastDraw']} — {last['date']} ({tod_label})</h2>
  <div>{balls}</div>
</div>

<div class="card">
  <h2>{t['suggestions']}</h2>
  <div>{sugg_html}</div>
  <details class="trans-toggle">
    <summary>{t['transBtn']}</summary>
    <div class="trans-wrap">{trans_html}</div>
  </details>
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
    canonical = f"{base_url}/predictions" + (f"?lang={lang}" if lang != "fr" else "")
    alt = "".join(
        f'<link rel="alternate" hreflang="{ll}" href="{base_url}/predictions{"?lang=" + ll if ll != "fr" else ""}"/>'
        for ll in SUPPORTED_LANGS
    )

    qs = f"?lang={lang}" if lang != "fr" else ""
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
