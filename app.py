"""
PREDIKTA — Flask Server  v2.0
"""

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask.json.provider import DefaultJSONProvider
import numpy as np
import os, json, re, threading, time
from datetime import datetime, date, timedelta
from scraper import (scrape_all, fetch_state, save_csv, load_csv,
                     STATES, fetch_months, parse_draws, fetch_url, BASE_URL)
from ml_engine import run_all_models
from biz_engine import analyze_project, INDUSTRIES, PLATFORMS, COUNTRIES_DATA


class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, np.integer):  return int(o)
        if isinstance(o, np.floating): return float(o)
        if isinstance(o, np.bool_):    return bool(o)
        if isinstance(o, np.ndarray):  return o.tolist()
        return super().default(o)


app = Flask(__name__, static_folder="static")
app.json_provider_class = NumpyJSONProvider
app.json = NumpyJSONProvider(app)

# ── Security headers ──────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "SAMEORIGIN"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]       = "geolocation=(), microphone=()"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# ── Mise à jour automatique en arrière-plan ───────────────────────────────
# Au lieu de cliquer manuellement sur "Mettre à jour", un thread de fond
# rafraîchit périodiquement les résultats de tous les États (LotteryPost &
# autres sources configurées dans scraper.py).
_AUTO_UPDATE_INTERVAL = int(os.environ.get("PREDIKTA_AUTOUPDATE_SEC", 30 * 60))  # 30 min par défaut
_auto_update_state = {"last_run": None, "last_status": "idle", "running": False}

def _auto_update_loop():
    # Laisse le serveur démarrer et passer le health-check avant de lancer
    # le premier scraping (évite les pics mémoire au boot sur les plans
    # gratuits / contraints en RAM).
    time.sleep(int(os.environ.get("PREDIKTA_AUTOUPDATE_DELAY_SEC", 120)))
    while True:
        try:
            _auto_update_state["running"] = True
            scrape_all(n_months=1)   # rafraîchissement léger périodique (1 mois glissant)
            _REPORT_CACHE.clear()    # nouvelles données → on invalide les analyses en cache
            _auto_update_state["last_run"] = datetime.utcnow().isoformat() + "Z"
            _auto_update_state["last_status"] = "ok"
        except Exception as e:
            _auto_update_state["last_status"] = f"error: {e}"
        finally:
            _auto_update_state["running"] = False
        time.sleep(_AUTO_UPDATE_INTERVAL)

def start_auto_update():
    if os.environ.get("PREDIKTA_DISABLE_AUTOUPDATE") == "1":
        return
    t = threading.Thread(target=_auto_update_loop, daemon=True, name="predikta-auto-update")
    t.start()

# Démarre seulement dans le processus principal (évite le double-lancement
# avec le reloader Flask en mode debug)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    start_auto_update()

@app.route("/api/autoupdate/status")
def api_autoupdate_status():
    return jsonify({
        "enabled": os.environ.get("PREDIKTA_DISABLE_AUTOUPDATE") != "1",
        "interval_sec": _AUTO_UPDATE_INTERVAL,
        **_auto_update_state,
    })

