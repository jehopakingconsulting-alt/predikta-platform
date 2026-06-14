"""
PREDIKTA — Comptes utilisateurs, abonnements & paywall
========================================================
Phase 2a : système de comptes (nom d'utilisateur + email + mot de passe),
plans payants PRO / VIP / ELITE avec essai gratuit, quotas quotidiens et
restriction par État. Le paiement réel (Stripe) est branché en Phase 2b —
en attendant, l'activation d'un plan démarre une période d'essai puis passe
le compte en statut "expired" (bloqué) tant qu'aucun paiement n'est
enregistré.

Persistance : PostgreSQL en production (variable d'env DATABASE_URL,
fournie par Render), SQLite en local (data/predikta.db) si DATABASE_URL
n'est pas définie.
"""

import os
import re
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime, date, timedelta

from flask import Blueprint, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ── Plans & tarifs ──────────────────────────────────────────────────────────
# NB stratégie tarifaire : essais courts (1/2/3 jours) demandés par le
# business — recommandation produit : envisager 3/7/14 jours pour améliorer
# la conversion (cf. discussion). Les valeurs ci-dessous restent
# configurables sans toucher au reste du code.
PLAN_CONFIG = {
    "pro": {
        "label": "PRO",
        "price_usd": 9.99,
        "trial_days": 3,
        "analyses_per_day": 1,
        "max_states": 4,
    },
    "vip": {
        "label": "VIP",
        "price_usd": 19.99,
        "trial_days": 7,
        "analyses_per_day": 7,
        "max_states": 20,
    },
    "elite": {
        "label": "ELITE",
        "price_usd": 49.99,
        "trial_days": 7,
        "analyses_per_day": -1,   # illimité
        "max_states": -1,         # tous (44+)
        "bizai_unlimited": True,  # Business AI : analyses illimitées
    },
    "business": {
        "label": "BUSINESS",
        "price_usd": 199.99,
        "trial_days": 7,
        "analyses_per_day": -1,   # illimité
        "max_states": -1,         # tous (44+)
        "bizai_unlimited": True,  # Business AI : analyses illimitées
    },
}

PLAN_ORDER = ["pro", "vip", "elite", "business"]


# ── Modèles ──────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email         = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Connexion via fournisseur externe (Google, Facebook, Microsoft...).
    # Un compte créé via OAuth n'a pas de mot de passe (password_hash=None).
    oauth_provider = db.Column(db.String(20), nullable=True)   # ex: "google"
    oauth_id       = db.Column(db.String(128), nullable=True)  # ID unique chez le fournisseur
    avatar_url     = db.Column(db.String(512), nullable=True)

    subscription = db.relationship("Subscription", uselist=False, back_populates="user",
                                    cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        sub = self.subscription
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "oauth_provider": self.oauth_provider,
            "has_password": bool(self.password_hash),
            "subscription": sub.to_dict() if sub else None,
        }


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    plan      = db.Column(db.String(16), nullable=True)     # pro | vip | elite | None (pas encore choisi)
    status    = db.Column(db.String(16), default="none")    # none | trial | active | past_due | canceled | expired
    trial_end = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)

    allowed_states = db.Column(db.Text, nullable=True)  # JSON list, ex: '["NY","FL","GA","TX"]'

    stripe_customer_id     = db.Column(db.String(64), nullable=True)
    stripe_subscription_id = db.Column(db.String(64), nullable=True)

    user = db.relationship("User", back_populates="subscription")

    def states_list(self) -> list[str]:
        import json
        if not self.allowed_states:
            return []
        try:
            return json.loads(self.allowed_states)
        except Exception:
            return []

    def set_states(self, states: list[str]):
        import json
        self.allowed_states = json.dumps(states)

    def is_active(self) -> bool:
        """Compte utilisable (essai en cours ou abonnement payé actif)."""
        now = datetime.utcnow()
        if self.status == "trial" and self.trial_end and now <= self.trial_end:
            return True
        if self.status == "active" and (self.current_period_end is None or now <= self.current_period_end):
            return True
        return False

    def days_left(self) -> int:
        now = datetime.utcnow()
        end = self.trial_end if self.status == "trial" else self.current_period_end
        if not end:
            return 0
        delta = end - now
        return max(0, delta.days + (1 if delta.seconds > 0 else 0))

    def to_dict(self):
        cfg = PLAN_CONFIG.get(self.plan, {})
        return {
            "plan": self.plan,
            "plan_label": cfg.get("label"),
            "status": self.status,
            "is_active": self.is_active(),
            "trial_end": self.trial_end.isoformat() if self.trial_end else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "days_left": self.days_left(),
            "analyses_per_day": cfg.get("analyses_per_day"),
            "max_states": cfg.get("max_states"),
            "allowed_states": self.states_list(),
            "has_stripe_customer": bool(self.stripe_customer_id),
        }


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token      = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used       = db.Column(db.Boolean, default=False)


