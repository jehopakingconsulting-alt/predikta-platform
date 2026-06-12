"""
PREDIKTA — Flask Server  v2.0
"""

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask.json.provider import DefaultJSONProvider
try:
    from flask_compress import Compress
except ImportError:
    Compress = None
import numpy as np
import os, json, re, threading, time
from collections import Counter
from datetime import datetime, date, timedelta
from scraper import (scrape_all, fetch_state, save_csv, load_csv,
                     STATES, fetch_months, parse_draws, fetch_url, BASE_URL)
from ml_engine import run_all_models, hot_cold_stats, digit_gap_analysis
from biz_engine import analyze_project, INDUSTRIES, PLATFORMS, COUNTRIES_DATA
from games_config import TOD_ORDER

try:
    from pywebpush import webpush, WebPushException
except ImportError:
    webpush = None
    WebPushException = Exception


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

# ── Secret key (sessions / cookies signés) ────────────────────────────────
app.secret_key = os.environ.get("PREDIKTA_SECRET_KEY", "dev-insecure-predikta-key-change-me")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ── Comptes utilisateurs / abonnements (SQLAlchemy) ───────────────────────
import auth as auth_module
auth_module.init_app(app)
app.register_blueprint(auth_module.auth_bp)

# ── Facturation Stripe (Phase 2b) ─────────────────────────────────────────
import billing as billing_module
app.register_blueprint(billing_module.billing_bp)

# ── Connexion via Google / Facebook / Microsoft (OAuth) ───────────────────
import oauth as oauth_module
oauth_module.init_app(app)
app.register_blueprint(oauth_module.oauth_bp)

# ── Compression (gzip/br) — réduit fortement le poids des pages HTML/JS
# (index.html ~2000 lignes, nav.js ~900 lignes) et des réponses JSON
# (/api/results/latest, /api/states, /api/report) → chargements plus rapides
# notamment sur connexions mobiles.
if Compress is not None:
    app.config["COMPRESS_MIMETYPES"] = [
        "text/html", "text/css", "text/javascript", "application/javascript",
        "application/json", "application/xml", "image/svg+xml",
    ]
    app.config["COMPRESS_LEVEL"] = 6
    Compress(app)

# ── Security headers ──────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "SAMEORIGIN"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]       = "geolocation=(), microphone=()"
    response.headers["Access-Control-Allow-Origin"] = "*"
    # Cache statique côté navigateur — fichiers JS/CSS/images versionnés via
    # cache court (5 min) pour limiter les requêtes répétées sans bloquer
    # les déploiements de correctifs.
    if request.path.startswith("/static/") or request.path in (
        "/nav.js", "/manifest.json", "/sw.js", "/robots.txt", "/sitemap.xml"
    ) or request.path.endswith((".js", ".css", ".png", ".jpg", ".svg", ".ico", ".woff2")):
        response.headers["Cache-Control"] = "public, max-age=300"
    return response

# ── Notifications push (Web Push / VAPID) ─────────────────────────────────
# Abonnement anonyme par navigateur (pas de compte utilisateur requis).
# Les abonnements sont stockés dans data/push_subscriptions.json et les
# clés VAPID dans data/vapid_private.pem / data/vapid_public.txt (générées
# une fois via `python -c "from py_vapid import Vapid02; ..."`).
_PUSH_SUBS_FILE   = os.path.join("data", "push_subscriptions.json")
_VAPID_PRIV_FILE  = os.path.join("data", "vapid_private.pem")
_VAPID_PUB_FILE   = os.path.join("data", "vapid_public.txt")
_PUSH_LAST_SENT_FILE = os.path.join("data", "push_last_sent.txt")
_VAPID_CLAIMS = {"sub": os.environ.get("PREDIKTA_VAPID_EMAIL", "mailto:contact@predikta.app")}


def _vapid_public_key():
    try:
        with open(_VAPID_PUB_FILE) as f:
            return f.read().strip()
    except Exception:
        return None