# ── Draw schedule ─────────────────────────────────────────────────────────
DRAW_SCHEDULE = {
    "NY": [{"tod":"Midday","time":"2:30 PM ET"},  {"tod":"Evening","time":"10:30 PM ET"}],
    "GA": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}],
    "TX": [{"tod":"Midday","time":"10:00 AM CT"}, {"tod":"Evening","time":"10:12 PM CT"}],
    "FL": [{"tod":"Midday","time":"1:30 PM ET"},  {"tod":"Evening","time":"9:45 PM ET"}],
    "CA": [{"tod":"Midday","time":"1:00 PM PT"},  {"tod":"Evening","time":"6:30 PM PT"}],
    "OH": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "PA": [{"tod":"Midday","time":"1:35 PM ET"},  {"tod":"Evening","time":"6:59 PM ET"}],
    "NJ": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"7:57 PM ET"}],
    "IL": [{"tod":"Midday","time":"12:40 PM CT"}, {"tod":"Evening","time":"9:22 PM CT"}],
    "NC": [{"tod":"Midday","time":"3:00 PM ET"},  {"tod":"Evening","time":"11:22 PM ET"}],
    "VA": [{"tod":"Midday","time":"1:59 PM ET"},  {"tod":"Evening","time":"11:00 PM ET"}],
    "MI": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "TN": [{"tod":"Midday","time":"1:00 PM CT"},  {"tod":"Evening","time":"6:29 PM CT"}],
    "SC": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}],
    "CT": [{"tod":"Midday","time":"1:57 PM ET"},  {"tod":"Evening","time":"10:29 PM ET"}],
    "MD": [{"tod":"Midday","time":"12:28 PM ET"}, {"tod":"Evening","time":"7:56 PM ET"}],
    "MA": [{"tod":"Midday","time":"1:00 PM ET"},  {"tod":"Evening","time":"7:29 PM ET"}],
    "IN": [{"tod":"Midday","time":"1:20 PM ET"},  {"tod":"Evening","time":"8:00 PM ET"}],
    "KY": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"11:00 PM ET"}],
    "MO": [{"tod":"Midday","time":"12:45 PM CT"}, {"tod":"Evening","time":"9:45 PM CT"}],
    "AZ": [{"tod":"Evening","time":"7:34 PM MT"}],
    "CO": [{"tod":"Midday","time":"12:30 PM MT"}, {"tod":"Evening","time":"7:35 PM MT"}],
    "LA": [{"tod":"Evening","time":"9:59 PM CT"}],
    "MS": [{"tod":"Midday","time":"12:29 PM CT"}, {"tod":"Evening","time":"7:29 PM CT"}],
    "AR": [{"tod":"Midday","time":"12:00 PM CT"}, {"tod":"Evening","time":"6:30 PM CT"}],
    "IA": [{"tod":"Midday","time":"12:40 PM CT"}, {"tod":"Evening","time":"9:20 PM CT"}],
    "KS": [{"tod":"Midday","time":"12:40 PM CT"}, {"tod":"Evening","time":"9:20 PM CT"}],
    "OK": [{"tod":"Evening","time":"9:00 PM CT"}],
    "DE": [{"tod":"Midday","time":"1:58 PM ET"},  {"tod":"Evening","time":"7:57 PM ET"}],
    "RI": [{"tod":"Midday","time":"1:00 PM ET"},  {"tod":"Evening","time":"7:29 PM ET"}],
    "NM": [{"tod":"Midday","time":"12:29 PM MT"}, {"tod":"Evening","time":"7:29 PM MT"}],
    "WV": [{"tod":"Midday","time":"12:53 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "DC": [{"tod":"Midday","time":"1:50 PM ET"},  {"tod":"Evening","time":"7:50 PM ET"}],
    "WI": [{"tod":"Midday","time":"1:00 PM CT"},  {"tod":"Evening","time":"9:00 PM CT"}],
    "MN": [{"tod":"Evening","time":"9:00 PM CT"}],
    "NE": [{"tod":"Evening","time":"9:00 PM CT"}],
    "NH": [{"tod":"Evening","time":"7:57 PM ET"}],
    "VT": [{"tod":"Evening","time":"7:57 PM ET"}],
    "ME": [{"tod":"Evening","time":"7:57 PM ET"}],
    "WA": [{"tod":"Evening","time":"8:00 PM PT"}],
    "OR": [{"tod":"Evening","time":"10:00 PM PT"}],
    "ID": [{"tod":"Evening","time":"8:00 PM MT"}],
    "AL": [{"tod":"Midday","time":"12:29 PM CT"}, {"tod":"Evening","time":"6:59 PM CT"}],
    "PR": [{"tod":"Evening","time":"9:00 PM AT"}],
}

STATE_FLAGS = {
    "NY":"🗽","GA":"🍑","TX":"⭐","FL":"🌴","CA":"☀️","OH":"🌻","PA":"🔔",
    "NJ":"🌊","IL":"🏙️","NC":"🌲","VA":"🦅","MI":"🚗","TN":"🎸","SC":"🌴",
    "CT":"⚓","MD":"🦀","MA":"🦞","IN":"🏁","KY":"🐎","MO":"⛵","AZ":"🌵",
    "CO":"🏔️","LA":"🎷","MS":"🎶","AR":"💎","IA":"🌽","KS":"🌾","OK":"🛢️",
    "DE":"🦆","RI":"⛵","NM":"🌶️","WV":"⛰️","DC":"🏛️","WI":"🧀","MN":"🌨️",
    "NE":"🌾","NH":"🏔️","VT":"🍁","ME":"🦞","WA":"🌧️","OR":"🌲","ID":"🥔",
    "AL":"🏈","PR":"🌺",
}

# ── Newsletter subscribers store (flat file for simplicity) ───────────────
SUBS_FILE = os.path.join(os.path.dirname(__file__), "data", "subscribers.json")

def load_subscribers():
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE) as f:
            return json.load(f)
    return []

