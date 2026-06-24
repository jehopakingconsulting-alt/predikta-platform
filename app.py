"""
ZYNORIQ Intelligence™ — Flask Server  v2.0
"""

from flask import Flask, jsonify, request, send_from_directory, make_response, Response, stream_with_context
from flask.json.provider import DefaultJSONProvider
try:
    from flask_compress import Compress
except ImportError:
    Compress = None
import numpy as np
import os, json, re, threading, time, queue, hmac
from collections import Counter, defaultdict
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from scraper import (scrape_all, fetch_state, save_csv, load_csv,
                     STATES, fetch_months, parse_draws, fetch_url, BASE_URL, DATA_DIR)
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
_secret_key = os.environ.get("ZYNORIQ_SECRET_KEY") or os.environ.get("PREDIKTA_SECRET_KEY")
if not _secret_key:
    import secrets as _secrets
    _secret_key = _secrets.token_hex(32)
    print("[WARNING] ZYNORIQ_SECRET_KEY not set — using a random key; sessions will not survive restarts")
app.secret_key = _secret_key
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER") is not None
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

# ── Comptes utilisateurs / abonnements (SQLAlchemy) ───────────────────────
import auth as auth_module
auth_module.init_app(app)
app.register_blueprint(auth_module.auth_bp)

# ── Facturation Stripe (Phase 2b) ─────────────────────────────────────────
import billing as billing_module
app.register_blueprint(billing_module.billing_bp)

# ── ZYNORIQ MEMORY™ ──────────────────────────────────────────────────────
import memory_engine as _mem
import agents_engine as _agents
import intelligence_graph as _igraph
import studio_engine as _studio

# ── Connexion via Google / Facebook / Microsoft (OAuth) ───────────────────
import oauth as oauth_module
oauth_module.init_app(app)

# Init Memory tables after auth DB is ready
_mem.init_memory(app, auth_module.db)
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
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://www.google-analytics.com https://cdn.jsdelivr.net; "
        "frame-ancestors 'self';"
    )
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
# automatiquement au premier démarrage si absentes, voir _ensure_vapid_keys).
_PUSH_SUBS_FILE   = os.path.join("data", "push_subscriptions.json")
_VAPID_PRIV_FILE  = os.path.join("data", "vapid_private.pem")
_VAPID_PUB_FILE   = os.path.join("data", "vapid_public.txt")
_PUSH_LAST_SENT_FILE = os.path.join("data", "push_last_sent.txt")
_VAPID_CLAIMS = {"sub": os.environ.get("PREDIKTA_VAPID_EMAIL", "mailto:contact@zynoriq.com")}


def _ensure_vapid_keys():
    """Utilise les clés VAPID depuis les variables d'env (priorité) ou les génère."""
    os.makedirs("data", exist_ok=True)

    # Priorité : variables d'environnement (Render)
    env_priv = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
    env_pub  = os.environ.get("VAPID_PUBLIC_KEY", "").strip()
    if env_priv and env_pub:
        with open(_VAPID_PRIV_FILE, "w") as f:
            f.write(env_priv)
        with open(_VAPID_PUB_FILE, "w") as f:
            f.write(env_pub)
        return

    if os.path.exists(_VAPID_PRIV_FILE) and os.path.exists(_VAPID_PUB_FILE):
        return
    try:
        from py_vapid import Vapid02
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        import base64

        vapid = Vapid02()
        vapid.generate_keys()

        with open(_VAPID_PRIV_FILE, "wb") as f:
            f.write(vapid.private_pem())

        raw_pub = vapid.public_key.public_bytes(
            encoding=Encoding.X962, format=PublicFormat.UncompressedPoint
        )
        pub_b64 = base64.urlsafe_b64encode(raw_pub).decode().rstrip("=")
        with open(_VAPID_PUB_FILE, "w") as f:
            f.write(pub_b64)

        print("  [push] Clés VAPID générées et enregistrées dans data/")
    except Exception as e:
        print(f"  [push] Impossible de générer les clés VAPID: {e}")


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
    # Write backup before overwriting to prevent data loss on crash
    if os.path.exists(_PUSH_SUBS_FILE):
        import shutil
        shutil.copy2(_PUSH_SUBS_FILE, _PUSH_SUBS_FILE + ".bak")
    with open(_PUSH_SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=2)


