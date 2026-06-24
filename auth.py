"""
ZYNORIQ — Comptes utilisateurs, abonnements & paywall
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
import json
import secrets
import string
import smtplib
import html as _html
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
        "price_usd": 19.99,
        "trial_days": 3,
        "analyses_per_day": 1,
        "max_states": 4,
    },
    "vip": {
        "label": "VIP",
        "price_usd": 49.99,
        "trial_days": 7,
        "analyses_per_day": 7,
        "max_states": 20,
    },
    "elite": {
        "label": "PREMIUM",
        "price_usd": 99.99,
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

# ── Programme de parrainage (Phase 2) ───────────────────────────────────────
# Paliers basés sur le nombre de filleuls inscrits (referral_count) :
#  - 3  filleuls  -> badge Ambassadeur ZYNORIQ
#  - 10 filleuls  -> 7 jours d'accès VIP offerts
#  - 25 filleuls  -> 30 jours d'accès PREMIUM (elite) offerts
REFERRAL_MILESTONES = {
    3:  {"type": "badge"},
    10: {"type": "access", "plan": "vip",   "days": 7},
    25: {"type": "access", "plan": "elite", "days": 30},
}

# Commission de parrainage : pourcentage du montant payé par le filleul,
# reversé au parrain à chaque paiement (Stripe invoice.paid).
REFERRAL_COMMISSION_RATES = {
    "pro": 0.25,
    "vip": 0.15,
    "elite": 0.10,
    "business": 0.10,
}


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

    is_admin = db.Column(db.Boolean, default=False, nullable=False, server_default="0")

    email_verified = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    email_verify_token = db.Column(db.String(64), nullable=True)

    # Programme de parrainage (Phase 2 — basé sur les comptes)
    ref_code         = db.Column(db.String(12), nullable=True)
    referred_by_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    referral_count   = db.Column(db.Integer, default=0, nullable=False, server_default="0")
    ambassador_badge = db.Column(db.Boolean, default=False, nullable=False, server_default="0")
    referral_rewards = db.Column(db.Text, nullable=True)  # JSON list des paliers déjà accordés
    referral_balance_usd = db.Column(db.Float, default=0, nullable=False, server_default="0")  # commissions cumulées

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
            "is_admin": bool(self.is_admin),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "subscription": sub.to_dict() if sub else None,
            "ref_code": self.ref_code,
            "referral_count": self.referral_count or 0,
            "ambassador_badge": bool(self.ambassador_badge),
            "referral_balance_usd": round(self.referral_balance_usd or 0, 2),
        }


class Comment(db.Model):
    __tablename__ = "comments"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    state_code = db.Column(db.String(4), nullable=False, index=True)
    body       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.user.username if self.user else "?",
            "avatar_url": self.user.avatar_url if self.user else None,
            "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id,
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

    trial_reminder_sent = db.Column(db.Boolean, default=False, nullable=False, server_default="0")

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


class ReferralCommission(db.Model):
    """Commission de parrainage versée à `referrer` sur un paiement de `referred_user`."""
    __tablename__ = "referral_commissions"

    id               = db.Column(db.Integer, primary_key=True)
    referrer_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    referred_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan             = db.Column(db.String(16), nullable=False)
    rate             = db.Column(db.Float, nullable=False)
    amount_usd       = db.Column(db.Float, nullable=False)       # montant payé par le filleul
    commission_usd   = db.Column(db.Float, nullable=False)       # part reversée au parrain
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "plan": self.plan,
            "plan_label": PLAN_CONFIG.get(self.plan, {}).get("label"),
            "rate": self.rate,
            "amount_usd": round(self.amount_usd, 2),
            "commission_usd": round(self.commission_usd, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReferralPayout(db.Model):
    """Versement de commissions de parrainage effectué par un administrateur
    (hors plateforme : virement, PayPal, etc.). Sert de journal comptable
    et fait diminuer `User.referral_balance_usd`."""
    __tablename__ = "referral_payouts"

    id          = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    amount_usd  = db.Column(db.Float, nullable=False)
    note        = db.Column(db.String(255), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "referrer_id": self.referrer_id,
            "amount_usd": round(self.amount_usd, 2),
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
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


class UserArchive(db.Model):
    """Historique des analyses visitées (synchronisé entre appareils pour les utilisateurs connectés)."""
    __tablename__ = "user_archives"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    client_id  = db.Column(db.String(64), nullable=False)   # UUID généré côté client (dédup)
    ts         = db.Column(db.BigInteger, nullable=False)    # timestamp ms (epoch)
    type       = db.Column(db.String(20), nullable=False, default="analyze")
    state      = db.Column(db.String(4), nullable=True)
    tod        = db.Column(db.String(20), nullable=True)
    url        = db.Column(db.Text, nullable=True)
    label      = db.Column(db.String(200), nullable=True)

    __table_args__ = (db.UniqueConstraint("user_id", "client_id", name="uq_user_archive"),)

    def to_dict(self):
        return {
            "id": self.client_id,
            "ts": self.ts,
            "type": self.type,
            "state": self.state,
            "tod": self.tod,
            "url": self.url,
            "label": self.label,
        }


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
        _ensure_column(db, "users", "is_admin", "BOOLEAN DEFAULT FALSE")
        _ensure_column(db, "users", "ref_code", "VARCHAR(12)")
        _ensure_column(db, "users", "referred_by_id", "INTEGER")
        _ensure_column(db, "users", "referral_count", "INTEGER DEFAULT 0")
        _ensure_column(db, "users", "ambassador_badge", "BOOLEAN DEFAULT FALSE")
        _ensure_column(db, "users", "referral_rewards", "TEXT")
        _ensure_column(db, "users", "referral_balance_usd", "FLOAT DEFAULT 0")
        _ensure_column(db, "subscriptions", "trial_reminder_sent", "BOOLEAN DEFAULT FALSE")
        _ensure_column(db, "users", "email_verified", "BOOLEAN DEFAULT FALSE")
        _ensure_column(db, "users", "email_verify_token", "VARCHAR(64)")


def _ensure_column(db, table, column, ddl_type):
    """Ajoute une colonne manquante sur une table existante (mini-migration,
    pour les bases créées avant l'ajout de ce champ)."""
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    cols = [c["name"] for c in inspector.get_columns(table)]
    if column in cols:
        return
    with db.engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
        conn.commit()


# ── Helpers ──────────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,20}$")


def _gen_user_ref_code() -> str:
    """Génère un code de parrainage court (6 caractères) et unique."""
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(10):
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if not User.query.filter_by(ref_code=code).first():
            return code
    return secrets.token_hex(4).upper()


def _extend_subscription(sub, days: int):
    """Prolonge l'abonnement actif (essai ou payant) de `days` jours, ou
    démarre un essai de `days` jours si aucun abonnement n'est en cours."""
    now = datetime.utcnow()
    if sub.status == "trial":
        base = sub.trial_end if (sub.trial_end and sub.trial_end > now) else now
        sub.trial_end = base + timedelta(days=days)
    elif sub.status == "active":
        base = sub.current_period_end if (sub.current_period_end and sub.current_period_end > now) else now
        sub.current_period_end = base + timedelta(days=days)
    else:
        sub.status = "trial"
        sub.trial_end = now + timedelta(days=days)


def _grant_referral_access(user, plan_key: str, days: int):
    """Accorde (ou prolonge) un accès bonus de `days` jours au plan `plan_key`,
    sans jamais rétrograder un abonnement existant de niveau supérieur."""
    sub = user.subscription
    if not sub:
        sub = Subscription(user_id=user.id)
        db.session.add(sub)
        user.subscription = sub

    current_rank = PLAN_ORDER.index(sub.plan) if sub.plan in PLAN_ORDER else -1
    reward_rank = PLAN_ORDER.index(plan_key)
    if not sub.is_active() or current_rank < reward_rank:
        sub.plan = plan_key
    _extend_subscription(sub, days)


def record_referral_commission(referred_user: "User", plan: str, amount_usd: float):
    """Crédite le parrain de `referred_user` d'une commission sur un paiement
    de `amount_usd` pour le plan `plan` (appelé depuis le webhook Stripe
    `invoice.paid`)."""
    if not referred_user.referred_by_id or amount_usd <= 0:
        return
    rate = REFERRAL_COMMISSION_RATES.get(plan, 0)
    if rate <= 0:
        return

    referrer = db.session.get(User, referred_user.referred_by_id)
    if not referrer:
        return

    commission = round(amount_usd * rate, 2)
    referrer.referral_balance_usd = (referrer.referral_balance_usd or 0) + commission
    db.session.add(ReferralCommission(
        referrer_id=referrer.id,
        referred_user_id=referred_user.id,
        plan=plan,
        rate=rate,
        amount_usd=amount_usd,
        commission_usd=commission,
    ))


def record_referral_payout(referrer: "User", amount_usd: float, note: str = None):
    """Enregistre un versement de commissions effectué par un admin (hors
    plateforme) et déduit le montant du solde de parrainage de `referrer`."""
    amount_usd = round(min(amount_usd, referrer.referral_balance_usd or 0), 2)
    if amount_usd <= 0:
        return None
    referrer.referral_balance_usd = round((referrer.referral_balance_usd or 0) - amount_usd, 2)
    payout = ReferralPayout(referrer_id=referrer.id, amount_usd=amount_usd, note=note)
    db.session.add(payout)
    return payout


def _apply_referral_rewards(referrer: "User"):
    """Vérifie les paliers de parrainage atteints par `referrer` et applique
    les récompenses pas encore accordées (badge, jours d'accès bonus)."""
    try:
        applied = json.loads(referrer.referral_rewards) if referrer.referral_rewards else []
    except Exception:
        applied = []

    changed = False
    for milestone, reward in REFERRAL_MILESTONES.items():
        if (referrer.referral_count or 0) >= milestone and milestone not in applied:
            if reward["type"] == "badge":
                referrer.ambassador_badge = True
            elif reward["type"] == "access":
                _grant_referral_access(referrer, reward["plan"], reward["days"])
            applied.append(milestone)
            changed = True

    if changed:
        referrer.referral_rewards = json.dumps(applied)


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
    user = User(username=username, email=email or f"{username}@{provider}.zynoriq.local",
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


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": "login_required", "message": "Connexion requise"}), 401
        if not user.is_admin:
            return jsonify({"error": "forbidden", "message": "Accès administrateur requis"}), 403
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


def _send_email(to: str, subject: str, body: str, html_body: str = None):
    """Envoie un email (texte + HTML optionnel) si le SMTP est configuré.
    Variables d'env : SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SMTP_FROM.
    Sans config SMTP, le message est loggé (dev local)."""
    smtp_host = os.environ.get("SMTP_HOST")
    if not smtp_host:
        text = f"[auth] (email non envoye, SMTP non configure) A: {to} | Sujet: {subject}\n{body}"
        print(text.encode("ascii", "replace").decode("ascii"))
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("SMTP_FROM", "noreply@zynoriq.com")
    msg["To"] = to
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        print(f"[auth] Email envoyé à {to} : {subject}")
    except Exception as e:
        print(f"[auth] Échec envoi email ({subject}) à {to}: {e}")


def send_password_reset_email(user, token: str):
    """Envoie l'email de réinitialisation de mot de passe."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    reset_link = f"{base_url}/reset-password?token={token}"

    _send_email(
        user.email,
        "ZYNORIQ — Réinitialisation de votre mot de passe",
        "Bonjour,\n\n"
        "Une demande de réinitialisation de mot de passe a été effectuée pour votre compte ZYNORIQ.\n"
        f"Cliquez sur ce lien pour choisir un nouveau mot de passe (valable 1 heure) :\n{reset_link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
    )


def send_verification_email(user):
    """Send email verification link after registration."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    token = secrets.token_urlsafe(32)
    user.email_verify_token = token
    db.session.commit()

    name = _html.escape(user.username or "")
    verify_url = f"{base_url}/api/auth/verify-email?token={token}"

    plain = (
        f"Bonjour {name},\n\n"
        "Vérifie ton adresse email pour activer ton compte ZYNORIQ.\n\n"
        f"Clique ici : {verify_url}\n\n"
        "Ce lien expire dans 24 heures.\n\n"
        "L'équipe ZYNORIQ Intelligence™"
    )
    html_body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#04040f;font-family:'Helvetica Neue',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#04040f;padding:40px 0">
<tr><td align="center">
<table width="520" cellpadding="0" cellspacing="0" style="max-width:520px;width:100%">
  <tr><td style="background:linear-gradient(135deg,#0d0d2e,#1a0a3d);border-radius:16px 16px 0 0;padding:28px 36px;text-align:center;border:1px solid #1a1a45;border-bottom:none">
    <div style="font-family:'Courier New',monospace;font-size:1.5rem;font-weight:900;color:#1479FF">ZYNORIQ</div>
    <div style="font-size:.65rem;color:#ffd700;letter-spacing:.12em;text-transform:uppercase;margin-top:4px">Intelligence Beyond Prediction</div>
  </td></tr>
  <tr><td style="background:#08081f;border:1px solid #1a1a45;border-top:none;border-bottom:none;padding:28px 36px;text-align:center">
    <p style="font-size:1.05rem;font-weight:700;color:#ffffff;margin:0 0 12px">Bonjour {name} !</p>
    <p style="font-size:.88rem;color:#a0aec0;margin:0 0 24px;line-height:1.7">V&eacute;rifie ton adresse email pour activer ton compte ZYNORIQ et acc&eacute;der &agrave; toutes les fonctionnalit&eacute;s.</p>
    <a href="{verify_url}" style="display:inline-block;padding:14px 40px;border-radius:12px;background:linear-gradient(135deg,#22e87a,#0e9e55);color:#ffffff;font-weight:800;font-size:.95rem;text-decoration:none;letter-spacing:.3px">
      V&eacute;rifier mon email
    </a>
    <p style="font-size:.72rem;color:#4d5a8a;margin-top:20px">Ce lien expire dans 24 heures.</p>
  </td></tr>
  <tr><td style="background:#06061a;border:1px solid #1a1a45;border-top:none;border-radius:0 0 16px 16px;padding:16px 36px;text-align:center">
    <p style="font-size:.62rem;color:#334155">Si tu n'as pas cr&eacute;&eacute; de compte sur ZYNORIQ, ignore cet email.</p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""

    _send_email(user.email, "ZYNORIQ — Vérifie ton adresse email", plain, html_body=html_body)


def send_welcome_email(user):
    """Email de bienvenue HTML envoyé juste après la création du compte."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    name = _html.escape(user.username or "là")

    plain = (
        f"Bonjour {name},\n\n"
        "Bienvenue sur ZYNORIQ Intelligence™ !\n\n"
        "Ta plateforme d'analyse prédictive couvre :\n"
        "• Pick 3 / Cash 3 / Daily 3 — 44+ États\n"
        "• Pick 4 / Cash 4 — Prédictions & résultats\n"
        "• Pick 5 / Cash 5 / Fantasy 5\n"
        "• Powerball & Mega Millions — Jackpots nationaux\n\n"
        "Selon ton plan, tu bénéficies de :\n"
        "• Prédictions consensus (7 modèles ML)\n"
        "• Combos Straight, Box, Double, Triple\n"
        "• Analyses de tendances, écarts & fréquences\n"
        "• Alertes push en temps réel\n\n"
        f"Démarrer → {base_url}/onboarding\n"
        f"Résultats → {base_url}/results\n"
        f"Plans & Tarifs → {base_url}/pro\n\n"
        "L'équipe ZYNORIQ Intelligence™\n"
        "support@zynoriq.com"
    )

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Bienvenue sur ZYNORIQ</title>
</head>
<body style="margin:0;padding:0;background:#04040f;font-family:'Helvetica Neue',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#04040f;padding:40px 0">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%">

  <!-- Header with Logo -->
  <tr><td style="background:linear-gradient(135deg,#0d0d2e,#1a0a3d);border-radius:16px 16px 0 0;padding:36px 40px;text-align:center;border:1px solid #1a1a45;border-bottom:none">
    <img src="{base_url}/static/zynoriq-hero.png" alt="ZYNORIQ Intelligence" style="width:100%;max-width:500px;border-radius:12px;margin-bottom:16px" />
    <div style="font-family:'Courier New',monospace;font-size:1.8rem;font-weight:900;letter-spacing:.08em;color:#1479FF">ZYNORIQ</div>
    <div style="font-family:'Courier New',monospace;font-size:.7rem;font-weight:700;letter-spacing:.15em;color:#ffd700;text-transform:uppercase;margin-top:4px">Intelligence Beyond Prediction</div>
  </td></tr>

  <!-- Body -->
  <tr><td style="background:#08081f;border:1px solid #1a1a45;border-top:none;border-bottom:none;padding:36px 40px">
    <p style="font-size:1.15rem;font-weight:800;color:#ffffff;margin:0 0 8px">Bonjour {name} 👋</p>
    <p style="font-size:.92rem;color:#a0aec0;margin:0 0 24px;line-height:1.8">
      Ton compte <strong style="color:#1479FF">ZYNORIQ Intelligence™</strong> est actif. Bienvenue dans la plateforme d'analyse prédictive la plus complète.
    </p>

    <!-- Jeux couverts -->
    <div style="background:#0d0d2e;border:1px solid #1a1a45;border-radius:12px;padding:20px;margin-bottom:16px">
      <div style="font-size:.85rem;font-weight:800;color:#ffffff;margin-bottom:12px">🎰 Jeux couverts — 44+ États</div>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:4px 0"><span style="color:#22e87a;font-weight:800;font-size:.82rem">🎯 Pick 3</span><span style="color:#8892b0;font-size:.75rem"> — Cash 3, Daily 3, Numbers</span></td>
        </tr>
        <tr>
          <td style="padding:4px 0"><span style="color:#4f9eff;font-weight:800;font-size:.82rem">4️⃣ Pick 4</span><span style="color:#8892b0;font-size:.75rem"> — Cash 4, Win 4, Daily 4</span></td>
        </tr>
        <tr>
          <td style="padding:4px 0"><span style="color:#a78bfa;font-weight:800;font-size:.82rem">5️⃣ Pick 5</span><span style="color:#8892b0;font-size:.75rem"> — Cash 5, Fantasy 5, Take 5</span></td>
        </tr>
        <tr>
          <td style="padding:4px 0"><span style="color:#ffd700;font-weight:800;font-size:.82rem">💰 Lotto</span><span style="color:#8892b0;font-size:.75rem"> — Powerball, Mega Millions, Cash4Life</span></td>
        </tr>
      </table>
    </div>

    <!-- Ce que tu obtiens -->
    <div style="background:#0d0d2e;border:1px solid #1a1a45;border-radius:12px;padding:20px;margin-bottom:16px">
      <div style="font-size:.85rem;font-weight:800;color:#ffffff;margin-bottom:12px">⚡ Selon ton plan tu bénéficies de :</div>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr><td style="padding:3px 0;color:#a0aec0;font-size:.8rem">✅ Prédictions consensus — <strong style="color:#ffffff">7 modèles ML</strong></td></tr>
        <tr><td style="padding:3px 0;color:#a0aec0;font-size:.8rem">✅ Combos <strong style="color:#22e87a">Straight</strong>, <strong style="color:#4f9eff">Box</strong>, <strong style="color:#ffd700">Double</strong>, <strong style="color:#a78bfa">Triple</strong></td></tr>
        <tr><td style="padding:3px 0;color:#a0aec0;font-size:.8rem">✅ Tendances, écarts & fréquences en temps réel</td></tr>
        <tr><td style="padding:3px 0;color:#a0aec0;font-size:.8rem">✅ Alertes push instantanées par État</td></tr>
        <tr><td style="padding:3px 0;color:#a0aec0;font-size:.8rem">✅ Track Record vérifié — résultats vs prédictions</td></tr>
        <tr><td style="padding:3px 0;color:#a0aec0;font-size:.8rem">✅ ZYNORIQ Copilot™ — assistant IA intégré</td></tr>
      </table>
    </div>

    <!-- CTA principal -->
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:16px">
      <tr><td align="center">
        <a href="{base_url}/onboarding" style="display:inline-block;padding:16px 40px;border-radius:12px;background:linear-gradient(135deg,#1479FF,#004DFF);color:#ffffff;font-weight:800;font-size:.95rem;text-decoration:none;letter-spacing:.3px">
          🚀 Démarrer maintenant →
        </a>
      </td></tr>
    </table>

    <!-- Plans -->
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td width="25%" align="center" style="padding:8px 4px">
          <div style="background:#0d0d2e;border:1px solid #1a1a45;border-radius:10px;padding:12px 6px;text-align:center">
            <div style="font-size:.7rem;font-weight:800;color:#4f9eff">PRO</div>
            <div style="font-size:.82rem;font-weight:900;color:#ffffff;margin-top:2px">$19.99</div>
            <div style="font-size:.6rem;color:#8892b0">/mois</div>
          </div>
        </td>
        <td width="25%" align="center" style="padding:8px 4px">
          <div style="background:#0d0d2e;border:1px solid #ffd700;border-radius:10px;padding:12px 6px;text-align:center">
            <div style="font-size:.7rem;font-weight:800;color:#ffd700">VIP</div>
            <div style="font-size:.82rem;font-weight:900;color:#ffffff;margin-top:2px">$49.99</div>
            <div style="font-size:.6rem;color:#8892b0">/mois</div>
          </div>
        </td>
        <td width="25%" align="center" style="padding:8px 4px">
          <div style="background:#0d0d2e;border:1px solid #a78bfa;border-radius:10px;padding:12px 6px;text-align:center">
            <div style="font-size:.7rem;font-weight:800;color:#a78bfa">PREMIUM</div>
            <div style="font-size:.82rem;font-weight:900;color:#ffffff;margin-top:2px">$99.99</div>
            <div style="font-size:.6rem;color:#8892b0">/mois</div>
          </div>
        </td>
        <td width="25%" align="center" style="padding:8px 4px">
          <div style="background:#0d0d2e;border:1px solid #22e87a;border-radius:10px;padding:12px 6px;text-align:center">
            <div style="font-size:.7rem;font-weight:800;color:#22e87a">BUSINESS</div>
            <div style="font-size:.82rem;font-weight:900;color:#ffffff;margin-top:2px">$199.99</div>
            <div style="font-size:.6rem;color:#8892b0">/mois</div>
          </div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Stats bar -->
  <tr><td style="background:#0a0a20;border:1px solid #1a1a45;border-top:none;border-bottom:none;padding:20px 40px">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center" style="padding:0 6px">
          <div style="font-size:1.1rem">🎯</div>
          <div style="font-size:.62rem;font-weight:800;color:#22e87a;margin-top:4px">7 MODÈLES ML</div>
        </td>
        <td align="center" style="padding:0 6px">
          <div style="font-size:1.1rem">📊</div>
          <div style="font-size:.62rem;font-weight:800;color:#4f9eff;margin-top:4px">44+ ÉTATS</div>
        </td>
        <td align="center" style="padding:0 6px">
          <div style="font-size:1.1rem">⚡</div>
          <div style="font-size:.62rem;font-weight:800;color:#a78bfa;margin-top:4px">TEMPS RÉEL</div>
        </td>
        <td align="center" style="padding:0 6px">
          <div style="font-size:1.1rem">🤖</div>
          <div style="font-size:.62rem;font-weight:800;color:#ffd700;margin-top:4px">COPILOT™ IA</div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#06061a;border:1px solid #1a1a45;border-top:none;border-radius:0 0 16px 16px;padding:20px 40px;text-align:center">
    <p style="font-size:.7rem;color:#4d5a8a;margin:0 0 6px">Tu reçois cet email car tu viens de créer un compte sur ZYNORIQ.</p>
    <p style="font-size:.7rem;color:#4d5a8a;margin:0 0 6px">
      <a href="{base_url}/results" style="color:#1479FF;text-decoration:none;font-weight:600">Résultats</a> &nbsp;·&nbsp;
      <a href="{base_url}/analyze" style="color:#1479FF;text-decoration:none;font-weight:600">Analyser</a> &nbsp;·&nbsp;
      <a href="{base_url}/pro" style="color:#1479FF;text-decoration:none;font-weight:600">Plans & Tarifs</a> &nbsp;·&nbsp;
      <a href="{base_url}/about" style="color:#1479FF;text-decoration:none;font-weight:600">À Propos</a>
    </p>
    <p style="font-size:.68rem;color:#4d5a8a;margin:6px 0 0">
      <a href="mailto:support@zynoriq.com" style="color:#1479FF;text-decoration:none">support@zynoriq.com</a>
      &nbsp;·&nbsp; <a href="mailto:privacy@zynoriq.com" style="color:#1479FF;text-decoration:none">privacy@zynoriq.com</a>
    </p>
    <p style="font-size:.58rem;color:#334155;margin:10px 0 0;line-height:1.5">© 2026 ZYNORIQ Intelligence™ — Analyses statistiques éducatives, sans garantie de gain. La loterie est un jeu de hasard.</p>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""

    _send_email(
        user.email,
        f"Bienvenue sur ZYNORIQ, {name} 🎯",
        plain,
        html_body=html,
    )


def send_trial_ending_email(user, sub):
    """Email de rappel envoyé lorsque la période d'essai arrive à échéance."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    cfg = PLAN_CONFIG.get(sub.plan, {})
    plan_label = cfg.get("label", sub.plan or "")
    _send_email(
        user.email,
        "ZYNORIQ — Ton essai gratuit se termine bientôt",
        f"Bonjour {user.username},\n\n"
        f"Ta période d'essai gratuite du plan {plan_label} se termine dans moins de 24 heures.\n"
        "Pour continuer à profiter de tes analyses et prédictions sans interruption, "
        "ajoute un moyen de paiement dès maintenant :\n"
        f"{base_url}/account\n\n"
        "À très vite,\nL'équipe ZYNORIQ"
    )


def send_payment_failed_email(user):
    """Email envoyé lorsqu'un paiement Stripe échoue (invoice.payment_failed)."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    _send_email(
        user.email,
        "ZYNORIQ — Échec de paiement",
        f"Bonjour {user.username},\n\n"
        "Le paiement de ton abonnement ZYNORIQ a échoué.\n"
        "Pour éviter toute interruption de ton accès, merci de mettre à jour ton moyen de paiement :\n"
        f"{base_url}/account\n\n"
        "À très vite,\nL'équipe ZYNORIQ"
    )


def send_new_result_alert_email(user, state: str, game_label: str, draw: dict):
    """Email envoyé lorsqu'un nouveau tirage est disponible pour une alerte
    « Nouveau tirage » (alert_type=new_result) créée par l'utilisateur."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    nums = ", ".join(draw.get("nums") or [])
    date_str = draw.get("date", "")
    tod = draw.get("tod", "")
    when = f"{date_str} ({tod})" if tod else date_str
    _send_email(
        user.email,
        f"ZYNORIQ — Nouveau tirage {state} {game_label}",
        f"Bonjour {user.username},\n\n"
        f"Un nouveau tirage est disponible pour {game_label} ({state}) :\n"
        f"Date : {when}\n"
        f"Résultat : {nums}\n\n"
        f"Consulte l'analyse complète :\n{base_url}/results?state={state.lower()}\n\n"
        "À très vite,\nL'équipe ZYNORIQ"
    )


def send_hotcold_alert_email(user, state: str, game_label: str, alert_type: str, items: list[dict]):
    """Email envoyé lorsqu'un chiffre devient HOT (alert_type=hot_number) ou
    COLD (alert_type=cold_number) pour l'État/jeu surveillé par l'utilisateur."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    pos_labels = {"d1": "1ère position", "d2": "2ème position", "d3": "3ème position"}
    label = "chaud(s)" if alert_type == "hot_number" else "froid(s)"
    title = "Numéro chaud" if alert_type == "hot_number" else "Numéro froid"
    lines = "\n".join(f"- Chiffre {it['digit']} ({pos_labels.get(it['pos'], it['pos'])})" for it in items)
    _send_email(
        user.email,
        f"ZYNORIQ — {title} détecté pour {state} {game_label}",
        f"Bonjour {user.username},\n\n"
        f"De nouveaux chiffres {label} ont été détectés pour {game_label} ({state}) "
        f"sur les 30 derniers tirages :\n\n"
        f"{lines}\n\n"
        f"Consulte l'analyse complète :\n{base_url}/results?state={state.lower()}\n\n"
        "À très vite,\nL'équipe ZYNORIQ"
    )


def send_custom_alert_email(user, state: str, game_label: str, number: str, draw: dict):
    """Email envoyé lorsqu'un numéro surveillé (alerte personnalisée,
    alert_type=custom) sort dans un nouveau tirage."""
    base_url = os.environ.get("PREDIKTA_BASE_URL", "https://www.zynoriq.com")
    date_str = draw.get("date", "")
    tod = draw.get("tod", "")
    when = f"{date_str} ({tod})" if tod else date_str
    _send_email(
        user.email,
        f"ZYNORIQ — Votre numéro {number} est sorti ! ({state} {game_label})",
        f"Bonjour {user.username},\n\n"
        f"Le numéro que tu surveilles, {number}, vient de sortir pour "
        f"{game_label} ({state}) :\n"
        f"Date : {when}\n\n"
        f"Consulte l'analyse complète :\n{base_url}/results?state={state.lower()}\n\n"
        "À très vite,\nL'équipe ZYNORIQ"
    )


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


# ── Rate limiter léger en mémoire (sans dépendance externe) ──────────────────
import time as _time
_rl_store: dict = {}  # {(ip, endpoint): [timestamps]}

def _rate_limit(max_calls: int, window_sec: int) -> bool:
    """Returns True (blocked) if the caller IP exceeds max_calls in window_sec."""
    ip = request.remote_addr or "unknown"
    key = (ip, request.endpoint)
    now = _time.time()
    calls = [t for t in _rl_store.get(key, []) if now - t < window_sec]
    calls.append(now)
    _rl_store[key] = calls
    return len(calls) > max_calls


# ── Blueprint : routes d'authentification & compte ──────────────────────────
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    if _rate_limit(5, 60):
        return jsonify({"error": "Trop de tentatives, réessaie dans 1 minute."}), 429
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

    ref_code = (data.get("ref_code") or "").strip().upper()
    referrer = User.query.filter_by(ref_code=ref_code).first() if ref_code else None

    user = User(username=username, email=email)
    user.set_password(password)
    user.ref_code = _gen_user_ref_code()
    if referrer:
        user.referred_by_id = referrer.id
    db.session.add(user)
    db.session.flush()

    sub = Subscription(user_id=user.id, plan=None, status="none")
    db.session.add(sub)

    if referrer:
        referrer.referral_count = (referrer.referral_count or 0) + 1
        _apply_referral_rewards(referrer)

    db.session.commit()

    send_verification_email(user)

    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"success": True, "user": user.to_dict(), "email_verification_sent": True})


@auth_bp.route("/verify-email")
def verify_email():
    token = request.args.get("token", "")
    if not token:
        return "<h2>Lien invalide.</h2>", 400

    user = User.query.filter_by(email_verify_token=token).first()
    if not user:
        return """<html><head><meta charset="UTF-8"/><title>ZYNORIQ — Erreur</title></head>
        <body style="background:#04040f;color:#e8eeff;font-family:sans-serif;text-align:center;padding:60px">
        <h2 style="color:#ff3d2e">Lien invalide ou expiré.</h2>
        <p>Connecte-toi et demande un nouveau lien de vérification.</p>
        <a href="/login" style="color:#1479FF">Se connecter</a>
        </body></html>""", 400

    user.email_verified = True
    user.email_verify_token = None
    db.session.commit()

    send_welcome_email(user)

    return f"""<html><head><meta charset="UTF-8"/><title>ZYNORIQ — Email vérifié</title></head>
    <body style="background:#04040f;color:#e8eeff;font-family:sans-serif;text-align:center;padding:60px">
    <h2 style="color:#22e87a">Email vérifié avec succès !</h2>
    <p>Bienvenue sur ZYNORIQ, {_html.escape(user.username)} !</p>
    <a href="/analyze" style="display:inline-block;margin-top:20px;padding:14px 32px;border-radius:12px;background:linear-gradient(135deg,#1479FF,#004DFF);color:#fff;font-weight:700;text-decoration:none">Commencer à analyser</a>
    </body></html>"""


@auth_bp.route("/resend-verification", methods=["POST"])
@login_required
def resend_verification():
    user = current_user()
    if user.email_verified:
        return jsonify({"message": "Email deja verifie."})
    if _rate_limit(2, 300):
        return jsonify({"error": "Attends 5 minutes avant de redemander."}), 429
    send_verification_email(user)
    return jsonify({"success": True, "message": "Email de verification renvoye."})


@auth_bp.route("/login", methods=["POST"])
def login():
    if _rate_limit(10, 60):
        return jsonify({"error": "Trop de tentatives, réessaie dans 1 minute."}), 429
    data = request.get_json(silent=True) or {}
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password   = data.get("password") or ""

    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Identifiants incorrects"}), 401

    if not user.email_verified and not user.oauth_provider:
        return jsonify({"error": "email_not_verified", "message": "Verifie ton email avant de te connecter. Consulte ta boite de reception."}), 403

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


@auth_bp.route("/referral")
@login_required
def referral_info():
    user = current_user()
    if not user.ref_code:
        user.ref_code = _gen_user_ref_code()
        db.session.commit()

    try:
        applied = json.loads(user.referral_rewards) if user.referral_rewards else []
    except Exception:
        applied = []

    recent = (ReferralCommission.query
              .filter_by(referrer_id=user.id)
              .order_by(ReferralCommission.created_at.desc())
              .limit(20).all())

    return jsonify({
        "ref_code": user.ref_code,
        "referral_count": user.referral_count or 0,
        "ambassador_badge": bool(user.ambassador_badge),
        "rewards": {str(m): (m in applied) for m in REFERRAL_MILESTONES},
        "commission_rates": {plan: REFERRAL_COMMISSION_RATES.get(plan, 0) for plan in PLAN_CONFIG},
        "referral_balance_usd": round(user.referral_balance_usd or 0, 2),
        "recent_commissions": [c.to_dict() for c in recent],
    })


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
    if _rate_limit(3, 300):
        return jsonify({"error": "Trop de tentatives, réessaie dans 5 minutes."}), 429
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


@auth_bp.route("/cron/trial-reminders", methods=["POST", "GET"])
def trial_reminders():
    """Envoie un email de rappel aux comptes dont l'essai gratuit se termine
    dans moins de 24h (une seule fois par essai). Destiné à être appelé
    périodiquement par un job cron externe, protégé par CRON_SECRET."""
    secret = os.environ.get("CRON_SECRET")
    if secret and request.args.get("secret") != secret:
        return jsonify({"error": "unauthorized"}), 401

    now = datetime.utcnow()
    soon = now + timedelta(hours=24)
    subs = Subscription.query.filter(
        Subscription.status == "trial",
        Subscription.trial_reminder_sent.is_(False),
        Subscription.trial_end.isnot(None),
        Subscription.trial_end <= soon,
        Subscription.trial_end > now,
    ).all()

    sent = 0
    for sub in subs:
        if sub.user:
            send_trial_ending_email(sub.user, sub)
            sub.trial_reminder_sent = True
            sent += 1

    db.session.commit()
    return jsonify({"success": True, "emails_sent": sent})