def save_subscriber(email, lang="fr"):
    subs = load_subscribers()
    emails = [s["email"] for s in subs]
    if email not in emails:
        subs.append({"email": email, "lang": lang, "date": date.today().isoformat()})
        os.makedirs(os.path.dirname(SUBS_FILE), exist_ok=True)
        with open(SUBS_FILE, "w") as f:
            json.dump(subs, f, indent=2)
        return True
    return False  # already subscribed


# ═══════════════════════════════════════════════════════════
# STATIC PAGES
# ═══════════════════════════════════════════════════════════

@app.route("/")
def index():       return send_from_directory("static", "home.html")

@app.route("/analyze")
def analyze():         return send_from_directory("static", "index.html")

@app.route("/presentation")
def presentation():    return send_from_directory("static", "presentation.html")

@app.route("/results")
def results_page(): return send_from_directory("static", "results.html")

@app.route("/pro")
def pro_page():    return send_from_directory("static", "pro.html")

@app.route("/about")
def about_page():  return send_from_directory("static", "about.html")

@app.route("/faq")
def faq_page():    return send_from_directory("static", "faq.html")

@app.route("/contact")
def contact_page(): return send_from_directory("static", "contact.html")

@app.route("/privacy")
def privacy_page(): return send_from_directory("static", "privacy.html")

@app.route("/terms")
def terms_page():  return send_from_directory("static", "terms.html")

@app.route("/offline")
def offline_page(): return send_from_directory("static", "offline.html")

@app.route("/nav.js")
def nav_js():
    resp = make_response(send_from_directory("static", "nav.js"))
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return resp


# ═══════════════════════════════════════════════════════════
# SEO & PWA
# ═══════════════════════════════════════════════════════════

@app.route("/robots.txt")
def robots():      return send_from_directory("static", "robots.txt")

@app.route("/sitemap.xml")
def sitemap():     return send_from_directory("static", "sitemap.xml")

@app.route("/manifest.json")
def manifest():    return send_from_directory("static", "manifest.json")

@app.route("/sw.js")
def sw():          return send_from_directory("static", "sw.js")


# ═══════════════════════════════════════════════════════════
# API — HEALTH
# ═══════════════════════════════════════════════════════════

@app.route("/api/health")
def health():
    states_with_data = sum(1 for c in STATES if load_csv(c))
    return jsonify({
        "status": "ok",
        "version": "2.0",
        "states_loaded": states_with_data,
        "total_states": len(STATES),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


# ═══════════════════════════════════════════════════════════
# API — NEWSLETTER & CONTACT
# ═══════════════════════════════════════════════════════════

@app.route("/api/subscribe", methods=["GET", "POST"])
def api_subscribe():
    if request.method == "GET":
        email = request.args.get("email", "").strip().lower()
        lang  = request.args.get("lang", "fr")
    else:
        data  = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        lang  = data.get("lang", "fr")

    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"success": False, "message": "Email invalide"}), 400

    is_new = save_subscriber(email, lang)
    return jsonify({
        "success": True,
        "message": "Inscription réussie!" if is_new else "Déjà inscrit",
        "new": is_new
    })


@app.route("/api/contact", methods=["GET", "POST"])
def api_contact():
    if request.method == "GET":
        name    = request.args.get("name","")
        email   = request.args.get("email","")
        subject = request.args.get("subject","")
        message = request.args.get("message","")
    else:
        data    = request.get_json(silent=True) or {}
        name    = data.get("name","")
        email   = data.get("email","")
        subject = data.get("subject","")
        message = data.get("message","")

    if not all([name, email, message]):
        return jsonify({"success": False, "message": "Champs requis manquants"}), 400

    # Save contact to file
    contacts_file = os.path.join(os.path.dirname(__file__), "data", "contacts.json")
    contacts = []
    if os.path.exists(contacts_file):
        with open(contacts_file) as f:
            contacts = json.load(f)
    contacts.append({
        "name": name, "email": email, "subject": subject,
        "message": message, "date": datetime.utcnow().isoformat()
    })
    with open(contacts_file, "w") as f:
        json.dump(contacts, f, indent=2)

    return jsonify({"success": True, "message": "Message envoyé avec succès!"})