def _send_push_to_all(title: str, body: str, url: str = "/all-results", state: str | None = None):
    """Envoie une notification push aux abonnés concernés.
    Si state est fourni, filtre les abonnés qui ont cet état dans leurs préférences
    (ou qui ont ["ALL"] / liste vide = tous les états)."""
    if webpush is None or not os.path.exists(_VAPID_PRIV_FILE):
        return {"sent": 0, "removed": 0, "error": "push not configured"}

    with open(_VAPID_PRIV_FILE) as f:
        private_key = f.read()

    all_subs = _load_subscriptions()
    # Filtrer par état si précisé
    if state:
        st_up = state.upper()
        subs = []
        for s in all_subs:
            prefs = s.get("states") or []
            if not prefs or "ALL" in prefs or st_up in prefs:
                subs.append(s)
    else:
        subs = all_subs

    payload = json.dumps({"title": title, "body": body, "url": url})
    sent, removed, kept = 0, 0, []

    for sub in subs:
        # subscription_info doit contenir endpoint + keys seulement
        sub_info = {"endpoint": sub["endpoint"], "keys": sub.get("keys", {})}
        try:
            webpush(
                subscription_info=sub_info,
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
        # Reconstruire la liste complète sans les morts
        dead_eps = {s["endpoint"] for s in all_subs if s not in kept and s in subs}
        _save_subscriptions([s for s in all_subs if s.get("endpoint") not in dead_eps])
    return {"sent": sent, "removed": removed}


def _check_new_result_alerts():
    """Envoie un email aux utilisateurs ayant une alerte active « Nouveau
    tirage » (alert_type=new_result) dès qu'un nouveau tirage est disponible
    pour leur État/jeu surveillé. Appelé après chaque cycle de scraping."""
    from games_scraper import load_game_results
    from games_config import STATE_GAMES
    import json as _json

    db = auth_module.db
    Alert = auth_module.Alert
    User = auth_module.User

    alerts = Alert.query.filter_by(active=True, alert_type="new_result").all()
    if not alerts:
        return

    latest_draw_cache = {}
    changed = False
    for alert in alerts:
        state = (alert.state or "").upper()
        slug = alert.game
        key = (state, slug)
        if key not in latest_draw_cache:
            draws = load_game_results(state, slug)
            latest_draw_cache[key] = draws[-1] if draws else None
        draw = latest_draw_cache[key]
        if not draw:
            continue

        try:
            criteria = _json.loads(alert.criteria) if alert.criteria else {}
        except Exception:
            criteria = {}

        draw_key = f"{draw.get('date','')}|{draw.get('tod','')}"
        if criteria.get("last_seen_date") == draw_key:
            continue

        user = db.session.get(User, alert.user_id)
        if not user:
            continue

        game_label = next((g["label"] for g in STATE_GAMES.get(state, []) if g["slug"] == slug), slug)
        auth_module.send_new_result_alert_email(user, state, game_label, draw)

        criteria["last_seen_date"] = draw_key
        alert.criteria = _json.dumps(criteria)
        alert.last_triggered_at = datetime.utcnow()
        changed = True

    if changed:
        db.session.commit()


def _check_hotcold_alerts():
    """Envoie un email aux utilisateurs ayant une alerte active « Numéro
    chaud » ou « Numéro froid » dès qu'un chiffre devient HOT/COLD pour
    leur État/jeu surveillé (calculé sur les 30 derniers tirages)."""
    from games_scraper import load_game_results
    from games_config import STATE_GAMES
    import json as _json

    db = auth_module.db
    Alert = auth_module.Alert
    User = auth_module.User

    alerts = Alert.query.filter(
        Alert.active == True,
        Alert.alert_type.in_(["hot_number", "cold_number"]),
    ).all()
    if not alerts:
        return

    stats_cache = {}
    changed = False
    for alert in alerts:
        state = (alert.state or "").upper()
        slug = alert.game
        key = (state, slug)
        if key not in stats_cache:
            draws = load_game_results(state, slug)
            # hot_cold_stats ne s'applique qu'aux jeux à 3 chiffres (pick3)
            pick3_draws = [d for d in draws if len(d.get("nums") or []) == 3]
            recent = [{"d1": d["nums"][0], "d2": d["nums"][1], "d3": d["nums"][2]} for d in reversed(pick3_draws[-30:])]
            stats_cache[key] = hot_cold_stats(recent, window=30) if recent else None
        stats = stats_cache[key]
        if not stats:
            continue

        target_status = "HOT" if alert.alert_type == "hot_number" else "COLD"
        found = []
        for pos, digits in stats.items():
            for digit, info in digits.items():
                if info.get("status") == target_status:
                    found.append({"pos": pos, "digit": digit})

        try:
            criteria = _json.loads(alert.criteria) if alert.criteria else {}
        except Exception:
            criteria = {}

        signature = ",".join(sorted(f"{f['pos']}:{f['digit']}" for f in found))
        if not found or criteria.get("last_signature") == signature:
            criteria["last_signature"] = signature
            alert.criteria = _json.dumps(criteria)
            continue

        user = db.session.get(User, alert.user_id)
        if not user:
            continue

        game_label = next((g["label"] for g in STATE_GAMES.get(state, []) if g["slug"] == slug), slug)
        auth_module.send_hotcold_alert_email(user, state, game_label, alert.alert_type, found)

        criteria["last_signature"] = signature
        alert.criteria = _json.dumps(criteria)
        alert.last_triggered_at = datetime.utcnow()
        changed = True

    if changed:
        db.session.commit()


def _check_custom_alerts():
    """Envoie un email aux utilisateurs ayant une alerte « Personnalisée »
    (alert_type=custom) dès que le numéro qu'ils surveillent (criteria.number)
    sort dans un nouveau tirage de leur État/jeu surveillé."""
    from games_scraper import load_game_results
    from games_config import STATE_GAMES
    import json as _json

    db = auth_module.db
    Alert = auth_module.Alert
    User = auth_module.User

    alerts = Alert.query.filter_by(active=True, alert_type="custom").all()
    if not alerts:
        return

    latest_draw_cache = {}
    changed = False
    for alert in alerts:
        try:
            criteria = _json.loads(alert.criteria) if alert.criteria else {}
        except Exception:
            criteria = {}

        number = str(criteria.get("number") or "").strip()
        if not number:
            continue

        state = (alert.state or "").upper()
        slug = alert.game
        key = (state, slug)
        if key not in latest_draw_cache:
            draws = load_game_results(state, slug)
            latest_draw_cache[key] = draws[-1] if draws else None
        draw = latest_draw_cache[key]
        if not draw:
            continue

        draw_key = f"{draw.get('date','')}|{draw.get('tod','')}"
        if criteria.get("last_seen_date") == draw_key:
            continue

        criteria["last_seen_date"] = draw_key
        drawn_number = "".join(draw.get("nums") or [])
        if drawn_number != number:
            alert.criteria = _json.dumps(criteria)
            continue

        user = db.session.get(User, alert.user_id)
        if not user:
            continue

        game_label = next((g["label"] for g in STATE_GAMES.get(state, []) if g["slug"] == slug), slug)
        auth_module.send_custom_alert_email(user, state, game_label, number, draw)

        alert.criteria = _json.dumps(criteria)
        alert.last_triggered_at = datetime.utcnow()
        changed = True

    if changed:
        db.session.commit()


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
            "🎰 ZYNORIQ — Nouveaux résultats !",
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

    states = data.get("states") or ["ALL"]  # ["ALL"] = tous les états

    subs = _load_subscriptions()
    subs = [s for s in subs if s.get("endpoint") != sub["endpoint"]]  # dédoublonne
    entry = {"endpoint": sub["endpoint"], "keys": sub.get("keys", {}), "states": states}
    subs.append(entry)
    _save_subscriptions(subs)
    return jsonify({"message": "Subscribed", "total": len(subs)})


@app.route("/api/push/preferences", methods=["POST"])
def api_push_preferences():
    """Met à jour les états préférés d'un abonné existant."""
    data    = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint", "")
    states   = data.get("states") or ["ALL"]
    if not endpoint:
        return jsonify({"error": "Missing endpoint"}), 400
    subs = _load_subscriptions()
    updated = False
    for s in subs:
        if s.get("endpoint") == endpoint:
            s["states"] = states
            updated = True
            break
    if updated:
        _save_subscriptions(subs)
    return jsonify({"ok": updated, "states": states})


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
    provided = request.args.get("secret", "")
    if not secret or not hmac.compare_digest(provided, secret):
        return jsonify({"error": "Forbidden"}), 403

    title = request.args.get("title", "🎰 ZYNORIQ")
    body  = request.args.get("body", "Les résultats du jour sont disponibles !")
    url   = request.args.get("url", "/all-results")
    result = _send_push_to_all(title, body, url)
    return jsonify(result)


# ── Mise à jour automatique en arrière-plan ───────────────────────────────
# Au lieu de cliquer manuellement sur "Mettre à jour", un thread de fond
# rafraîchit périodiquement les résultats de tous les États (LotteryPost &
# autres sources configurées dans scraper.py).
_AUTO_UPDATE_INTERVAL = int(os.environ.get("PREDIKTA_AUTOUPDATE_SEC", 25 * 60))  # 25 min par défaut
_auto_update_state = {"last_run": None, "last_status": "idle", "running": False}


def _retry_stale_states():
    """
    After each scrape cycle, detect states whose latest CSV draw is >18h old
    despite daily draws being expected, and immediately retry scraping them.
    Prevents permanently stuck draws when lotteryusa.com is temporarily slow.
    """
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import csv as _csv

    now_et = datetime.now(ZoneInfo("America/New_York"))
    stale_threshold = now_et - timedelta(hours=18)
    stale_threshold_str = stale_threshold.strftime("%Y-%m-%d")

    stale = []
    for code in STATES:
        path = os.path.join("data", f"{code.lower()}.csv")
        if not os.path.exists(path):
            continue
        try:
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(_csv.DictReader(f))
            if not rows:
                continue
            latest_date = max(r["date"] for r in rows)
            if latest_date <= stale_threshold_str:
                stale.append(code)
        except Exception:
            continue

    if stale:
        print(f"  [stale-retry] {len(stale)} états bloqués: {stale} — re-scrape immédiat")
        for code in stale:
            try:
                draws = fetch_state(code, n_months=1)
                if draws:
                    save_csv(code, draws)
                    print(f"  [stale-retry] [{code}] {len(draws)} tirages récupérés")
            except Exception as e:
                print(f"  [stale-retry] [{code}] erreur: {e}")
            time.sleep(0.5)

def _auto_update_loop():
    # Laisse le serveur démarrer et passer le health-check avant de lancer
    # le premier scraping (évite les pics mémoire au boot sur les plans
    # gratuits / contraints en RAM).
    time.sleep(int(os.environ.get("PREDIKTA_AUTOUPDATE_DELAY_SEC", 120)))
    while True:
        try:
            _auto_update_state["running"] = True
            scrape_all(n_months=1)   # rafraîchissement léger périodique (1 mois glissant)

            # Re-scrape ciblé pour les états avec des tirages bloqués (>18h sans mise à jour)
            try:
                _retry_stale_states()
            except Exception as _se:
                print(f"  [stale-retry] error: {_se}")

            # Rafraîchit les données Pick 4 en même temps
            try:
                import scraper4
                scraper4.scrape_all4(states=scraper4.HOT_PICK4_STATES, n_months=1)
                _TRACK_RECORD4_CACHE.clear()
                _ACCURACY4_CACHE.clear()
            except Exception as e4:
                print(f"  [auto-update][pick4] error: {e4}")

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

            # Recalibrate dynamic weights for HOT states after each scrape
            try:
                from weight_calibrator import calibrate_if_needed
                from scraper import load_csv
                HOT_STATES = ["NY", "FL", "GA", "TX", "NJ", "PA", "IL", "OH"]
                for _st in HOT_STATES:
                    _draws = load_csv(_st)
                    if not _draws:
                        continue
                    _tods = list({d.get("tod", "Evening") for d in _draws})
                    for _tod in _tods:
                        _tod_draws = [d for d in _draws if d.get("tod", "Evening") == _tod]
                        if len(_tod_draws) >= 70:
                            calibrate_if_needed(_st, _tod, _tod_draws)
            except Exception as _we:
                print(f"  [auto-update][weights] error: {_we}")

            # Recalibrate Pick 4 dynamic weights
            try:
                from weight_calibrator4 import calibrate4_if_needed
                from scraper4 import load_csv4, HOT_PICK4_STATES
                for _st4 in HOT_PICK4_STATES:
                    _draws4 = load_csv4(_st4)
                    if not _draws4:
                        continue
                    _tods4 = list({d.get("tod", "Evening") for d in _draws4})
                    for _tod4 in _tods4:
                        _tod_draws4 = [d for d in _draws4 if d.get("tod", "Evening") == _tod4]
                        if len(_tod_draws4) >= 70:
                            calibrate4_if_needed(_st4, _tod4, _tod_draws4)
            except Exception as _we4:
                print(f"  [auto-update][weights4] error: {_we4}")

            # Recalibrate Cash 5 / Fantasy 5 lotto weights
            try:
                from weight_calibrator_lotto import calibrate_lotto_if_needed
                from games_scraper import load_game_results as _lgr
                _lotto_games = globals().get("LOTTO_GAMES", {})
                for _lstate, _lgames in _lotto_games.items():
                    for _lgame in _lgames:
                        _ldraws = _lgr(_lstate, _lgame["slug"])
                        if len(_ldraws) >= 50:
                            calibrate_lotto_if_needed(_lstate, _lgame["slug"], _ldraws)
            except Exception as _wel:
                print(f"  [auto-update][weights_lotto] error: {_wel}")

            _warm_popular_reports()  # pré-calcule les rapports des États les plus consultés
            try:
                _verify_draw_schedule()
            except Exception as se:
                print(f"  [schedule-check] error: {se}")
            try:
                with app.app_context():
                    _check_new_result_alerts()
            except Exception as ae:
                print(f"  [alerts] error: {ae}")
            try:
                with app.app_context():
                    _check_hotcold_alerts()
            except Exception as ae:
                print(f"  [alerts] error: {ae}")
            try:
                with app.app_context():
                    _check_custom_alerts()
            except Exception as ae:
                print(f"  [alerts] error: {ae}")
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
    try:
        _verify_draw_schedule()
    except Exception as e:
        print(f"  [schedule-check][initial] error: {e}")

_draw_watcher_triggered: dict[str, float] = {}  # "{state}_{tod}" -> epoch secs
_draw_watcher_lock = threading.Lock()

def _seconds_to_next_draw() -> float:
    """
    Calcule le nombre de secondes jusqu'au prochain tirage (tous États confondus).
    Retourne 300 (5 min) si le calcul échoue.
    """
    try:
        from draw_schedule import DRAW_SCHEDULE, _parse_schedule_time
        from zoneinfo import ZoneInfo
        from datetime import timezone as _tz, timedelta as _td

        now_utc = datetime.utcnow().replace(tzinfo=_tz.utc)
        min_delta = None

        for sessions in DRAW_SCHEDULE.values():
            for session in sessions:
                try:
                    hour, minute, tz_name = _parse_schedule_time(session["time"])
                    tz = ZoneInfo(tz_name)
                    now_local = now_utc.astimezone(tz)
                    draw_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if draw_local <= now_local:
                        draw_local += _td(days=1)
                    delta = (draw_local.astimezone(_tz.utc) - now_utc).total_seconds()
                    if min_delta is None or delta < min_delta:
                        min_delta = delta
                except Exception:
                    pass

        return max(30.0, min_delta or 300.0)
    except Exception:
        return 300.0


def _draw_watcher_loop():
    """
    Polling adaptatif basé sur les horaires de tirage :

    Situation                          → intervalle de polling
    ─────────────────────────────────────────────────────────
    > 20 min avant prochain tirage     → 10 min  (veille)
    5–20 min avant prochain tirage     → 2 min   (pré-tirage)
    0–15 min après tirage              → 1 min   (post-tirage rapide)
    15–45 min après tirage             → 3 min   (confirmation)
    > 45 min après tirage              → 10 min  (calme)

    Source 0 = official_scraper (sites officiels, 1-3 min de latence)
    puis fallback smart_scraper (lotteryusa → usamega → lotterypost)
    """
    time.sleep(60)  # laisse le serveur démarrer

    while True:
        try:
            from smart_scraper import get_states_due_now, scrape_state
            from draw_schedule import DRAW_SCHEDULE, _parse_schedule_time
            from zoneinfo import ZoneInfo
            from datetime import timezone as _dttz, timedelta as _td

            now_utc = datetime.utcnow().replace(tzinfo=_dttz.utc)
            now_epoch = time.time()

            # ── Calcul de la prochaine fenêtre de tirage ────────────────────
            secs_to_next = _seconds_to_next_draw()
            min_to_next  = secs_to_next / 60

            # ── Sauvegarder les prédictions PRÉ-TIRAGE (fenêtre -10 à -2 min) ─
            try:
                from draw_schedule import DRAW_SCHEDULE as _DS, _parse_schedule_time as _PST
                from zoneinfo import ZoneInfo as _ZI
                from live_track_record import save_prediction as _save_pred, get_pending_predictions
                _pre_saved = {f"{p['state']}_{p['tod']}_{p['date']}" for p in get_pending_predictions()}
                for _st, _sessions in _DS.items():
                    for _sess in _sessions:
                        try:
                            _h, _m, _tzn = _PST(_sess["time"])
                            _tz = _ZI(_tzn)
                            _nl = now_utc.astimezone(_tz)
                            _dl = _nl.replace(hour=_h, minute=_m, second=0, microsecond=0)
                            if _dl <= _nl:
                                _dl += timedelta(days=1)
                            _mins_to = (_dl.astimezone(_dttz.utc) - now_utc).total_seconds() / 60
                            _today = now_utc.strftime("%Y-%m-%d")
                            _pkey  = f"{_st}_{_sess['tod']}_{_today}"
                            # Fenêtre pré-tirage : 10 → 2 min avant
                            if 2 <= _mins_to <= 10 and _pkey not in _pre_saved:
                                _rep = _build_report(_st, _sess["tod"])
                                if _rep:
                                    _save_pred(_st, _sess["tod"], _rep)
                        except Exception:
                            pass
            except Exception as _lte:
                print(f"[draw-watcher][pre-draw-save] error: {_lte}")

            # ── États dont le tirage vient de passer (fenêtre post-tirage) ──
            due_rapid  = get_states_due_now(buffer_min=1,  window_min=15)
            due_normal = get_states_due_now(buffer_min=16, window_min=29)

            to_scrape_now = []
            with _draw_watcher_lock:
                for state, tod in due_rapid + due_normal:
                    key = f"{state}_{tod}"
                    last = _draw_watcher_triggered.get(key, 0)
                    min_cycle = 3 * 60 if (state, tod) in due_rapid else 45 * 60
                    if now_epoch - last > min_cycle:
                        _draw_watcher_triggered[key] = now_epoch
                        to_scrape_now.append((state, (state, tod) in due_rapid))

            # ── Scraping ciblé + vérification Track Record ──────────────────
            if to_scrape_now:
                unique = list(dict.fromkeys(s for s, _ in to_scrape_now))
                rapid_set = {s for s, rapid in to_scrape_now if rapid}
                print(f"[draw-watcher] scraping {unique} (rapide: {list(rapid_set)})")
                for st in unique:
                    try:
                        src = ["official", "lotteryusa", "usamega"] if st in rapid_set \
                              else ["lotteryusa", "usamega", "lotterypost"]
                        res = scrape_state(st, sources=src)
                        if res["added"] > 0:
                            keys_to_del = [k for k in list(_REPORT_CACHE.keys())
                                           if k.startswith(f"{st.lower()}|")]
                            for k in keys_to_del:
                                _REPORT_CACHE.pop(k, None)
                            _LATEST_CACHE["data"] = None
                            print(f"  [draw-watcher][{st}] +{res['added']} via {res['source']}")
                            # ── Broadcast SSE + Track Record Live ───────────
                            try:
                                from scraper import load_csv as _lcsv
                                _draws = _lcsv(st)
                                if _draws:
                                    for _new_d in _draws[:res["added"]]:
                                        _tod_of_draw = _new_d.get("tod", "Evening")
                                        # SSE → tous les clients connectés
                                        _broadcast_sse("new_draw", {
                                            "state":      st,
                                            "state_name": STATES.get(st, {}).get("name", st),
                                            "tod":        _tod_of_draw,
                                            "d1": _new_d["d1"], "d2": _new_d["d2"], "d3": _new_d["d3"],
                                            "date":       _new_d["date"],
                                            "source":     res["source"],
                                        })
                                        # Track Record Live
                                        _tr_result = None
                                        try:
                                            from live_track_record import record_result as _rec_res
                                            _tr_result = _rec_res(st, _tod_of_draw, _new_d)
                                        except Exception as _tre:
                                            print(f"  [draw-watcher][track-record][{st}] error: {_tre}")
                                        # ML Feedback — recalibration des poids si nécessaire
                                        try:
                                            def _recalib(_st=st, _tod=_tod_of_draw, _draws=_draws):
                                                from weight_calibrator import calibrate_if_needed
                                                from scraper import load_csv as _lc2
                                                _tod_draws = [d for d in _lc2(_st) if d.get("tod") == _tod]
                                                if len(_tod_draws) >= 70:
                                                    calibrate_if_needed(_st, _tod, _tod_draws)
                                            threading.Thread(target=_recalib, daemon=True).start()
                                        except Exception as _mle:
                                            print(f"  [draw-watcher][ml-feedback][{st}] error: {_mle}")
                                        # Push notification
                                        try:
                                            _sn = STATES.get(st, {}).get("name", st)
                                            _digs = f"{_new_d['d1']}-{_new_d['d2']}-{_new_d['d3']}"
                                            _tod_icon = "☀️" if _tod_of_draw == "Midday" else "🌙"
                                            _ptitle = f"🎯 {_sn} {_tod_icon} {_tod_of_draw}: {_digs}"
                                            if _tr_result and _tr_result.get("hit_straight"):
                                                _pbody = f"✅ EXACT ! Votre combo #1 était {_tr_result['consensus_top10'][0]}"
                                            elif _tr_result and _tr_result.get("hit_box"):
                                                _pbody = f"📦 BOX hit ! Rang #{_tr_result.get('consensus_box_rank','?')} · {_digs}"
                                            else:
                                                _pbody = f"Résultat officiel: {_digs}"
                                            _send_push_to_all(_ptitle, _pbody, f"/results?state={st}", state=st)
                                        except Exception as _pe:
                                            print(f"  [draw-watcher][push][{st}] error: {_pe}")
                            except Exception as _se:
                                print(f"  [draw-watcher][sse+tr][{st}] error: {_se}")
                    except Exception as e:
                        print(f"  [draw-watcher][{st}] error: {e}")
                    time.sleep(0.5)

            # ── Intervalle adaptatif ─────────────────────────────────────────
            if due_rapid:
                sleep_sec = 60          # post-tirage immédiat → 1 min
            elif due_normal:
                sleep_sec = 3 * 60      # post-tirage tardif → 3 min
            elif min_to_next <= 5:
                sleep_sec = 2 * 60      # pré-tirage imminent → 2 min
            elif min_to_next <= 20:
                sleep_sec = 3 * 60      # pré-tirage proche → 3 min
            else:
                sleep_sec = min(10 * 60, max(60, secs_to_next - 20 * 60))

            print(f"[draw-watcher] prochain tirage dans {min_to_next:.0f} min → pause {sleep_sec//60} min")

        except Exception as e:
            print(f"[draw-watcher] error: {e}")
            sleep_sec = 5 * 60

        time.sleep(sleep_sec)


def start_auto_update():
    if os.environ.get("PREDIKTA_DISABLE_AUTOUPDATE") == "1":
        return
    threading.Thread(target=_initial_warm_loop, daemon=True, name="predikta-warm-cache").start()
    t = threading.Thread(target=_auto_update_loop, daemon=True, name="predikta-auto-update")
    t.start()
    threading.Thread(target=_draw_watcher_loop, daemon=True, name="predikta-draw-watcher").start()

# Démarre seulement dans le processus principal (évite le double-lancement
# avec le reloader Flask en mode debug)
if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
    _ensure_vapid_keys()
    start_auto_update()

@app.route("/api/autoupdate/status")
def api_autoupdate_status():
    return jsonify({
        "enabled": os.environ.get("PREDIKTA_DISABLE_AUTOUPDATE") != "1",
        "interval_sec": _AUTO_UPDATE_INTERVAL,
        **_auto_update_state,
    })

# ── SSE — Server-Sent Events broadcaster ─────────────────────────────────
_sse_subscribers: list[queue.Queue] = []
_sse_lock = threading.Lock()

def _broadcast_sse(event_type: str, data: dict):
    """Pousse un événement SSE à tous les clients connectés."""
    payload = json.dumps(data, ensure_ascii=False, default=str)
    with _sse_lock:
        dead = []
        for q in _sse_subscribers:
            try:
                q.put_nowait({"event": event_type, "payload": payload})
            except queue.Full:
                dead.append(q)
        for q in dead:
            try: _sse_subscribers.remove(q)
            except ValueError: pass

@app.route("/api/results/stream")
def api_results_stream():
    """
    SSE endpoint — pousse les nouveaux tirages en temps réel vers le navigateur.
    Événements :
      connected   → confirmation de connexion
      new_draw    → {state, tod, d1, d2, d3, date, state_name}
      heartbeat   → keep-alive toutes les 25 s
    """
    def generate():
        client_q = queue.Queue(maxsize=30)
        with _sse_lock:
            _sse_subscribers.append(client_q)
        try:
            yield "data: {\"type\":\"connected\"}\n\n"
            while True:
                try:
                    msg = client_q.get(timeout=25)
                    yield f"event: {msg['event']}\ndata: {msg['payload']}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            with _sse_lock:
                try: _sse_subscribers.remove(client_q)
                except ValueError: pass

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",   # désactive le buffering Nginx / Render
            "Connection": "keep-alive",
        }
    )

@app.route("/api/track-record/live")
def api_track_record_live():
    """
    Track record PROSPECTIF — prédictions sauvegardées AVANT chaque tirage
    puis comparées au résultat réel. Différent du backtest /api/track-record.
    """
    state = request.args.get("state") or None
    days  = min(90, max(1, int(request.args.get("days", 30))))
    try:
        from live_track_record import get_stats
        return jsonify(get_stats(state=state, days=days))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/track-record/live/pending")