def _load_subscriptions():
    try:
        with open(_PUSH_SUBS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_subscriptions(subs):
    os.makedirs("data", exist_ok=True)
    with open(_PUSH_SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)


def _send_push_to_all(title: str, body: str, url: str = "/all-results"):
    """Envoie une notification push à tous les abonnés. Retire automatiquement
    les abonnements expirés/invalides (HTTP 404/410)."""
    if webpush is None or not os.path.exists(_VAPID_PRIV_FILE):
        return {"sent": 0, "removed": 0, "error": "push not configured"}

    with open(_VAPID_PRIV_FILE) as f:
        private_key = f.read()

    subs = _load_subscriptions()
    payload = json.dumps({"title": title, "body": body, "url": url})
    sent, removed, kept = 0, 0, []

    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=private_key,
                vapid_claims=dict(_VAPID_CLAIMS),
            )
            sent += 1
            kept.append(sub)
        except WebPushException as e:
            status = getattr(e.response, "status_code", None)
            if status in (404, 410):
                removed += 1
                continue
            kept.append(sub)
        except Exception:
            kept.append(sub)

    if removed:
        _save_subscriptions(kept)
    return {"sent": sent, "removed": removed}


def _maybe_send_daily_push():
    """Envoie une notification push une fois par jour (au plus), dès que les
    nouveaux résultats du jour sont disponibles après une mise à jour auto."""
    if webpush is None or not os.path.exists(_VAPID_PRIV_FILE):
        return
    if not _load_subscriptions():
        return

    today = date.today().isoformat()
    try:
        with open(_PUSH_LAST_SENT_FILE) as f:
            last_sent = f.read().strip()
    except Exception:
        last_sent = ""

    if last_sent == today:
        return

    try:
        os.makedirs("data", exist_ok=True)
        with open(_PUSH_LAST_SENT_FILE, "w") as f:
            f.write(today)
        _send_push_to_all(
            "🎰 PREDIKTA — Nouveaux résultats !",
            "Les tirages du jour sont disponibles. Consulte tes prédictions maintenant.",
            "/all-results",
        )
    except Exception as e:
        print(f"  [push] daily notification skipped: {e}")


@app.route("/api/push/vapid-public-key")
def api_push_vapid_key():
    key = _vapid_public_key()
    if not key:
        return jsonify({"error": "Push notifications not configured"}), 503
    return jsonify({"key": key})


@app.route("/api/push/subscribe", methods=["POST"])
def api_push_subscribe():
    data = request.get_json(silent=True) or {}
    sub = data.get("subscription")
    if not sub or "endpoint" not in sub:
        return jsonify({"error": "Invalid subscription"}), 400

    subs = _load_subscriptions()
    if not any(s.get("endpoint") == sub["endpoint"] for s in subs):
        subs.append(sub)
        _save_subscriptions(subs)
    return jsonify({"message": "Subscribed", "total": len(subs)})


@app.route("/api/push/unsubscribe", methods=["POST"])
def api_push_unsubscribe():
    data = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint")
    if not endpoint:
        return jsonify({"error": "Missing endpoint"}), 400

    subs = _load_subscriptions()
    new_subs = [s for s in subs if s.get("endpoint") != endpoint]
    _save_subscriptions(new_subs)
    return jsonify({"message": "Unsubscribed", "total": len(new_subs)})


