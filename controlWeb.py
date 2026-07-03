<<<<<<< HEAD
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, g, make_response
import os
import logging
import traceback
from logging.handlers import RotatingFileHandler
from urllib.parse import quote
import json, re  # <-- added imports
import psutil
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import secrets
import importlib.util
import sys
from datetime import timedelta
from extensions import csrf
=======
>>>>>>> origin/develop


from flask import Flask
from app_config import logger, SECRET, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from app_context import inject_user, inject_machine_info

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
<<<<<<< HEAD
controlWeb.logger.setLevel(logging.DEBUG)

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
controlWeb.logger.setLevel(logging.DEBUG)

# Enregistrer les Blueprints de manière robuste (import + enregistrement en try/except)
def try_register(bp_module, bp_name, url_prefix=""):
    try:
        mod = __import__(bp_module, fromlist=[bp_name])
        bp = getattr(mod, bp_name)
        controlWeb.register_blueprint(bp, url_prefix=url_prefix)
        logger.info("Successfully registered blueprint %s from %s", bp_name, bp_module)
        return
    except Exception as e:
        logger.warning("Import of %s failed: %s", bp_module, e)

    # Fallback : tenter de charger le module depuis le filesystem si l'import normal échoue
    try:
        module_path = os.path.join(os.path.dirname(__file__), *bp_module.split('.')) + '.py'
        if os.path.exists(module_path):
            spec = importlib.util.spec_from_file_location(bp_module, module_path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[bp_module] = mod
            spec.loader.exec_module(mod)
            bp = getattr(mod, bp_name)
            controlWeb.register_blueprint(bp, url_prefix=url_prefix)
            logger.info("Successfully registered blueprint %s from file %s", bp_name, module_path)
            return
        else:
            logger.warning("Module file not found for %s at %s", bp_module, module_path)
    except Exception as e:
        logger.error("Fallback import failed for %s: %s", bp_module, e)
        logger.error("Traceback: %s", traceback.format_exc())

# tenter d'enregistrer les blueprints attendus
logger.info("Registering blueprints...")
try_register('routes.home', 'home_bp', "")
try_register('routes.minecraft', 'minecraft_bp', "")
try_register('routes.satisfactory', 'satisfactory_bp', "")
try_register('routes.auth', 'auth_bp', "")
try_register('routes.admin', 'admin_bp', "")
try_register('routes.api', 'api_bp', "")
try_register('routes.hytale', 'hytale_bp', "")
try_register('routes.game_servers', 'game_servers_bp', "")

# Exempt pure-API blueprints from CSRF — they are protected by session auth + SameSite=Lax.
# The auth blueprint form routes (login, signup, etc.) DO use CSRF tokens (added in templates).
# The auth blueprint JSON API sub-routes are also protected via @csrf.exempt in routes/auth.py.
try:
    from routes.api import api_bp as _api_bp
    csrf.exempt(_api_bp)
except Exception:
    logger.warning("Could not apply CSRF exemption to api_bp")

try:
    from routes.admin import admin_bp as _admin_bp
    csrf.exempt(_admin_bp)
except Exception:
    logger.warning("Could not apply CSRF exemption to admin_bp")

# route minimale restante
@controlWeb.route("/about")
def about():
    return render_template("about.html")


# secret key for sessions (must be set in env, refuse default)
SECRET = os.getenv("FLASK_SECRET")
if not SECRET or SECRET == "change-me-in-production":
    logger.critical("FLASK_SECRET environment variable is not set or uses the default value. Refusing to start for security reasons.")
    raise RuntimeError("FLASK_SECRET environment variable must be set to a strong random value in production.")
=======
>>>>>>> origin/develop
controlWeb.secret_key = SECRET
controlWeb.logger.setLevel(logger.level)

<<<<<<< HEAD
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
=======
# Enregistrement des context processors
controlWeb.context_processor(inject_user)
controlWeb.context_processor(inject_machine_info)
>>>>>>> origin/develop

# Enregistrement des blueprints génériques
controlWeb.register_blueprint(routes_bp)
controlWeb.register_blueprint(user_api_bp)

<<<<<<< HEAD
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

# rendre la session disponible dans les templates
@controlWeb.context_processor
def inject_user():
    def safe_url_for(endpoint, **values):
        """Version sécurisée de url_for qui ne plante pas si l'endpoint n'existe pas"""
        try:
            return url_for(endpoint, **values)
        except Exception:
            # Essayer avec le préfixe auth. si pas de préfixe
            if '.' not in endpoint:
                try:
                    return url_for(f'auth.{endpoint}', **values)
                except Exception:
                    pass
            # Retourner une URL par défaut si rien ne marche
            logger.warning("Could not build URL for endpoint '%s', using fallback", endpoint)
            return f"/{endpoint}"
    
    # determine avatar_url for templates
    avatar_url = None
    try:
        username = session.get('user')
        if username:
            users = _load_users_list()
            u = next((x for x in users if x.get('username') == username), None)
            if u:
                avatar_url = u.get('avatar_url')
    except Exception:
        logger.debug("Could not resolve avatar_url for user in context processor")

    if not avatar_url:
        try:
            avatar_url = url_for('static', filename='images/utilisateur.png')
        except Exception:
            avatar_url = '/static/images/utilisateur.png'

    return {
        'current_user': session.get('user'),
        'current_role': session.get('role'),
        'is_admin': session.get('role') == 'admin',
        'is_manager': session.get('role') == 'manager',
        'can_control_services': session.get('role') in ('admin', 'manager'),
        'safe_url_for': safe_url_for,  # Version sûre de url_for pour les templates
        'url_for': safe_url_for,  # Remplacer url_for par la version sûre
        'avatar_url': avatar_url,
        'csp_nonce': getattr(g, 'csp_nonce', ''),
    }

# --- nouveau: injecter machine_info globalement pour tous les templates ---
@controlWeb.context_processor
def inject_machine_info():
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        machine_info = {
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used": f"{mem.used / (1024 ** 3):.2f} GB",
            "ram_total": f"{mem.total / (1024 ** 3):.2f} GB",
            "disk_percent": round(disk.percent, 1),
            "disk_used": f"{disk.used / (1024 ** 3):.2f} GB",
            "disk_total": f"{disk.total / (1024 ** 3):.2f} GB"
        }
    except Exception:
        machine_info = None
    return {"machine_info": machine_info}

# Add helper to provide machine info for API use (keeps logic DRY)
def _get_machine_info():
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        return {
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used": f"{mem.used / (1024 ** 3):.2f} GB",
            "ram_total": f"{mem.total / (1024 ** 3):.2f} GB",
            "disk_percent": round(disk.percent, 1),
            "disk_used": f"{disk.used / (1024 ** 3):.2f} GB",
            "disk_total": f"{disk.total / (1024 ** 3):.2f} GB"
        }
    except Exception as e:
        logger.error("Error collecting machine info: %s", e)
        return None

# --- NEW: API endpoint for machine info (polled by frontend) ---
@controlWeb.route('/api/machine', methods=['GET'])
def api_machine():
    info = _get_machine_info()
    if info is None:
        return jsonify({"error": "server_error"}), 500
    return jsonify(info)

# quick health check
@controlWeb.route("/_ping")
def _ping():
    return "ok", 200

# Gestionnaire d'erreur pour les erreurs de build d'URL
@controlWeb.errorhandler(404)
def not_found_error(e):
    logger.warning("404 error: %s for path %s", e, request.path)
    # Si c'est une tentative d'accès à une page d'auth manquante, rediriger vers login
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

# ---------- NEW: user color API (uses session['user']) ----------
CONFIG_USERS = os.path.normpath(os.path.join(os.path.dirname(__file__), 'config', 'users.json'))

def _load_users_list():
    with open(CONFIG_USERS, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_users_list(users):
    tmp = CONFIG_USERS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_USERS)

def _get_session_username():
    # session['user'] expected to be the username string
    return session.get('user')

COLOR_RE = re.compile(r'^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$')

@controlWeb.route('/api/user', methods=['GET'])
def api_user():
    username = _get_session_username()
    if not username:
        return jsonify({'error': 'unauthenticated'}), 401
    try:
        users = _load_users_list()
        # users.json is an array of user objects
        user = next((u for u in users if u.get('username') == username), None)
        if not user:
            return jsonify({'error': 'not_found'}), 404
        return jsonify({
            'username': user.get('username'),
            'main_color': user.get('main_color'),
            'role': user.get('role')
        })
    except Exception as e:
        logger.error("Error in /api/user: %s", e)
        return jsonify({'error': 'server_error'}), 500

@controlWeb.route('/api/user/main-color', methods=['GET'])
def api_get_main_color():
    username = _get_session_username()
    if not username:
        return jsonify({'error': 'unauthenticated'}), 401
    try:
        users = _load_users_list()
        user = next((u for u in users if u.get('username') == username), None)
        if not user:
            return jsonify({'error': 'not_found'}), 404
        return jsonify({'username': user.get('username'), 'main_color': user.get('main_color')})
    except Exception as e:
        logger.error("Error in /api/user/main-color GET: %s", e)
        return jsonify({'error': 'server_error'}), 500

@controlWeb.route('/api/user/main-color', methods=['POST'])
def api_set_main_color():
    username = _get_session_username()
    if not username:
        return jsonify({'success': False, 'error': 'unauthenticated'}), 401
    data = request.get_json(silent=True) or {}
    color = data.get('main_color')
    if not color or not COLOR_RE.match(color):
        return jsonify({'success': False, 'error': 'invalid_color'}), 400
    try:
        users = _load_users_list()
        updated = False
        for u in users:
            if u.get('username') == username:
                u['main_color'] = color
                updated = True
                break
        if not updated:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        _save_users_list(users)
        return jsonify({'success': True, 'main_color': color})
    except Exception as e:
        logger.error("Error in /api/user/main-color POST: %s", e)
        return jsonify({'success': False, 'error': 'server_error'}), 500

# ---------- NEW: avatar upload/delete handling ----------
STATIC_IMAGES = os.path.join(os.path.dirname(__file__), 'static', 'images')
os.makedirs(STATIC_IMAGES, exist_ok=True)
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_filename(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

@controlWeb.route('/api/user/avatar', methods=['POST'])
def user_avatar():
    username = _get_session_username()
    if not username:
        return jsonify({'success': False, 'error': 'unauthenticated'}), 401

    # Delete request (JSON)
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if data.get('avatar_action') == 'delete_avatar':
            try:
                users = _load_users_list()
                for u in users:
                    if u.get('username') == username:
                        # remove avatar file if present
                        avatar_url = u.get('avatar_url')
                        if avatar_url:
                            try:
                                rel = avatar_url.split('/static/')[-1]
                                fpath = os.path.join(os.path.dirname(__file__), 'static', rel)
                                if os.path.exists(fpath):
                                    os.remove(fpath)
                            except Exception:
                                logger.exception("Failed removing avatar file")
                        # also remove user's images folder if empty (best effort)
                        u.pop('avatar_url', None)
                        _save_users_list(users)
                        return jsonify({'success': True})
                return jsonify({'success': False, 'error': 'not_found'}), 404
            except Exception as e:
                logger.error("Error deleting avatar: %s", e)
                return jsonify({'success': False, 'error': 'server_error'}), 500

    # Upload (multipart/form-data)
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'no_file'}), 400
    file = request.files['avatar']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'empty_filename'}), 400
    if not _allowed_filename(file.filename):
        return jsonify({'success': False, 'error': 'invalid_extension'}), 400

    try:
        # create per-user images folder
        user_folder = os.path.join(STATIC_IMAGES, secure_filename(username))
        os.makedirs(user_folder, exist_ok=True)
        # choose stable filename: avatar + original extension
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower() if ext else '.png'
        filename = secure_filename(f"avatar{ext}")
        save_path = os.path.join(user_folder, filename)

        # remove existing avatar files in user's folder (same name or others with avatar*)
        try:
            for existing in os.listdir(user_folder):
                if existing.startswith('avatar'):
                    try: os.remove(os.path.join(user_folder, existing))
                    except Exception: logger.debug("Could not remove existing avatar %s", existing)
        except Exception:
            logger.debug("No existing avatar cleanup needed for %s", user_folder)

        file.save(save_path)
        avatar_url = url_for('static', filename=f"images/{secure_filename(username)}/{filename}")
        users = _load_users_list()
        updated = False
        for u in users:
            if u.get('username') == username:
                u['avatar_url'] = avatar_url
                updated = True
                break
        if not updated:
            # cleanup file if no user found
            try: os.remove(save_path)
            except Exception: pass
            return jsonify({'success': False, 'error': 'not_found'}), 404
        _save_users_list(users)
        return jsonify({'success': True, 'avatar_url': avatar_url})
    except Exception as e:
        logger.error("Error saving avatar: %s", e)
        return jsonify({'success': False, 'error': 'server_error'}), 500