# ═══════════════════════════════════════════════════════════
# API — ANALYZER
# ═══════════════════════════════════════════════════════════

# Cache léger des analyses ML (coûteuses : ~20-25s) — évite de recalculer
# le même rapport à chaque clic. Invalidé automatiquement après quelques
# minutes ou dès qu'un nouveau scraping change les données.
_REPORT_CACHE = {}
_REPORT_CACHE_TTL = int(os.environ.get("PREDIKTA_REPORT_CACHE_SEC", 10 * 60))  # 10 min

@app.route("/api/report")
def api_report():
    state      = request.args.get("state", "NY").upper()
    tod_filter = request.args.get("tod", "all")

    if state not in STATES:
        return jsonify({"error": f"Unknown state: {state}"}), 400

    cache_key = (state, tod_filter)
    cached = _REPORT_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - cached["ts"]) < _REPORT_CACHE_TTL:
        return jsonify(cached["data"])

    draws = load_csv(state)
    if not draws:
        return jsonify({"error": f"No data for {state}. Click Scrape first."}), 200

    if tod_filter != "all":
        draws = [d for d in draws if d.get("tod","").lower() == tod_filter.lower()]
        if not draws:
            return jsonify({"error": f"No {tod_filter} draws for {state}."}), 200

    result = run_all_models(draws)
    result["state"]       = state
    result["state_name"]  = STATES[state]["name"]
    result["tod_filter"]  = tod_filter
    result["dpd"]         = STATES[state].get("dpd", 2)
    result["schedule"]    = DRAW_SCHEDULE.get(state, [])
    result["cached"]      = False

    _REPORT_CACHE[cache_key] = {"ts": now, "data": {**result, "cached": True}}
    return jsonify(result)


@app.route("/api/scrape")
def api_scrape():
    state  = request.args.get("state", None)
    months = min(int(request.args.get("months", 12)), 60)

    if state:
        state = state.upper()
        if state not in STATES:
            return jsonify({"error": f"Unknown state: {state}"}), 400
        draws = fetch_state(state, n_months=months)
        if draws:
            total = save_csv(state, draws)
            for k in list(_REPORT_CACHE):
                if k[0] == state:
                    _REPORT_CACHE.pop(k, None)
            return jsonify({"message": f"{len(draws)} draws fetched · {total} total saved for {state}"})
        return jsonify({"message": f"No data found for {state}"})

    scrape_all(n_months=months)
    _REPORT_CACHE.clear()
    return jsonify({"message": "Scraping complete for all states"})


# ═══════════════════════════════════════════════════════════
# API — STATES LIST
# ═══════════════════════════════════════════════════════════

@app.route("/api/states")
def api_states():
    result = {}
    # Ordre d'affichage logique pour les créneaux de tirage
    _TOD_ORDER = {"Morning": 0, "Midday": 1, "Day": 2, "Evening": 3, "Night": 4}
    for code, cfg in STATES.items():
        draws = load_csv(code)
        # Tirages réellement disponibles pour cet État (Matin/Midi/Soir/Nuit
        # selon les données réelles — optimisé et à jour par État)
        tods = sorted({d.get("tod","") for d in draws if d.get("tod")},
                      key=lambda t: _TOD_ORDER.get(t, 99))
        result[code] = {
            "name":      cfg["name"],
            "slug":      cfg["slug"],
            "dpd":       cfg.get("dpd", 2),
            "draws":     len(draws),
            "last_draw": draws[0] if draws else None,
            "flag":      STATE_FLAGS.get(code, "🎰"),
            "schedule":  DRAW_SCHEDULE.get(code, []),
            "tods":      tods,
        }
    return jsonify(result)


# ═══════════════════════════════════════════════════════════
# API — RESULTS HUB
# ═══════════════════════════════════════════════════════════