@app.route("/api/push/send", methods=["POST", "GET"])
def api_push_send():
    """Déclenchement manuel/admin (protégé par PREDIKTA_ADMIN_SECRET)."""
    secret = os.environ.get("PREDIKTA_ADMIN_SECRET")
    if not secret or request.args.get("secret") != secret:
        return jsonify({"error": "Forbidden"}), 403

    title = request.args.get("title", "🎰 PREDIKTA")
    body  = request.args.get("body", "Les résultats du jour sont disponibles !")
    url   = request.args.get("url", "/all-results")
    result = _send_push_to_all(title, body, url)
    return jsonify(result)


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

            # Rafraîchit aussi les données "Tous résultats" (/all-results) pour
            # chaque État du registre multi-jeux — sinon elles restent figées.
            try:
                from games_config import STATE_GAMES
                from games_scraper import fetch_all_games_for_state
                for st_code in STATE_GAMES.keys():
                    try:
                        fetch_all_games_for_state(st_code, n_months=1)
                    except Exception as ge:
                        print(f"  [auto-update][games:{st_code}] error: {ge}")
            except Exception as e:
                print(f"  [auto-update][games] skipped: {e}")

            _REPORT_CACHE.clear()    # nouvelles données → on invalide les analyses en cache
            _LATEST_CACHE["data"] = None
            _warm_popular_reports()  # pré-calcule les rapports des États les plus consultés
            _auto_update_state["last_run"] = datetime.utcnow().isoformat() + "Z"
            _auto_update_state["last_status"] = "ok"
            _maybe_send_daily_push()
        except Exception as e:
            _auto_update_state["last_status"] = f"error: {e}"
        finally:
            _auto_update_state["running"] = False
        time.sleep(_AUTO_UPDATE_INTERVAL)

def _initial_warm_loop():
    """Au démarrage, pré-calcule les rapports populaires dès que possible
    (à partir des données déjà sur disque), sans attendre le 1er cycle de
    scraping (qui démarre après PREDIKTA_AUTOUPDATE_DELAY_SEC)."""
    time.sleep(5)  # laisse le serveur finir de démarrer / passer le health-check
    try:
        _warm_popular_reports()
    except Exception as e:
        print(f"  [warm-cache][initial] error: {e}")