# ---------- NEW: migrate / reset password routes ----------
@controlWeb.route('/migrate-password', methods=['GET'])
def migrate_password_get():
    # page simple pour permettre migration (template optional)
    try:
        return render_template('migrate_password.html')
    except Exception:
        return "Migrate password page", 200


@controlWeb.route('/migrate-password', methods=['POST'])
def migrate_password_post():
    # Accept JSON or form data: { "username": "...", "new_password": "..." }
    data = request.get_json(silent=True) or request.form or {}
    username = data.get('username')
    new_password = data.get('new_password') or data.get('password')
    if not username or not new_password:
        return jsonify({'success': False, 'error': 'missing_fields'}), 400
    try:
        users = _load_users_list()
        updated = False
        for u in users:
            if u.get('username') == username:
                u['password'] = generate_password_hash(new_password)
                u['migrated'] = True
                updated = True
                break
        if not updated:
            return jsonify({'success': False, 'error': 'not_found'}), 404
        _save_users_list(users)
        return jsonify({'success': True})
    except Exception as e:
        logger.error("Error in migrate-password POST: %s", e)
        return jsonify({'success': False, 'error': 'server_error'}), 500


@controlWeb.route('/reset-password', methods=['GET'])
def reset_password_get():
    try:
        return render_template('reset_password.html')
    except Exception:
        return "Reset password page", 200


