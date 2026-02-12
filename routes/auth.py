from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from utils.users import (
    load_users, save_users_dict, load_pending, save_pending,
    load_reset_requests, save_reset_requests, save_user_record, verify_scrypt_hash
)
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.form or {}
        username = (data.get("username") or "").strip()
        password = (data.get("password") or "").strip()
        role = (data.get("role") or "user").strip()
        if not username or not password:
            return render_template("signup.html", error="Utilisateur et mot de passe requis.")
        users = load_users()
        pending = load_pending()
        if username in users or any(p.get("username") == username for p in pending):
            return render_template("signup.html", error="Nom d'utilisateur déjà utilisé.")
        if role == "admin":
            role = "user"
        hashed = generate_password_hash(password)
        pending.append({"username": username, "password": hashed, "role": role})
        save_pending(pending)
        return render_template("signup.html", success="Demande enregistrée. Un administrateur validera votre compte.")
    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    users = load_users()
    if request.method == "POST":
        data = request.form or {}
        username = (data.get("username") or "").strip()
        password = data.get("password", "")
        logger.info("Login attempt for username=%r", username)
        
        u = users.get(username)
        if not u:
            logger.warning("Login failed: user %r not found", username)
            return render_template("login.html", error="Identifiants invalides", next=request.args.get("next", "/"))
        
        stored = u.get("password", "")
        logger.debug("Stored password starts with: %s", stored[:20] if stored else "EMPTY")
        ok = False
        
        try:
            # Vérifier d'abord si c'est un hash pbkdf2 moderne (priorité absolue)
            if stored.startswith("pbkdf2:"):
                ok = check_password_hash(stored, password)
                logger.debug("pbkdf2 check result: %s", ok)
                
                if ok:
                    session["user"] = username
                    session["role"] = u.get("role", "user")
                    logger.info("Login successful for user %s with pbkdf2 hash", username)
                    nxt = request.args.get("next") or request.form.get("next") or "/"
                    return redirect(nxt)
                else:
                    logger.warning("pbkdf2 password mismatch for user %s", username)
                    return render_template("login.html", error="Identifiants invalides", next=request.args.get("next", "/"))
                
            # Si c'est un ancien hash scrypt, rediriger vers la page de migration
            elif stored.startswith("scrypt:"):
                logger.info("User %s has legacy scrypt hash, redirecting to migration", username)
                return redirect(url_for("auth.migrate_password", username=username, next=request.args.get("next", "/")))
                
            # Fallback pour les mots de passe en clair (très anciens)
            else:
                logger.debug("Trying plaintext comparison for user %s", username)
                if stored == password:
                    ok = True
                    # Migrer immédiatement vers pbkdf2
                    users[username]["password"] = generate_password_hash(password)
                    save_users_dict(users)
                    logger.info("Migrated user %s from plaintext to pbkdf2", username)
                    
                    session["user"] = username
                    session["role"] = u.get("role", "user")
                    nxt = request.args.get("next") or request.form.get("next") or "/"
                    return redirect(nxt)
                else:
                    logger.debug("Plaintext comparison failed")
                    
        except Exception:
            logger.exception("Password verify error for user %s", username)
            ok = False
        
        # Si on arrive ici, c'est que l'authentification a échoué
        logger.warning("Login failed: password mismatch for user %s", username)
        return render_template("login.html", error="Identifiants invalides", next=request.args.get("next", "/"))
            
    return render_template("login.html", next=request.args.get("next", "/"))