def api_track_record_pending():
    """Prédictions sauvegardées en attente de vérification (pré-tirage)."""
    try:
        from live_track_record import get_pending_predictions
        return jsonify({"pending": get_pending_predictions()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/confidence/summary")
def api_confidence_summary():
    """
    Retourne le top combo + confidence_pct pour chaque état déjà en cache.
    Zéro calcul ML — lecture seule du _REPORT_CACHE.
    Clé de réponse : { "NY_Midday": { combo, pct, label, models, cached_ago_min }, ... }
    """
    import time as _t
    now = _t.time()
    out = {}
    for cache_key, entry in list(_REPORT_CACHE.items()):
        data = entry.get("data", {})
        consensus = data.get("consensus") or []
        if not consensus:
            continue
        top = consensus[0]
        # Nombre de modèles ML qui ont voté pour ce combo
        breakdown = top.get("breakdown", {})
        model_contribs = breakdown.get("model_weights", {}) if breakdown else {}
        models_count = sum(1 for v in model_contribs.values() if v > 0) if model_contribs else None
        out[cache_key] = {
            "combo":     top.get("combo"),
            "pct":       top.get("confidence_pct"),
            "label":     top.get("confidence_label"),
            "models":    models_count,
            "cached_ago_min": round((now - entry["ts"]) / 60, 1),
        }
    return jsonify(out)

@app.route("/api/archive/verdicts")
def api_archive_verdicts():
    """Verdicts du track record live indexés par STATE_Tod_YYYY-MM-DD."""
    try:
        import json as _json
        _log_path = os.path.join("data", "live_track_record.json")
        try:
            with open(_log_path, encoding="utf-8") as _f:
                _log = _json.load(_f)
        except Exception:
            _log = []
        verdicts = {}
        for r in (_log if isinstance(_log, list) else []):
            k = f"{r.get('state','').upper()}_{r.get('tod','')}_{r.get('date','')}"
            verdicts[k] = {
                "actual":            r.get("actual"),
                "hit_straight":      r.get("hit_straight", False),
                "hit_box":           r.get("hit_box", False),
                "consensus_rank":    r.get("consensus_straight_rank"),
                "box_rank":          r.get("consensus_box_rank"),
                "top10":             r.get("consensus_top10", [])[:3],
                "verified_at":       r.get("verified_at"),
            }
        return jsonify(verdicts)
    except Exception as e:
        return jsonify({}), 200  # fail silently — archive page still works

@app.route("/api/scraper/status")
def api_scraper_status():
    """Stats des sources utilisées par le smart scraper (fiabilité par état)."""
    try:
        from smart_scraper import get_source_stats, get_states_due_now
        due = get_states_due_now(buffer_min=15, window_min=30)
    except Exception as e:
        return jsonify({"error": str(e)})
    with _draw_watcher_lock:
        triggered = dict(_draw_watcher_triggered)
    return jsonify({
        "source_stats": get_source_stats(),
        "states_due_now": [{"state": s, "tod": t} for s, t in due],
        "recently_triggered": {k: int(v) for k, v in triggered.items()},
    })

@app.route("/api/scraper/run", methods=["POST"])
def api_scraper_run():
    """Lance un scraping immédiat via smart_scraper pour un ou plusieurs états."""
    data = request.get_json(silent=True) or {}
    states = data.get("states") or []
    if not states:
        from scraper import STATES
        states = list(STATES.keys())
    def _bg():
        from smart_scraper import scrape_states_batch
        results = scrape_states_batch(states, delay=0.8)
        ok = sum(1 for r in results if r.get("ok"))
        added = sum(r.get("added", 0) for r in results)
        print(f"[api/scraper/run] {ok}/{len(results)} états OK, +{added} tirages")
        _REPORT_CACHE.clear()
        _LATEST_CACHE["data"] = None
    threading.Thread(target=_bg, daemon=True).start()
    return jsonify({"status": "started", "states": states, "count": len(states)})

# ── Draw schedule ─────────────────────────────────────────────────────────
from draw_schedule import DRAW_SCHEDULE, next_draw_session

_SCHEDULE_CHECK = {"last_run": None, "issues": []}

def _verify_draw_schedule():
    """Automated sanity check: compare DRAW_SCHEDULE's declared draw
    times-of-day against the tods actually observed in each state's recent
    data (last ~45 days). Catches drift like a state adding/dropping a draw
    or a 'tod' label mismatch (e.g. the VT 'Evening' vs 6:55 PM ET case)
    without needing a manual audit. Results are logged and exposed via
    /api/schedule-check."""
    issues = []
    cutoff = (datetime.now() - timedelta(days=45)).date()

    for code, sched in DRAW_SCHEDULE.items():
        sched_tods = {e["tod"] for e in sched}
        try:
            draws = load_csv(code)
        except Exception:
            continue
        if not draws:
            continue

        recent_tods = set()
        for d in draws:
            try:
                if datetime.strptime(d["date"], "%Y-%m-%d").date() >= cutoff:
                    recent_tods.add(d.get("tod", ""))
            except ValueError:
                continue

        extra_in_data = recent_tods - sched_tods
        extra_in_schedule = sched_tods - recent_tods
        if extra_in_data:
            issues.append({"state": code, "type": "tod_in_data_not_in_schedule", "tods": sorted(extra_in_data)})
        if extra_in_schedule:
            issues.append({"state": code, "type": "tod_in_schedule_not_in_data", "tods": sorted(extra_in_schedule)})

    for code in STATES:
        if code not in DRAW_SCHEDULE:
            try:
                draws = load_csv(code)
            except Exception:
                draws = []
            if draws:
                issues.append({"state": code, "type": "state_missing_from_schedule", "tods": []})

    _SCHEDULE_CHECK["last_run"] = datetime.utcnow().isoformat() + "Z"
    _SCHEDULE_CHECK["issues"] = issues
    if issues:
        print(f"  [schedule-check] {len(issues)} discrepancy(ies) found:")
        for it in issues:
            print(f"    - {it['state']}: {it['type']} {it['tods']}")
    else:
        print("  [schedule-check] OK — DRAW_SCHEDULE matches observed data for all states")
    return issues

@app.route("/api/schedule-check")
def api_schedule_check():
    return jsonify(_SCHEDULE_CHECK)

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

@app.route("/api/hot-pick3")
def hot_pick3():
    """Public lightweight endpoint: hottest Pick3 digits/combo per state + draw (tirage/date/heure)."""
    import analyzer

    try:
        limit = int(request.args.get("limit", "5"))
    except ValueError:
        limit = 5
    limit = max(1, min(limit, 12))

    entries = []
    for code in HOT_PICK3_STATES:
        try:
            draws = analyzer.load_draws(code)
        except Exception:
            continue
        if not draws:
            continue

        by_tod = defaultdict(list)
        for d in draws:
            by_tod[d.get("tod", "")].append(d)

        for tod, tdraws in by_tod.items():
            if not tdraws:
                continue
            hot30 = analyzer.hot_cold(tdraws, 30)
            hot_digits = sorted(
                (dg for dg, v in hot30.items() if v.get("status") == "HOT"),
                key=lambda dg: hot30[dg]["pct"], reverse=True
            )
            suggestions = analyzer.weighted_suggestions(tdraws, top_n=1, state_code=code, tod=tod)
            top = suggestions[0] if suggestions else None
            last_draw = tdraws[0]
            last_date = last_draw["date"]
            try:
                next_date = (datetime.strptime(last_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
            except ValueError:
                next_date = last_date
            entries.append({
                "state": code,
                "name": STATES[code]["name"],
                "tod": tod,
                "date": last_date,
                "last_result": f"{last_draw['d1']}{last_draw['d2']}{last_draw['d3']}",
                "next_date": next_date,
                "hot_digits": hot_digits[:5],
                "top_combo": top["combo"] if top else None,
                "confidence": top["confidence"] if top else None,
                "score": top["score"] if top else 0,
            })

    # Un seul tirage (le plus chaud) par État, dans l'ordre NY-FL-GA-TX-NJ-TN.
    best_by_state = {}
    for e in entries:
        cur = best_by_state.get(e["state"])
        if cur is None or e["score"] > cur["score"]:
            best_by_state[e["state"]] = e

    ordered = [best_by_state[code] for code in HOT_PICK3_STATES if code in best_by_state]
    return jsonify(ordered[:limit])

_TRACK_RECORD_CACHE = {}
_TRACK_RECORD_CACHE_TTL = int(os.environ.get("PREDIKTA_TRACK_RECORD_CACHE_SEC", 30 * 60))  # 30 min

@app.route("/api/track-record")
def api_track_record():
    """
    Transparency endpoint: for each state/tod, replay the last N draws and
    show what ZYNORIQ's TOP PICK would have suggested (using only data
    available before that draw) vs. what was actually drawn.
    """
    import analyzer

    try:
        n = int(request.args.get("n", "15"))
    except ValueError:
        n = 15
    n = max(1, min(n, 30))

    cache_key = n
    cached = _TRACK_RECORD_CACHE.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _TRACK_RECORD_CACHE_TTL:
        return jsonify(cached["data"])

    out = []
    grand_n = grand_straight = grand_box = 0
    for code in HOT_PICK3_STATES:
        draws = analyzer.load_draws(code)
        if not draws:
            continue

        by_tod = defaultdict(list)
        for d in draws:
            by_tod[d.get("tod", "")].append(d)

        tods_out = {}
        state_n = state_straight = state_box = 0
        for tod, tdraws in by_tod.items():
            rows = analyzer.backtest_suggestions(tdraws, n=n)
            if not rows:
                continue
            straight = sum(1 for r in rows if r["hit_straight"])
            box = sum(1 for r in rows if r["hit_box"])
            tods_out[tod] = {
                "rows": rows,
                "n": len(rows),
                "straight_hits": straight,
                "box_hits": box,
            }
            state_n += len(rows)
            state_straight += straight
            state_box += box

        if not tods_out:
            continue

        out.append({
            "state": code,
            "name": STATES[code]["name"],
            "tods": tods_out,
            "totals": {"n": state_n, "straight_hits": state_straight, "box_hits": state_box},
        })
        grand_n += state_n
        grand_straight += state_straight
        grand_box += state_box

    payload = {
        "states": out,
        "grand_totals": {"n": grand_n, "straight_hits": grand_straight, "box_hits": grand_box},
        "updated_at": datetime.now(tz=ZoneInfo("America/New_York")).isoformat(),
    }
    _TRACK_RECORD_CACHE[cache_key] = {"ts": time.time(), "data": payload}
    # Evict expired entries to prevent unbounded memory growth
    now_ts = time.time()
    expired = [k for k, v in _TRACK_RECORD_CACHE.items() if now_ts - v["ts"] > _TRACK_RECORD_CACHE_TTL]
    for k in expired:
        _TRACK_RECORD_CACHE.pop(k, None)
    return jsonify(payload)


_ACCURACY_CACHE = {}
_ACCURACY_CACHE_TTL = int(os.environ.get("PREDIKTA_ACCURACY_CACHE_SEC", 30 * 60))  # 30 min
ACCURACY_WINDOWS = [7, 30, 90]


@app.route("/api/accuracy")
def api_accuracy():
    """
    ZYNORIQ Accuracy Score: for each state, replay the last 7/30/90 draws
    per draw-time and compute straight & box hit rates vs. the random-chance
    baseline (~0.1% straight, ~0.6% box for Pick 3).
    """
    import analyzer

    cached = _ACCURACY_CACHE.get("data")
    if cached and (time.time() - cached["ts"]) < _ACCURACY_CACHE_TTL:
        return jsonify(cached["data"])

    max_n = max(ACCURACY_WINDOWS)
    out = []
    grand = {w: {"n": 0, "straight": 0, "box": 0} for w in ACCURACY_WINDOWS}

    for code in HOT_PICK3_STATES:
        draws = analyzer.load_draws(code)
        if not draws:
            continue

        by_tod = defaultdict(list)
        for d in draws:
            by_tod[d.get("tod", "")].append(d)

        state_totals = {w: {"n": 0, "straight": 0, "box": 0} for w in ACCURACY_WINDOWS}
        any_data = False
        for tod, tdraws in by_tod.items():
            rows = analyzer.backtest_suggestions(tdraws, n=max_n)
            if not rows:
                continue
            any_data = True
            for w in ACCURACY_WINDOWS:
                window_rows = rows[:w]
                n = len(window_rows)
                state_totals[w]["n"] += n
                state_totals[w]["straight"] += sum(1 for r in window_rows if r["hit_straight"])
                state_totals[w]["box"] += sum(1 for r in window_rows if r["hit_box"])

        if not any_data:
            continue

        out.append({"state": code, "name": STATES[code]["name"], "windows": state_totals})
        for w in ACCURACY_WINDOWS:
            grand[w]["n"] += state_totals[w]["n"]
            grand[w]["straight"] += state_totals[w]["straight"]
            grand[w]["box"] += state_totals[w]["box"]

    def rate(d, key):
        return (d[key] / d["n"] * 100) if d["n"] else 0.0

    best_states = sorted(
        (s for s in out if s["windows"][90]["n"] >= 20),
        key=lambda s: rate(s["windows"][90], "box"),
        reverse=True,
    )[:3]
    best_states = [{
        "state": s["state"], "name": s["name"],
        "n": s["windows"][90]["n"],
        "straight_rate": round(rate(s["windows"][90], "straight"), 2),
        "box_rate": round(rate(s["windows"][90], "box"), 2),
    } for s in best_states]

    payload = {
        "windows": ACCURACY_WINDOWS,
        "baseline": {"straight_pct": 0.1, "box_pct": 0.6},
        "states": out,
        "grand_totals": grand,
        "best_states": best_states,
        "updated_at": datetime.now(tz=ZoneInfo("America/New_York")).isoformat(),
    }
    _ACCURACY_CACHE["data"] = {"ts": time.time(), "data": payload}
    return jsonify(payload)

_TRACK_RECORD4_CACHE = {}
_ACCURACY4_CACHE = {}
_CACHE4_TTL = int(os.environ.get("PREDIKTA_TRACK_RECORD_CACHE_SEC", 30 * 60))


@app.route("/api/hot-pick4")
def hot_pick4():
    """Public endpoint: hottest Pick4 digits/combo per state."""
    import analyzer4
    from scraper4 import STATES4, HOT_PICK4_STATES

    try:
        limit = int(request.args.get("limit", "5"))
    except ValueError:
        limit = 5
    limit = max(1, min(limit, 12))

    entries = []
    for code in HOT_PICK4_STATES:
        if code not in STATES4:
            continue
        try:
            draws = analyzer4.load_draws4(code)
        except Exception:
            continue
        if not draws:
            continue

        by_tod = defaultdict(list)
        for d in draws:
            by_tod[d.get("tod", "")].append(d)

        for tod, tdraws in by_tod.items():
            if not tdraws:
                continue
            hot30 = analyzer4.hot_cold4(tdraws, 30)
            hot_digits = sorted(
                (dg for dg, v in hot30.items() if v.get("status") == "HOT"),
                key=lambda dg: hot30[dg]["pct"], reverse=True
            )
            suggestions = analyzer4.weighted_suggestions4(tdraws, top_n=1)
            top = suggestions[0] if suggestions else None
            last_draw = tdraws[0]
            last_date = last_draw["date"]
            try:
                next_date = (datetime.strptime(last_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()
            except ValueError:
                next_date = last_date
            entries.append({
                "state": code,
                "name": STATES4[code]["name"],
                "tod": tod,
                "date": last_date,
                "last_result": f"{last_draw['d1']}{last_draw['d2']}{last_draw['d3']}{last_draw['d4']}",
                "next_date": next_date,
                "hot_digits": hot_digits[:5],
                "top_combo": top["combo"] if top else None,
                "confidence": top["confidence"] if top else None,
                "score": top["score"] if top else 0,
            })

    best_by_state = {}
    for e in entries:
        cur = best_by_state.get(e["state"])
        if cur is None or e["score"] > cur["score"]:
            best_by_state[e["state"]] = e

    ordered = [best_by_state[code] for code in HOT_PICK4_STATES if code in best_by_state]
    return jsonify(ordered[:limit])


@app.route("/api/results-4/<state_code>")
def api_results4(state_code):
    """Latest Pick4 results for a state."""
    from scraper4 import load_csv4, STATES4
    code = state_code.upper()
    if code not in STATES4:
        return jsonify({"error": f"Unknown Pick4 state: {code}"}), 404
    try:
        n = int(request.args.get("n", "30"))
    except ValueError:
        n = 30
    draws = load_csv4(code)
    return jsonify({"state": code, "name": STATES4[code]["name"], "draws": draws[:n]})


@app.route("/api/report-4/<state_code>")
@auth_module.subscription_required
def api_report4(state_code):
    """Full Pick4 statistical report — uses ml_engine4 for full ML ensemble."""
    from scraper4 import STATES4, load_csv4
    code = state_code.upper()
    if code not in STATES4:
        return jsonify({"error": f"Unknown Pick4 state: {code}"}), 404

    draws = load_csv4(code)
    if not draws:
        return jsonify({"error": f"No Pick4 data for {code}. Run scraper first."}), 200

    try:
        import ml_engine4
        result = ml_engine4.run_all_models4(draws)
    except Exception as e:
        import analyzer4
        result = analyzer4.full_report4(code, draws)
        result["ml_error"] = str(e)

    result["state"] = code
    result["state_name"] = STATES4[code]["name"]
    result["total_draws"] = len(draws)
    result["last_draw"] = draws[0] if draws else None
    return jsonify(result)


@app.route("/api/track-record-4")
def api_track_record4():
    """Pick4 track record: backtest last N draws per state."""
    import analyzer4
    from scraper4 import STATES4, HOT_PICK4_STATES

    try:
        n = int(request.args.get("n", "15"))
    except ValueError:
        n = 15
    n = max(1, min(n, 30))

    cached = _TRACK_RECORD4_CACHE.get(n)
    if cached and (time.time() - cached["ts"]) < _CACHE4_TTL:
        return jsonify(cached["data"])

    out = []
    grand_n = grand_straight = grand_box = 0
    for code in HOT_PICK4_STATES:
        if code not in STATES4:
            continue
        draws = analyzer4.load_draws4(code)
        if not draws:
            continue

        by_tod = defaultdict(list)
        for d in draws:
            by_tod[d.get("tod", "")].append(d)

        tods_out = {}
        state_n = state_straight = state_box = 0
        for tod, tdraws in by_tod.items():
            rows = analyzer4.backtest_suggestions4(tdraws, n=n)
            if not rows:
                continue
            straight = sum(1 for r in rows if r["hit_straight"])
            box = sum(1 for r in rows if r["hit_box"])
            tods_out[tod] = {"rows": rows, "n": len(rows), "straight_hits": straight, "box_hits": box}
            state_n += len(rows)
            state_straight += straight
            state_box += box

        if not tods_out:
            continue

        out.append({
            "state": code,
            "name": STATES4[code]["name"],
            "tods": tods_out,
            "totals": {"n": state_n, "straight_hits": state_straight, "box_hits": state_box},
        })
        grand_n += state_n
        grand_straight += state_straight
        grand_box += state_box

    payload = {
        "states": out,
        "grand_totals": {"n": grand_n, "straight_hits": grand_straight, "box_hits": grand_box},
        "updated_at": datetime.now(tz=ZoneInfo("America/New_York")).isoformat(),
    }
    _TRACK_RECORD4_CACHE[n] = {"ts": time.time(), "data": payload}
    return jsonify(payload)


@app.route("/api/accuracy-4")
def api_accuracy4():
    """Pick4 accuracy score: backtest windows 7/30/90."""
    import analyzer4
    from scraper4 import STATES4, HOT_PICK4_STATES

    cached = _ACCURACY4_CACHE.get("data")
    if cached and (time.time() - cached["ts"]) < _CACHE4_TTL:
        return jsonify(cached["data"])

    WINDOWS = [7, 30, 90]
    max_n = max(WINDOWS)
    out = []
    grand = {w: {"n": 0, "straight": 0, "box": 0} for w in WINDOWS}

    for code in HOT_PICK4_STATES:
        if code not in STATES4:
            continue
        draws = analyzer4.load_draws4(code)
        if not draws:
            continue

        by_tod = defaultdict(list)
        for d in draws:
            by_tod[d.get("tod", "")].append(d)

        state_totals = {w: {"n": 0, "straight": 0, "box": 0} for w in WINDOWS}
        any_data = False
        for tod, tdraws in by_tod.items():
            rows = analyzer4.backtest_suggestions4(tdraws, n=max_n)
            if not rows:
                continue
            any_data = True
            for w in WINDOWS:
                window_rows = rows[:w]
                n = len(window_rows)
                state_totals[w]["n"] += n
                state_totals[w]["straight"] += sum(1 for r in window_rows if r["hit_straight"])
                state_totals[w]["box"] += sum(1 for r in window_rows if r["hit_box"])

        if not any_data:
            continue

        out.append({"state": code, "name": STATES4[code]["name"], "windows": state_totals})
        for w in WINDOWS:
            grand[w]["n"] += state_totals[w]["n"]
            grand[w]["straight"] += state_totals[w]["straight"]
            grand[w]["box"] += state_totals[w]["box"]

    payload = {
        "windows": WINDOWS,
        "baseline": {"straight_pct": 0.01, "box_pct": 0.06},
        "states": out,
        "grand_totals": grand,
        "updated_at": datetime.now(tz=ZoneInfo("America/New_York")).isoformat(),
    }
    _ACCURACY4_CACHE["data"] = {"ts": time.time(), "data": payload}
    return jsonify(payload)


@app.route("/api/scrape-4", methods=["POST", "GET"])
def api_scrape4():
    """Trigger Pick4 scrape for one or all states."""
    import scraper4

    state = request.args.get("state", "").upper()
    if state and state not in scraper4.STATES4:
        return jsonify({"error": f"Unknown Pick4 state: {state}"}), 400

    def _run():
        targets = [state] if state else list(scraper4.HOT_PICK4_STATES)
        for code in targets:
            draws = scraper4.fetch_state4(code)
            if draws:
                scraper4.save_csv4(code, draws)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"status": "started", "states": [state] if state else list(scraper4.HOT_PICK4_STATES)})


@app.route("/track-record")
def track_record_page(): return send_from_directory("static", "track-record.html")

@app.route("/track-record-4")
def track_record4_page(): return send_from_directory("static", "track-record-4.html")

@app.route("/analyze")
def analyze():         return send_from_directory("static", "index.html")

@app.route("/presentation")
def presentation():    return send_from_directory("static", "presentation.html")

@app.route("/results")
def results_page(): return send_from_directory("static", "results.html")

@app.route("/pro")
def pro_page():    return send_from_directory("static", "pro.html")

@app.route("/onboarding")
def onboarding_page(): return send_from_directory("static", "onboarding.html")

@app.route("/about")
def about_page():  return send_from_directory("static", "about.html")

@app.route("/faq")
def faq_page():    return send_from_directory("static", "faq.html")

@app.route("/contact")
def contact_page(): return send_from_directory("static", "contact.html")

@app.route("/archives")
def archives_page(): return send_from_directory("static", "archives.html")

@app.route("/api/admin/system")
def api_admin_system():
    """Dashboard admin — métriques système en temps réel. Protégé par ADMIN_TOKEN."""
    _token = os.environ.get("ADMIN_TOKEN", "")
    _req_token = request.headers.get("X-Admin-Token", "") or request.args.get("token", "")
    if not _token or not hmac.compare_digest(_req_token, _token):
        return jsonify({"error": "unauthorized"}), 401

    import time as _time

    # Push subscribers
    try:
        with open(_PUSH_SUBS_FILE, encoding="utf-8") as _f:
            _subs = json.load(_f)
        push_count = len(_subs) if isinstance(_subs, list) else 0
    except Exception:
        push_count = 0

    # SSE connections
    with _sse_lock:
        sse_count = len(_sse_subscribers)

    # Report cache
    cache_size = len(_REPORT_CACHE)
    cache_keys = list(_REPORT_CACHE.keys())[:20]

    # Draw watcher — derniers tirages reçus
    with _draw_watcher_lock:
        triggered = dict(_draw_watcher_triggered)

    recent_draws = sorted(
        [{"key": k, "ts": int(v), "ago_min": round((_time.time() - v) / 60, 1)}
         for k, v in triggered.items()],
        key=lambda x: x["ts"], reverse=True
    )[:20]

    # Scraper source stats
    try:
        from smart_scraper import get_source_stats, get_states_due_now
        source_stats = get_source_stats()
        states_due = [{"state": s, "tod": t} for s, t in get_states_due_now(buffer_min=15, window_min=30)]
    except Exception as _e:
        source_stats = {}
        states_due = []

    # Live track record pending
    try:
        from live_track_record import get_pending_predictions
        pending_preds = len(get_pending_predictions())
    except Exception:
        pending_preds = 0

    # Uptime approx (process start time)
    try:
        import psutil, os as _os
        _proc = psutil.Process(_os.getpid())
        uptime_sec = int(_time.time() - _proc.create_time())
    except Exception:
        uptime_sec = None

    # ML calibration stats
    try:
        import glob as _glob
        _w_dir = os.path.join("data", "weights")
        _w_files = _glob.glob(os.path.join(_w_dir, "*.json"))
        calib_entries = []
        for _wf in sorted(_w_files)[:30]:
            try:
                with open(_wf, encoding="utf-8") as _f:
                    _wd = json.load(_f)
                _m = _wd.get("meta", {})
                calib_entries.append({
                    "key": os.path.basename(_wf).replace(".json", ""),
                    "weights": _wd.get("weights", {}),
                    "draw_count": _m.get("draw_count"),
                    "window": _m.get("window"),
                    "avg_rank": _m.get("avg_rank_percentile", {}),
                })
            except Exception:
                pass
    except Exception:
        calib_entries = []

    return jsonify({
        "ts": _time.time(),
        "push_subscribers": push_count,
        "sse_connections": sse_count,
        "report_cache_entries": cache_size,
        "pending_predictions": pending_preds,
        "recent_draws": recent_draws,
        "states_due_now": states_due,
        "source_stats": source_stats,
        "uptime_sec": uptime_sec,
        "ml_calibrations": calib_entries,
    })

@app.route("/parrainage")
def referral_page(): return send_from_directory("static", "referral.html")

@app.route("/login")
def login_page(): return send_from_directory("static", "login.html")

@app.route("/register")
def register_page(): return send_from_directory("static", "register.html")

@app.route("/forgot-password")
def forgot_password_page(): return send_from_directory("static", "forgot-password.html")

@app.route("/reset-password")
def reset_password_page(): return send_from_directory("static", "reset-password.html")

@app.route("/account")
def account_page(): return send_from_directory("static", "account.html")

@app.route("/privacy")
def privacy_page(): return send_from_directory("static", "privacy.html")

@app.route("/terms")
def terms_page():  return send_from_directory("static", "terms.html")

@app.route("/responsible-gaming")
def responsible_gaming_page(): return send_from_directory("static", "responsible-gaming.html")

@app.route("/accuracy")
def accuracy_page(): return send_from_directory("static", "accuracy.html")

@app.route("/offline")
def offline_page(): return send_from_directory("static", "offline.html")

@app.route("/lottery-predictions")
def lottery_predictions_page(): return send_from_directory("static", "lottery-predictions.html")

@app.route("/pick3-predictions")
def pick3_predictions_page(): return send_from_directory("static", "pick3-predictions.html")

@app.route("/pick4-predictions")
@app.route("/pick4")
def pick4_predictions_page(): return send_from_directory("static", "pick4-predictions.html")

@app.route("/powerball-analysis")
def powerball_analysis_page(): return send_from_directory("static", "powerball-analysis.html")

@app.route("/business-ai")
def business_ai_page(): return send_from_directory("static", "business-ai.html")

@app.route("/api")
def api_info_page(): return send_from_directory("static", "api.html")

@app.route("/world-map")
def world_map_page(): return send_from_directory("static", "world-map.html")

@app.route("/predikta-tv")
@app.route("/zynoriq-tv")
def zynoriq_tv_page(): return send_from_directory("static", "predikta-tv.html")

@app.route("/community")
def community_page(): return send_from_directory("static", "community.html")

@app.route("/founders")
def founders_page(): return send_from_directory("static", "founders.html")

@app.route("/ambassadors")
def ambassadors_page(): return send_from_directory("static", "ambassadors.html")

@app.route("/blog")
def blog_index_page(): return send_from_directory("static", "blog.html")

@app.route("/blog/chaines-markov-loterie")
def blog_markov_page(): return send_from_directory("static", "blog-markov.html")

@app.route("/blog/simulation-monte-carlo-loterie")
def blog_montecarlo_page(): return send_from_directory("static", "blog-montecarlo.html")

@app.route("/blog/guide-predictions-pick3-ia")
def blog_pick3_guide_page(): return send_from_directory("static", "blog-pick3-guide.html")

@app.route("/blog/guide-analyse-powerball-ia")
def blog_powerball_guide_page(): return send_from_directory("static", "blog-powerball-guide.html")

@app.route("/blog/loterie-floride-predictions")
def blog_florida_page(): return send_from_directory("static", "blog-florida.html")

@app.route("/blog/loterie-californie-predictions")
def blog_california_page(): return send_from_directory("static", "blog-california.html")

@app.route("/tracking.js")
def tracking_js():
    resp = make_response(send_from_directory("static", "tracking.js"))
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return resp

@app.route("/favicon.svg")
def favicon_svg():
    return send_from_directory("static", "favicon.svg", mimetype="image/svg+xml")

@app.route("/nav.js")
def nav_js():
    resp = make_response(send_from_directory("static", "nav.js"))
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return resp


@app.route("/pwa-prompt.js")
def pwa_prompt_js():
    resp = make_response(send_from_directory("static", "pwa-prompt.js"))
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

@app.route("/og-image.png")
def og_image():    return send_from_directory("static", "og-image.png")


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


# ── Founders Program (500 places) ─────────────────────────────────────────
FOUNDERS_MAX = 500

@app.route("/api/founders/status")
def api_founders_status():
    _, User = auth_module.db, auth_module.User
    count = User.query.filter(User.founder_badge == True).count()
    return jsonify({"total": FOUNDERS_MAX, "claimed": count, "remaining": FOUNDERS_MAX - count})

@app.route("/api/founders/claim", methods=["POST"])
@auth_module.login_required
def api_founders_claim():
    user = auth_module.current_user()
    if user.founder_badge:
        return jsonify({"error": "already_founder", "number": user.founder_number})
    _, User = auth_module.db, auth_module.User
    count = User.query.filter(User.founder_badge == True).count()
    if count >= FOUNDERS_MAX:
        return jsonify({"error": "sold_out"}), 410
    user.founder_badge = True
    user.founder_number = count + 1
    auth_module.db.session.commit()
    return jsonify({"success": True, "number": user.founder_number, "remaining": FOUNDERS_MAX - count - 1})


# ── Social Proof (public, cached) ─────────────────────────────────────────
_SOCIAL_PROOF_CACHE = {"ts": 0, "data": None}

@app.route("/api/social-proof")
def api_social_proof():
    now = time.time()
    if _SOCIAL_PROOF_CACHE["data"] and (now - _SOCIAL_PROOF_CACHE["ts"]) < 300:
        return jsonify(_SOCIAL_PROOF_CACHE["data"])
    _, User = auth_module.db, auth_module.User
    total_users = User.query.count()
    total_analyses = sum(
        getattr(u, 'usage_count', 0) or 0 for u in User.query.all()
    )
    data = {
        "users": total_users,
        "states": len(STATES),
        "algorithms": 7,
        "analyses": max(total_analyses, total_users * 3),
        "countries": min(total_users // 2 + 1, 25),
        "languages": 5,
    }
    _SOCIAL_PROOF_CACHE.update({"ts": now, "data": data})
    return jsonify(data)


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
_REPORT_CACHE_TTL = int(os.environ.get("PREDIKTA_REPORT_CACHE_SEC", 30 * 60))  # 30 min

# États les plus consultés — pré-calculés en arrière-plan après chaque
# scraping pour que le 1er clic utilisateur tombe déjà en cache (évite
# l'attente de 15-25s sur les états les plus populaires).
PRIORITY_STATES = ['NY','FL','GA','TX','NJ','TN','CA','PA','IL','OH','VA']

# États retenus pour le Top 6 Pick3 "les plus chauds" de la page d'accueil.
HOT_PICK3_STATES = ['NY','FL','GA','TX','NJ','TN']

def _build_report(state: str, tod_filter: str = "all", exclude_dow: tuple = (), exclude_dom: tuple = (), with_lstm: bool = False):
    """Compute (or raise) the analysis report for a state/tod. Returns dict or None if no data.
    with_lstm=True uniquement pour le pré-cache background (_warm_popular_reports).
    """
    draws = load_csv(state)
    if not draws:
        return None

    if tod_filter != "all":
        draws = [d for d in draws if d.get("tod","").lower() == tod_filter.lower()]
        if not draws:
            return None

    if exclude_dow:
        draws = [d for d in draws if datetime.strptime(d["date"], "%Y-%m-%d").weekday() not in exclude_dow]
        if not draws:
            return None

    if exclude_dom:
        draws = [d for d in draws if int(d["date"][8:10]) not in exclude_dom]
        if not draws:
            return None

    result = run_all_models(draws, with_lstm=with_lstm)
    result["state"]       = state
    result["state_name"]  = STATES[state]["name"]
    result["tod_filter"]  = tod_filter
    result["exclude_dow"] = list(exclude_dow)
    result["exclude_dom"] = list(exclude_dom)
    result["dpd"]         = STATES[state].get("dpd", 2)
    result["schedule"]    = DRAW_SCHEDULE.get(state, [])
    result["updated_at"]  = _data_updated_at(state)
    result["cached"]      = False
    return result

def _warm_popular_reports():
    """Pre-compute & cache the 'all' report for the most popular states."""
    now = time.time()
    for state in PRIORITY_STATES:
        cache_key = (state, "all", (), ())
        cached = _REPORT_CACHE.get(cache_key)
        if cached and (now - cached["ts"]) < _REPORT_CACHE_TTL:
            continue
        try:
            result = _build_report(state, "all", with_lstm=True)
            if result:
                _REPORT_CACHE[cache_key] = {"ts": time.time(), "data": {**result, "cached": True}}
        except Exception as e:
            print(f"  [warm-cache][{state}] error: {e}")

def _parse_int_list(raw: str, lo: int, hi: int) -> tuple:
    out = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            v = int(part)
        except ValueError:
            continue
        if lo <= v <= hi:
            out.add(v)
    return tuple(sorted(out))

@app.route("/api/report")
@auth_module.subscription_required
def api_report():
    state       = request.args.get("state", "NY").upper()
    tod_filter  = request.args.get("tod", "all")
    exclude_dow = _parse_int_list(request.args.get("exclude_dow", ""), 0, 6)
    exclude_dom = _parse_int_list(request.args.get("exclude_dom", ""), 1, 31)

    if state not in STATES:
        return jsonify({"error": f"Unknown state: {state}"}), 400

    cache_key = (state, tod_filter, exclude_dow, exclude_dom)
    cached = _REPORT_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - cached["ts"]) < _REPORT_CACHE_TTL:
        auth_module.record_usage(auth_module.current_user().id)
        return jsonify(cached["data"])

    if not load_csv(state):
        return jsonify({"error": f"No data for {state}. Click Scrape first."}), 200

    result = _build_report(state, tod_filter, exclude_dow, exclude_dom)
    if result is None:
        return jsonify({"error": f"No draws left for {state} after applying filters."}), 200

    _REPORT_CACHE[cache_key] = {"ts": now, "data": {**result, "cached": True}}
    # Evict expired entries to prevent unbounded memory growth
    _expired_r = [k for k, v in _REPORT_CACHE.items() if now - v["ts"] > _REPORT_CACHE_TTL]
    for k in _expired_r:
        _REPORT_CACHE.pop(k, None)
    user = auth_module.current_user()
    auth_module.record_usage(user.id)
    try:
        _mem.track_activity(user.id, "analysis", state=state, game="pick3")
    except Exception:
        pass
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

def _data_updated_at(code):
    """Horodatage (ISO, heure US/Eastern) de la dernière écriture du CSV
    de cet État — sert d'indicateur de fraîcheur des données scrapées."""
    path = os.path.join(DATA_DIR, f"{code.lower()}.csv")
    try:
        ts = os.path.getmtime(path)
    except OSError:
        return None
    return datetime.fromtimestamp(ts, tz=ZoneInfo("America/New_York")).isoformat()


@app.route("/api/states")
def api_states():
    result = {}
    for code, cfg in STATES.items():
        draws = load_csv(code)
        # Tirages réellement disponibles pour cet État (Matin/Midi/Soir/Nuit
        # selon les données réelles — optimisé et à jour par État)
        tods_from_data = {d.get("tod","") for d in draws if d.get("tod")}
        tods_from_sched = {s["tod"] for s in DRAW_SCHEDULE.get(code, [])}
        tods = sorted(tods_from_data | tods_from_sched,
                      key=lambda t: TOD_ORDER.get(t, 99))
        result[code] = {
            "name":       cfg["name"],
            "slug":       cfg["slug"],
            "dpd":        cfg.get("dpd", 2),
            "draws":      len(draws),
            "last_draw":  draws[0] if draws else None,
            "flag":       STATE_FLAGS.get(code, "🎰"),
            "schedule":   DRAW_SCHEDULE.get(code, []),
            "tods":       tods,
            "updated_at": _data_updated_at(code),
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

    # Les tirages sont datés en heure US (ET) ; le serveur (Render) tourne en UTC,
    # donc date.today() peut déjà être "demain" par rapport aux dates des tirages US.
    today_us      = datetime.now(ZoneInfo("America/New_York")).date()
    today_str     = today_us.isoformat()
    yesterday_str = (today_us - timedelta(days=1)).isoformat()
    result = {}

    for code, cfg in STATES.items():
        draws = load_csv(code)
        if not draws:
            result[code] = {
                "name": cfg["name"], "flag": STATE_FLAGS.get(code,"🎰"),
                "schedule": DRAW_SCHEDULE.get(code,[]),
                "latest": [], "has_data": False,
                "updated_at": _data_updated_at(code),
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
            "updated_at":  _data_updated_at(code),
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
# API — COMMUNAUTÉ / COMMENTAIRES
# ═══════════════════════════════════════════════════════════

COMMENT_MAX_LEN = 500


@app.route("/api/comments/<state_code>")
def api_comments_list(state_code):
    state_code = state_code.upper()
    if state_code not in STATES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400

    db = auth_module.db
    user = auth_module.current_user()
    comments = (
        db.session.query(auth_module.Comment)
        .filter_by(state_code=state_code)
        .order_by(auth_module.Comment.created_at.desc())
        .limit(50)
        .all()
    )
    out = []
    for c in comments:
        d = c.to_dict()
        d["is_own"] = bool(user and user.id == c.user_id)
        out.append(d)
    return jsonify({"comments": out, "total": len(out)})


@app.route("/api/comments/<state_code>", methods=["POST"])
@auth_module.login_required
def api_comments_post(state_code):
    state_code = state_code.upper()
    if state_code not in STATES:
        return jsonify({"error": f"Unknown state: {state_code}"}), 400

    user = auth_module.current_user()
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "empty", "message": "Le commentaire est vide."}), 400
    if len(body) > COMMENT_MAX_LEN:
        return jsonify({"error": "too_long", "message": f"Le commentaire dépasse {COMMENT_MAX_LEN} caractères."}), 400

    db = auth_module.db
    comment = auth_module.Comment(user_id=user.id, state_code=state_code, body=body)
    db.session.add(comment)
    db.session.commit()
    d = comment.to_dict()
    d["is_own"] = True
    return jsonify(d), 201


@app.route("/api/comments/<int:comment_id>", methods=["DELETE"])
@auth_module.login_required
def api_comments_delete(comment_id):
    db = auth_module.db
    user = auth_module.current_user()
    comment = db.session.get(auth_module.Comment, comment_id)
    if not comment:
        return jsonify({"error": "not_found"}), 404
    if comment.user_id != user.id and not user.is_admin:
        return jsonify({"error": "forbidden"}), 403
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"ok": True})


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

@app.route("/cash5")
def cash5_page(): return send_from_directory("static", "cash5.html")

# Multi-ball lotto games supported on the Cash 5 page
LOTTO_GAMES = {
    "CA": [{"slug": "fantasy5",      "label": "Fantasy 5",      "pool": 39}],
    "FL": [{"slug": "fantasy5",      "label": "Fantasy 5",      "pool": 36}],
    "GA": [{"slug": "fantasy5",      "label": "Fantasy 5",      "pool": 42}],
    "MI": [{"slug": "fantasy5",      "label": "Fantasy 5",      "pool": 47}],
    "NC": [{"slug": "cash5",         "label": "Cash 5",         "pool": 43}],
    "NJ": [{"slug": "cash5",         "label": "Cash 5",         "pool": 45}, {"slug": "jersey-cash-5", "label": "Jersey Cash 5", "pool": 45}],
    "NY": [{"slug": "take5",         "label": "Take 5",         "pool": 39}, {"slug": "take5-midday",  "label": "Take 5 Midday", "pool": 39}],
    "OH": [{"slug": "rolling-cash-5","label": "Rolling Cash 5", "pool": 35}],
    "PA": [{"slug": "cash5",         "label": "Cash 5",         "pool": 43}],
    "TX": [{"slug": "cash5",         "label": "Cash 5",         "pool": 35}],
    "VA": [{"slug": "cash5",         "label": "Cash 5",         "pool": 45},
           {"slug": "bank-a-million","label": "Bank a Million", "pool": 40}],
    "MA": [{"slug": "masscash",      "label": "Mass Cash",      "pool": 35}],
    "MD": [{"slug": "bonus-match-5", "label": "Bonus Match 5",  "pool": 39}],
}

@app.route("/api/cash5/states")
def api_cash5_states():
    """Return list of states+games available on the Cash 5 page."""
    from games_scraper import load_game_results
    result = []
    for state_code, games in LOTTO_GAMES.items():
        state_name = STATES.get(state_code, {}).get("name", state_code)
        for g in games:
            draws = load_game_results(state_code, g["slug"])
            result.append({
                "state": state_code,
                "name": state_name,
                "slug": g["slug"],
                "label": g["label"],
                "pool": g["pool"],
                "total_draws": len(draws),
            })
    return jsonify(sorted(result, key=lambda x: (x["name"], x["label"])))

@app.route("/api/cash5/<state_code>/<slug>")
def api_cash5_report(state_code, slug):
    """Full statistical report for a multi-ball Cash5/Fantasy5/Take5 game."""
    import analyzer_lotto
    from games_scraper import load_game_results
    code = state_code.upper()
    draws = load_game_results(code, slug)
    if not draws:
        return jsonify({"error": f"No data for {code}/{slug}. Scrape first."}), 200
    # Exclude digit games (numbers 0-9 only)
    if all(int(n) <= 9 for d in draws[:20] for n in d.get("nums", []) if n.isdigit()):
        return jsonify({"error": f"{slug} is a digit game — use the Pick 5 analyzer instead."}), 200
    result = analyzer_lotto.full_report(draws, state_code=code, slug=slug)
    result["state_name"] = STATES.get(code, {}).get("name", code)
    game_info = next((g for g in LOTTO_GAMES.get(code, []) if g["slug"] == slug), {})
    result["label"] = game_info.get("label", slug)
    return jsonify(result)

@app.route("/api/cash5/<state_code>/<slug>/track-record")
def api_cash5_track(state_code, slug):
    """Backtest track record for a multi-ball game."""
    import analyzer_lotto
    from games_scraper import load_game_results
    code = state_code.upper()
    try:
        n = int(request.args.get("n", "15"))
    except ValueError:
        n = 15
    n = max(1, min(n, 30))
    draws = load_game_results(code, slug)
    if not draws:
        return jsonify({"error": "No data"}), 200
    rows = analyzer_lotto.backtest(draws, n=n)
    game_info = next((g for g in LOTTO_GAMES.get(code, []) if g["slug"] == slug), {})
    return jsonify({
        "state": code,
        "slug": slug,
        "label": game_info.get("label", slug),
        "rows": rows,
        "hit3": sum(1 for r in rows if r["hit_3"]),
        "hit4": sum(1 for r in rows if r["hit_4"]),
        "hit5": sum(1 for r in rows if r["hit_5"]),
        "n": len(rows),
    })

# ── Pick 5 Digit Game (FL/OH/PA) ─────────────────────────────────────────
# 5 independent digit positions 0-9, displayed as "d1d2d3-d4d5" format.
# Uses analyzer_multi.py (n=5), separate from the multi-ball cash5 engine.

PICK5_DIGIT_STATES = {
    "FL": [
        {"slug": "pick5",        "label": "Pick 5 Evening", "tod": "Evening"},
        {"slug": "pick5-midday", "label": "Pick 5 Midday",  "tod": "Midday"},
    ],
    "OH": [
        {"slug": "pick5", "label": "Pick 5 Evening", "tod": "Evening"},
    ],
    "PA": [
        {"slug": "pick5",        "label": "Pick 5 Evening", "tod": "Evening"},
        {"slug": "pick5-midday", "label": "Pick 5 Midday",  "tod": "Midday"},
    ],
}

def _fmt_p5(nums):
    """Format 5 digits as 'ddd-dd'."""
    if not nums or len(nums) < 5:
        return "".join(str(n) for n in nums)
    return f"{''.join(str(n) for n in nums[:3])}-{''.join(str(n) for n in nums[3:5])}"

def _fmt_p5c2(nums):
    """Combo 2: swap last two digits for box coverage."""
    if not nums or len(nums) < 5:
        return "".join(str(n) for n in nums)
    return f"{''.join(str(n) for n in nums[:3])}-{nums[4]}{nums[3]}"

@app.route("/pick5")
def pick5_page():
    return send_from_directory("static", "pick5.html")

@app.route("/api/pick5/states")
def api_pick5_states():
    result = {}
    for code, games in PICK5_DIGIT_STATES.items():
        result[code] = games
    return jsonify(result)

@app.route("/api/pick5/<state_code>/<slug>")
def api_pick5_report(state_code, slug):
    import analyzer_multi
    from games_scraper import load_game_results
    code = state_code.upper()
    if code not in PICK5_DIGIT_STATES:
        return jsonify({"error": f"State {code} not supported for Pick 5"}), 400
    draws = load_game_results(code, slug)
    if not draws:
        return jsonify({"error": "No data"}), 200
    # Filter to draws that actually have exactly 5 digits (guard against mixed/malformed data)
    draws = [d for d in draws if len(d.get("nums", [])) == 5]
    if not draws:
        return jsonify({"error": "No valid 5-digit draws found"}), 200

    report = analyzer_multi.full_report(draws, n=5)

    # Enrich suggestions with digit field in breakdown
    suggs = report.get("suggestions", [])
    for s in suggs:
        raw_nums = s.get("combo", "").replace("-", "")
        # combo from analyzer_multi is "d1-d2-d3-d4-d5", rebuild as list
        nums = s.get("combo", "").split("-")
        s["combo1_fmt"] = _fmt_p5(nums)
        s["combo2_fmt"] = _fmt_p5c2(nums)
        # tag each breakdown entry with digit
        for i, b in enumerate(s.get("breakdown", [])):
            b["digit"] = nums[i] if i < len(nums) else "?"

    # Build per-position frequency maps
    per_pos = {}
    for pi in range(5):
        per_pos[f"d{pi+1}"] = analyzer_multi.digit_frequencies(draws, pos=pi, n=5)

    # Backtest with formatted combos
    backtest_rows = report.get("backtest", [])
    # If analyzer_multi doesn't include backtest, compute from suggestions
    # We do a simple last-15-draws comparison
    def _backtest_p5(draws, n=15, min_hist=60):
        rows = []
        for i in range(min(n, len(draws))):
            history = draws[i+1:]
            if len(history) < min_hist:
                break
            sugg = analyzer_multi.weighted_suggestions(history, n=5, top_n=1)
            if not sugg:
                continue
            top = sugg[0]
            pred_nums = top["combo"].split("-")
            act_nums = draws[i]["nums"][:5]
            pred_fmt = _fmt_p5(pred_nums)
            act_fmt = _fmt_p5(act_nums)
            # Check straight hit (exact order)
            straight = (pred_nums == act_nums)
            # Check box hit (same digits any order)
            box = (not straight and sorted(pred_nums) == sorted(act_nums))
            rows.append({
                "date": draws[i].get("date", ""),
                "tod": draws[i].get("tod", ""),
                "predicted": top["combo"],
                "predicted_fmt": pred_fmt,
                "actual": "-".join(act_nums),
                "actual_fmt": act_fmt,
                "straight": straight,
                "box": box,
            })
        return rows

    backtest_rows = _backtest_p5(draws)

    game_info = next((g for g in PICK5_DIGIT_STATES.get(code, []) if g["slug"] == slug), {})
    return jsonify({
        "state": code,
        "slug": slug,
        "label": game_info.get("label", slug),
        "total_draws": report.get("total_draws", len(draws)),
        "last_draw": report.get("last_draw", draws[0] if draws else {}),
        "suggestions": suggs,
        "per_position_freq": per_pos,
        "hot_cold": report.get("hot_cold", {}),
        "backtest": backtest_rows,
    })


# ZYNORIQ BUSINESS AI — Routes
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


# ═══════════════════════════════════════════════════════════
# DASHBOARD — Favoris, alertes & rapports Business AI
# ═══════════════════════════════════════════════════════════

MAX_SAVED_PREDICTIONS = 50
MAX_ALERTS = 10
MAX_BUSINESS_REPORTS = 20


@app.route("/api/dashboard/summary")
@auth_module.login_required
def dashboard_summary():
    user = auth_module.current_user()
    sub = user.subscription
    return jsonify({
        "subscription": sub.to_dict() if sub else None,
        "saved_predictions_count": auth_module.SavedPrediction.query.filter_by(user_id=user.id).count(),
        "alerts_count": auth_module.Alert.query.filter_by(user_id=user.id).count(),
        "business_reports_count": auth_module.BusinessReport.query.filter_by(user_id=user.id).count(),
    })


@app.route("/api/dashboard/predictions", methods=["GET", "POST"])
@auth_module.login_required
def dashboard_predictions():
    user = auth_module.current_user()
    db = auth_module.db

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        state = (data.get("state") or "").upper()
        game  = data.get("game") or ""
        numbers = data.get("numbers")
        if not state or not game or numbers is None:
            return jsonify({"error": "state, game et numbers sont requis"}), 400

        count = auth_module.SavedPrediction.query.filter_by(user_id=user.id).count()
        if count >= MAX_SAVED_PREDICTIONS:
            return jsonify({"error": "limit_reached",
                            "message": f"Limite de {MAX_SAVED_PREDICTIONS} prédictions sauvegardées atteinte."}), 429

        import json as _json
        saved = auth_module.SavedPrediction(
            user_id=user.id, state=state, game=game,
            tod=data.get("tod"), label=data.get("label"),
            numbers=_json.dumps(numbers), source=data.get("source"),
        )
        db.session.add(saved)
        db.session.commit()
        return jsonify({"success": True, "prediction": saved.to_dict()})

    items = (auth_module.SavedPrediction.query
             .filter_by(user_id=user.id)
             .order_by(auth_module.SavedPrediction.created_at.desc())
             .all())
    return jsonify({"predictions": [p.to_dict() for p in items]})


@app.route("/api/dashboard/predictions/<int:pred_id>", methods=["DELETE"])
@auth_module.login_required
def dashboard_delete_prediction(pred_id):
    user = auth_module.current_user()
    db = auth_module.db
    item = auth_module.SavedPrediction.query.filter_by(id=pred_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/dashboard/alerts", methods=["GET", "POST"])
@auth_module.login_required
def dashboard_alerts():
    user = auth_module.current_user()
    db = auth_module.db

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        state = (data.get("state") or "").upper()
        game  = data.get("game") or ""
        alert_type = data.get("alert_type") or ""
        if not state or not game or not alert_type:
            return jsonify({"error": "state, game et alert_type sont requis"}), 400

        count = auth_module.Alert.query.filter_by(user_id=user.id).count()
        if count >= MAX_ALERTS:
            return jsonify({"error": "limit_reached",
                            "message": f"Limite de {MAX_ALERTS} alertes atteinte."}), 429

        import json as _json
        criteria = data.get("criteria")
        alert = auth_module.Alert(
            user_id=user.id, state=state, game=game, alert_type=alert_type,
            criteria=_json.dumps(criteria) if criteria is not None else None,
            active=True,
        )
        db.session.add(alert)
        db.session.commit()
        return jsonify({"success": True, "alert": alert.to_dict()})

    items = (auth_module.Alert.query
             .filter_by(user_id=user.id)
             .order_by(auth_module.Alert.created_at.desc())
             .all())
    return jsonify({"alerts": [a.to_dict() for a in items]})


@app.route("/api/dashboard/alerts/<int:alert_id>", methods=["PATCH", "DELETE"])
@auth_module.login_required
def dashboard_alert_detail(alert_id):
    user = auth_module.current_user()
    db = auth_module.db
    item = auth_module.Alert.query.filter_by(id=alert_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "not_found"}), 404

    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True})

    data = request.get_json(silent=True) or {}
    if "active" in data:
        item.active = bool(data["active"])
    db.session.commit()
    return jsonify({"success": True, "alert": item.to_dict()})