def start_auto_update():
    if os.environ.get("PREDIKTA_DISABLE_AUTOUPDATE") == "1":
        return
    threading.Thread(target=_initial_warm_loop, daemon=True, name="predikta-warm-cache").start()
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
    "AR": [{"tod":"Midday","time":"12:59 PM CT"}, {"tod":"Evening","time":"6:59 PM CT"}],
    "AZ": [{"tod":"Evening","time":"7:00 PM MST"}],
    "CA": [{"tod":"Midday","time":"1:00 PM PT"},  {"tod":"Evening","time":"6:30 PM PT"}],
    "CO": [{"tod":"Midday","time":"1:30 PM MT"}, {"tod":"Evening","time":"7:30 PM MT"}],
    "CT": [{"tod":"Day","time":"1:57 PM ET"},  {"tod":"Night","time":"10:29 PM ET"}],
    "DC": [{"tod":"Midday","time":"1:50 PM ET"}, {"tod":"Evening","time":"7:50 PM ET"}, {"tod":"Night","time":"11:30 PM ET"}],
    "DE": [{"tod":"Day","time":"1:58 PM ET"},  {"tod":"Night","time":"7:57 PM ET"}],
    "FL": [{"tod":"Midday","time":"1:30 PM ET"},  {"tod":"Night","time":"9:45 PM ET"}],
    "GA": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}, {"tod":"Night","time":"11:34 PM ET"}],
    "IA": [{"tod":"Midday","time":"12:20 PM CT"}, {"tod":"Night","time":"10:00 PM CT"}],
    "ID": [{"tod":"Day","time":"1:59 PM MT"}, {"tod":"Night","time":"7:59 PM MT"}],
    "IL": [{"tod":"Midday","time":"12:40 PM CT"}, {"tod":"Night","time":"9:22 PM CT"}],
    "IN": [{"tod":"Midday","time":"1:20 PM ET"},  {"tod":"Night","time":"11:00 PM ET"}],
    "KS": [{"tod":"Midday","time":"1:10 PM CT"}, {"tod":"Night","time":"9:10 PM CT"}],
    "KY": [{"tod":"Midday","time":"1:20 PM ET"}, {"tod":"Night","time":"11:00 PM ET"}],
    "LA": [{"tod":"Night","time":"9:59 PM CT"}],
    "MA": [{"tod":"Midday","time":"2:00 PM ET"},  {"tod":"Night","time":"9:00 PM ET"}],
    "MD": [{"tod":"Midday","time":"12:27 PM ET"}, {"tod":"Evening","time":"7:56 PM ET"}],
    "ME": [{"tod":"Day","time":"1:10 PM ET"}, {"tod":"Evening","time":"6:50 PM ET"}],
    "MI": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "MN": [{"tod":"Evening","time":"6:17 PM CT"}],
    "MO": [{"tod":"Midday","time":"12:45 PM CT"}, {"tod":"Evening","time":"8:59 PM CT"}],
    "MS": [{"tod":"Midday","time":"2:30 PM CT"}, {"tod":"Night","time":"9:30 PM CT"}],
    "NC": [{"tod":"Day","time":"3:00 PM ET"},  {"tod":"Night","time":"11:22 PM ET"}],
    "NE": [{"tod":"Night","time":"9:59 PM CT"}],
    "NH": [{"tod":"Day","time":"1:10 PM ET"}, {"tod":"Evening","time":"6:55 PM ET"}],
    "NJ": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Night","time":"10:57 PM ET"}],
    "NM": [{"tod":"Day","time":"1:00 PM MT"}, {"tod":"Night","time":"9:30 PM MT"}],
    "NY": [{"tod":"Midday","time":"2:30 PM ET"},  {"tod":"Night","time":"10:30 PM ET"}],
    "OH": [{"tod":"Midday","time":"12:29 PM ET"}, {"tod":"Evening","time":"7:29 PM ET"}],
    "OK": [{"tod":"Night","time":"9:10 PM CT"}],
    "OR": [{"tod":"Midday","time":"1:00 PM PT"}, {"tod":"Midday","time":"4:00 PM PT"}, {"tod":"Evening","time":"7:00 PM PT"}, {"tod":"Night","time":"10:00 PM PT"}],
    "PA": [{"tod":"Day","time":"1:35 PM ET"},  {"tod":"Evening","time":"6:59 PM ET"}],
    "PR": [{"tod":"Day","time":"2:00 PM AT"}, {"tod":"Night","time":"9:00 PM AT"}],
    "RI": [{"tod":"Midday","time":"1:30 PM ET"},  {"tod":"Evening","time":"7:29 PM ET"}],
    "SC": [{"tod":"Midday","time":"12:59 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}],
    "TN": [{"tod":"Morning","time":"9:28 AM CT"}, {"tod":"Midday","time":"12:28 PM CT"}, {"tod":"Evening","time":"6:28 PM CT"}],
    "TX": [{"tod":"Morning","time":"10:00 AM CT"}, {"tod":"Midday","time":"12:27 PM CT"}, {"tod":"Evening","time":"6:00 PM CT"}, {"tod":"Night","time":"10:12 PM CT"}],
    "VA": [{"tod":"Day","time":"1:59 PM ET"},  {"tod":"Night","time":"11:00 PM ET"}],
    "VT": [{"tod":"Day","time":"1:10 PM ET"}, {"tod":"Evening","time":"6:59 PM ET"}],
    "WA": [{"tod":"Evening","time":"8:00 PM PT"}],
    "WI": [{"tod":"Midday","time":"1:30 PM CT"},  {"tod":"Night","time":"9:00 PM CT"}],
    "WV": [{"tod":"Evening","time":"6:59 PM ET"}],

}

STATE_FLAGS = {
    "AR":"💎","AZ":"🌵","CA":"☀️","CO":"🏔️","CT":"⚓","DC":"🏛️",
    "DE":"🦆","FL":"🌴","GA":"🍑","IA":"🌽","ID":"🥔","IL":"🏙️","IN":"🏁",
    "KS":"🌾","KY":"🐎","LA":"🎷","MA":"🦞","MD":"🦀","ME":"🦞","MI":"🚗",
    "MN":"🌨️","MO":"⛵","MS":"🎶","NC":"🌲","NE":"🌾","NH":"🏔️","NJ":"🌊",
    "NM":"🌶️","NY":"🗽","OH":"🌻","OK":"🛢️","OR":"🌲","PA":"🔔","PR":"🌺",
    "RI":"⛵","SC":"🌴","TN":"🎸","TX":"⭐","VA":"🦅","VT":"🍁","WA":"🌧️",
    "WI":"🧀","WV":"⛰️",

}

# ── Newsletter subscribers store (flat file for simplicity) ───────────────
SUBS_FILE = os.path.join(os.path.dirname(__file__), "data", "subscribers.json")

def load_subscribers():
    if os.path.exists(SUBS_FILE):
        with open(SUBS_FILE) as f:
            return json.load(f)
    return []


def _save_subscribers_list(subs):
    os.makedirs(os.path.dirname(SUBS_FILE), exist_ok=True)
    with open(SUBS_FILE, "w") as f:
        json.dump(subs, f, indent=2)


def _gen_ref_code(email: str) -> str:
    """Code de parrainage court et stable, dérivé de l'email (pas de compte requis)."""
    import hashlib
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:8].upper()


