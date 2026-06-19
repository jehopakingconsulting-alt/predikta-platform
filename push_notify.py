"""
PREDIKTA — Push Notifications (Web Push / VAPID)

Stockage des abonnements : data/push_subscriptions.json
"""

import json
import os
import threading
from datetime import datetime, timezone

_DIR  = os.path.join(os.path.dirname(__file__), "data")
_FILE = os.path.join(_DIR, "push_subscriptions.json")
_lock = threading.Lock()

# ── VAPID config ─────────────────────────────────────────────────────────────
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY",
    "BGspzulRJI0kweKfLtQV5OLGFLnPMjrO5c38nvPw6Xs8g9b3LZBr_TLewG5C6WopeyJrWm11YUlC_AMS1BA6QZY")

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgm7B9x8Fz81jABcc+
0KARXzwQUv6WJMvb3/T72QvV8n+hRANCAARrKc7pUSSNJMHiny7UFeTixhS5zzI6
zuXN/J7z8Ol7PIPW9y2Qa/0y3sBuQulqKXsia1ptdWFJQvwDEtQQOkGW
-----END PRIVATE KEY-----""")

VAPID_CLAIMS = {"sub": "mailto:admin@predikta.app"}

# ── Stockage abonnements ──────────────────────────────────────────────────────

def _read() -> list:
    try:
        with open(_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _write(data: list):
    os.makedirs(_DIR, exist_ok=True)
    tmp = _FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _FILE)

def add_subscription(sub: dict) -> bool:
    """Enregistre un abonnement push (évite les doublons par endpoint)."""
    endpoint = sub.get("endpoint", "")
    if not endpoint:
        return False
    with _lock:
        subs = _read()
        subs = [s for s in subs if s.get("endpoint") != endpoint]
        subs.append({"endpoint": endpoint, "keys": sub.get("keys", {}),
                     "added_at": datetime.now(timezone.utc).isoformat()})
        _write(subs)
    return True

def remove_subscription(endpoint: str):
    with _lock:
        subs = [s for s in _read() if s.get("endpoint") != endpoint]
        _write(subs)

def get_subscriptions() -> list:
    with _lock:
        return _read()

# ── Envoi d'une notification ──────────────────────────────────────────────────

def send_push(title: str, body: str, data: dict | None = None, icon: str = "/static/icon-192.png"):
    """
    Envoie une notification push à tous les abonnés.
    Retourne (ok_count, fail_count).
    """
    from pywebpush import webpush, WebPushException

    subs     = get_subscriptions()
    ok, fail = 0, 0
    dead     = []

    payload = json.dumps({
        "title": title,
        "body":  body,
        "icon":  icon,
        "data":  data or {},
    }, ensure_ascii=False)

    for sub in subs:
        try:
            webpush(
                subscription_info={"endpoint": sub["endpoint"], "keys": sub["keys"]},
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS,
            )
            ok += 1
        except WebPushException as e:
            status = getattr(e.response, "status_code", 0) if e.response else 0
            if status in (404, 410):   # abonnement expiré/révoqué
                dead.append(sub["endpoint"])
            else:
                print(f"  [push] erreur {status}: {e}")
            fail += 1
        except Exception as e:
            print(f"  [push] erreur inattendue: {e}")
            fail += 1

    # Purge des abonnements morts
    if dead:
        with _lock:
            alive = [s for s in _read() if s.get("endpoint") not in dead]
            _write(alive)

    print(f"  [push] '{title}' → {ok} OK / {fail} échec")
    return ok, fail


def send_draw_notification(state: str, state_name: str, tod: str,
                            d1: str, d2: str, d3: str,
                            tr_result: dict | None = None):
    """
    Notif spécialisée pour un nouveau tirage.
    tr_result : résultat du live track record (optionnel) pour message contextuel.
    """
    tod_icon = "☀️" if tod == "Midday" else "🌙"
    digits   = f"{d1}-{d2}-{d3}"
    title    = f"🎯 {state_name} {tod_icon} {tod}: {digits}"

    if tr_result:
        if tr_result.get("hit_straight"):
            body = f"✅ EXACT ! Votre combo #1 était {tr_result['consensus_top10'][0]}"
        elif tr_result.get("hit_box"):
            rank = tr_result.get("consensus_box_rank", "?")
            body = f"📦 BOX hit ! Rang #{rank} dans vos prédictions"
        elif tr_result.get("consensus_box_rank"):
            rank = tr_result.get("consensus_box_rank")
            body = f"Proche ! Rang #{rank} dans vos combos. Tirage: {digits}"
        else:
            body = f"Résultat: {digits} · Vos prédictions n'étaient pas dans le Top 10"
    else:
        body = f"Résultat officiel: {digits}"

    send_push(title, body, data={
        "state": state, "tod": tod,
        "digits": digits, "url": f"/results?state={state}"
    })
