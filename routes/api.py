from flask import Blueprint, jsonify, session, request
import subprocess
import re
from utils.users import load_users, save_users_dict, generate_password_hash, check_password_hash  # imported if needed for future
api_bp = Blueprint('api', __name__)

@api_bp.route("/api/services/<service_name>/<action>", methods=["POST"])
def api_service_control(service_name, action):
    user_role = session.get("role")
    if user_role not in ("admin", "manager"):
        return jsonify({"error": "forbidden", "message": "Seuls les administrateurs et managers peuvent contrôler les services"}), 403
    if action not in ("start", "stop", "restart", "enable", "disable"):
        return jsonify({"error": "invalid_action", "message": "Action non valide"}), 400
    if not re.match(r'^[a-zA-Z0-9_.-]+$', service_name):
        return jsonify({"error": "invalid_service_name", "message": "Nom de service invalide"}), 400
    try:
        cmd = ["sudo", "systemctl", action, service_name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": f"Service {service_name} {action} exécuté avec succès",
                "service": service_name,
                "action": action
            })
        else:
            return jsonify({
                "error": "command_failed",
                "message": f"Échec de l'opération {action} sur le service {service_name}",
                "details": result.stderr
            }), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "timeout", "message": f"Timeout lors de l'exécution de {action} sur {service_name}"}), 500
    except Exception as e:
        return jsonify({"error": "system_error", "message": f"Erreur système: {str(e)}"}), 500

@api_bp.route("/api/services/<service_name>/status", methods=["GET"])
def api_service_status(service_name):
    if not re.match(r'^[a-zA-Z0-9_.-]+$', service_name):
        return jsonify({"error": "invalid_service_name"}), 400
    try:
        cmd = ["systemctl", "is-active", service_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        is_active = result.stdout.strip()
        cmd_enabled = ["systemctl", "is-enabled", service_name]
        result_enabled = subprocess.run(cmd_enabled, capture_output=True, text=True)
        is_enabled = result_enabled.stdout.strip()
        return jsonify({
            "service": service_name,
            "status": is_active,
            "enabled": is_enabled,
            "can_control": session.get("role") in ("admin", "manager")
        })
    except Exception as e:
        return jsonify({"error": "status_check_failed", "message": str(e)}), 500

@api_bp.route("/user/change-password", methods=["POST"])
def change_password():
    if not session.get("user"):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")
        confirm_password = data.get("confirm_password", "")
        
        username = session.get("user")
        logger.info("Password change attempt for user %s", username)
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            return jsonify({"error": "Tous les champs sont requis"}), 400
            
        if new_password != confirm_password:
            return jsonify({"error": "Les nouveaux mots de passe ne correspondent pas"}), 400
            
        if len(new_password) < 6:
            return jsonify({"error": "Le nouveau mot de passe doit contenir au moins 6 caractères"}), 400
        
        # Charger les utilisateurs et vérifier le mot de passe actuel
        users = load_users()
        if username not in users:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
            
        stored_password = users[username].get("password", "")
        logger.info("Current password for %s starts with: %s", username, stored_password[:20])
        
        # Vérifier le mot de passe actuel (supporter les deux formats)
        password_ok = False
        if stored_password.startswith("pbkdf2:"):
            password_ok = check_password_hash(stored_password, current_password)
            logger.debug("pbkdf2 password check result: %s", password_ok)
        elif stored_password.startswith("scrypt:"):
            from utils.users import verify_scrypt_hash
            password_ok = verify_scrypt_hash(stored_password, current_password)
            logger.debug("scrypt password check result: %s", password_ok)
        else:
            # Fallback pour les anciens mots de passe en clair
            password_ok = (stored_password == current_password)
            logger.debug("plaintext password check result: %s", password_ok)
        
        if not password_ok:
            logger.warning("Password verification failed for user %s", username)
            return jsonify({"error": "Mot de passe actuel incorrect"}), 400
        
        # FORCER l'utilisation de pbkdf2 pour le nouveau mot de passe
        new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        logger.info("Generated new pbkdf2 hash for %s: %s", username, new_hash[:30])
        
        users[username]["password"] = new_hash
        
        # Sauvegarder
        if save_users_dict(users):
            # Vérifier que la sauvegarde a fonctionné
            users_check = load_users()
            saved_hash = users_check.get(username, {}).get("password", "")
            logger.info("Verification - saved password for %s starts with: %s", username, saved_hash[:20])
            
            if saved_hash.startswith("pbkdf2:"):
                logger.info("Password changed successfully for user %s (now using pbkdf2)", username)
                return jsonify({"success": True, "message": "Mot de passe modifié avec succès"})
            else:
                logger.error("Password change failed - hash not saved correctly for %s", username)
                return jsonify({"error": "Erreur lors de la sauvegarde du nouveau mot de passe"}), 500
        else:
            logger.error("Failed to save new password for user %s", username)
            return jsonify({"error": "Erreur lors de la sauvegarde"}), 500
            
    except Exception as e:
        logger.error("Error changing password for user %s: %s", session.get("user"), e)
        logger.error("Password change traceback: %s", traceback.format_exc())
        return jsonify({"error": "Erreur interne du serveur"}), 500

@api_bp.route("/user/change-username", methods=["POST"])
def change_username():
    if not session.get("user"):
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        new_username = (data.get("new_username", "") or "").strip()
        current_password = data.get("current_password", "")
        
        current_username = session.get("user")
        
        # Validation
        if not new_username or not current_password:
            return jsonify({"error": "Tous les champs sont requis"}), 400
            
        if len(new_username) < 3:
            return jsonify({"error": "Le nom d'utilisateur doit contenir au moins 3 caractères"}), 400
            
        if new_username == current_username:
            return jsonify({"error": "Le nouveau nom d'utilisateur doit être différent"}), 400
        
        # Charger les utilisateurs
        users = load_users()
        if current_username not in users:
            return jsonify({"error": "Utilisateur actuel non trouvé"}), 404
            
        if new_username in users:
            return jsonify({"error": "Ce nom d'utilisateur est déjà pris"}), 400
        
        # Vérifier le mot de passe actuel
        stored_password = users[current_username].get("password", "")
        password_ok = False
        
        if stored_password.startswith("pbkdf2:"):
            password_ok = check_password_hash(stored_password, current_password)
        elif stored_password.startswith("scrypt:"):
            from utils.users import verify_scrypt_hash
            password_ok = verify_scrypt_hash(stored_password, current_password)
        else:
            password_ok = (stored_password == current_password)
        
        if not password_ok:
            return jsonify({"error": "Mot de passe incorrect"}), 400
        
        # Effectuer le changement de nom d'utilisateur
        user_data = users[current_username].copy()
        del users[current_username]
        users[new_username] = user_data
        
        # Sauvegarder
        if save_users_dict(users):
            # Mettre à jour la session
            session["user"] = new_username
            logger.info("Username changed from %s to %s", current_username, new_username)
            return jsonify({"success": True, "message": "Nom d'utilisateur modifié avec succès", "new_username": new_username})
        else:
            return jsonify({"error": "Erreur lors de la sauvegarde"}), 500
            
    except Exception as e:
        logger.error("Error changing username for user %s: %s", session.get("user"), e)
        return jsonify({"error": "Erreur interne du serveur"}), 500