def save_subscriber(email, lang="fr", ref_code=None):
    """Enregistre un nouvel abonné (newsletter / parrainage). Chaque abonné
    reçoit automatiquement son propre code de parrainage. Si `ref_code`
    correspond à un abonné existant (et différent de l'email lui-même),
    son compteur de filleuls est incrémenté."""
    subs = load_subscribers()
    emails = [s["email"] for s in subs]

    if email not in emails:
        entry = {
            "email": email,
            "lang": lang,
            "date": date.today().isoformat(),
            "ref_code": _gen_ref_code(email),
            "referral_count": 0,
            "referred_by": None,
        }

        if ref_code:
            ref_code = ref_code.strip().upper()
            referrer = next((s for s in subs if s.get("ref_code") == ref_code), None)
            if referrer and referrer["email"] != email:
                referrer["referral_count"] = referrer.get("referral_count", 0) + 1
                entry["referred_by"] = referrer["email"]

        subs.append(entry)
        _save_subscribers_list(subs)
        return True
    else:
        # Abonné existant sans code (anciennes entrées) : on lui en attribue un.
        for s in subs:
            if s["email"] == email and not s.get("ref_code"):
                s["ref_code"] = _gen_ref_code(email)
                s.setdefault("referral_count", 0)
                s.setdefault("referred_by", None)
                _save_subscribers_list(subs)
                break
        return False  # already subscribed


def _find_subscriber(email: str):
    email = (email or "").strip().lower()
    for s in load_subscribers():
        if s["email"] == email:
            return s
    return None


# ═══════════════════════════════════════════════════════════
# STATIC PAGES
# ═══════════════════════════════════════════════════════════

@app.route("/")
def index():       return send_from_directory("static", "home.html")

@app.route("/predictions")
def predictions_index():
    import seo_pages
    lang = request.args.get("lang", "fr")
    return seo_pages.render_predictions_index(request.url_root.rstrip("/"), lang)

@app.route("/predictions/<state_code>")
def predictions_state(state_code):
    import seo_pages
    from scraper import STATES as _STATES
    if state_code.upper() not in _STATES:
        if os.path.exists("static/404.html"):
            return send_from_directory("static", "404.html"), 404
        return "Not found", 404
    lang = request.args.get("lang", "fr")
    return seo_pages.render_prediction_page(state_code, request.url_root.rstrip("/"), lang)

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

@app.route("/archives")
def archives_page(): return send_from_directory("static", "archives.html")

@app.route("/parrainage")
def referral_page(): return send_from_directory("static", "referral.html")

@app.route("/login")
def login_page(): return send_from_directory("static", "login.html")

@app.route("/register")
def register_page(): return send_from_directory("static", "register.html")

