"""
ZYNORIQ — Connexion via fournisseurs externes (OAuth / OIDC)
================================================================
Phase : Google Sign-In (Authlib). Facebook / Microsoft pourront être
ajoutés plus tard sur le même modèle.

Configuration (variables d'environnement) :
  GOOGLE_CLIENT_ID      — Client ID OAuth (Google Cloud Console)
  GOOGLE_CLIENT_SECRET  — Client Secret correspondant

Si ces variables ne sont pas définies, les routes /api/auth/oauth/google/*
répondent avec {"error": "oauth_not_configured"} et le frontend masque
simplement le bouton "Continuer avec Google".
"""

import os

from flask import Blueprint, jsonify, redirect, session, url_for, request

try:
    from authlib.integrations.flask_client import OAuth
except ImportError:
    OAuth = None

from auth import db, find_or_create_oauth_user

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

oauth = OAuth() if OAuth is not None else None


def google_enabled() -> bool:
    return bool(oauth is not None and GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def init_app(app):
    if oauth is None:
        return
    oauth.init_app(app)
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )


oauth_bp = Blueprint("oauth", __name__, url_prefix="/api/auth/oauth")


@oauth_bp.route("/config")
def oauth_config():
    """Indique au frontend quels boutons "Continuer avec ..." afficher."""
    return jsonify({
        "google": google_enabled(),
        "facebook": False,
        "microsoft": False,
    })


@oauth_bp.route("/google/login")
def google_login():
    if not google_enabled():
        return jsonify({"error": "oauth_not_configured",
                        "message": "La connexion Google n'est pas configurée sur ce serveur."}), 503

    # Mémorise le plan choisi (ex: /register?plan=vip) pour rediriger
    # correctement après la connexion.
    plan = (request.args.get("plan") or "").lower()
    if plan:
        session["oauth_plan"] = plan

    redirect_uri = url_for("oauth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route("/google/callback")
def google_callback():
    if not google_enabled():
        return redirect("/login?oauth_error=not_configured")

    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo = oauth.google.userinfo(token=token)
    except Exception:
        return redirect("/login?oauth_error=google_failed")

    google_id = userinfo.get("sub")
    email = userinfo.get("email") or ""
    name = userinfo.get("name") or userinfo.get("given_name") or ""
    picture = userinfo.get("picture") or ""

    if not google_id:
        return redirect("/login?oauth_error=google_failed")

    user, created = find_or_create_oauth_user(
        provider="google", oauth_id=google_id, email=email, name=name, avatar_url=picture,
    )

    session["user_id"] = user.id
    session.permanent = True

    plan = session.pop("oauth_plan", None)
    if not user.subscription or not user.subscription.plan:
        if plan:
            return redirect(f"/account?plan={plan}&welcome=1")
        return redirect("/account?welcome=1")

    return redirect("/account")