@app.route("/api/dashboard/reports", methods=["GET", "POST"])
@auth_module.login_required
def dashboard_reports():
    user = auth_module.current_user()
    db = auth_module.db

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        title = data.get("title") or "Rapport Business AI"
        report = data.get("report")
        if report is None:
            return jsonify({"error": "report est requis"}), 400

        count = auth_module.BusinessReport.query.filter_by(user_id=user.id).count()
        if count >= MAX_BUSINESS_REPORTS:
            return jsonify({"error": "limit_reached",
                            "message": f"Limite de {MAX_BUSINESS_REPORTS} rapports sauvegardés atteinte."}), 429

        import json as _json
        saved = auth_module.BusinessReport(
            user_id=user.id, title=title[:160],
            input_json=_json.dumps(data.get("input")) if data.get("input") is not None else None,
            report_json=_json.dumps(report),
        )
        db.session.add(saved)
        db.session.commit()
        return jsonify({"success": True, "report": saved.to_dict(include_report=False)})

    items = (auth_module.BusinessReport.query
             .filter_by(user_id=user.id)
             .order_by(auth_module.BusinessReport.created_at.desc())
             .all())
    return jsonify({"reports": [r.to_dict(include_report=False) for r in items]})


@app.route("/api/dashboard/reports/<int:report_id>")
@auth_module.login_required
def dashboard_report_detail(report_id):
    user = auth_module.current_user()
    item = auth_module.BusinessReport.query.filter_by(id=report_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "not_found"}), 404
    return jsonify({"report": item.to_dict(include_report=True)})