class UsageLog(db.Model):
    __tablename__ = "usage_log"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day            = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    analyses_count = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("user_id", "day", name="uq_usage_user_day"),)


class BizUsage(db.Model):
    """Compteur mensuel d'analyses Business Intelligence (/bizai)."""
    __tablename__ = "biz_usage"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    month          = db.Column(db.String(7), nullable=False)  # YYYY-MM
    analyses_count = db.Column(db.Integer, default=0)

    __table_args__ = (db.UniqueConstraint("user_id", "month", name="uq_bizusage_user_month"),)


class SavedPrediction(db.Model):
    """Prédiction enregistrée par l'utilisateur depuis /predictions (favoris)."""
    __tablename__ = "saved_predictions"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    state      = db.Column(db.String(4), nullable=False)
    game       = db.Column(db.String(32), nullable=False)
    tod        = db.Column(db.String(16), nullable=True)   # midday | evening | all
    label      = db.Column(db.String(120), nullable=True)  # nom personnalisé optionnel
    numbers    = db.Column(db.Text, nullable=False)        # JSON : ex. "[1,2,3]" ou {"digits":[...]}
    source     = db.Column(db.String(32), nullable=True)   # ex: "consensus", "markov", "ml"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        try:
            numbers = json.loads(self.numbers)
        except Exception:
            numbers = self.numbers
        return {
            "id": self.id,
            "state": self.state,
            "game": self.game,
            "tod": self.tod,
            "label": self.label,
            "numbers": numbers,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Alert(db.Model):
    """Alerte personnalisée (ex: nouveau tirage, numéro chaud/froid) pour un État/jeu."""
    __tablename__ = "alerts"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    state       = db.Column(db.String(4), nullable=False)
    game        = db.Column(db.String(32), nullable=False)
    alert_type  = db.Column(db.String(32), nullable=False)  # new_result | hot_number | cold_number | custom
    criteria    = db.Column(db.Text, nullable=True)         # JSON libre (ex: numéro surveillé)
    active      = db.Column(db.Boolean, default=True)
    last_triggered_at = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        try:
            criteria = json.loads(self.criteria) if self.criteria else None
        except Exception:
            criteria = self.criteria
        return {
            "id": self.id,
            "state": self.state,
            "game": self.game,
            "alert_type": self.alert_type,
            "criteria": criteria,
            "active": self.active,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BusinessReport(db.Model):
    """Rapport Business AI sauvegardé (depuis /bizai)."""
    __tablename__ = "business_reports"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title       = db.Column(db.String(160), nullable=False)
    input_json  = db.Column(db.Text, nullable=True)   # paramètres saisis par l'utilisateur
    report_json = db.Column(db.Text, nullable=False)  # rapport généré (12 sections)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, include_report=True):
        import json
        out = {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_report:
            try:
                out["input"] = json.loads(self.input_json) if self.input_json else None
            except Exception:
                out["input"] = None
            try:
                out["report"] = json.loads(self.report_json)
            except Exception:
                out["report"] = None
        return out


# ── Setup ─────────────────────────────────────────────────────────────────
def init_app(app):
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgres://"):
        # SQLAlchemy 1.4+/2.x exige le préfixe "postgresql://"
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if not db_url:
        os.makedirs("data", exist_ok=True)
        db_url = "sqlite:///" + os.path.join(os.path.dirname(__file__), "data", "predikta.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    db.init_app(app)

    with app.app_context():
        db.create_all()


# ── Helpers ──────────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def make_unique_username(base: str) -> str:
    """Génère un nom d'utilisateur valide et unique à partir d'une chaîne
    (ex: la partie locale d'un email OAuth)."""
    base = re.sub(r"[^a-zA-Z0-9_]", "", base or "")[:16] or "user"
    if len(base) < 3:
        base = (base + "user")[:16]
    candidate = base
    suffix = 0
    while User.query.filter_by(username=candidate).first():
        suffix += 1
        candidate = f"{base}{suffix}"[:20]
    return candidate


def find_or_create_oauth_user(provider: str, oauth_id: str, email: str, name: str = "",
                               avatar_url: str = ""):
    """Retourne (user, created) pour une connexion OAuth. Lie le compte à un
    utilisateur existant (même email) ou en crée un nouveau."""
    email = (email or "").strip().lower()

    user = User.query.filter_by(oauth_provider=provider, oauth_id=oauth_id).first()
    if user:
        return user, False

    user = User.query.filter_by(email=email).first() if email else None
    if user:
        # Compte existant (créé par mot de passe) → on le lie au fournisseur OAuth
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        db.session.commit()
        return user, False

    base = (email.split("@")[0] if email else name) or "user"
    username = make_unique_username(base)
    user = User(username=username, email=email or f"{username}@{provider}.predikta.local",
                 oauth_provider=provider, oauth_id=oauth_id, avatar_url=avatar_url or None)
    db.session.add(user)
    db.session.flush()

    sub = Subscription(user_id=user.id, plan=None, status="none")
    db.session.add(sub)
    db.session.commit()
    return user, True


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return db.session.get(User, uid)


def login_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({"error": "login_required", "message": "Connexion requise"}), 401
        return f(*args, **kwargs)

    return wrapper


def subscription_required(f):
    """Vérifie : connecté + abonnement actif (essai ou payé) + quota du jour
    + accès à l'État demandé. Doit être placé sur les routes premium
    (ex: /api/report)."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "login_required", "message": "Connexion requise"}), 401

        sub = user.subscription
        if not sub or not sub.plan:
            return jsonify({"error": "no_plan", "message": "Choisis un plan PRO, VIP ou ELITE pour continuer"}), 402

        if not sub.is_active():
            return jsonify({"error": "subscription_expired",
                            "message": "Ton essai/abonnement est terminé. Souscris à un plan pour continuer."}), 402

        cfg = PLAN_CONFIG.get(sub.plan, {})

        # Quota d'analyses par jour
        limit = cfg.get("analyses_per_day", 0)
        if limit is not None and limit >= 0:
            today = date.today().isoformat()
            log = UsageLog.query.filter_by(user_id=user.id, day=today).first()
            count = log.analyses_count if log else 0
            if count >= limit:
                return jsonify({"error": "quota_exceeded",
                                "message": f"Limite de {limit} analyse(s)/jour atteinte pour le plan {cfg.get('label')}."}), 429

        # Restriction par État (PRO/VIP)
        max_states = cfg.get("max_states", -1)
        if max_states is not None and max_states >= 0:
            state = (request.args.get("state") or "").upper()
            allowed = sub.states_list()
            if allowed and state and state not in allowed:
                return jsonify({"error": "state_not_allowed",
                                "message": f"L'État {state} n'est pas dans tes États sélectionnés ({cfg.get('label')})."}), 403

        return f(*args, **kwargs)

    return wrapper


def send_password_reset_email(user, token: str):
    """Envoie l'email de réinitialisation si le SMTP est configuré
    (variables d'env SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS/SMTP_FROM).
    En l'absence de configuration (dev local), le lien est juste loggé."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://predikta-tez2.onrender.com")
    reset_link = f"{base_url}/reset-password?token={token}"

    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        print(f"[auth] Lien de réinitialisation pour {user.email}: {reset_link}")
        return

    msg = EmailMessage()
    msg["Subject"] = "PREDIKTA — Réinitialisation de votre mot de passe"
    msg["From"] = os.environ.get("SMTP_FROM", "no-reply@predikta.app")
    msg["To"] = user.email
    msg.set_content(
        "Bonjour,\n\n"
        "Une demande de réinitialisation de mot de passe a été effectuée pour votre compte PREDIKTA.\n"
        f"Cliquez sur ce lien pour choisir un nouveau mot de passe (valable 1 heure) :\n{reset_link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
    )

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        print(f"[auth] Échec envoi email de réinitialisation: {e}")


def record_usage(user_id: int):
    """Incrémente le compteur d'analyses du jour pour un utilisateur."""
    today = date.today().isoformat()
    log = UsageLog.query.filter_by(user_id=user_id, day=today).first()
    if log:
        log.analyses_count += 1
    else:
        log = UsageLog(user_id=user_id, day=today, analyses_count=1)
        db.session.add(log)
    db.session.commit()


# ── Business Intelligence (/bizai) — quota Free = 1 analyse/mois ────────────
FREE_BIZAI_ANALYSES_PER_MONTH = 1


def bizai_access_required(f):
    """Vérifie : connecté + (abonnement ELITE/BUSINESS actif OU quota Free
    du mois non atteint). Seuls les abonnés avec `bizai_unlimited` actif
    (ELITE, BUSINESS) ont un accès illimité au module Business Intelligence ;
    les comptes Free, PRO et VIP sont limités à `FREE_BIZAI_ANALYSES_PER_MONTH`
    analyse(s) par mois civil."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        # Les rapports d'exemple (démo, pré-remplis) restent en accès libre
        # et ne consomment pas le quota.
        if request.method == "POST":
            body = request.get_json(silent=True) or {}
            if body.get("_example"):
                return f(*args, **kwargs)

        user = current_user()
        if not user:
            return jsonify({"error": "login_required",
                            "message": "Connecte-toi pour lancer une analyse Business Intelligence."}), 401

        sub = user.subscription
        if sub and sub.is_active() and PLAN_CONFIG.get(sub.plan, {}).get("bizai_unlimited"):
            return f(*args, **kwargs)

        month = date.today().strftime("%Y-%m")
        log = BizUsage.query.filter_by(user_id=user.id, month=month).first()
        count = log.analyses_count if log else 0
        if count >= FREE_BIZAI_ANALYSES_PER_MONTH:
            return jsonify({"error": "quota_exceeded",
                            "message": f"Limite de {FREE_BIZAI_ANALYSES_PER_MONTH} analyse(s)/mois atteinte pour le plan Free. "
                                       "Passe à un plan supérieur pour continuer."}), 429

        return f(*args, **kwargs)

    return wrapper


def record_bizai_usage(user_id: int):
    """Incrémente le compteur mensuel d'analyses Business Intelligence."""
    month = date.today().strftime("%Y-%m")
    log = BizUsage.query.filter_by(user_id=user_id, month=month).first()
    if log:
        log.analyses_count += 1
    else:
        log = BizUsage(user_id=user_id, month=month, analyses_count=1)
        db.session.add(log)
    db.session.commit()


def bizai_quota_status(user) -> dict:
    """Retourne l'état du quota Business Intelligence pour l'utilisateur."""
    sub = user.subscription if user else None
    unlimited = bool(sub and sub.is_active() and PLAN_CONFIG.get(sub.plan, {}).get("bizai_unlimited"))
    month = date.today().strftime("%Y-%m")
    log = BizUsage.query.filter_by(user_id=user.id, month=month).first() if user else None
    used = log.analyses_count if log else 0
    return {
        "unlimited": unlimited,
        "limit": None if unlimited else FREE_BIZAI_ANALYSES_PER_MONTH,
        "used": used,
        "remaining": None if unlimited else max(0, FREE_BIZAI_ANALYSES_PER_MONTH - used),
    }


# ── Blueprint : routes d'authentification & compte ──────────────────────────
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    disclaimer_accepted = bool(data.get("disclaimer_accepted"))

    if not USERNAME_RE.match(username):
        return jsonify({"error": "Nom d'utilisateur invalide (3-20 caractères, lettres/chiffres/_)"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Email invalide"}), 400
    if len(password) < 8:
        return jsonify({"error": "Le mot de passe doit contenir au moins 8 caractères"}), 400
    if not disclaimer_accepted:
        return jsonify({"error": "Vous devez accepter l'avertissement sur le jeu responsable pour créer un compte."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Ce nom d'utilisateur est déjà pris"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Cet email est déjà utilisé"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    sub = Subscription(user_id=user.id, plan=None, status="none")
    db.session.add(sub)
    db.session.commit()

    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"success": True, "user": user.to_dict()})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password   = data.get("password") or ""

    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Identifiants incorrects"}), 401

    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"success": True, "user": user.to_dict()})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"success": True})


@auth_bp.route("/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/plan", methods=["POST"])
@login_required
def choose_plan():
    """Démarre (ou change) le plan de l'utilisateur. En l'absence de Stripe
    (Phase 2b), choisir un plan démarre directement la période d'essai."""
    data = request.get_json(silent=True) or {}
    plan = (data.get("plan") or "").lower()
    if plan not in PLAN_CONFIG:
        return jsonify({"error": "Plan inconnu"}), 400

    user = current_user()
    sub = user.subscription
    if not sub:
        sub = Subscription(user_id=user.id)
        db.session.add(sub)

    cfg = PLAN_CONFIG[plan]
    sub.plan = plan
    sub.status = "trial"
    sub.trial_end = datetime.utcnow() + timedelta(days=cfg["trial_days"])
    sub.current_period_end = None

    db.session.commit()
    return jsonify({"success": True, "subscription": sub.to_dict()})


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Demande de réinitialisation : génère un token valable 1h et envoie
    le lien par email. Réponse identique que l'email existe ou non, pour
    ne pas révéler quels emails sont enregistrés."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    generic_msg = "Si un compte existe avec cet email, un lien de réinitialisation a été envoyé."
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Email invalide"}), 400

    user = User.query.filter_by(email=email).first()
    if user and user.password_hash:
        token = secrets.token_urlsafe(32)
        reset = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.session.add(reset)
        db.session.commit()
        send_password_reset_email(user, token)

    return jsonify({"success": True, "message": generic_msg})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """Finalise la réinitialisation à partir du token reçu par email."""
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    password = data.get("password") or ""

    if not token:
        return jsonify({"error": "Lien invalide ou expiré"}), 400
    if len(password) < 8:
        return jsonify({"error": "Le mot de passe doit contenir au moins 8 caractères"}), 400

    reset = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not reset or reset.expires_at < datetime.utcnow():
        return jsonify({"error": "Lien invalide ou expiré"}), 400

    user = db.session.get(User, reset.user_id)
    if not user:
        return jsonify({"error": "Lien invalide ou expiré"}), 400

    user.set_password(password)
    reset.used = True
    db.session.commit()
    return jsonify({"success": True})


@auth_bp.route("/states", methods=["POST"])
@login_required
def set_states():
    """Définit les États accessibles pour les plans PRO/VIP (limite max_states)."""
    data = request.get_json(silent=True) or {}
    states = [s.strip().upper() for s in (data.get("states") or []) if s.strip()]

    user = current_user()
    sub = user.subscription
    if not sub or not sub.plan:
        return jsonify({"error": "no_plan", "message": "Choisis d'abord un plan"}), 402

    cfg = PLAN_CONFIG[sub.plan]
    max_states = cfg.get("max_states", -1)
    if max_states is not None and max_states >= 0 and len(states) > max_states:
        return jsonify({"error": f"Le plan {cfg['label']} permet au maximum {max_states} États"}), 400

    sub.set_states(states)
    db.session.commit()
    return jsonify({"success": True, "subscription": sub.to_dict()})
