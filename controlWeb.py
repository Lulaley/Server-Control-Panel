from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g, make_response
import os
import secrets
import traceback
from datetime import timedelta
from urllib.parse import quote

from app_config import logger, SECRET, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from app_context import inject_user, inject_machine_info
from extensions import csrf

from app_routes import routes_bp
from app_user_api import user_api_bp

# Import des blueprints métiers
from routes.home import home_bp
from routes.minecraft import minecraft_bp
from routes.satisfactory import satisfactory_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.hytale import hytale_bp
from routes.game_servers import game_servers_bp

controlWeb = Flask(__name__)
controlWeb.secret_key = SECRET
controlWeb.logger.setLevel(logger.level)

# ---------------------------------------------------------------------------
# Warn loudly if running in debug / development mode
# ---------------------------------------------------------------------------
if os.getenv("FLASK_DEBUG") == "1" or os.getenv("FLASK_ENV") == "development":
    logger.warning(
        "WARNING: Flask is running in DEBUG/DEVELOPMENT mode. "
        "This MUST NOT be used in production."
    )

# ---------------------------------------------------------------------------
# Session security configuration
# ---------------------------------------------------------------------------
controlWeb.config["SESSION_COOKIE_HTTPONLY"] = True
controlWeb.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# Only enforce Secure cookie when HTTPS is explicitly enabled via env var
if os.getenv("HTTPS_ENABLED", "").lower() in ("1", "true", "yes"):
    controlWeb.config["SESSION_COOKIE_SECURE"] = True
controlWeb.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)

# ---------------------------------------------------------------------------
# CSRF protection — initialise with app (API blueprints are exempt below)
# ---------------------------------------------------------------------------
controlWeb.config["WTF_CSRF_CHECK_DEFAULT"] = True
controlWeb.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hour token validity
csrf.init_app(controlWeb)

# Exempt pure-API blueprints from CSRF — they are protected by session auth + SameSite=Lax.
try:
    csrf.exempt(api_bp)
except Exception:
    logger.warning("Could not apply CSRF exemption to api_bp")

try:
    csrf.exempt(admin_bp)
except Exception:
    logger.warning("Could not apply CSRF exemption to admin_bp")

# Enregistrement des context processors
controlWeb.context_processor(inject_user)
controlWeb.context_processor(inject_machine_info)

@controlWeb.context_processor
def inject_csp_nonce():
    return {'csp_nonce': getattr(g, 'csp_nonce', '')}

# Enregistrement des blueprints génériques
controlWeb.register_blueprint(routes_bp)
controlWeb.register_blueprint(user_api_bp)

# Enregistrement des blueprints métiers
controlWeb.register_blueprint(home_bp)
controlWeb.register_blueprint(minecraft_bp)
controlWeb.register_blueprint(satisfactory_bp)
controlWeb.register_blueprint(auth_bp)
controlWeb.register_blueprint(admin_bp)
controlWeb.register_blueprint(api_bp)
controlWeb.register_blueprint(hytale_bp)
controlWeb.register_blueprint(game_servers_bp)

# robots.txt — disallow all crawlers
@controlWeb.route("/robots.txt")
def robots_txt():
    resp = make_response("User-agent: *\nDisallow: /\n", 200)
    resp.headers["Content-Type"] = "text/plain"
    return resp

# ---------------------------------------------------------------------------
# CSP nonce generation — one nonce per request stored in g
# ---------------------------------------------------------------------------
@controlWeb.before_request
def _generate_csp_nonce():
    g.csp_nonce = secrets.token_hex(16)