@app.route("/api/dashboard/reports/<int:report_id>", methods=["DELETE"])
@auth_module.login_required
def dashboard_delete_report(report_id):
    user = auth_module.current_user()
    db = auth_module.db
    item = auth_module.BusinessReport.query.filter_by(id=report_id, user_id=user.id).first()
    if not item:
        return jsonify({"error": "not_found"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"success": True})


MAX_ARCHIVE_ENTRIES = 200

@app.route("/api/dashboard/archives", methods=["GET"])
@auth_module.login_required
def dashboard_archives_get():
    user = auth_module.current_user()
    items = (auth_module.UserArchive.query
             .filter_by(user_id=user.id)
             .order_by(auth_module.UserArchive.ts.desc())
             .limit(MAX_ARCHIVE_ENTRIES).all())
    return jsonify({"entries": [i.to_dict() for i in items]})


@app.route("/api/dashboard/archives/sync", methods=["POST"])
@auth_module.login_required
def dashboard_archives_sync():
    """Bulk upsert: client sends its localStorage entries; server merges and returns the full list."""
    user = auth_module.current_user()
    db = auth_module.db
    data = request.get_json(silent=True) or {}
    entries = data.get("entries", [])

    for e in entries[:MAX_ARCHIVE_ENTRIES]:
        cid = str(e.get("id", ""))[:64]
        if not cid:
            continue
        existing = auth_module.UserArchive.query.filter_by(user_id=user.id, client_id=cid).first()
        if not existing:
            row = auth_module.UserArchive(
                user_id=user.id, client_id=cid,
                ts=int(e.get("ts", 0)),
                type=str(e.get("type", "analyze"))[:20],
                state=str(e.get("state", "") or "")[:4] or None,
                tod=str(e.get("tod", "") or "")[:20] or None,
                url=str(e.get("url", "") or "")[:500] or None,
                label=str(e.get("label", "") or "")[:200] or None,
            )
            db.session.add(row)

    # Enforce cap: keep only the MAX_ARCHIVE_ENTRIES most recent
    all_ids = (auth_module.UserArchive.query
               .filter_by(user_id=user.id)
               .order_by(auth_module.UserArchive.ts.desc())
               .with_entities(auth_module.UserArchive.id)
               .all())
    if len(all_ids) > MAX_ARCHIVE_ENTRIES:
        to_delete = [r.id for r in all_ids[MAX_ARCHIVE_ENTRIES:]]
        auth_module.UserArchive.query.filter(
            auth_module.UserArchive.id.in_(to_delete)).delete(synchronize_session=False)

    db.session.commit()

    items = (auth_module.UserArchive.query
             .filter_by(user_id=user.id)
             .order_by(auth_module.UserArchive.ts.desc())
             .limit(MAX_ARCHIVE_ENTRIES).all())
    return jsonify({"entries": [i.to_dict() for i in items]})