@app.route("/api/results/latest")
def api_results_latest():
    today_str     = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    result = {}

    for code, cfg in STATES.items():
        draws = load_csv(code)
        if not draws:
            result[code] = {
                "name": cfg["name"], "flag": STATE_FLAGS.get(code,"🎰"),
                "schedule": DRAW_SCHEDULE.get(code,[]),
                "latest": [], "has_data": False,
            }
            continue

        by_date = {}
        for d in draws:
            by_date.setdefault(d["date"], []).append(d)

        latest_date  = max(by_date.keys())
        latest_draws = sorted(by_date[latest_date], key=lambda x: x.get("tod",""))

        result[code] = {
            "name":        cfg["name"],
            "flag":        STATE_FLAGS.get(code, "🎰"),
            "schedule":    DRAW_SCHEDULE.get(code, []),
            "latest_date": latest_date,
            "latest":      latest_draws,
            "is_today":    latest_date == today_str,
            "is_yesterday":latest_date == yesterday_str,
            "total_draws": len(draws),
            "has_data":    True,
        }

    return jsonify(result)


@app.route("/api/results/<state_code>")
def api_results_state(state_code):
    state_code = state_code.upper()
    if state_code not in STATES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400

    draws = load_csv(state_code)
    if not draws:
        new_draws = fetch_state(state_code, n_months=2)
        if new_draws:
            save_csv(state_code, new_draws)
            draws = load_csv(state_code)
    if not draws:
        return jsonify({"error": f"No data for {state_code}"}), 200

    cutoff = (date.today() - timedelta(days=30)).isoformat()
    draws  = [d for d in draws if d["date"] >= cutoff]

    by_date = {}
    for d in draws:
        by_date.setdefault(d["date"], []).append(d)

    days = [
        {"date": dt, "draws": sorted(by_date[dt], key=lambda x: x.get("tod",""))}
        for dt in sorted(by_date.keys(), reverse=True)
    ]

    cfg = STATES[state_code]
    return jsonify({
        "state": state_code, "name": cfg["name"],
        "flag": STATE_FLAGS.get(state_code,"🎰"),
        "schedule": DRAW_SCHEDULE.get(state_code,[]),
        "days": days, "total": len(draws),
    })


@app.route("/api/results/<state_code>/month/<int:year>/<int:month>")
def api_results_month(state_code, year, month):
    state_code = state_code.upper()
    if state_code not in STATES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400

    cfg    = STATES[state_code]
    prefix = f"{year:04d}-{month:02d}"

    draws       = load_csv(state_code)
    month_draws = [d for d in draws if d["date"].startswith(prefix)]

    if not month_draws:
        url  = f"{BASE_URL}/results/{state_code.lower()}/{cfg['slug']}/past/{year}/{month}"
        html = fetch_url(url)
        if html:
            month_draws = parse_draws(html)
            if month_draws:
                save_csv(state_code, month_draws)

    if not month_draws:
        return jsonify({"error": f"No data for {state_code} {year}/{month:02d}"}), 200

    by_date = {}
    for d in month_draws:
        by_date.setdefault(d["date"], []).append(d)

    days = [
        {"date": dt, "draws": sorted(by_date[dt], key=lambda x: x.get("tod",""))}
        for dt in sorted(by_date.keys(), reverse=True)
    ]

    return jsonify({
        "state": state_code, "name": cfg["name"],
        "flag": STATE_FLAGS.get(state_code,"🎰"),
        "schedule": DRAW_SCHEDULE.get(state_code,[]),
        "days": days, "total": len(month_draws),
        "year": year, "month": month,
    })


# ═══════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found", "code": 404}), 404
    return send_from_directory("static", "404.html"), 404

@app.errorhandler(500)
def server_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error", "code": 500}), 500
    return send_from_directory("static", "404.html"), 500


# ═══════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════
# COMPLETE GAMES RESULTS — Routes
# ═══════════════════════════════════════════════════════════

from games_config import STATE_GAMES, GAME_TYPES
from games_scraper import (fetch_all_games_for_state, get_today_all_games,
                            load_game_results, save_game_results, fetch_game)

@app.route("/all-results")
def all_results_page():
    return send_from_directory("static", "all_results.html")

