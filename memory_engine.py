"""
ZYNORIQ MEMORY™ — Personal Intelligence Memory Engine v1.0
Profiles, preferences, conversation memory, recommendations, analytics
"""
import os, json, time, threading
from datetime import datetime, date, timedelta
from collections import defaultdict, Counter

# ── Import DB from auth module (lazy) ─────────────────────────────────────
_db = None
_User = None

def _get_db():
    global _db, _User
    if _db is None:
        import auth as _auth
        _db = _auth.db
        _User = _auth.User
    return _db, _User


# ═══════════════════════════════════════════════════════════════════════════
# DB MODELS
# ═══════════════════════════════════════════════════════════════════════════
from flask_sqlalchemy import SQLAlchemy

db_ref = None  # set by init_memory()

class UserMemory:
    """Proxy for the memory table — created dynamically after db init."""
    pass

_MemoryProfile = None
_MemoryConversation = None
_MemoryActivity = None

def _define_models(db):
    global _MemoryProfile, _MemoryConversation, _MemoryActivity

    if _MemoryProfile is not None:
        return

    class MemoryProfile(db.Model):
        __tablename__ = "memory_profiles"
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False, index=True)
        data_json = db.Column(db.Text, default="{}")
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def get_data(self):
            try:
                return json.loads(self.data_json or "{}")
            except Exception:
                return {}

        def set_data(self, data):
            self.data_json = json.dumps(data, ensure_ascii=False)

        def to_dict(self):
            d = self.get_data()
            d["user_id"] = self.user_id
            d["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
            return d

    class MemoryConversation(db.Model):
        __tablename__ = "memory_conversations"
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        mode = db.Column(db.String(20), default="lottery")
        page = db.Column(db.String(200), default="/")
        lang = db.Column(db.String(5), default="fr")
        question = db.Column(db.Text, nullable=False)
        answer = db.Column(db.Text, default="")
        used_ai = db.Column(db.Boolean, default=False)

        def to_dict(self):
            return {
                "id": self.id,
                "ts": self.created_at.isoformat() if self.created_at else None,
                "mode": self.mode,
                "page": self.page,
                "lang": self.lang,
                "question": self.question[:200],
                "answer": self.answer[:500],
                "ai": self.used_ai,
            }

    class MemoryActivity(db.Model):
        __tablename__ = "memory_activities"
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        activity_type = db.Column(db.String(30), nullable=False)  # page_visit, analysis, report, search
        page = db.Column(db.String(200), default="/")
        state = db.Column(db.String(6), nullable=True)
        game = db.Column(db.String(30), nullable=True)
        details_json = db.Column(db.Text, default="{}")

        def to_dict(self):
            return {
                "id": self.id,
                "ts": self.created_at.isoformat() if self.created_at else None,
                "type": self.activity_type,
                "page": self.page,
                "state": self.state,
                "game": self.game,
            }

    _MemoryProfile = MemoryProfile
    _MemoryConversation = MemoryConversation
    _MemoryActivity = MemoryActivity


def init_memory(app, db):
    """Initialize Memory tables. Call after auth.init_app()."""
    global db_ref
    db_ref = db
    _define_models(db)
    with app.app_context():
        db.create_all()


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY SERVICE — Profile CRUD
# ═══════════════════════════════════════════════════════════════════════════
_DEFAULT_PROFILE = {
    "preferred_lang": "fr",
    "country": "",
    "favorite_states": [],
    "favorite_games": [],
    "favorite_dashboards": [],
    "theme": "dark",
    "usage_frequency": "unknown",
    "recent_searches": [],
    "recent_analyses": [],
    "recent_reports": [],
    "business_projects": [],
    "display_prefs": {},
    "notification_prefs": {"push": True, "email": True, "sms": False},
    "visit_count": 0,
    "last_visit": None,
    "first_visit": None,
}


def get_profile(user_id):
    """Get or create a memory profile for a user."""
    if not _MemoryProfile:
        return dict(_DEFAULT_PROFILE)
    prof = _MemoryProfile.query.filter_by(user_id=user_id).first()
    if not prof:
        return dict(_DEFAULT_PROFILE)
    data = prof.get_data()
    merged = dict(_DEFAULT_PROFILE)
    merged.update(data)
    return merged


def save_profile(user_id, data):
    """Save (merge) profile data for a user."""
    if not _MemoryProfile or not db_ref:
        return False
    prof = _MemoryProfile.query.filter_by(user_id=user_id).first()
    if not prof:
        prof = _MemoryProfile(user_id=user_id)
        db_ref.session.add(prof)
    existing = prof.get_data()
    existing.update(data)
    prof.set_data(existing)
    db_ref.session.commit()
    return True


def update_profile_field(user_id, field, value):
    """Update a single field in the user profile."""
    profile = get_profile(user_id)
    profile[field] = value
    return save_profile(user_id, profile)


def clear_memory(user_id):
    """Delete all memory for a user (GDPR-friendly)."""
    if not db_ref:
        return False
    if _MemoryProfile:
        _MemoryProfile.query.filter_by(user_id=user_id).delete()
    if _MemoryConversation:
        _MemoryConversation.query.filter_by(user_id=user_id).delete()
    if _MemoryActivity:
        _MemoryActivity.query.filter_by(user_id=user_id).delete()
    db_ref.session.commit()
    return True


def export_memory(user_id):
    """Export all user memory data (GDPR data portability)."""
    profile = get_profile(user_id)
    convos = get_conversations(user_id, limit=100)
    activities = get_activities(user_id, limit=200)
    return {
        "profile": profile,
        "conversations": convos,
        "activities": activities,
        "exported_at": datetime.utcnow().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CONVERSATION MEMORY
# ═══════════════════════════════════════════════════════════════════════════
def save_conversation(user_id, question, answer, mode, page, lang, used_ai):
    """Save a conversation to persistent DB."""
    if not _MemoryConversation or not db_ref:
        return
    entry = _MemoryConversation(
        user_id=user_id, question=question[:1000], answer=answer[:2000],
        mode=mode, page=page, lang=lang, used_ai=used_ai,
    )
    db_ref.session.add(entry)
    db_ref.session.commit()


def get_conversations(user_id, limit=20):
    if not _MemoryConversation:
        return []
    rows = (_MemoryConversation.query
            .filter_by(user_id=user_id)
            .order_by(_MemoryConversation.id.desc())
            .limit(limit).all())
    return [r.to_dict() for r in reversed(rows)]


def get_frequent_questions(user_id, limit=5):
    convos = get_conversations(user_id, limit=100)
    questions = [c["question"] for c in convos]
    counts = Counter(questions)
    return [q for q, _ in counts.most_common(limit)]


# ═══════════════════════════════════════════════════════════════════════════
# ACTIVITY TRACKING
# ═══════════════════════════════════════════════════════════════════════════
def track_activity(user_id, activity_type, page="/", state=None, game=None, details=None):
    """Track a user activity (page visit, analysis, report, etc.)."""
    if not _MemoryActivity or not db_ref:
        return
    entry = _MemoryActivity(
        user_id=user_id, activity_type=activity_type,
        page=page, state=state, game=game,
        details_json=json.dumps(details or {}, ensure_ascii=False),
    )
    db_ref.session.add(entry)
    db_ref.session.commit()

    # Auto-update profile based on activity
    _auto_learn(user_id, activity_type, page, state, game)


def get_activities(user_id, limit=50, activity_type=None):
    if not _MemoryActivity:
        return []
    q = _MemoryActivity.query.filter_by(user_id=user_id)
    if activity_type:
        q = q.filter_by(activity_type=activity_type)
    rows = q.order_by(_MemoryActivity.id.desc()).limit(limit).all()
    return [r.to_dict() for r in reversed(rows)]


def _auto_learn(user_id, activity_type, page, state, game):
    """Automatically update user profile based on activity patterns."""
    try:
        profile = get_profile(user_id)

        # Track visit count
        profile["visit_count"] = profile.get("visit_count", 0) + 1
        profile["last_visit"] = datetime.utcnow().isoformat()
        if not profile.get("first_visit"):
            profile["first_visit"] = profile["last_visit"]

        # Learn favorite states
        if state:
            favs = profile.get("favorite_states", [])
            if state not in favs:
                favs.append(state)
            if len(favs) > 10:
                favs = favs[-10:]
            profile["favorite_states"] = favs

        # Learn favorite games
        if game:
            fav_games = profile.get("favorite_games", [])
            if game not in fav_games:
                fav_games.append(game)
            if len(fav_games) > 10:
                fav_games = fav_games[-10:]
            profile["favorite_games"] = fav_games

        # Track recent analyses
        if activity_type == "analysis":
            profile["analysis_count"] = profile.get("analysis_count", 0) + 1
            recent = profile.get("recent_analyses", [])
            recent.append({"state": state, "game": game, "ts": datetime.utcnow().isoformat()})
            profile["recent_analyses"] = recent[-20:]

        # Track recent searches
        if activity_type == "search":
            recent = profile.get("recent_searches", [])
            recent.append({"page": page, "ts": datetime.utcnow().isoformat()})
            profile["recent_searches"] = recent[-20:]

        # Determine usage frequency
        vc = profile["visit_count"]
        if vc >= 100:
            profile["usage_frequency"] = "power_user"
        elif vc >= 30:
            profile["usage_frequency"] = "regular"
        elif vc >= 10:
            profile["usage_frequency"] = "active"
        else:
            profile["usage_frequency"] = "new"

        save_profile(user_id, profile)
    except Exception as e:
        print(f"[memory] auto_learn error: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════
def get_recommendations(user_id, lang="fr"):
    """Generate personalized recommendations based on ML-like behavior scoring."""
    profile = get_profile(user_id)
    recs = []
    scores = {}  # {rec_type: float score 0-1}

    fav_states = profile.get("favorite_states", [])
    recent_analyses = profile.get("recent_analyses", [])
    recent_searches = profile.get("recent_searches", [])
    visit_count = profile.get("visit_count", 0)
    plan = profile.get("plan")
    usage = profile.get("usage_frequency", "new")
    fav_games = profile.get("favorite_games", [])

    # ── Behavior-weighted scoring ──────────────────────────────────
    # Score each recommendation based on user behavior patterns

    # 1. Explore new states — higher score if user has few favorites
    all_top_states = ["NY","FL","GA","TX","CA","PA","NJ","OH","IL","NC","MD","TN","VA","SC","MI","CT","WI","LA","CO"]
    unexplored = [s for s in all_top_states if s not in fav_states][:3]
    if unexplored:
        explore_score = max(0.3, 1.0 - len(fav_states) * 0.08)
        scores["explore_states"] = explore_score
        recs.append({
            "type": "explore_states",
            "title": _rt(lang, "explore_states"),
            "description": _rt(lang, "explore_states_desc").format(states=", ".join(unexplored)),
            "action": "/results",
            "score": explore_score,
        })

    # 2. First analysis — only if truly no analyses
    if not recent_analyses:
        scores["first_analysis"] = 1.0
        recs.append({
            "type": "first_analysis",
            "title": _rt(lang, "first_analysis"),
            "description": _rt(lang, "first_analysis_desc"),
            "action": "/analyze",
            "score": 1.0,
        })

    # 3. Upgrade — check real subscription from DB
    real_plan = None
    u = None
    try:
        _, User = _get_db()
        u = User.query.get(user_id)
        if u and u.subscription:
            real_plan = u.subscription.plan
    except Exception:
        real_plan = plan
    plan_order = {"pro": 1, "vip": 2, "elite": 3, "business": 4}
    current_level = plan_order.get(real_plan, 0)

    if current_level == 0:
        recs.append({"type": "upgrade", "title": _rt(lang, "upgrade"), "description": _rt(lang, "upgrade_desc"), "action": "/pro", "score": 0.8})
    elif current_level < 3:
        next_plan = {1: "VIP", 2: "PREMIUM"}.get(current_level, "PREMIUM")
        recs.append({"type": "upgrade", "title": _rt(lang, "upgrade_next").format(plan=next_plan), "description": _rt(lang, "upgrade_next_desc"), "action": "/pro", "score": 0.5})

    # 3b. Founders program — if not already a founder
    is_founder = getattr(u, 'founder_badge', False) if u else False
    if not is_founder and current_level > 0:
        recs.append({"type": "founders", "title": _rt(lang, "try_founders"), "description": _rt(lang, "try_founders_desc"), "action": "/founders", "score": 0.6})

    # 3c. Ambassadors — if enough visits
    if visit_count >= 5:
        recs.append({"type": "ambassadors", "title": _rt(lang, "try_ambassadors"), "description": _rt(lang, "try_ambassadors_desc"), "action": "/ambassadors", "score": 0.4})

    # 4. Business AI — for engaged users who haven't tried it
    biz_used = any("bizai" in (a.get("page") or "") for a in recent_analyses + recent_searches)
    if visit_count >= 10 and not biz_used:
        biz_score = min(0.8, 0.3 + visit_count * 0.02)
        scores["try_business"] = biz_score
        recs.append({
            "type": "try_business",
            "title": _rt(lang, "try_business"),
            "description": _rt(lang, "try_business_desc"),
            "action": "/bizai",
            "score": biz_score,
        })

    # 5. Copilot — for users who haven't tried it much
    convos = get_conversations(user_id, limit=5)
    if len(convos) < 3:
        copilot_score = max(0.4, 0.8 - len(convos) * 0.15)
        recs.append({
            "type": "try_copilot",
            "title": _rt(lang, "try_copilot"),
            "description": _rt(lang, "try_copilot_desc"),
            "action": "#copilot",
            "score": copilot_score,
        })

    # 6. Pick 4 — if user only uses Pick 3
    if fav_games and "pick3" in str(fav_games).lower() and "pick4" not in str(fav_games).lower():
        recs.append({
            "type": "try_pick4",
            "title": _rt(lang, "try_pick4"),
            "description": _rt(lang, "try_pick4_desc"),
            "action": "/pick4-predictions",
            "score": 0.5,
        })

    # 7. Memory Center — for users who don't know it exists
    if visit_count >= 5 and not any(s.get("page") == "/memory" for s in recent_searches):
        recs.append({
            "type": "memory_center",
            "title": _rt(lang, "try_memory"),
            "description": _rt(lang, "try_memory_desc"),
            "action": "/memory",
            "score": 0.35,
        })

    # Sort by score (ML-weighted, highest first)
    return sorted(recs, key=lambda r: r.get("score", 0.5), reverse=True)


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD CONTEXT (what changed since last visit)
# ═══════════════════════════════════════════════════════════════════════════
def get_dashboard_context(user_id, lang="fr"):
    """Generate personalized dashboard content for the user."""
    profile = get_profile(user_id)
    last_visit = profile.get("last_visit")

    ctx = {
        "greeting_name": "",
        "visit_count": profile.get("visit_count", 0),
        "analysis_count": profile.get("analysis_count", 0),
        "usage_level": profile.get("usage_frequency", "new"),
        "favorite_states": profile.get("favorite_states", []),
        "recent_analyses": profile.get("recent_analyses", [])[-5:],
        "recent_reports": profile.get("recent_reports", [])[-5:],
        "recommendations": get_recommendations(user_id, lang),
        "last_visit": last_visit,
    }

    # Get user name
    try:
        _, User = _get_db()
        user = User.query.get(user_id)
        if user:
            ctx["greeting_name"] = user.username
    except Exception:
        pass

    return ctx


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY PREFERENCES (toggle categories)
# ═══════════════════════════════════════════════════════════════════════════
_DEFAULT_PREFS = {
    "track_conversations": True,
    "track_activities": True,
    "track_searches": True,
    "personalized_recommendations": True,
    "personalized_dashboard": True,
}

def get_preferences(user_id):
    profile = get_profile(user_id)
    prefs = profile.get("memory_preferences", {})
    merged = dict(_DEFAULT_PREFS)
    merged.update(prefs)
    return merged

def save_preferences(user_id, prefs):
    return update_profile_field(user_id, "memory_preferences", prefs)


# ═══════════════════════════════════════════════════════════════════════════
# RECOMMENDATION TRANSLATIONS
# ═══════════════════════════════════════════════════════════════════════════
_REC_T = {
    'fr': {
        'explore_states': 'Explorer de nouveaux États',
        'explore_states_desc': 'Découvrez les analyses pour {states} — ces États ont des données riches et des tendances intéressantes.',
        'first_analysis': 'Lancez votre première analyse',
        'first_analysis_desc': 'Allez sur /analyze, choisissez un État et découvrez les prédictions de nos 7 modèles ML.',
        'upgrade': 'Passez au plan PRO',
        'upgrade_desc': 'Débloquez plus d\'analyses, d\'alertes et de fonctionnalités avancées.',
        'upgrade_next': 'Passez au plan {plan}',
        'upgrade_next_desc': 'Débloquez plus d\'États, d\'analyses et de fonctionnalités premium.',
        'try_business': 'Essayez Business AI',
        'try_business_desc': 'Analysez un projet entrepreneurial avec notre moteur d\'intelligence d\'affaires.',
        'try_copilot': 'Utilisez ZYNORIQ Copilot',
        'try_copilot_desc': 'Posez des questions sur vos prédictions, tendances et stratégies à notre assistant IA.',
        'try_founders': 'Devenez Membre Fondateur',
        'try_founders_desc': 'Verrouillez votre prix à $29/mois à vie — 500 places seulement.',
        'try_ambassadors': 'Programme Ambassadeur',
        'try_ambassadors_desc': 'Parrainez vos amis et gagnez des commissions récurrentes.',
        'try_memory': 'Découvrez Memory Center',
        'try_memory_desc': 'Votre profil intelligent — consultez vos statistiques et préférences.',
        'try_pick4': 'Essayez Pick 4',
        'try_pick4_desc': 'Étendez vos prédictions aux jeux Pick 4 / Cash 4.',
    },
    'en': {
        'explore_states': 'Explore new States',
        'explore_states_desc': 'Discover analyses for {states} — these states have rich data and interesting trends.',
        'first_analysis': 'Run your first analysis',
        'first_analysis_desc': 'Go to /analyze, pick a state and discover predictions from our 7 ML models.',
        'upgrade': 'Upgrade to PRO',
        'upgrade_desc': 'Unlock more analyses, alerts and advanced features.',
        'upgrade_next': 'Upgrade to {plan}',
        'upgrade_next_desc': 'Unlock more states, analyses and premium features.',
        'try_business': 'Try Business AI',
        'try_business_desc': 'Analyze a business project with our intelligence engine.',
        'try_copilot': 'Use ZYNORIQ Copilot',
        'try_copilot_desc': 'Ask questions about your predictions, trends and strategies to our AI assistant.',
        'try_founders': 'Become a Founding Member',
        'try_founders_desc': 'Lock your price at $29/mo for life — 500 spots only.',
        'try_ambassadors': 'Ambassador Program',
        'try_ambassadors_desc': 'Refer friends and earn recurring commissions.',
        'try_memory': 'Discover Memory Center',
        'try_memory_desc': 'Your smart profile — view your stats and preferences.',
        'try_pick4': 'Try Pick 4',
        'try_pick4_desc': 'Expand your predictions to Pick 4 / Cash 4 games.',
    },
    'es': {
        'explore_states': 'Explorar nuevos Estados',
        'explore_states_desc': 'Descubre análisis para {states} — estos estados tienen datos ricos y tendencias interesantes.',
        'first_analysis': 'Ejecuta tu primer análisis',
        'first_analysis_desc': 'Ve a /analyze, elige un estado y descubre predicciones de nuestros 7 modelos ML.',
        'upgrade': 'Actualiza a PRO',
        'upgrade_desc': 'Desbloquea más análisis, alertas y funciones avanzadas.',
        'upgrade_next': 'Actualiza a {plan}',
        'upgrade_next_desc': 'Desbloquea más estados, análisis y funciones premium.',
        'try_business': 'Prueba Business AI',
        'try_business_desc': 'Analiza un proyecto empresarial con nuestro motor de inteligencia.',
        'try_copilot': 'Usa ZYNORIQ Copilot',
        'try_copilot_desc': 'Pregunta sobre predicciones, tendencias y estrategias a nuestro asistente IA.',
        'try_founders': 'Conviértase en Miembro Fundador',
        'try_founders_desc': 'Asegure su precio a $29/mes de por vida — solo 500 plazas.',
        'try_ambassadors': 'Programa Embajador',
        'try_ambassadors_desc': 'Recomiende amigos y gane comisiones recurrentes.',
        'try_memory': 'Descubra Memory Center',
        'try_memory_desc': 'Su perfil inteligente — consulte sus estadísticas y preferencias.',
        'try_pick4': 'Pruebe Pick 4',
        'try_pick4_desc': 'Amplíe sus predicciones a los juegos Pick 4 / Cash 4.',
    },
    'pt': {
        'explore_states': 'Explorar novos Estados',
        'explore_states_desc': 'Descubra análises para {states} — esses estados têm dados ricos e tendências interessantes.',
        'first_analysis': 'Execute sua primeira análise',
        'first_analysis_desc': 'Vá para /analyze, escolha um estado e descubra previsões dos nossos 7 modelos ML.',
        'upgrade': 'Atualize para PRO',
        'upgrade_desc': 'Desbloqueie mais análises, alertas e recursos avançados.',
        'upgrade_next': 'Atualize para {plan}',
        'upgrade_next_desc': 'Desbloqueie mais estados, análises e recursos premium.',
        'try_business': 'Experimente Business AI',
        'try_business_desc': 'Analise um projeto empresarial com nosso motor de inteligência.',
        'try_copilot': 'Use ZYNORIQ Copilot',
        'try_copilot_desc': 'Pergunte sobre previsões, tendências e estratégias ao nosso assistente IA.',
        'try_founders': 'Torne-se Membro Fundador',
        'try_founders_desc': 'Garanta seu preço a $29/mês para sempre — apenas 500 vagas.',
        'try_ambassadors': 'Programa Embaixador',
        'try_ambassadors_desc': 'Indique amigos e ganhe comissões recorrentes.',
        'try_memory': 'Descubra Memory Center',
        'try_memory_desc': 'Seu perfil inteligente — veja suas estatísticas e preferências.',
        'try_pick4': 'Experimente Pick 4',
        'try_pick4_desc': 'Expanda suas previsões para jogos Pick 4 / Cash 4.',
    },
    'ht': {
        'explore_states': 'Eksplore nouvo Eta',
        'explore_states_desc': 'Dekouvri analiz pou {states} — eta sa yo gen done rich ak tandans enterasan.',
        'first_analysis': 'Lanse premye analiz ou',
        'first_analysis_desc': 'Ale sou /analyze, chwazi yon eta epi dekouvri prediksyon 7 modèl ML nou yo.',
        'upgrade': 'Pase nan plan PRO',
        'upgrade_desc': 'Debloke plis analiz, alèt ak fonksyon avanse.',
        'upgrade_next': 'Pase nan plan {plan}',
        'upgrade_next_desc': 'Debloke plis eta, analiz ak fonksyon premium.',
        'try_business': 'Eseye Business AI',
        'try_business_desc': 'Analize yon pwojè biznis ak motè entèlijans nou an.',
        'try_copilot': 'Itilize ZYNORIQ Copilot',
        'try_copilot_desc': 'Poze kesyon sou prediksyon, tandans ak estrateji bay asistan IA nou an.',
        'try_founders': 'Vin Manm Fondatè',
        'try_founders_desc': 'Asire pri ou a $29/mwa pou tout lavi — 500 plas sèlman.',
        'try_ambassadors': 'Pwogram Anbasadè',
        'try_ambassadors_desc': 'Envite zanmi ou epi touche komisyon regilye.',
        'try_memory': 'Dekouvri Memory Center',
        'try_memory_desc': 'Pwofil entelijan ou — gade estatistik ak preferans ou.',
        'try_pick4': 'Eseye Pick 4',
        'try_pick4_desc': 'Elaji prediksyon ou nan jwèt Pick 4 / Cash 4.',
    },
}

def _rt(lang, key):
    return (_REC_T.get(lang) or _REC_T['en']).get(key, _REC_T['en'].get(key, key))
