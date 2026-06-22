"""
ZYNORIQ — Facturation Stripe (Phase 2b)
==========================================
Gère les abonnements payants PRO / VIP / PREMIUM / BUSINESS via Stripe
Checkout + Customer Portal, et synchronise l'état de l'abonnement (essai,
actif, impayé, annulé) via les webhooks Stripe.

Configuration (variables d'environnement) :
  STRIPE_SECRET_KEY        — clé secrète (sk_test_... / sk_live_...)
  STRIPE_PUBLISHABLE_KEY   — clé publique (pk_test_... / pk_live_...)
  STRIPE_WEBHOOK_SECRET    — secret du endpoint webhook (whsec_...)
  STRIPE_PRICE_PRO         — ID du Price Stripe pour le plan PRO
  STRIPE_PRICE_VIP         — ID du Price Stripe pour le plan VIP
  STRIPE_PRICE_ELITE       — ID du Price Stripe pour le plan PREMIUM (elite)
  STRIPE_PRICE_BUSINESS    — ID du Price Stripe pour le plan BUSINESS

Si STRIPE_SECRET_KEY n'est pas défini, les routes de facturation
répondent avec {"error": "stripe_not_configured"} — le frontend bascule
alors sur le mode "essai gratuit direct" (auth.choose_plan), pratique pour
le développement local sans compte Stripe.
"""

import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from auth import db, current_user, login_required, Subscription, PLAN_CONFIG

try:
    import stripe
except ImportError:
    stripe = None


STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

STRIPE_PRICE_IDS = {
    "pro":      os.environ.get("STRIPE_PRICE_PRO", ""),
    "vip":      os.environ.get("STRIPE_PRICE_VIP", ""),
    "elite":    os.environ.get("STRIPE_PRICE_ELITE", ""),
    "business": os.environ.get("STRIPE_PRICE_BUSINESS", ""),
}

if stripe is not None and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    # Échappatoire DEV UNIQUEMENT : certains environnements Windows locaux
    # interceptent le TLS (antivirus/proxy) et cassent la vérification du
    # certificat de api.stripe.com. Ne JAMAIS activer en production
    # (Render/Linux n'a pas ce problème).
    if os.environ.get("STRIPE_INSECURE_SSL") == "1":
        from stripe._http_client import RequestsClient
        stripe.default_http_client = RequestsClient(verify_ssl_certs=False)


def stripe_enabled() -> bool:
    return bool(stripe is not None and STRIPE_SECRET_KEY)


# ── Mapping statut Stripe → statut interne ──────────────────────────────────
_STRIPE_STATUS_MAP = {
    "trialing": "trial",
    "active": "active",
    "past_due": "past_due",
    "unpaid": "expired",
    "canceled": "canceled",
    "incomplete": "expired",
    "incomplete_expired": "expired",
    "paused": "expired",
}


def _get(obj, key, default=None):
    """Accès sûr type dict.get() pour les StripeObject (qui n'implémentent
    pas .get() dans certaines versions du SDK)."""
    try:
        return obj[key]
    except (KeyError, TypeError):
        return default


def _site_url() -> str:
    return os.environ.get("PREDIKTA_SITE_URL", "https://www.zynoriq.com")


billing_bp = Blueprint("billing", __name__, url_prefix="/api/billing")


@billing_bp.route("/config")
def billing_config():
    """Expose la clé publique Stripe au frontend (pas de secret ici)."""
    return jsonify({
        "enabled": stripe_enabled(),
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
    })


@billing_bp.route("/create-checkout-session", methods=["POST"])
@login_required
def create_checkout_session():
    if not stripe_enabled():
        return jsonify({"error": "stripe_not_configured",
                        "message": "Le paiement Stripe n'est pas encore configuré sur ce serveur."}), 503

    data = request.get_json(silent=True) or {}
    plan = (data.get("plan") or "").lower()
    if plan not in PLAN_CONFIG:
        return jsonify({"error": "Plan inconnu"}), 400

    price_id = STRIPE_PRICE_IDS.get(plan)
    if not price_id:
        return jsonify({"error": "stripe_price_missing",
                        "message": f"Aucun prix Stripe configuré pour le plan {plan.upper()}."}), 503

    user = current_user()
    sub = user.subscription
    if not sub:
        sub = Subscription(user_id=user.id)
        db.session.add(sub)
        db.session.commit()

    # Réutilise (ou crée) le Customer Stripe associé à ce compte
    customer_id = sub.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(email=user.email, name=user.username,
                                           metadata={"predikta_user_id": str(user.id)})
        customer_id = customer.id
        sub.stripe_customer_id = customer_id
        db.session.commit()

    cfg = PLAN_CONFIG[plan]
    base_url = _site_url()

    session_kwargs = dict(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base_url}/onboarding?checkout=success",
        cancel_url=f"{base_url}/account?checkout=cancel",
        client_reference_id=str(user.id),
        metadata={"predikta_user_id": str(user.id), "plan": plan},
        subscription_data={
            "metadata": {"predikta_user_id": str(user.id), "plan": plan},
        },
        allow_promotion_codes=True,
    )

    # Essai gratuit uniquement si l'utilisateur n'a jamais eu d'abonnement
    # Stripe payant auparavant (évite les essais répétés à l'infini).
    if not sub.stripe_subscription_id and cfg.get("trial_days", 0) > 0:
        session_kwargs["subscription_data"]["trial_period_days"] = cfg["trial_days"]

    checkout_session = stripe.checkout.Session.create(**session_kwargs)
    return jsonify({"checkout_url": checkout_session.url})