@app.route("/api/games/today/<state_code>")
def api_games_today(state_code):
    """All games results for today (or most recent) for a state."""
    state_code = state_code.upper()
    if state_code not in STATE_GAMES:
        return jsonify({"error": f"No games configured for {state_code}"}), 400
    results = get_today_all_games(state_code)
    return jsonify({
        "state": state_code,
        "games": results,
        "total_games": len(STATE_GAMES.get(state_code, [])),
        "has_data": len(results) > 0,
    })

@app.route("/api/games/all-states/today")
def api_games_all_states_today():
    """Quick summary: most recent draw for all configured games across all states."""
    today = date.today().isoformat()
    result = {}
    for state_code in STATE_GAMES:
        games = get_today_all_games(state_code)
        if games:
            result[state_code] = {
                "flag":      STATE_FLAGS.get(state_code, "🎰"),
                "name":      STATE_GAMES[state_code][0]["label"].split(" (")[0] if STATE_GAMES[state_code] else state_code,
                "games":     games,
                "is_today":  any(g["is_today"] for g in games),
                "game_count": len(games),
            }
    return jsonify(result)

@app.route("/api/games/scrape/<state_code>")
def api_games_scrape(state_code):
    """Scrape all games for a state."""
    state_code = state_code.upper()
    if state_code not in STATE_GAMES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400
    results = fetch_all_games_for_state(state_code, n_months=2)
    total = sum(len(v) for v in results.values())
    return jsonify({"message": f"Scraped {len(results)} games, {total} draws for {state_code}"})

@app.route("/api/games/config")
def api_games_config():
    """Return full game configuration for all states."""
    return jsonify({
        "states": {
            code: [{"slug": g["slug"], "label": g["label"], "type": g["type"]} for g in games]
            for code, games in STATE_GAMES.items()
        },
        "game_types": GAME_TYPES,
    })

# PREDIKTA BUSINESS AI — Routes
# ═══════════════════════════════════════════════════════════

@app.route("/bizai")
def bizai_page():
    return send_from_directory("static", "bizai.html")

@app.route("/api/bizai/meta")
def bizai_meta():
    """Return industries, platforms, countries for the wizard dropdowns."""
    return jsonify({
        "industries": {k: v["label"] for k, v in INDUSTRIES.items()},
        "countries":  list(COUNTRIES_DATA.keys()),
        "platforms":  {k: {"name": v["name"], "icon": v["icon"]} for k, v in PLATFORMS.items()},
    })

@app.route("/api/bizai/analyze", methods=["GET", "POST"])
def bizai_analyze():
    """Run the full business analysis."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = {
            "project_name":  request.args.get("project_name", "Mon Projet"),
            "description":   request.args.get("description", ""),
            "industry":      request.args.get("industry", "other"),
            "model":         request.args.get("model", "B2C"),
            "stage":         request.args.get("stage", "idea"),
            "prod_type":     request.args.get("prod_type", "service"),
            "budget_tier":   request.args.get("budget_tier", "low"),
            "price_range":   request.args.get("price_range", "medium"),
            "target_ages":   request.args.getlist("target_ages") or ["25-35"],
            "geo_scope":     request.args.get("geo_scope", "national"),
            "geo_countries": request.args.getlist("geo_countries") or ["USA"],
            "timeline":      request.args.get("timeline", "6-12"),
            "goal":          request.args.get("goal", "sales"),
            "usp":           request.args.get("usp", ""),
            "competitors":   request.args.getlist("competitors"),
            "languages":     request.args.getlist("languages") or ["fr"],
        }

    if not data.get("project_name"):
        return jsonify({"error": "Nom du projet requis"}), 400

    try:
        report = analyze_project(data)
        return jsonify({"success": True, "report": report})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 45)
    print("  PREDIKTA  v4.0  - READY")
    print("=" * 45)
    print("  Home        : http://localhost:5000")
    print("  Analyzer    : http://localhost:5000/analyze")
    print("  Results     : http://localhost:5000/results")
    print("  All Results : http://localhost:5000/all-results")
    print("  Business Intelligence : http://localhost:5000/bizai")
    print("  PRO         : http://localhost:5000/pro")
    print("  Presentation: http://localhost:5000/presentation")
    print("  Health      : http://localhost:5000/api/health")
    print("=" * 45)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port, threaded=True)
