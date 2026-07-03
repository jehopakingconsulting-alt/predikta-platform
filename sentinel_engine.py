"""
ZYNORIQ SENTINEL™ — Pre-draw AI Alert Engine v1.0
Scans all states every 5 min, scores predictions via cache (read-only),
selects Top 3 strongest draws, alerts PREMIUM/BUSINESS users 30-65 min before each draw.
ZERO modification to ML engine — pure read-only access to _REPORT_CACHE.
"""
import os, json, time, threading, smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zoneinfo import ZoneInfo
from draw_schedule import DRAW_SCHEDULE, _parse_schedule_time

# ── Config ─────────────────────────────────────────────────────────────────
SENTINEL_PLANS  = {"premium", "elite", "business", "enterprise"}
ALERT_MIN_MIN   = 30     # alert window start: 30 min before draw
ALERT_MAX_MIN   = 65     # alert window end: 65 min before draw
COOLDOWN_HOURS  = 6      # no re-alert for same (state, tod) within this window
TOP_N           = 3      # top states to include per alert email
MAX_CACHE_AGE_H = 8      # skip cache entries older than this (hours)

_SENT_FILE = os.path.join("data", "sentinel_sent.json")
_sent_lock = threading.Lock()
# _SUBS_FILE removed — subscriptions now live in PostgreSQL (SentinelSubscription model)

STATE_NAMES = {
    "NY":"New York","GA":"Georgia","TX":"Texas","FL":"Florida",
    "CA":"California","PA":"Pennsylvania","NJ":"New Jersey",
    "IL":"Illinois","OH":"Ohio","NC":"North Carolina",
    "VA":"Virginia","MA":"Massachusetts","MI":"Michigan",
    "MD":"Maryland","TN":"Tennessee","SC":"South Carolina",
    "CT":"Connecticut","IN":"Indiana","KY":"Kentucky",
    "MO":"Missouri","AZ":"Arizona","CO":"Colorado",
    "LA":"Louisiana","MS":"Mississippi","AR":"Arkansas",
    "IA":"Iowa","KS":"Kansas","OK":"Oklahoma","DE":"Delaware",
    "NM":"New Mexico","WV":"West Virginia","DC":"Washington DC",
    "WI":"Wisconsin","MN":"Minnesota","NE":"Nebraska",
    "NH":"New Hampshire","VT":"Vermont","ME":"Maine",
    "WA":"Washington","ID":"Idaho","PR":"Puerto Rico",
}

# ── Subscription helpers — DB-backed (PostgreSQL, survit aux redeploys) ────
def subscribe_user(user_id: int, active: bool = True):
    from auth import db, SentinelSubscription
    row = db.session.get(SentinelSubscription, user_id)
    if row:
        row.active = active
    else:
        db.session.add(SentinelSubscription(user_id=user_id, active=active))
    db.session.commit()

def unsubscribe_user(user_id: int):
    subscribe_user(user_id, active=False)

def get_subscription(user_id: int) -> dict:
    from auth import SentinelSubscription
    row = SentinelSubscription.query.get(user_id)
    return {"active": bool(row and row.active)}