@app.route("/api/dashboard/archives/<client_id>", methods=["DELETE"])
@auth_module.login_required
def dashboard_archive_delete(client_id):
    user = auth_module.current_user()
    db = auth_module.db
    row = auth_module.UserArchive.query.filter_by(user_id=user.id, client_id=client_id).first()
    if row:
        db.session.delete(row)
        db.session.commit()
    return jsonify({"success": True})


@app.route("/api/dashboard/archives", methods=["DELETE"])
@auth_module.login_required
def dashboard_archives_clear():
    user = auth_module.current_user()
    db = auth_module.db
    auth_module.UserArchive.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/dashboard")
def dashboard_page():
    return send_from_directory("static", "dashboard.html")


# ═══════════════════════════════════════════════════════════════════════
# ADMIN — Panneau d'administration (gestion utilisateurs & abonnements)
# ═══════════════════════════════════════════════════════════════════════
@app.route("/api/admin/claim", methods=["POST"])
@auth_module.login_required
def admin_claim():
    """Permet à l'utilisateur connecté de devenir admin s'il fournit le
    secret PREDIKTA_ADMIN_SECRET (configuré côté serveur)."""
    db = auth_module.db
    secret = os.environ.get("PREDIKTA_ADMIN_SECRET")
    data = request.get_json(silent=True) or {}
    provided = data.get("secret") or ""
    if not secret or not hmac.compare_digest(provided, secret):
        return jsonify({"error": "Forbidden"}), 403
    user = auth_module.current_user()
    user.is_admin = True
    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()})


@app.route("/api/admin/stats")
@auth_module.admin_required
def admin_stats():
    db = auth_module.db
    User = auth_module.User
    Subscription = auth_module.Subscription
    SavedPrediction = auth_module.SavedPrediction
    Alert = auth_module.Alert
    BusinessReport = auth_module.BusinessReport
    PLAN_CONFIG = auth_module.PLAN_CONFIG

    total_users = User.query.count()
    now = datetime.utcnow()
    new_7d = User.query.filter(User.created_at >= now - timedelta(days=7)).count()
    new_30d = User.query.filter(User.created_at >= now - timedelta(days=30)).count()

    by_plan = {}
    by_status = {}
    active_count = 0
    mrr_usd = 0.0
    mrr_trial_usd = 0.0
    for sub in Subscription.query.all():
        plan_key = sub.plan or "none"
        by_plan[plan_key] = by_plan.get(plan_key, 0) + 1
        status_key = sub.status or "none"
        by_status[status_key] = by_status.get(status_key, 0) + 1
        if sub.is_active():
            active_count += 1
            price = PLAN_CONFIG.get(sub.plan, {}).get("price_usd", 0)
            if sub.status == "trial":
                mrr_trial_usd += price
            else:
                mrr_usd += price

    referral_balance_total = db.session.query(
        db.func.coalesce(db.func.sum(User.referral_balance_usd), 0)
    ).scalar() or 0

    return jsonify({
        "total_users": total_users,
        "new_users_7d": new_7d,
        "new_users_30d": new_30d,
        "active_subscriptions": active_count,
        "mrr_usd": round(mrr_usd, 2),
        "mrr_trial_usd": round(mrr_trial_usd, 2),
        "referral_balance_total_usd": round(referral_balance_total, 2),
        "by_plan": by_plan,
        "by_status": by_status,
        "total_saved_predictions": SavedPrediction.query.count(),
        "total_alerts": Alert.query.count(),
        "total_business_reports": BusinessReport.query.count(),
    })