@controlWeb.route('/reset-password', methods=['POST'])
def reset_password_post():
    # JSON-driven flow:
    # 1) { "action": "request_reset", "username": "..." } -> generates reset_token (returned here for dev)
    # 2) { "action": "confirm_reset", "username": "...", "token": "...", "new_password": "..." } -> sets new password
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    username = data.get('username')
    if not action or not username:
        return jsonify({'success': False, 'error': 'missing_fields'}), 400
    try:
        users = _load_users_list()
        user = next((u for u in users if u.get('username') == username), None)
        if not user:
            return jsonify({'success': False, 'error': 'not_found'}), 404

        if action == 'request_reset':
            token = secrets.token_urlsafe(24)
            user['reset_token'] = token
            _save_users_list(users)
            # In production send token by email; for dev return token
            return jsonify({'success': True, 'reset_token': token})

        if action == 'confirm_reset':
            token = data.get('token')
            new_password = data.get('new_password') or data.get('password')
            if not token or not new_password:
                return jsonify({'success': False, 'error': 'missing_fields'}), 400
            if user.get('reset_token') != token:
                return jsonify({'success': False, 'error': 'invalid_token'}), 400
            user['password'] = generate_password_hash(new_password)
            user.pop('reset_token', None)
            _save_users_list(users)
            return jsonify({'success': True})

        return jsonify({'success': False, 'error': 'unknown_action'}), 400
    except Exception as e:
        logger.error("Error in reset-password POST: %s", e)
        return jsonify({'success': False, 'error': 'server_error'}), 500