# ── Sent-alert tracker ────────────────────────────────────────────────────
def _load_sent():
    try:
        if os.path.exists(_SENT_FILE):
            with open(_SENT_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_sent(sent):
    try:
        os.makedirs("data", exist_ok=True)
        with open(_SENT_FILE, "w", encoding="utf-8") as f:
            json.dump(sent, f)
    except Exception:
        pass

def _already_sent(state: str, tod: str, draw_date: str) -> bool:
    key = f"{state}_{tod}_{draw_date}"
    with _sent_lock:
        sent = _load_sent()
        entry = sent.get(key)
        if not entry:
            return False
        try:
            sent_at = datetime.fromisoformat(entry["sent_at"])
            return (datetime.utcnow() - sent_at).total_seconds() < COOLDOWN_HOURS * 3600
        except Exception:
            return False

def _mark_sent(state: str, tod: str, draw_date: str):
    key = f"{state}_{tod}_{draw_date}"
    with _sent_lock:
        sent = _load_sent()
        sent[key] = {"sent_at": datetime.utcnow().isoformat()}
        cutoff = datetime.utcnow() - timedelta(hours=48)
        sent = {k: v for k, v in sent.items()
                if datetime.fromisoformat(v["sent_at"]) > cutoff}
        _save_sent(sent)

# ── Schedule scanner ──────────────────────────────────────────────────────
def _upcoming_draws(min_min=ALERT_MIN_MIN, max_min=ALERT_MAX_MIN):
    """Return list of (state, tod, time_str, minutes_away) in the alert window."""
    now_utc = datetime.now(ZoneInfo("UTC"))
    upcoming = []
    for state, entries in DRAW_SCHEDULE.items():
        for entry in entries:
            try:
                hour, minute, tz_name = _parse_schedule_time(entry["time"])
                local_now = now_utc.astimezone(ZoneInfo(tz_name))
                draw_dt = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if draw_dt < local_now:
                    draw_dt += timedelta(days=1)
                minutes_away = (draw_dt - local_now).total_seconds() / 60
                if min_min <= minutes_away <= max_min:
                    upcoming.append((state, entry["tod"], entry["time"], round(minutes_away)))
            except Exception:
                pass
    return upcoming

# ── Prediction scorer (read-only cache) ──────────────────────────────────
def _score_draw(state: str, tod: str, report_cache: dict) -> dict | None:
    """Read prediction quality from _REPORT_CACHE. Never calls ML engine."""
    entry = report_cache.get(f"{state}|{tod}")
    if not entry:
        return None

    # Skip stale cache entries
    cache_age_min = (time.time() - entry.get("ts", 0)) / 60
    if cache_age_min > MAX_CACHE_AGE_H * 60:
        return None

    data = entry.get("data", {})
    consensus = data.get("consensus") or []
    if not consensus:
        return None

    top3_picks = consensus[:3]
    top = top3_picks[0]
    confidence = float(top.get("confidence_pct") or 0)

    # Number of models in agreement
    breakdown = top.get("breakdown", {}) or {}
    model_weights = breakdown.get("model_weights", {}) or {}
    models_in_agreement = sum(1 for v in model_weights.values() if v and v > 0)

    # Live hit rate from track record embedded in report
    track = data.get("track_record") or {}
    hit_rate = float(track.get("box_rate") or 0)

    # Composite score: confidence 60%, hit_rate 30%, freshness 10%
    freshness = max(0.0, 1.0 - cache_age_min / (MAX_CACHE_AGE_H * 60))
    score = (confidence * 0.6) + (hit_rate * 0.3) + (freshness * 10)

    # Hot/cold digits
    hot = data.get("hot") or []
    cold = data.get("cold") or []

    return {
        "state":          state,
        "state_name":     STATE_NAMES.get(state, state),
        "tod":            tod,
        "confidence":     round(confidence, 1),
        "label":          top.get("confidence_label", ""),
        "top_picks":      [p.get("combo", "???") for p in top3_picks],
        "models_count":   models_in_agreement,
        "hot_digits":     hot[:4],
        "cold_digits":    cold[:4],
        "hit_rate":       round(hit_rate, 1),
        "cache_age_min":  round(cache_age_min, 1),
        "score":          round(score, 2),
    }

# ── Email builder ─────────────────────────────────────────────────────────
_SUBJECTS = {
    "fr": "🎯 ZYNORIQ Sentinel™ — Top 3 Alertes Pré-Tirage",
    "en": "🎯 ZYNORIQ Sentinel™ — Top 3 Pre-Draw Alerts",
    "es": "🎯 ZYNORIQ Sentinel™ — Top 3 Alertas Pre-Sorteo",
    "pt": "🎯 ZYNORIQ Sentinel™ — Top 3 Alertas Pré-Sorteio",
    "ht": "🎯 ZYNORIQ Sentinel™ — Top 3 Alèt Anvan Tiraj",
}
_GREET = {
    "fr": ("Bonjour", "Le Sentinel a scanné tous les algorithmes ZYNORIQ et identifié les <strong style='color:#4ade80;'>3 meilleures opportunités</strong> avant les prochains tirages."),
    "en": ("Hello",   "The Sentinel has scanned all ZYNORIQ algorithms and identified the <strong style='color:#4ade80;'>3 best opportunities</strong> before the next draws."),
    "es": ("Hola",    "El Sentinel escaneó todos los algoritmos de ZYNORIQ e identificó las <strong style='color:#4ade80;'>3 mejores oportunidades</strong> antes de los próximos sorteos."),
    "pt": ("Olá",     "O Sentinel varreu todos os algoritmos ZYNORIQ e identificou as <strong style='color:#4ade80;'>3 melhores oportunidades</strong> antes dos próximos sorteios."),
    "ht": ("Bonjou",  "Sentinel te eskane tout algoritm ZYNORIQ yo epi jwenn <strong style='color:#4ade80;'>3 pi bon opòtinite</strong> anvan pwochen tiraj yo."),
}
_DRAW_LABEL = {
    "fr": "Tirage dans ~{m} min",
    "en": "Draw in ~{m} min",
    "es": "Sorteo en ~{m} min",
    "pt": "Sorteio em ~{m} min",
    "ht": "Tiraj nan ~{m} min",
}
_DISCLAIMER = {
    "fr": "⚠️ Les analyses ZYNORIQ sont statistiques et éducatives. Aucun résultat garanti. Jouez de façon responsable.",
    "en": "⚠️ ZYNORIQ analyses are statistical and educational. No result guaranteed. Play responsibly.",
    "es": "⚠️ Los análisis de ZYNORIQ son estadísticos y educativos. Ningún resultado garantizado. Juega responsablemente.",
    "pt": "⚠️ As análises da ZYNORIQ são estatísticas e educativas. Nenhum resultado garantido. Jogue com responsabilidade.",
    "ht": "⚠️ Analiz ZYNORIQ yo estatistik ak edikasyon. Pa gen rezilta garanti. Jwe ak responsablite.",
}

def _build_email_html(name: str, top3: list, lang: str) -> str:
    greet_word, intro = _GREET.get(lang, _GREET["fr"])
    draw_label_tpl   = _DRAW_LABEL.get(lang, _DRAW_LABEL["fr"])
    disclaimer       = _DISCLAIMER.get(lang, _DISCLAIMER["fr"])

    rows = ""
    for i, pick in enumerate(top3, 1):
        picks_str = "  ·  ".join(pick["top_picks"])
        hot_str   = "  ".join(str(d) for d in pick["hot_digits"]) if pick["hot_digits"] else "—"
        draw_lbl  = draw_label_tpl.format(m=pick.get("minutes_away", "?"))
        model_txt = f"{pick['models_count']} modèles" if pick.get("models_count") else ""
        rows += f"""
        <tr style="border-bottom:1px solid #0f172a;">
          <td style="padding:14px 10px;color:#a78bfa;font-weight:800;font-size:18px;">#{i}</td>
          <td style="padding:14px 10px;">
            <div style="font-weight:700;color:#f1f5f9;font-size:15px;">{pick['state_name']}</div>
            <div style="font-size:12px;color:#a78bfa;">{pick['tod']}</div>
            <div style="font-size:11px;color:#64748b;margin-top:2px;">{draw_lbl}</div>
          </td>
          <td style="padding:14px 10px;text-align:center;">
            <div style="font-size:20px;font-weight:800;color:#4ade80;letter-spacing:3px;">{picks_str}</div>
            <div style="font-size:10px;color:#64748b;margin-top:2px;">{model_txt}</div>
          </td>
          <td style="padding:14px 10px;text-align:center;">
            <div style="font-size:20px;font-weight:800;color:#facc15;">{pick['confidence']}%</div>
            <div style="font-size:11px;color:#64748b;">{pick['label']}</div>
          </td>
          <td style="padding:14px 10px;text-align:center;color:#fb923c;font-size:13px;letter-spacing:2px;">
            🔥 {hot_str}
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0e1a;font-family:system-ui,-apple-system,sans-serif;">
<div style="max-width:620px;margin:0 auto;padding:28px 20px;">

  <!-- Header -->
  <div style="text-align:center;margin-bottom:28px;">
    <div style="font-size:13px;color:#64748b;letter-spacing:4px;text-transform:uppercase;margin-bottom:8px;">Intelligence au-delà de la prédiction</div>
    <div style="font-size:30px;font-weight:900;background:linear-gradient(135deg,#a78bfa,#4ade80);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">ZYNORIQ Sentinel™</div>
  </div>

  <!-- Greeting -->
  <div style="background:#1e293b;border-radius:12px;padding:20px 24px;margin-bottom:20px;">
    <p style="color:#94a3b8;margin:0 0 8px;">{greet_word} {name},</p>
    <p style="color:#e2e8f0;margin:0;line-height:1.6;">{intro}</p>
  </div>

  <!-- Top 3 Table -->
  <div style="background:#1e293b;border-radius:12px;overflow:hidden;margin-bottom:20px;">
    <div style="background:#0f172a;padding:12px 16px;border-bottom:1px solid #334155;">
      <span style="color:#a78bfa;font-weight:700;font-size:13px;letter-spacing:1px;">🎯 TOP 3 — TIRAGES IMMINENTS</span>
    </div>
    <table style="width:100%;border-collapse:collapse;">
      <thead>
        <tr style="background:#0f172a;">
          <th style="padding:10px;color:#475569;font-size:10px;text-align:left;font-weight:600;">#</th>
          <th style="padding:10px;color:#475569;font-size:10px;text-align:left;font-weight:600;">ÉTAT</th>
          <th style="padding:10px;color:#475569;font-size:10px;text-align:center;font-weight:600;">NUMÉROS SUGGÉRÉS</th>
          <th style="padding:10px;color:#475569;font-size:10px;text-align:center;font-weight:600;">SCORE</th>
          <th style="padding:10px;color:#475569;font-size:10px;text-align:center;font-weight:600;">CHAUDS</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
  </div>

  <!-- CTA -->
  <div style="text-align:center;margin-bottom:24px;">
    <a href="https://zynoriq.com/analyze" style="display:inline-block;background:#7c3aed;color:#fff;text-decoration:none;padding:13px 32px;border-radius:8px;font-weight:700;font-size:14px;margin-right:10px;">⚡ Analyser maintenant</a>
    <a href="https://zynoriq.com/all-results" style="display:inline-block;background:#1e293b;border:1px solid #334155;color:#94a3b8;text-decoration:none;padding:13px 24px;border-radius:8px;font-weight:600;font-size:14px;">📊 Tous les résultats</a>
  </div>

  <!-- Disclaimer -->
  <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px 18px;margin-bottom:20px;">
    <p style="color:#64748b;font-size:11px;margin:0;line-height:1.5;">{disclaimer}</p>
  </div>

  <!-- Footer -->
  <p style="text-align:center;color:#334155;font-size:11px;margin:0;">
    ZYNORIQ Intelligence™ · Plan PREMIUM/BUSINESS ·
    <a href="https://zynoriq.com/dashboard" style="color:#4c4c8a;">Gérer mes alertes Sentinel</a>
  </p>
</div>
</body></html>"""


def _send_sentinel_email(user_email: str, name: str, top3: list, lang: str = "fr") -> bool:
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    smtp_from = os.environ.get("SMTP_FROM", smtp_user)
    smtp_port = int(os.environ.get("SMTP_PORT", 465))

    subject = _SUBJECTS.get(lang, _SUBJECTS["fr"])
    html    = _build_email_html(name, top3, lang)

    if not smtp_host or not smtp_user:
        print(f"  [sentinel] SMTP non configuré — alerte simulée pour {user_email}")
        print(f"  [sentinel] Top3: {[(p['state'],p['tod'],p['confidence']) for p in top3]}")
        return True  # don't fail in dev

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"ZYNORIQ Sentinel™ <{smtp_from}>"
        msg["To"]      = user_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as srv:
                srv.login(smtp_user, smtp_pass)
                srv.sendmail(smtp_from, [user_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as srv:
                srv.starttls()
                srv.login(smtp_user, smtp_pass)
                srv.sendmail(smtp_from, [user_email], msg.as_string())
        return True
    except Exception as e:
        print(f"  [sentinel] email error → {user_email}: {e}")
        return False

# ── Main sentinel loop ─────────────────────────────────────────────────────
def run_sentinel_loop(flask_app, report_cache: dict):
    """Entry point — run this in a daemon thread from app.py."""
    print("[sentinel] ZYNORIQ Sentinel™ démarré — surveillance pré-tirage active")
    time.sleep(90)  # let server + cache warm up

    while True:
        try:
            _run_cycle(flask_app, report_cache)
        except Exception as e:
            print(f"[sentinel] erreur cycle: {e}")
        time.sleep(5 * 60)  # run every 5 minutes


def _run_cycle(flask_app, report_cache: dict):
    upcoming = _upcoming_draws()
    if not upcoming:
        return

    # Score each upcoming draw from cache (read-only)
    scored = []
    for state, tod, time_str, minutes_away in upcoming:
        result = _score_draw(state, tod, report_cache)
        if result:
            result["minutes_away"] = minutes_away
            result["time_str"]     = time_str
            scored.append(result)

    if not scored:
        return

    scored.sort(key=lambda x: x["score"], reverse=True)
    top3 = scored[:TOP_N]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    new_picks = [s for s in top3 if not _already_sent(s["state"], s["tod"], today)]
    if not new_picks:
        return

    print(f"  [sentinel] Top3 → {[(s['state'],s['tod'],str(s['confidence'])+'%') for s in top3]}")

    # Load active subscribers + verify premium plan — all in one DB query
    with flask_app.app_context():
        try:
            from auth import User, Subscription as Sub, SentinelSubscription
            users = (User.query
                     .join(Sub, User.id == Sub.user_id, isouter=True)
                     .join(SentinelSubscription, User.id == SentinelSubscription.user_id)
                     .filter(SentinelSubscription.active == True)
                     .filter(Sub.plan.in_(SENTINEL_PLANS))
                     .filter(Sub.status.in_(["active", "trial"]))
                     .all())
        except Exception as e:
            print(f"  [sentinel] DB error: {e}")
            return

    if not users:
        return

    sent_count = 0
    for user in users:
        lang = (getattr(user, "preferred_lang", None) or "fr")[:2]
        ok   = _send_sentinel_email(user.email, user.username or "Joueur", top3, lang)
        if ok:
            sent_count += 1

    print(f"  [sentinel] {sent_count}/{len(users)} alertes envoyées")

    # Mark all top3 as sent (cooldown applies)
    for pick in top3:
        _mark_sent(pick["state"], pick["tod"], today)

# ── Sentinel status (for API) ──────────────────────────────────────────────
def sentinel_status(report_cache: dict) -> dict:
    """Return current sentinel snapshot for the /api/sentinel/status route."""
    upcoming = _upcoming_draws()
    scored = []
    for state, tod, time_str, minutes_away in upcoming:
        r = _score_draw(state, tod, report_cache)
        if r:
            r["minutes_away"] = minutes_away
            r["time_str"]     = time_str
            scored.append(r)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "upcoming_draws": len(upcoming),
        "scored":         len(scored),
        "top3":           scored[:TOP_N],
        "alert_window":   f"{ALERT_MIN_MIN}-{ALERT_MAX_MIN} min",
        "checked_at":     datetime.utcnow().isoformat() + "Z",
    }