@billing_bp.route("/portal", methods=["POST"])
@login_required
def billing_portal():
    if not stripe_enabled():
        return jsonify({"error": "stripe_not_configured",
                        "message": "Le paiement Stripe n'est pas encore configuré sur ce serveur."}), 503

    user = current_user()
    sub = user.subscription
    if not sub or not sub.stripe_customer_id:
        return jsonify({"error": "no_stripe_customer",
                        "message": "Aucun abonnement Stripe associé à ce compte."}), 404

    base_url = _site_url()
    portal_session = stripe.billing_portal.Session.create(
        customer=sub.stripe_customer_id,
        return_url=f"{base_url}/account",
    )
    return jsonify({"portal_url": portal_session.url})


# ── Webhook ──────────────────────────────────────────────────────────────────
def _find_subscription_by_stripe_id(stripe_sub_id):
    return Subscription.query.filter_by(stripe_subscription_id=stripe_sub_id).first()


def _find_subscription_by_customer(customer_id):
    return Subscription.query.filter_by(stripe_customer_id=customer_id).first()


def _sync_subscription_from_stripe(sub: Subscription, stripe_sub):
    """Met à jour notre Subscription locale à partir d'un objet Stripe Subscription."""
    sub.stripe_subscription_id = stripe_sub.id
    sub.status = _STRIPE_STATUS_MAP.get(stripe_sub.status, sub.status)

    # Détermine le plan à partir du Price Stripe de la ligne d'abonnement
    try:
        price_id = stripe_sub["items"]["data"][0]["price"]["id"]
        for plan_key, pid in STRIPE_PRICE_IDS.items():
            if pid and pid == price_id:
                sub.plan = plan_key
                break
    except (KeyError, IndexError, TypeError):
        pass

    if _get(stripe_sub, "trial_end"):
        sub.trial_end = datetime.utcfromtimestamp(stripe_sub["trial_end"])
    if _get(stripe_sub, "current_period_end"):
        sub.current_period_end = datetime.utcfromtimestamp(stripe_sub["current_period_end"])


@billing_bp.route("/webhook", methods=["POST"])
def stripe_webhook():
    if not stripe_enabled():
        return jsonify({"error": "stripe_not_configured"}), 503

    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        if STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        else:
            # Pas de secret configuré (dev) — on fait confiance au payload tel quel.
            import json as _json
            event = stripe.Event.construct_from(_json.loads(payload), stripe.api_key)
    except (ValueError, Exception) as e:  # signature invalide ou payload corrompu
        return jsonify({"error": f"invalid webhook: {e}"}), 400

    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        metadata = _get(obj, "metadata") or {}
        user_id = _get(metadata, "predikta_user_id") or _get(obj, "client_reference_id")
        customer_id = _get(obj, "customer")
        stripe_sub_id = _get(obj, "subscription")

        sub = None
        if user_id:
            from auth import User
            user = db.session.get(User, int(user_id))
            if user:
                sub = user.subscription or Subscription(user_id=user.id)
                db.session.add(sub)
        if sub is None and customer_id:
            sub = _find_subscription_by_customer(customer_id)

        if sub is not None:
            sub.stripe_customer_id = customer_id
            if stripe_sub_id:
                stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
                _sync_subscription_from_stripe(sub, stripe_sub)
            db.session.commit()

    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        sub = _find_subscription_by_stripe_id(obj["id"]) or _find_subscription_by_customer(_get(obj, "customer"))
        if sub is not None:
            _sync_subscription_from_stripe(sub, obj)
            db.session.commit()

    elif etype == "customer.subscription.deleted":
        sub = _find_subscription_by_stripe_id(obj["id"])
        if sub is not None:
            sub.status = "canceled"
            db.session.commit()

    elif etype == "invoice.payment_failed":
        customer_id = _get(obj, "customer")
        sub = _find_subscription_by_customer(customer_id)
        if sub is not None:
            # Non-paiement → blocage automatique de l'accès
            sub.status = "past_due"
            if sub.user:
                from auth import send_payment_failed_email
                send_payment_failed_email(sub.user)
            db.session.commit()

    elif etype == "invoice.paid":
        customer_id = _get(obj, "customer")
        sub = _find_subscription_by_customer(customer_id)
        if sub is not None:
            if sub.status in ("past_due", "expired"):
                sub.status = "active"

            amount_paid = (_get(obj, "amount_paid") or 0) / 100.0
            if amount_paid > 0 and sub.plan and sub.user:
                from auth import record_referral_commission
                record_referral_commission(sub.user, sub.plan, amount_paid)

            db.session.commit()

    return jsonify({"received": True})
