"""
ZYNORIQ COPILOT™ — Service Layer v2.0
Context gathering, data injection, quotas, history, prompt building
"""
import os, json, time, threading
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

# ── Quota configuration per plan ──────────────────────────────────────────
COPILOT_QUOTAS = {
    None: 5,         # free / no plan
    "free": 5,
    "pro": 50,
    "vip": 200,
    "elite": 1000,
    "premium": 200,
    "business": 1000,
    "enterprise": 10000,
}

# File-backed usage tracker (persists across restarts)
_USAGE_FILE = os.path.join("data", "copilot_usage.json")
_usage = {}
_usage_lock = threading.Lock()

def _load_usage():
    global _usage
    try:
        if os.path.exists(_USAGE_FILE):
            with open(_USAGE_FILE, "r") as f:
                _usage = json.load(f)
    except Exception:
        _usage = {}

def _save_usage():
    try:
        os.makedirs("data", exist_ok=True)
        with open(_USAGE_FILE, "w") as f:
            json.dump(_usage, f)
    except Exception:
        pass

_load_usage()

# File-backed history (persists across restarts)
_HISTORY_FILE = os.path.join("data", "copilot_history.json")
_history = defaultdict(list)
_history_lock = threading.Lock()

def _load_history():
    global _history
    try:
        if os.path.exists(_HISTORY_FILE):
            with open(_HISTORY_FILE, "r") as f:
                raw = json.load(f)
                _history = defaultdict(list, {k: v for k, v in raw.items()})
    except Exception:
        _history = defaultdict(list)

def _save_history():
    try:
        os.makedirs("data", exist_ok=True)
        with open(_HISTORY_FILE, "w") as f:
            json.dump(dict(_history), f)
    except Exception:
        pass

_load_history()

# Logs
_logs = []
_logs_lock = threading.Lock()
_MAX_LOGS = 500


# ── Quota Service ─────────────────────────────────────────────────────────
def check_quota(user_id, plan):
    """Returns (allowed: bool, remaining: int, limit: int)."""
    limit = COPILOT_QUOTAS.get(plan, COPILOT_QUOTAS.get(None, 5))
    today = date.today().isoformat()
    uid = str(user_id)
    with _usage_lock:
        entry = _usage.get(uid, {})
        if entry.get("date") != today:
            entry = {"date": today, "count": 0}
            _usage[uid] = entry
        remaining = max(0, limit - entry["count"])
        return remaining > 0, remaining, limit


def consume_quota(user_id):
    """Increment usage counter for today."""
    today = date.today().isoformat()
    uid = str(user_id)
    with _usage_lock:
        entry = _usage.get(uid, {})
        if entry.get("date") != today:
            entry = {"date": today, "count": 0}
        entry["count"] += 1
        _usage[uid] = entry
        _save_usage()


# ── History Service ───────────────────────────────────────────────────────
def save_history(user_id, question, answer, mode, page, lang, used_ai):
    """Save a conversation entry (file-backed, max 50 per user)."""
    uid = str(user_id)
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "question": question[:500],
        "answer": answer[:1000],
        "mode": mode,
        "page": page,
        "lang": lang,
        "ai": used_ai,
    }
    with _history_lock:
        h = _history[uid]
        h.append(entry)
        if len(h) > 50:
            _history[uid] = h[-50:]
        _save_history()


def get_history(user_id, limit=20):
    """Return last N history entries for a user."""
    with _history_lock:
        return list(_history.get(str(user_id), []))[-limit:]


# ── Log Service ───────────────────────────────────────────────────────────
def log_request(user_id, mode, page, latency_ms, status, error=None):
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "mode": mode,
        "page": page,
        "latency_ms": round(latency_ms),
        "status": status,
    }
    if error:
        entry["error"] = str(error)[:200]
    with _logs_lock:
        _logs.append(entry)
        if len(_logs) > _MAX_LOGS:
            _logs.pop(0)


def get_logs(limit=100):
    with _logs_lock:
        return list(_logs[-limit:])