@app.route("/account")
def account_page(): return send_from_directory("static", "account.html")

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
        ref   = request.args.get("ref", "").strip()
    else:
        data  = request.get_json(silent=True) or {}
        email = data.get("email", "").strip().lower()
        lang  = data.get("lang", "fr")
        ref   = (data.get("ref") or "").strip()

    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"success": False, "message": "Email invalide"}), 400

    is_new = save_subscriber(email, lang, ref_code=ref or None)
    sub = _find_subscriber(email)
    return jsonify({
        "success": True,
        "message": "Inscription réussie!" if is_new else "Déjà inscrit",
        "new": is_new,
        "ref_code": sub.get("ref_code") if sub else None,
    })


# ── Programme de parrainage (Phase 1 — basé sur l'email, sans compte) ─────
@app.route("/api/referral/me")
def api_referral_me():
    email = request.args.get("email", "").strip().lower()
    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"error": "Email invalide"}), 400

    sub = _find_subscriber(email)
    if not sub:
        # Auto-inscription silencieuse pour générer un code de parrainage
        save_subscriber(email)
        sub = _find_subscriber(email)
    elif not sub.get("ref_code"):
        # Ancienne entrée (avant l'ajout du parrainage) : on lui attribue un code.
        subs = load_subscribers()
        for s in subs:
            if s["email"] == email:
                s["ref_code"] = _gen_ref_code(email)
                s.setdefault("referral_count", 0)
                s.setdefault("referred_by", None)
        _save_subscribers_list(subs)
        sub = _find_subscriber(email)

    return jsonify({
        "email": sub["email"],
        "ref_code": sub["ref_code"],
        "referral_count": sub.get("referral_count", 0),
        "referred_by": sub.get("referred_by"),
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

# États les plus consultés — pré-calculés en arrière-plan après chaque
# scraping pour que le 1er clic utilisateur tombe déjà en cache (évite
# l'attente de 15-25s sur les états les plus populaires).
PRIORITY_STATES = ['NY','FL','GA','TX','NJ','TN','CA','PA','IL','OH','VA']

def _build_report(state: str, tod_filter: str = "all"):
    """Compute (or raise) the analysis report for a state/tod. Returns dict or None if no data."""
    draws = load_csv(state)
    if not draws:
        return None

    if tod_filter != "all":
        draws = [d for d in draws if d.get("tod","").lower() == tod_filter.lower()]
        if not draws:
            return None

    result = run_all_models(draws)
    result["state"]       = state
    result["state_name"]  = STATES[state]["name"]
    result["tod_filter"]  = tod_filter
    result["dpd"]         = STATES[state].get("dpd", 2)
    result["schedule"]    = DRAW_SCHEDULE.get(state, [])
    result["cached"]      = False
    return result

def _warm_popular_reports():
    """Pre-compute & cache the 'all' report for the most popular states."""
    now = time.time()
    for state in PRIORITY_STATES:
        cache_key = (state, "all")
        cached = _REPORT_CACHE.get(cache_key)
        if cached and (now - cached["ts"]) < _REPORT_CACHE_TTL:
            continue
        try:
            result = _build_report(state, "all")
            if result:
                _REPORT_CACHE[cache_key] = {"ts": time.time(), "data": {**result, "cached": True}}
        except Exception as e:
            print(f"  [warm-cache][{state}] error: {e}")

@app.route("/api/report")
@auth_module.subscription_required
def api_report():
    state      = request.args.get("state", "NY").upper()
    tod_filter = request.args.get("tod", "all")

    if state not in STATES:
        return jsonify({"error": f"Unknown state: {state}"}), 400

    cache_key = (state, tod_filter)
    cached = _REPORT_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - cached["ts"]) < _REPORT_CACHE_TTL:
        auth_module.record_usage(auth_module.current_user().id)
        return jsonify(cached["data"])

    if not load_csv(state):
        return jsonify({"error": f"No data for {state}. Click Scrape first."}), 200

    result = _build_report(state, tod_filter)
    if result is None:
        return jsonify({"error": f"No {tod_filter} draws for {state}."}), 200

    _REPORT_CACHE[cache_key] = {"ts": now, "data": {**result, "cached": True}}
    auth_module.record_usage(auth_module.current_user().id)
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
            _LATEST_CACHE["data"] = None
            return jsonify({"message": f"{len(draws)} draws fetched · {total} total saved for {state}"})
        return jsonify({"message": f"No data found for {state}"})

    scrape_all(n_months=months)
    _REPORT_CACHE.clear()
    _LATEST_CACHE["data"] = None
    return jsonify({"message": "Scraping complete for all states"})


# ═══════════════════════════════════════════════════════════
# API — STATES LIST
# ═══════════════════════════════════════════════════════════

@app.route("/api/states")
def api_states():
    result = {}
    for code, cfg in STATES.items():
        draws = load_csv(code)
        # Tirages réellement disponibles pour cet État (Matin/Midi/Soir/Nuit
        # selon les données réelles — optimisé et à jour par État)
        tods = sorted({d.get("tod","") for d in draws if d.get("tod")},
                      key=lambda t: TOD_ORDER.get(t, 99))
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

_LATEST_CACHE = {"ts": 0, "data": None}
_LATEST_CACHE_TTL = 60  # secondes — données rafraîchies au plus toutes les 60s

@app.route("/api/results/latest")
def api_results_latest():
    now = time.time()
    if _LATEST_CACHE["data"] is not None and (now - _LATEST_CACHE["ts"]) < _LATEST_CACHE_TTL:
        return jsonify(_LATEST_CACHE["data"])

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
        latest_draws = sorted(by_date[latest_date], key=lambda x: TOD_ORDER.get(x.get("tod",""), 99))

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

    _LATEST_CACHE["ts"] = now
    _LATEST_CACHE["data"] = result
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
        {"date": dt, "draws": sorted(by_date[dt], key=lambda x: TOD_ORDER.get(x.get("tod",""), 99))}
        for dt in sorted(by_date.keys(), reverse=True)
    ]

    cfg = STATES[state_code]
    return jsonify({
        "state": state_code, "name": cfg["name"],
        "flag": STATE_FLAGS.get(state_code,"🎰"),
        "schedule": DRAW_SCHEDULE.get(state_code,[]),
        "days": days, "total": len(draws),
    })