@auth_bp.route("/migrate-password", methods=["GET", "POST"])
def migrate_password():
    """Page pour migrer les anciens mots de passe scrypt vers pbkdf2"""
    if request.method == "POST":
        data = request.form or {}
        username = (data.get("username") or "").strip()
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")
        
        logger.info("Migration attempt for user: %s", username)
        
        if not username or not new_password or not confirm_password:
            return render_template("migrate_password.html", 
                                 username=username,
                                 next=request.form.get("next", "/"),
                                 error="Tous les champs sont requis")
        
        if new_password != confirm_password:
            return render_template("migrate_password.html", 
                                 username=username,
                                 next=request.form.get("next", "/"),
                                 error="Les mots de passe ne correspondent pas")
        
        if len(new_password) < 6:
            return render_template("migrate_password.html", 
                                 username=username,
                                 next=request.form.get("next", "/"),
                                 error="Le mot de passe doit contenir au moins 6 caractères")
        
        # Recharger les utilisateurs pour éviter les problèmes de cache
        users = load_users()
        if username not in users:
            return render_template("migrate_password.html", 
                                 username=username,
                                 next=request.form.get("next", "/"),
                                 error="Utilisateur non trouvé")
        
        stored = users[username].get("password", "")
        logger.info("Current stored password for %s starts with: %s", username, stored[:20] if stored else "EMPTY")
        
        # Vérifier si ce n'est pas déjà migré
        if stored.startswith("pbkdf2:"):
            logger.info("User %s already has pbkdf2 hash, redirecting to login", username)
            # Connecter automatiquement l'utilisateur puisque le mot de passe est déjà migré
            session["user"] = username
            session["role"] = users[username].get("role", "user")
            nxt = request.form.get("next") or "/"
            return redirect(nxt)
        
        if not stored.startswith("scrypt:"):
            return render_template("migrate_password.html", 
                                 username=username,
                                 next=request.form.get("next", "/"),
                                 error="Ce compte n'a pas besoin de migration")
        
        # Effectuer la migration
        try:
            # FORCER l'utilisation de pbkdf2 au lieu de scrypt
            new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            logger.info("Generated new pbkdf2 hash for %s: %s", username, new_hash[:30])
            
            # Mettre à jour directement dans le dictionnaire
            users[username]["password"] = new_hash
            
            # Forcer la sauvegarde
            if save_users_dict(users):
                logger.info("Successfully saved migrated user %s", username)
                
                # Vérifier que la sauvegarde a bien fonctionné en rechargeant
                users_check = load_users()
                saved_hash = users_check.get(username, {}).get("password", "")
                logger.info("Verification - saved password for %s starts with: %s", username, saved_hash[:20])
                
                if saved_hash.startswith("pbkdf2:"):
                    # Connecter automatiquement l'utilisateur
                    session["user"] = username
                    session["role"] = users_check[username].get("role", "user")
                    logger.info("Successfully migrated and logged in user %s with new pbkdf2 hash", username)
                    
                    nxt = request.form.get("next") or "/"
                    return redirect(nxt)
                else:
                    logger.error("Migration failed - hash not saved correctly for %s. Expected pbkdf2:, got: %s", username, saved_hash[:20])
                    return render_template("migrate_password.html", 
                                         username=username,
                                         next=request.form.get("next", "/"),
                                         error="Erreur lors de la sauvegarde de la migration. Réessayez.")
            else:
                logger.error("Failed to save migrated user %s", username)
                return render_template("migrate_password.html", 
                                     username=username,
                                     next=request.form.get("next", "/"),
                                     error="Erreur lors de la sauvegarde. Contactez un administrateur.")
        except Exception as e:
            logger.error("Migration error for user %s: %s", username, e)
            logger.error("Migration traceback: %s", traceback.format_exc())
            return render_template("migrate_password.html", 
                                 username=username,
                                 next=request.form.get("next", "/"),
                                 error="Erreur lors de la migration. Contactez un administrateur.")
    
    # GET request
    username = request.args.get("username", "")
    next_url = request.args.get("next", "/")
    
    # Vérifier si l'utilisateur a encore besoin de migration
    if username:
        users = load_users()
        if username in users:
            stored = users[username].get("password", "")
            if stored.startswith("pbkdf2:"):
                logger.info("User %s already migrated, redirecting to login", username)
                return redirect(url_for("auth.login", next=next_url))
    
    return render_template("migrate_password.html", username=username, next=next_url)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        data = request.form or {}
        username = (data.get("username") or "").strip()
        if not username:
            return render_template("reset_password.html", error="Nom d'utilisateur requis.")
        users = load_users()
        if username not in users:
            return render_template("reset_password.html", error="Utilisateur non trouvé.")
        reset_requests = load_reset_requests()
        if any(r.get("username") == username for r in reset_requests):
            return render_template("reset_password.html", error="Une demande de reset est déjà en cours pour cet utilisateur.")
        reset_requests.append({"username": username})
        save_reset_requests(reset_requests)
        return render_template("reset_password.html", success="Demande de reset envoyée. Un administrateur validera votre demande.")
    return render_template("reset_password.html")