# ── Context Builder ───────────────────────────────────────────────────────
def build_page_context(page_data):
    """Build a compact text description of what the user sees on the current page."""
    ctx = page_data or {}
    parts = []

    url = ctx.get("url", "")
    parts.append(f"Page: {url}")

    if ctx.get("state"):
        parts.append(f"État sélectionné: {ctx['state']}")
    if ctx.get("game"):
        parts.append(f"Jeu: {ctx['game']}")
    if ctx.get("tod"):
        parts.append(f"Tirage: {ctx['tod']}")

    # Predictions on page
    preds = ctx.get("predictions")
    if preds and isinstance(preds, list):
        top5 = preds[:5]
        pred_str = ", ".join(
            f"#{i+1} {p.get('combo','?')} ({p.get('confidence',0)}%)"
            for i, p in enumerate(top5)
        )
        parts.append(f"Top 5 prédictions: {pred_str}")

    # Latest draws
    draws = ctx.get("latest_draws")
    if draws and isinstance(draws, list):
        draw_str = ", ".join(
            f"{d.get('date','?')} {d.get('tod','')}: {d.get('d1','')}-{d.get('d2','')}-{d.get('d3','')}"
            for d in draws[:5]
        )
        parts.append(f"Derniers tirages: {draw_str}")

    # Hot/cold
    hot = ctx.get("hot_digits")
    cold = ctx.get("cold_digits")
    if hot:
        parts.append(f"Chiffres chauds: {hot}")
    if cold:
        parts.append(f"Chiffres froids: {cold}")

    # Accuracy
    acc = ctx.get("accuracy")
    if acc:
        parts.append(f"Accuracy: Straight {acc.get('straight_rate',0)}%, Box {acc.get('box_rate',0)}%")

    # Track record
    tr = ctx.get("track_record")
    if tr:
        parts.append(f"Track Record: {tr.get('total_predictions',0)} prédictions, "
                      f"Straight {tr.get('straight_hits',0)}, Box {tr.get('box_hits',0)}")

    # Business AI
    biz = ctx.get("business")
    if biz:
        parts.append(f"Business AI — Projet: {biz.get('name','?')}, Score: {biz.get('score','?')}/100")

    # User plan
    plan = ctx.get("plan")
    if plan:
        parts.append(f"Plan utilisateur: {plan}")

    # Filters
    filters = ctx.get("filters")
    if filters:
        parts.append(f"Filtres actifs: {json.dumps(filters, ensure_ascii=False)}")

    return "\n".join(parts)


# ── Prompt Builder ────────────────────────────────────────────────────────
_SYSTEM_BASE = {
    'lottery': """Tu es ZYNORIQ Copilot™, l'assistant IA officiel de ZYNORIQ Intelligence™.

PLATEFORME: 44+ États US · Pick 3/4/5 · Powerball · Mega Millions · 7 modèles ML (XGBoost, Random Forest, Gradient Boosting, Markov 1/2/3, Monte Carlo 50K, Fourier, Gap Analysis)

TERMES: Straight=ordre exact (1/1000). Box=tout ordre (1/167 six-way). Double=2 chiffres identiques. Triple=3 identiques. Chaud=fréquent. Froid=rare. En retard=écart>moyenne.

RÈGLES ABSOLUES:
1. Réponds UNIQUEMENT avec les données fournies dans le CONTEXTE ci-dessous
2. Si une donnée manque, dis: "Je n'ai pas cette information sur la page actuelle. Va sur [page pertinente] pour la voir."
3. Ne JAMAIS inventer de chiffres, taux, ou statistiques
4. Ne JAMAIS promettre de gains — les loteries sont des jeux de hasard
5. Pour des prédictions spécifiques, redirige vers /analyze
6. Réponds dans la langue de l'utilisateur
7. Max 250 mots. Utilise **gras**, listes •, structure claire
8. Structure: résumé court → analyse → points importants → action recommandée""",

    'business': """Tu es ZYNORIQ Copilot™ en mode Business Intelligence.
Tu aides avec: analyse de viabilité, plans 30-60-90 jours, risques, opportunités, KPIs.

RÈGLES:
1. Base tes réponses UNIQUEMENT sur les données du CONTEXTE
2. Si données insuffisantes: "Données insuffisantes pour répondre avec précision."
3. Max 300 mots. Structure: résumé → analyse → recommandations → prochaine action
4. Réponds dans la langue de l'utilisateur""",

    'analyst': """Tu es ZYNORIQ Copilot™ en mode Data Analyst.
Tu expliques: fréquences, écarts, distributions, performances ML, tendances historiques, scores.

RÈGLES:
1. UNIQUEMENT les données du CONTEXTE — jamais d'invention
2. Sois précis avec les chiffres
3. Max 250 mots
4. Réponds dans la langue de l'utilisateur""",

    'coach': """Tu es ZYNORIQ Copilot™ en mode Coach.
Tu guides: stratégies, interprétation, utilisation de la plateforme, jeu responsable.

RÈGLES:
1. Ton amical et encourageant
2. TOUJOURS rappeler le jeu responsable
3. Base tes conseils sur les données réelles du CONTEXTE
4. Max 200 mots
5. Réponds dans la langue de l'utilisateur""",
}