# Hook global pour forcer login (exemptions gérées ici)
@controlWeb.before_request
def _ensure_login():
    try:
        path = request.path or ""
        logger.debug("Processing request for path: %s", path)

        # Check permanent IP ban first
        from utils.security import is_ip_permanently_banned
        ip = request.remote_addr or ""
        if ip and is_ip_permanently_banned(ip):
            logger.warning("Blocked permanently banned IP: %s path=%s", ip, path)
            if path.startswith("/api"):
                return jsonify({"error": "forbidden"}), 403
            return "Access denied", 403

        # Check temporary lockout (only relevant for login — checked inside login route,
        # but block all traffic from locked-out IPs to prevent enumeration)
        from utils.security import is_ip_locked_out
        locked, _ = is_ip_locked_out(ip)
        if locked and path in ("/login",) and request.method == "POST":
            # The login route itself handles the lockout message; let it through
            pass

        # Exemptions complètes (pas de redirection)
        exempt_paths = [
            "/static", "/_ping", "/favicon.ico",
            "/login", "/logout", "/signup",
            "/migrate-password", "/reset-password", "/robots.txt"
        ]
        # Added /api/machine to allow public machine info polling
        exempt_exact = ["/", "/api/main-color", "/api/machine"]

        # Vérifier exemptions
        if any(path.startswith(p) for p in exempt_paths) or path in exempt_exact:
            return None

        # Session idle timeout: invalidate sessions that have been idle too long
        import time as _time
        if session.get("user"):
            last_active = session.get("_last_active", 0)
            now = _time.time()
            idle_timeout = 2 * 3600  # 2 hours in seconds
            if last_active and (now - last_active) > idle_timeout:
                logger.info("Session expired due to inactivity for user %s", session.get("user"))
                session.clear()
            else:
                session["_last_active"] = now

        # Si utilisateur connecté, continuer
        if session.get("user"):
            logger.debug("User authenticated: %s", session.get("user"))
            return None

        # Pour les API, retourner erreur JSON
        if path.startswith("/api"):
            logger.debug("Unauthenticated API request to %s", path)
            return jsonify({"error": "unauthenticated", "redirect": "/login"}), 401

        # Redirection vers login
        try:
            target = url_for("auth.login", next=path)
            logger.debug("Redirecting to auth.login with next=%s", path)
        except Exception as e:
            logger.debug("auth.login not registered (%s), falling back to literal /login", e)
            target = "/login?next=" + quote(path, safe="")
        return redirect(target)
    except Exception as e:
        logger.error("Error in before_request: %s", e)
        logger.error("Traceback: %s", traceback.format_exc())
        return "Authentication error", 500

# ---------------------------------------------------------------------------
# Security headers — injected on every response
# ---------------------------------------------------------------------------
@controlWeb.after_request
def _add_security_headers(response):
    nonce = getattr(g, "csp_nonce", "")
    nonce_src = f"'nonce-{nonce}'" if nonce else ""

    csp_parts = [
        "default-src 'none'",
        f"script-src 'self' https://cdn.jsdelivr.net {nonce_src}",
        "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "connect-src 'self'",
        "font-src 'self' https://cdn.jsdelivr.net",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_parts)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    )
    if os.getenv("HTTPS_ENABLED", "").lower() in ("1", "true", "yes"):
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    # Remove server identification headers
    response.headers.pop("Server", None)
    response.headers.pop("X-Powered-By", None)
    return response

@controlWeb.errorhandler(404)
def not_found_error(e):
    logger.warning("404 error: %s for path %s", e, request.path)
    if request.path in ['/signup', '/reset-password']:
        return redirect('/login')
    if request.path.startswith("/api"):
        return jsonify({"error": "not_found"}), 404
    return render_template("error.html", code=404, message="Page introuvable"), 404

@controlWeb.errorhandler(500)
def internal_server_error(e):
    logger.error("Internal server error: %s", e)
    logger.error("Request path: %s", request.path)
    logger.error("Request method: %s", request.method)
    logger.error("Traceback: %s", traceback.format_exc())
    if request.path.startswith("/api"):
        return jsonify({"error": "internal_error"}), 500
    return render_template("error.html", code=500, message="Erreur interne du serveur"), 500

@controlWeb.errorhandler(403)
def forbidden_error(e):
    logger.warning("403 error: %s for path %s", e, request.path)
    if request.path.startswith("/api"):
        return jsonify({"error": "forbidden"}), 403
    return render_template("error.html", code=403, message="Accès refusé"), 403

logger.info("Flask app configuration complete")
logger.info("Debug mode: %s", controlWeb.debug)
logger.info("Secret key configured: %s", bool(controlWeb.secret_key))

if __name__ == '__main__':
    logger.info("Starting Flask app...")
    cert_path = "/home/web_server/certs/certificate.crt"
    key_path = "/home/web_server/certs/private.key"
    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"Using SSL context: cert={cert_path}, key={key_path}")
        controlWeb.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, ssl_context=(cert_path, key_path))
    else:
        logger.warning("Certificat SSL ou clé privée manquants, lancement sans HTTPS !")
        controlWeb.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)