# Add startup logging
logger.info("Flask app configuration complete")
logger.info("Debug mode: %s", controlWeb.debug)
logger.info("Secret key configured: %s", bool(controlWeb.secret_key))

# Protection contre l'exécution multiple
=======
# Enregistrement des blueprints métiers
controlWeb.register_blueprint(home_bp)
controlWeb.register_blueprint(minecraft_bp)
controlWeb.register_blueprint(satisfactory_bp)
controlWeb.register_blueprint(auth_bp)
controlWeb.register_blueprint(admin_bp)
controlWeb.register_blueprint(api_bp)
controlWeb.register_blueprint(hytale_bp)
controlWeb.register_blueprint(game_servers_bp)

>>>>>>> origin/develop
if __name__ == '__main__':
    logger.info("Starting Flask app...")
    _debug = os.getenv("FLASK_DEBUG", "0") == "1"
    _host = os.getenv("FLASK_HOST", "0.0.0.0")
    _port = int(os.getenv("FLASK_PORT", "5000"))
    cert_path = "/home/web_server/certs/certificate.crt"
    key_path = "/home/web_server/certs/private.key"
    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"Using SSL context: cert={cert_path}, key={key_path}")
<<<<<<< HEAD
        controlWeb.run(debug=_debug, host=_host, port=_port, ssl_context=(cert_path, key_path))
    else:
        logger.warning("Certificat SSL ou clé privée manquants, lancement sans HTTPS !")
        controlWeb.run(debug=_debug, host=_host, port=_port)
=======
        controlWeb.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, ssl_context=(cert_path, key_path))
    else:
        logger.warning("Certificat SSL ou clé privée manquants, lancement sans HTTPS !")
        controlWeb.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)


# Protection contre l'exécution multiple
if __name__ == '__main__':
    logger.info("Starting Flask app...")
    cert_path = "/home/web_server/certs/certificate.crt"
    key_path = "/home/web_server/certs/private.key"
    # Par défaut, ne pas binder sur 0.0.0.0 sauf si explicitement demandé
    flask_host = os.getenv("FLASK_HOST", "127.0.0.1")
    flask_port = int(os.getenv("FLASK_PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"Using SSL context: cert={cert_path}, key={key_path}")
        controlWeb.run(debug=debug_mode, host=flask_host, port=flask_port, ssl_context=(cert_path, key_path))
    else:
        logger.warning("Certificat SSL ou clé privée manquants, lancement sans HTTPS !")
        controlWeb.run(debug=debug_mode, host=flask_host, port=flask_port)
>>>>>>> origin/develop