@app.route("/api/admin/users")
@auth_module.admin_required
def admin_users_list():
    db = auth_module.db
    User = auth_module.User
    Subscription = auth_module.Subscription

    q = (request.args.get("q") or "").strip()
    plan = (request.args.get("plan") or "").strip()
    status = (request.args.get("status") or "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 25))))

    query = User.query
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(User.username.ilike(like), User.email.ilike(like)))
    if plan or status:
        query = query.join(Subscription, isouter=True)
        if plan:
            query = query.filter(Subscription.plan == plan)
        if status:
            query = query.filter(Subscription.status == status)

    total = query.count()
    items = (query.order_by(User.created_at.desc())
             .offset((page - 1) * per_page).limit(per_page).all())

    return jsonify({
        "users": [u.to_dict() for u in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if per_page else 1,
    })


@app.route("/api/admin/users/<int:user_id>")
@auth_module.admin_required
def admin_user_detail(user_id):
    db = auth_module.db
    User = auth_module.User
    SavedPrediction = auth_module.SavedPrediction
    Alert = auth_module.Alert
    BusinessReport = auth_module.BusinessReport

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    return jsonify({
        "user": user.to_dict(),
        "counts": {
            "saved_predictions": SavedPrediction.query.filter_by(user_id=user.id).count(),
            "alerts": Alert.query.filter_by(user_id=user.id).count(),
            "business_reports": BusinessReport.query.filter_by(user_id=user.id).count(),
        },
        "created_at": user.created_at.isoformat() if user.created_at else None,
    })


@app.route("/api/admin/users/<int:user_id>", methods=["PATCH"])
@auth_module.admin_required
def admin_user_update(user_id):
    db = auth_module.db
    User = auth_module.User
    Subscription = auth_module.Subscription
    PLAN_ORDER = auth_module.PLAN_ORDER

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True) or {}

    if "is_admin" in data:
        user.is_admin = bool(data["is_admin"])

    sub = user.subscription
    if sub is None:
        sub = Subscription(user_id=user.id, plan=None, status="none")
        db.session.add(sub)

    if "plan" in data:
        plan = data["plan"]
        if plan not in (None, "", *PLAN_ORDER):
            return jsonify({"error": f"plan invalide (attendu: {', '.join(PLAN_ORDER)})"}), 400
        sub.plan = plan or None

    if "status" in data:
        valid_status = {"none", "trial", "active", "past_due", "canceled", "expired"}
        if data["status"] not in valid_status:
            return jsonify({"error": f"status invalide (attendu: {', '.join(sorted(valid_status))})"}), 400
        sub.status = data["status"]

    if "extend_days" in data:
        try:
            days = int(data["extend_days"])
        except (TypeError, ValueError):
            return jsonify({"error": "extend_days doit être un entier"}), 400
        now = datetime.utcnow()
        if sub.status == "trial":
            base = sub.trial_end if (sub.trial_end and sub.trial_end > now) else now
            sub.trial_end = base + timedelta(days=days)
        else:
            base = sub.current_period_end if (sub.current_period_end and sub.current_period_end > now) else now
            sub.current_period_end = base + timedelta(days=days)

    db.session.commit()
    return jsonify({"success": True, "user": user.to_dict()})


@app.route("/api/admin/referrals")
@auth_module.admin_required
def admin_referrals_list():
    """Liste des parrains ayant un solde de commissions à verser."""
    db = auth_module.db
    User = auth_module.User

    rows = (User.query
            .filter(User.referral_balance_usd > 0)
            .order_by(User.referral_balance_usd.desc())
            .all())

    total = db.session.query(
        db.func.coalesce(db.func.sum(User.referral_balance_usd), 0)
    ).scalar() or 0

    return jsonify({
        "total_pending_usd": round(total, 2),
        "referrers": [{
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "referral_balance_usd": round(u.referral_balance_usd or 0, 2),
        } for u in rows],
    })


@app.route("/api/admin/referrals/<int:user_id>/payout", methods=["POST"])
@auth_module.admin_required
def admin_referrals_payout(user_id):
    """Enregistre un versement (hors plateforme) des commissions de parrainage
    dues à l'utilisateur `user_id` et déduit le montant de son solde."""
    db = auth_module.db
    User = auth_module.User

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "not_found"}), 404

    data = request.get_json(silent=True) or {}
    amount = data.get("amount_usd")
    if amount is None:
        amount = user.referral_balance_usd or 0
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "amount_usd invalide"}), 400

    if amount <= 0 or amount > (user.referral_balance_usd or 0):
        return jsonify({"error": "amount_usd doit être > 0 et <= au solde disponible"}), 400

    payout = auth_module.record_referral_payout(user, amount, note=data.get("note"))
    db.session.commit()
    return jsonify({"success": True, "payout": payout.to_dict() if payout else None,
                     "referral_balance_usd": round(user.referral_balance_usd or 0, 2)})


@app.route("/admin")
def admin_page():
    return send_from_directory("static", "admin.html")


# ═══════════════════════════════════════════════════════════
# ZYNORIQ COPILOT™ — MVP API
# ═══════════════════════════════════════════════════════════
_COPILOT_LOTTERY_KEYWORDS = {
    'chaud','froid','hot','cold','tendance','trend','retard','overdue','gap',
    'fréquence','frequency','position','somme','sum','pair','impair','even','odd',
    'double','triple','markov','monte carlo','fourier','xgboost','prédiction',
    'prediction','numéro','number','combo','straight','box','analyse','analyze',
}
_COPILOT_RESPONSES = {
    'fr':{
        'hot_cold': "**Chiffres Chauds / Froids** — Les chiffres \"chauds\" sont ceux tirés le plus souvent dans les 30 derniers tirages. Les \"froids\" apparaissent rarement. ZYNORIQ pondère ces fréquences par position (P1/P2/P3) pour affiner les suggestions.",
        'gap': "**Analyse des Écarts** — Un chiffre \"en retard\" a un écart actuel supérieur à sa moyenne historique. Le badge 🔥 99% signifie qu'il dépasse 99% de ses écarts habituels — statistiquement, il est \"dû\".",
        'prediction': "**Comment fonctionnent les prédictions** — ZYNORIQ combine 7 modèles ML (XGBoost, Random Forest, Gradient Boosting, Markov 1/2/3, Monte Carlo 50K, Fourier, Gap Analysis). Le score consensus pondère chaque modèle par sa précision historique sur votre état.",
        'box_straight': "**Straight vs Box** — Straight = les 3 chiffres dans l'ordre exact (probabilité 1/1000). Box = les 3 chiffres dans n'importe quel ordre (1/167 pour 6-way, 1/333 pour 3-way). Le gain Straight est plus élevé, mais le Box offre plus de chances.",
        'sum': "**Distribution des Sommes** — La somme des 3 chiffres (0-27) suit une courbe en cloche. Les sommes 13-14 sont les plus fréquentes. ZYNORIQ identifie quand certaines sommes sont en retard par rapport à leur moyenne.",
        'models': "**Nos 7 Modèles ML**\n• **XGBoost** — Gradient boosting optimisé\n• **Random Forest** — Ensemble d'arbres de décision\n• **Gradient Boosting** — Boosting séquentiel\n• **Markov 1/2/3** — Chaînes de transitions\n• **Monte Carlo** — 50,000 simulations\n• **Fourier** — Détection de cycles\n• **Gap Analysis** — Chiffres en retard",
        'default': "Je suis ZYNORIQ Copilot™. Je peux vous aider à comprendre les prédictions, les tendances, les modèles ML et les stratégies. Essayez de me demander :\n• Pourquoi ces numéros ?\n• Qu'est-ce que le score de confiance ?\n• Comment fonctionne Markov ?",
        'business': "**ZYNORIQ Business Intelligence** analyse votre projet avec des modèles IA : scoring de viabilité, analyse concurrentielle, plan 30-60-90 jours, identification des risques, et recommandations budgétaires. Soumettez votre projet via /bizai.",
        'coach': "**Conseils de Coach** :\n1. Ne jouez jamais plus que ce que vous pouvez perdre\n2. Utilisez le mode Box pour de meilleures chances\n3. Consultez les tendances sur 30+ tirages\n4. Diversifiez entre Straight et Box\n5. Suivez les chiffres en retard (écarts élevés)",
    },
    'en':{
        'hot_cold': "**Hot / Cold Digits** — \"Hot\" digits are drawn most often in the last 30 draws. \"Cold\" appear rarely. ZYNORIQ weights these frequencies by position (P1/P2/P3) to refine suggestions.",
        'gap': "**Gap Analysis** — An \"overdue\" digit has a current gap above its historical average. The 🔥 99% badge means it exceeds 99% of its usual gaps — statistically, it's \"due\".",
        'prediction': "**How predictions work** — ZYNORIQ combines 7 ML models (XGBoost, Random Forest, Gradient Boosting, Markov 1/2/3, Monte Carlo 50K, Fourier, Gap Analysis). The consensus score weights each model by its historical accuracy on your state.",
        'box_straight': "**Straight vs Box** — Straight = exact order (1/1000 odds). Box = any order (1/167 for 6-way, 1/333 for 3-way). Straight pays more, Box offers better odds.",
        'sum': "**Sum Distribution** — The sum of 3 digits (0-27) follows a bell curve. Sums 13-14 are most frequent. ZYNORIQ identifies when certain sums are overdue vs their average.",
        'models': "**Our 7 ML Models**\n• **XGBoost** — Optimized gradient boosting\n• **Random Forest** — Decision tree ensemble\n• **Gradient Boosting** — Sequential boosting\n• **Markov 1/2/3** — Transition chains\n• **Monte Carlo** — 50,000 simulations\n• **Fourier** — Cycle detection\n• **Gap Analysis** — Overdue digits",
        'default': "I'm ZYNORIQ Copilot™. I can help you understand predictions, trends, ML models and strategies. Try asking:\n• Why these numbers?\n• What is the confidence score?\n• How does Markov work?",
        'business': "**ZYNORIQ Business Intelligence** analyzes your project with AI models: viability scoring, competitive analysis, 30-60-90 day plan, risk identification, and budget recommendations. Submit your project via /bizai.",
        'coach': "**Coach Tips**:\n1. Never play more than you can afford to lose\n2. Use Box mode for better chances\n3. Check trends over 30+ draws\n4. Diversify between Straight and Box\n5. Follow overdue digits (high gaps)",
    },
}

import copilot_service as _cps

_COPILOT_SYSTEM_PROMPTS = {
    'lottery': """Tu es ZYNORIQ Copilot™, l'assistant IA officiel de la plateforme ZYNORIQ Intelligence™ — la plateforme d'analyse prédictive de loteries la plus avancée.

PLATEFORME:
- 44+ États américains couverts (Pick 3, Pick 4, Pick 5, Powerball, Mega Millions)
- 7 modèles ML : XGBoost, Random Forest, Gradient Boosting, Markov 1/2/3, Monte Carlo 50K, Fourier, Gap Analysis
- Score consensus pondéré par performance historique de chaque modèle
- Mises à jour en temps réel, alertes push, track record vérifié

TERMES CLÉS:
- Straight = ordre exact (1/1000). Box = n'importe quel ordre (1/167 six-way, 1/333 three-way)
- Chaud = chiffre fréquent. Froid = chiffre rare. En retard = écart > moyenne
- Double = 2 chiffres identiques. Triple = 3 identiques
- Confiance = % de consensus entre les 7 modèles

RÈGLES:
- Réponds dans la langue de l'utilisateur
- Sois concis (max 200 mots) mais précis et utile
- Utilise le markdown (**gras**, *italique*, listes •)
- Ne promets JAMAIS de gains. Les loteries sont des jeux de hasard
- Si on te demande des numéros spécifiques, redirige vers /analyze
- Mentionne les fonctionnalités de la plateforme quand pertinent""",

    'business': """Tu es ZYNORIQ Copilot™ en mode Business Intelligence. Tu aides les entrepreneurs et chefs d'entreprise avec :
- Analyse de viabilité de projets
- Plans stratégiques 30-60-90 jours
- Identification des risques et opportunités
- Analyse concurrentielle
- Recommandations budgétaires et KPIs

RÈGLES:
- Réponds dans la langue de l'utilisateur
- Sois concis (max 250 mots) mais actionnable
- Structure tes réponses avec des sections claires
- Donne des conseils pratiques, pas vagues
- Mentionne ZYNORIQ Business Intelligence (/bizai) pour les analyses approfondies""",

    'analyst': """Tu es ZYNORIQ Copilot™ en mode Data Analyst. Tu aides à comprendre :
- Les données statistiques (fréquences, écarts, distributions)
- Les performances des modèles ML
- Les tendances historiques par état/position
- L'interprétation des scores de confiance et accuracy
- Les métriques de la plateforme

RÈGLES:
- Réponds dans la langue de l'utilisateur
- Sois précis avec les chiffres et pourcentages
- Explique les concepts statistiques simplement
- Max 200 mots""",

    'coach': """Tu es ZYNORIQ Copilot™ en mode Coach. Tu guides les utilisateurs pour :
- Optimiser leur utilisation de la plateforme
- Comprendre les stratégies Straight vs Box
- Interpréter les analyses et tendances
- Jouer de manière responsable (budget, limites)
- Naviguer les différentes fonctionnalités

RÈGLES:
- Ton amical et encourageant
- Réponds dans la langue de l'utilisateur
- Insiste toujours sur le jeu responsable
- Sois concis (max 200 mots)
- TOUJOURS rappeler que la loterie est un jeu de hasard""",
}