@auth_bp.route("/profile")
def profile():
    return render_template("profile.html")

@auth_bp.route("/api/whoami")
def api_whoami():
    user = session.get("user")
    role = session.get("role")
    if not user:
        return jsonify({"user": None}), 401
    return jsonify({"user": user, "role": role})

# User color API
@auth_bp.route("/api/user/main-color", methods=["GET", "POST"])
def api_user_main_color():
    user = session.get("user")
    if not user:
        return jsonify({"error": "unauthenticated"}), 401
    if request.method == "GET":
        users = load_users()
        u = users.get(user)
        return jsonify({"main_color": u.get("main_color", "#4caf50") if u else "#4caf50"})
    data = request.get_json() or {}
    main_color = data.get("main_color", "#4caf50")
    if not isinstance(main_color, str) or not main_color.startswith("#") or len(main_color) != 7:
        return jsonify({"success": False, "error": "Format de couleur invalide"}), 400
    users = load_users()
    if user in users:
        users[user]["main_color"] = main_color
        if save_users_dict(users):
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Erreur de sauvegarde"}), 500
    return jsonify({"success": False, "error": "Utilisateur non trouvé"}), 404

# Change username/password endpoints
@auth_bp.route("/api/user/change-username", methods=["POST"])
def api_change_username():
    current_username = session.get("user")
    if not current_username:
        return jsonify({"error": "unauthenticated"}), 401
    data = request.get_json() or {}
    new_username = (data.get("new_username") or "").strip()
    current_password = data.get("current_password", "")
    if not new_username or not current_password:
        return jsonify({"error": "Nouveau nom d'utilisateur et mot de passe actuel requis"}), 400
    users = load_users()
    current_user = users.get(current_username)
    if not current_user:
        return jsonify({"error": "Utilisateur actuel non trouvé"}), 404
    stored_password = current_user.get("password", "")
    password_valid = False
    try:
        password_valid = check_password_hash(stored_password, current_password)
    except Exception:
        password_valid = False
    if not password_valid and stored_password != current_password:
        return jsonify({"error": "Mot de passe actuel incorrect"}), 400
    if new_username in users and new_username != current_username:
        return jsonify({"error": "Ce nom d'utilisateur est déjà utilisé"}), 400
    pending = load_pending()
    if any(p.get("username") == new_username for p in pending):
        return jsonify({"error": "Ce nom d'utilisateur est déjà en attente de validation"}), 400
    user_data = users.pop(current_username)
    user_data["username"] = new_username
    users[new_username] = user_data
    if not save_users_dict(users):
        return jsonify({"error": "Erreur lors de la sauvegarde"}), 500
    session["user"] = new_username
    return jsonify({"status": "success", "message": "Nom d'utilisateur modifié avec succès"})

@auth_bp.route("/api/user/change-password", methods=["POST"])
def api_change_password():
    username = session.get("user")
    if not username:
        return jsonify({"error": "unauthenticated"}), 401
    data = request.get_json() or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")
    if not current_password or not new_password or not confirm_password:
        return jsonify({"error": "Tous les champs sont requis"}), 400
    if new_password != confirm_password:
        return jsonify({"error": "Les nouveaux mots de passe ne correspondent pas"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "Le nouveau mot de passe doit contenir au moins 6 caractères"}), 400
    users = load_users()
    user = users.get(username)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    stored_password = user.get("password", "")
    password_valid = False
    try:
        password_valid = check_password_hash(stored_password, current_password)
    except Exception:
        password_valid = False
    if not password_valid and stored_password != current_password:
        return jsonify({"error": "Mot de passe actuel incorrect"}), 400
    users[username]["password"] = generate_password_hash(new_password)
    if not save_users_dict(users):
        return jsonify({"error": "Erreur lors de la sauvegarde"}), 500
    return jsonify({"status": "success", "message": "Mot de passe modifié avec succès"})