# ═══════════════════════════════════════════════════════════
# API — QUICK TOOLS (instantanés, sans calcul ML)
# ═══════════════════════════════════════════════════════════

@app.route("/api/digit-stats/<state_code>")
def api_digit_stats(state_code):
    """Stats légères (sans ML) : chiffre le plus/moins sorti, hot/cold 30 tirages."""
    state_code = state_code.upper()
    if state_code not in STATES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400

    draws = load_csv(state_code)
    if not draws:
        return jsonify({"error": f"No data for {state_code}"}), 200

    # Fréquence globale tous chiffres confondus (toutes positions)
    overall = Counter()
    for d in draws:
        for pos in ["d1", "d2", "d3"]:
            overall[int(d[pos])] += 1
    total = sum(overall.values()) or 1
    most_common = overall.most_common()
    hottest = most_common[0]
    coldest = most_common[-1]

    return jsonify({
        "state": state_code,
        "state_name": STATES[state_code]["name"],
        "total_draws": len(draws),
        "hot_cold": hot_cold_stats(draws, window=30),
        "gaps": digit_gap_analysis(draws),
        "overall_frequency": {str(k): {"count": v, "pct": round(v/total*100, 2)} for k, v in overall.items()},
        "hottest_digit": {"digit": hottest[0], "count": hottest[1], "pct": round(hottest[1]/total*100, 2)},
        "coldest_digit": {"digit": coldest[0], "count": coldest[1], "pct": round(coldest[1]/total*100, 2)},
        "last_draws": draws[:10],
    })