def _call_claude(message, mode, lang, history, page):
    """Call Claude API via Anthropic SDK. Returns (reply, used_ai)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, False

    try:
        import httpx
        system = _COPILOT_SYSTEM_PROMPTS.get(mode, _COPILOT_SYSTEM_PROMPTS['lottery'])
        system += f"\n\nContexte: l'utilisateur est sur la page {page}. Langue préférée: {lang}."

        messages = []
        for h in (history or [])[-8:]:
            role = h.get("role", "user")
            if role == "assistant":
                messages.append({"role": "assistant", "content": h.get("content", "")})
            else:
                messages.append({"role": "user", "content": h.get("content", "")})

        if not messages or messages[-1]["role"] != "user":
            messages.append({"role": "user", "content": message})

        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 512,
                "system": system,
                "messages": messages,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("content", [{}])[0].get("text", "")
            return text, True
        else:
            print(f"[copilot] Claude API error {resp.status_code}: {resp.text[:200]}")
            return None, False
    except Exception as e:
        print(f"[copilot] Claude API exception: {e}")
        return None, False


@app.route("/api/copilot", methods=["POST"])
def api_copilot():
    data = request.get_json(silent=True) or {}
    msg = (data.get("message") or "").strip()
    mode = data.get("mode", "lottery")
    lang = data.get("lang", "fr")
    page = data.get("page", "/")
    history = data.get("history", [])
    page_context = data.get("context", {})

    if not msg:
        return jsonify({"error": "Empty message"}), 400

    # ── Identify user & plan ──
    user = auth_module.current_user() if hasattr(auth_module, 'current_user') else None
    user_id = user.id if user else 0
    plan = None
    if user and user.subscription:
        plan = user.subscription.plan

    # ── Quota check ──
    allowed, remaining, limit = _cps.check_quota(user_id, plan)
    if not allowed:
        return jsonify({
            "reply": _cps.fallback_reply(lang, 'quota', limit=limit),
            "disclaimer": False, "mode": mode, "ai": False,
            "quota": {"remaining": 0, "limit": limit},
        })

    # ── Build page context text ──
    page_context["url"] = page
    page_context["plan"] = plan or "free"

    # Server-side data enrichment: inject real data based on page
    _enrich_context(page_context, page)

    context_text = _cps.build_page_context(page_context)

    # ── Lottery keyword detection ──
    is_lottery = mode == 'lottery' or any(kw in msg.lower() for kw in _COPILOT_LOTTERY_KEYWORDS)

    # ── Call Claude with real context ──
    reply, used_ai, latency = _cps.call_claude(msg, mode, lang, history, context_text)

    # ── Fallback if Claude unavailable ──
    if not reply:
        msg_lower = msg.lower()
        responses = _COPILOT_RESPONSES.get(lang, _COPILOT_RESPONSES.get('en', {}))
        if mode == 'business' or 'business' in msg_lower:
            reply = responses.get('business', responses.get('default'))
        elif mode == 'coach' or 'coach' in msg_lower:
            reply = responses.get('coach', responses.get('default'))
        elif any(w in msg_lower for w in ('chaud','froid','hot','cold')):
            reply = responses.get('hot_cold')
        elif any(w in msg_lower for w in ('écart','gap','retard','overdue')):
            reply = responses.get('gap')
        elif any(w in msg_lower for w in ('prédiction','prediction','pourquoi','numéro')):
            reply = responses.get('prediction')
        elif any(w in msg_lower for w in ('box','straight')):
            reply = responses.get('box_straight')
        elif any(w in msg_lower for w in ('modèle','model','ml','xgboost','markov')):
            reply = responses.get('models')
        else:
            reply = responses.get('default')
        latency = 0

    # ── Consume quota & save history ──
    _cps.consume_quota(user_id)
    _cps.save_history(user_id, msg, reply or "", mode, page, lang, used_ai)
    _cps.log_request(user_id, mode, page, latency, "ok" if reply else "fallback")

    # ── Save to Memory™ DB ──
    if user_id:
        try:
            _mem.save_conversation(user_id, msg, reply or "", mode, page, lang, used_ai)
            _mem.track_activity(user_id, "copilot", page=page)
        except Exception:
            pass

    return jsonify({
        "reply": reply or _cps.fallback_reply(lang, 'default'),
        "disclaimer": is_lottery,
        "mode": mode,
        "ai": used_ai,
        "quota": {"remaining": max(0, remaining - 1), "limit": limit},
    })


def _enrich_context(ctx, page):
    """Inject real server-side data into context based on current page."""
    try:
        state = ctx.get("state")

        # Results page: inject latest draws for selected state
        if "/results" in page or "/all-results" in page:
            if state and state.upper() in STATES:
                draws = load_csv(state.upper())[:10]
                ctx["latest_draws"] = draws

        # Analyze page: inject report cache if available
        if "/analyze" in page and state:
            cache_key_candidates = [
                k for k in _REPORT_CACHE
                if isinstance(k, tuple) and len(k) >= 1 and k[0] == state.upper()
            ]
            if cache_key_candidates:
                cached = _REPORT_CACHE.get(cache_key_candidates[0])
                if cached:
                    report = cached.get("data", {})
                    top = report.get("top", [])[:5]
                    ctx["predictions"] = [
                        {"combo": s.get("combo", ""), "confidence": round(s.get("pct", 0), 1)}
                        for s in top
                    ]
                    hc = report.get("hot_cold", {})
                    if hc:
                        ctx["hot_digits"] = hc.get("hot", [])
                        ctx["cold_digits"] = hc.get("cold", [])

        # Accuracy / Track Record
        if "/accuracy" in page or "/track-record" in page:
            acc_cached = _ACCURACY_CACHE.get("data")
            if acc_cached:
                acc_data = acc_cached.get("data", {})
                ctx["accuracy"] = {
                    "grand_totals": acc_data.get("grand_totals", {}),
                    "best_states": acc_data.get("best_states", []),
                }
    except Exception as e:
        print(f"[copilot] enrich error: {e}")


@app.route("/api/copilot/history")
def api_copilot_history():
    user = auth_module.current_user() if hasattr(auth_module, 'current_user') else None
    if not user:
        return jsonify({"error": "Login required"}), 401
    entries = _cps.get_history(user.id, limit=20)
    return jsonify({"history": entries})


@app.route("/api/copilot/logs")
def api_copilot_logs():
    _token = os.environ.get("ADMIN_TOKEN", "")
    _req = request.headers.get("X-Admin-Token", "") or request.args.get("token", "")
    if not _token or not hmac.compare_digest(_req, _token):
        return jsonify({"error": "unauthorized"}), 401
    return jsonify({"logs": _cps.get_logs(100)})


# ── PDF Report Generation ────────────────────────────────────────────────
import copilot_report as _cpr

@app.route("/api/copilot/report", methods=["POST"])
def api_copilot_report():
    data = request.get_json(silent=True) or {}
    report_type = data.get("report_type", "prediction")
    lang = data.get("lang", "fr")
    page_context = data.get("context", {})
    analysis = data.get("analysis", "")

    if report_type not in _cpr.REPORT_TYPES:
        return jsonify({"error": f"Invalid report type: {report_type}"}), 400

    user = auth_module.current_user() if hasattr(auth_module, 'current_user') else None
    user_id = user.id if user else 0
    plan = None
    if user and user.subscription:
        plan = user.subscription.plan

    allowed, remaining, limit = _cpr.check_report_quota(user_id, plan)
    if not allowed:
        return jsonify({"error": "quota_exceeded", "limit": limit, "remaining": 0}), 429

    # Enrich context with server data
    page = data.get("page", "/")
    page_context["url"] = page
    page_context["plan"] = plan or "free"
    _enrich_context(page_context, page)

    # Generate AI analysis if not provided
    if not analysis and os.environ.get("ANTHROPIC_API_KEY"):
        prompt = f"Generate a professional {report_type} report analysis for the following data. Be structured: summary, key findings, recommendations, next action. Max 400 words."
        context_text = _cps.build_page_context(page_context)
        analysis, _, _ = _cps.call_claude(prompt, "analyst", lang, [], context_text)

    try:
        filepath = _cpr.generate_report(
            report_type=report_type,
            lang=lang,
            data=page_context,
            analysis_text=analysis or "",
            user_plan=plan,
        )
    except Exception as e:
        print(f"[copilot/report] PDF generation error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"error": f"PDF generation error: {str(e)[:100]}"}), 500

    if not filepath:
        return jsonify({"error": "PDF library not available (fpdf2)"}), 500

    _cpr.consume_report_quota(user_id)
    token = _cpr.register_file(filepath, user_id)

    return jsonify({
        "success": True,
        "download_url": f"/api/copilot/report/download/{token}",
        "report_type": report_type,
        "quota": {"remaining": max(0, remaining - 1), "limit": limit},
    })


@app.route("/api/copilot/report/download/<token>")
def api_copilot_report_download(token):
    user = auth_module.current_user() if hasattr(auth_module, 'current_user') else None
    user_id = user.id if user else 0
    filepath = _cpr.get_file(token, user_id)
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "Report not found or expired"}), 404
    filename = os.path.basename(filepath)
    return send_from_directory(
        os.path.dirname(os.path.abspath(filepath)),
        filename,
        as_attachment=True,
        download_name=filename,
    )


# ═══════════════════════════════════════════════════════════
@app.route("/copilot.js")
def copilot_js():
    resp = make_response(send_from_directory("static", "copilot.js"))
    resp.headers["Content-Type"] = "application/javascript; charset=utf-8"
    return resp


# ═══════════════════════════════════════════════════════════
# ZYNORIQ MEMORY™ — API Endpoints
# ═══════════════════════════════════════════════════════════
@app.route("/memory")
def memory_page():
    return send_from_directory("static", "memory.html")


@app.route("/api/memory/profile")
@auth_module.login_required
def api_memory_profile():
    user = auth_module.current_user()
    profile = _mem.get_profile(user.id)
    return jsonify({"profile": profile})


@app.route("/api/memory/profile", methods=["POST"])
@auth_module.login_required
def api_memory_profile_update():
    user = auth_module.current_user()
    data = request.get_json(silent=True) or {}
    _mem.save_profile(user.id, data)
    return jsonify({"success": True})


@app.route("/api/memory/conversations")
@auth_module.login_required
def api_memory_conversations():
    user = auth_module.current_user()
    limit = min(100, int(request.args.get("limit", "20")))
    convos = _mem.get_conversations(user.id, limit=limit)
    return jsonify({"conversations": convos})


@app.route("/api/memory/recommendations")
@auth_module.login_required
def api_memory_recommendations():
    user = auth_module.current_user()
    lang = request.args.get("lang", "fr")
    recs = _mem.get_recommendations(user.id, lang=lang)
    return jsonify({"recommendations": recs})


@app.route("/api/memory/dashboard")
@auth_module.login_required
def api_memory_dashboard():
    user = auth_module.current_user()
    lang = request.args.get("lang", "fr")
    ctx = _mem.get_dashboard_context(user.id, lang=lang)
    return jsonify(ctx)


@app.route("/api/memory/preferences")
@auth_module.login_required
def api_memory_preferences():
    user = auth_module.current_user()
    prefs = _mem.get_preferences(user.id)
    return jsonify({"preferences": prefs})


@app.route("/api/memory/preferences", methods=["POST"])
@auth_module.login_required
def api_memory_preferences_update():
    user = auth_module.current_user()
    data = request.get_json(silent=True) or {}
    current = _mem.get_preferences(user.id)
    current.update(data)
    _mem.save_preferences(user.id, current)
    return jsonify({"success": True})


@app.route("/api/memory/export")
@auth_module.login_required
def api_memory_export():
    user = auth_module.current_user()
    data = _mem.export_memory(user.id)
    return jsonify(data)


@app.route("/api/memory/clear", methods=["POST"])
@auth_module.login_required
def api_memory_clear():
    user = auth_module.current_user()
    _mem.clear_memory(user.id)
    return jsonify({"success": True})


@app.route("/api/memory/track", methods=["POST"])
@auth_module.login_required
def api_memory_track():
    user = auth_module.current_user()
    data = request.get_json(silent=True) or {}
    prefs = _mem.get_preferences(user.id)
    if not prefs.get("track_activities", True):
        return jsonify({"skipped": True})
    _mem.track_activity(
        user.id,
        activity_type=data.get("type", "page_visit"),
        page=data.get("page", "/"),
        state=data.get("state"),
        game=data.get("game"),
        details=data.get("details"),
    )
    return jsonify({"success": True})


# ═══════════════════════════════════════════════════════════
# ZYNORIQ AGENTS™ — Specialized AI Agents API
# ═══════════════════════════════════════════════════════════
@app.route("/api/agents")
def api_agents_list():
    lang = request.args.get("lang", "fr")
    return jsonify({"agents": _agents.get_agent_info(lang)})


@app.route("/api/agents/run", methods=["POST"])
def api_agents_run():
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agent")
    message = (data.get("message") or "").strip()
    lang = data.get("lang", "fr")
    page = data.get("page", "/")
    page_context = data.get("context", {})
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Empty message"}), 400
    if agent_id not in _agents.AGENTS:
        return jsonify({"error": f"Unknown agent: {agent_id}"}), 400

    user = auth_module.current_user() if hasattr(auth_module, 'current_user') else None
    user_id = user.id if user else 0
    plan = None
    if user and user.subscription:
        plan = user.subscription.plan

    # Quota check (shared with Copilot)
    allowed, remaining, limit = _cps.check_quota(user_id, plan)
    if not allowed:
        return jsonify({
            "error": "quota_exceeded",
            "quota": {"remaining": 0, "limit": limit},
        }), 429

    # Build context
    page_context["url"] = page
    page_context["plan"] = plan or "free"
    _enrich_context(page_context, page)
    context_text = _cps.build_page_context(page_context)

    # Run agent
    reply, latency, error = _agents.run_agent(agent_id, message, context_text, lang, history)
    _cps.consume_quota(user_id)

    if error and not reply:
        return jsonify({"error": error, "agent": agent_id}), 500

    # Save to memory
    if user_id:
        try:
            _mem.save_conversation(user_id, f"[{agent_id}] {message}", reply or "", "agent", page, lang, True)
        except Exception:
            pass

    is_lottery = agent_id in ("lottery_expert", "statistician", "accuracy_analyst", "coach", "risk_analyst")

    return jsonify({
        "reply": reply or "Agent could not generate a response.",
        "agent": agent_id,
        "agent_name": _agents.AGENTS[agent_id]["name"],
        "agent_icon": _agents.AGENTS[agent_id]["icon"],
        "disclaimer": is_lottery,
        "latency_ms": round(latency),
        "quota": {"remaining": max(0, remaining - 1), "limit": limit},
    })


@app.route("/api/agents/multi", methods=["POST"])
def api_agents_multi():
    data = request.get_json(silent=True) or {}
    agent_ids = data.get("agents", [])
    message = (data.get("message") or "").strip()
    lang = data.get("lang", "fr")
    page = data.get("page", "/")
    page_context = data.get("context", {})

    if not message or not agent_ids:
        return jsonify({"error": "Missing message or agents"}), 400

    page_context["url"] = page
    _enrich_context(page_context, page)
    context_text = _cps.build_page_context(page_context)

    results = _agents.run_multi_agent(agent_ids[:3], message, context_text, lang)
    return jsonify({"results": results})


# ═══════════════════════════════════════════════════════════
# ZYNORIQ INTELLIGENCE GRAPH™ — Knowledge Graph API
# ═══════════════════════════════════════════════════════════
@app.route("/api/graph/state/<state_code>")
def api_graph_state(state_code):
    code = state_code.upper()
    if code not in STATES:
        return jsonify({"error": f"Unknown state: {code}"}), 404
    draws = load_csv(code)
    report = None
    for k, v in _REPORT_CACHE.items():
        if isinstance(k, tuple) and len(k) >= 1 and k[0] == code:
            report = v.get("data")
            break
    graph = _igraph.build_state_graph(code, draws, report)
    return jsonify(graph)


@app.route("/api/graph/cross")
def api_graph_cross():
    codes = (request.args.get("states") or "NY,FL,GA,TX").split(",")
    states_data = {}
    for code in codes[:10]:
        c = code.strip().upper()
        if c in STATES:
            states_data[c] = {"draws": load_csv(c)}
    graph = _igraph.build_cross_state_graph(states_data)
    return jsonify(graph)


@app.route("/api/graph/entity/<entity_type>/<entity_id>")
def api_graph_entity(entity_type, entity_id):
    state = request.args.get("state", "NY").upper()
    draws = load_csv(state) if state in STATES else []
    connections = _igraph.get_entity_connections(entity_type, entity_id, draws)
    return jsonify({"entity": entity_id, "type": entity_type, "connections": connections})


# ═══════════════════════════════════════════════════════════
# ZYNORIQ STUDIO™ — Content Creation API
# ═══════════════════════════════════════════════════════════
@app.route("/api/studio/types")
def api_studio_types():
    lang = request.args.get("lang", "fr")
    return jsonify({"types": _studio.get_content_types(lang)})


@app.route("/api/studio/generate", methods=["POST"])
def api_studio_generate():
    data = request.get_json(silent=True) or {}
    content_type = data.get("type", "daily_summary")
    lang = data.get("lang", "fr")
    context = data.get("context", {})
    use_ai = data.get("ai", False)

    # Enrich with server data
    state = context.get("state")
    if state and state.upper() in STATES:
        draws = load_csv(state.upper())
        context["total_draws"] = len(draws)
        if draws:
            last = draws[0]
            context["last_draw_date"] = last.get("date", "")
            context["last_draw_numbers"] = f"{last.get('d1','')}-{last.get('d2','')}-{last.get('d3','')}"

        # Hot/cold from frequency
        from collections import Counter as _C
        freq = _C()
        for d in draws[:30]:
            for p in ["d1", "d2", "d3"]:
                v = str(d.get(p, ""))
                if v:
                    freq[v] += 1
        if freq:
            total = sum(freq.values()) or 1
            hot = [d for d, c in freq.most_common() if c / total > 0.12][:3]
            cold = [d for d, c in freq.most_common()[::-1] if c / total < 0.08][:3]
            context["hot_digits"] = ", ".join(hot) or "—"
            context["cold_digits"] = ", ".join(cold) or "—"

    # Get predictions from cache
    if state:
        for k, v in _REPORT_CACHE.items():
            if isinstance(k, tuple) and len(k) >= 1 and k[0] == state.upper():
                report = v.get("data", {})
                top = report.get("top", [])[:5]
                context["predictions"] = [
                    {"combo": s.get("combo", ""), "confidence": round(s.get("pct", 0), 1)}
                    for s in top
                ]
                break

    result = _studio.generate_content(content_type, lang, context, use_ai)
    return jsonify(result)


@app.route("/studio")
def studio_page():
    return send_from_directory("static", "studio.html")


if __name__ == "__main__":
    print("=" * 45)
    print("  ZYNORIQ Intelligence  v5.0  - READY")
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