def build_system_prompt(mode, page_context_text, lang):
    """Build the full system prompt with real data context."""
    base = _SYSTEM_BASE.get(mode, _SYSTEM_BASE['lottery'])
    return f"""{base}

LANGUE: {lang}

══════ CONTEXTE DE LA PAGE (données réelles) ══════
{page_context_text}
══════ FIN DU CONTEXTE ══════

Utilise UNIQUEMENT ces données pour répondre. Ne fabrique rien."""


# ── Claude API Call ───────────────────────────────────────────────────────
def call_claude(message, mode, lang, history, page_context_text):
    """Call Claude Haiku with real data context. Returns (reply, used_ai, latency_ms)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, False, 0

    start = time.time()
    try:
        import httpx
        system = build_system_prompt(mode, page_context_text, lang)

        messages = []
        for h in (history or [])[-8:]:
            role = h.get("role", "user")
            r = "assistant" if role == "assistant" else "user"
            messages.append({"role": r, "content": h.get("content", "")})

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
                "max_tokens": 600,
                "system": system,
                "messages": messages,
            },
            timeout=15,
        )
        latency = (time.time() - start) * 1000
        if resp.status_code == 200:
            data = resp.json()
            text = data.get("content", [{}])[0].get("text", "")
            return text, True, latency
        else:
            print(f"[copilot] Claude API error {resp.status_code}: {resp.text[:200]}")
            return None, False, latency
    except Exception as e:
        latency = (time.time() - start) * 1000
        print(f"[copilot] Claude API exception: {e}")
        return None, False, latency


# ── Fallback Templates ────────────────────────────────────────────────────
FALLBACK = {
    'fr': {
        'no_data': "Je n'ai pas assez de données sur cette page pour répondre avec précision. Essaie d'aller sur **/analyze** pour lancer une analyse ou **/results** pour voir les derniers tirages.",
        'quota': "Tu as atteint ta limite quotidienne de questions ({limit}/jour). Passe au plan supérieur pour plus de questions, ou réessaie demain.",
        'error': "Désolé, une erreur s'est produite. Réessaie dans un instant.",
        'default': "Je suis **ZYNORIQ Copilot™**. Pose-moi une question sur tes prédictions, tendances, scores ou stratégies !",
    },
    'en': {
        'no_data': "I don't have enough data on this page to answer accurately. Try going to **/analyze** to run an analysis or **/results** to see latest draws.",
        'quota': "You've reached your daily question limit ({limit}/day). Upgrade your plan for more, or try again tomorrow.",
        'error': "Sorry, an error occurred. Please try again shortly.",
        'default': "I'm **ZYNORIQ Copilot™**. Ask me about your predictions, trends, scores or strategies!",
    },
}

def fallback_reply(lang, key, **kwargs):
    fb = FALLBACK.get(lang, FALLBACK.get('en', {}))
    text = fb.get(key, fb.get('default', ''))
    if kwargs:
        text = text.format(**kwargs)
    return text