@app.route("/api/combo-check/<state_code>/<combo>")
def api_combo_check(state_code, combo):
    """Recherche d'une combinaison (ex: 452) dans l'historique d'un État."""
    state_code = state_code.upper()
    if state_code not in STATES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400

    if not re.match(r"^\d{2,4}$", combo):
        return jsonify({"error": "Combo must be 2-4 digits"}), 400

    draws = load_csv(state_code)
    if not draws:
        return jsonify({"error": f"No data for {state_code}"}), 200

    digits = [int(c) for c in combo]
    exact_matches, any_order_matches = [], []
    sorted_digits = sorted(digits)

    for i, d in enumerate(draws):
        draw_digits = [int(d["d1"]), int(d["d2"]), int(d["d3"])][:len(digits)]
        if draw_digits == digits:
            exact_matches.append({**d, "draws_ago": i})
        if sorted(draw_digits) == sorted_digits:
            any_order_matches.append({**d, "draws_ago": i})

    total = len(draws)
    return jsonify({
        "state": state_code,
        "state_name": STATES[state_code]["name"],
        "combo": combo,
        "total_draws": total,
        "exact_count": len(exact_matches),
        "exact_pct": round(len(exact_matches)/total*100, 3) if total else 0,
        "exact_last": exact_matches[0] if exact_matches else None,
        "any_order_count": len(any_order_matches),
        "any_order_pct": round(len(any_order_matches)/total*100, 3) if total else 0,
        "any_order_last": any_order_matches[0] if any_order_matches else None,
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
        {"date": dt, "draws": sorted(by_date[dt], key=lambda x: TOD_ORDER.get(x.get("tod",""), 99))}
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
import analyzer_multi

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
        "schedule": DRAW_SCHEDULE.get(state_code, []),
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


@app.route("/api/games/analyze/<state_code>/<slug>")
@auth_module.subscription_required
def api_games_analyze(state_code, slug):
    """
    Statistical analysis (frequency, hot/cold, gaps, Markov, suggestions)
    for a Pick3/Pick4/digit-Pick5 game — generalization of /api/report to
    games beyond the main Pick3 CSVs (Win4, Cash4, Daily4, etc).
    """
    state_code = state_code.upper()
    games = STATE_GAMES.get(state_code, [])
    game = next((g for g in games if g["slug"] == slug), None)
    if not game:
        return jsonify({"error": f"Unknown game {slug} for {state_code}"}), 400

    draws = load_game_results(state_code, slug)
    if not draws:
        return jsonify({"error": f"No data for {state_code}/{slug}. Scrape first."}), 200

    n = GAME_TYPES.get(game["type"], {}).get("num_balls", 3)

    # Only digit games (each position is a single digit 0-9) support this
    # analysis — multi-ball lotto games (Take 5, Fantasy 5, Pick 10...) draw
    # numbers up to 39+ and are not modeled as independent digit positions.
    if any(int(v) > 9 for d in draws[:50] for v in d["nums"][:n]):
        return jsonify({"error": f"{game['label']} is not a digit game (numbers > 9) — analysis not applicable."}), 200

    result = analyzer_multi.full_report(draws, n)
    result["state"] = state_code
    result["state_name"] = STATES.get(state_code, {}).get("name", state_code)
    result["slug"] = slug
    result["label"] = game["label"]
    result["game_type"] = game["type"]

    auth_module.record_usage(auth_module.current_user().id)
    return jsonify(result)

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

@app.route("/api/bizai/quota")
def bizai_quota():
    """Return the current user's Business Intelligence quota status."""
    user = auth_module.current_user()
    if not user:
        return jsonify({"logged_in": False, "unlimited": False,
                         "limit": auth_module.FREE_BIZAI_ANALYSES_PER_MONTH,
                         "used": 0,
                         "remaining": auth_module.FREE_BIZAI_ANALYSES_PER_MONTH})
    status = auth_module.bizai_quota_status(user)
    status["logged_in"] = True
    return jsonify(status)

@app.route("/api/bizai/analyze", methods=["GET", "POST"])
@auth_module.bizai_access_required
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
        user = auth_module.current_user()
        if user and not data.get("_example"):
            auth_module.record_bizai_usage(user.id)
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
