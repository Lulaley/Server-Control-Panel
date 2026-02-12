import os
import json
import logging
import re
import hashlib
import base64
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_PATH = os.path.join(BASE_DIR, "config", "users.json")
PENDING_PATH = os.path.join(BASE_DIR, "config", "pending_users.json")
RESET_PATH = os.path.join(BASE_DIR, "config", "reset_requests.json")

# fallback if config is in parent dir
if not os.path.exists(USERS_PATH):
    alt = os.path.join(os.path.dirname(BASE_DIR), "config", "users.json")
    if os.path.exists(alt):
        USERS_PATH = alt
logger.debug("users.py: USING USERS_PATH %s", USERS_PATH)

def load_users():
    try:
        if os.path.exists(USERS_PATH):
            with open(USERS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f) or []
            out = {}
            for u in data:
                if isinstance(u, dict) and u.get("username"):
                    out[u["username"]] = u
            return out
    except Exception:
        logger.exception("load_users failed")
    return {}

def save_users_dict(users_dict):
    try:
        for u in users_dict.values():
            pw = u.get("password", "")
            if isinstance(pw, str) and not pw.startswith("pbkdf2:"):
                u["password"] = generate_password_hash(pw)
        os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump(list(users_dict.values()), f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logger.exception("save_users_dict failed")
        return False

def load_pending():
    try:
        if os.path.exists(PENDING_PATH):
            with open(PENDING_PATH, "r", encoding="utf-8") as f:
                return json.load(f) or []
    except Exception:
        logger.exception("load_pending failed")
    return []

def save_pending(pending_list):
    """
    Écrit la liste pending et envoie un email pour chaque nouvel utilisateur
    ajouté (comparé à la liste existante retournée par load_pending()).
    """
    try:
        old = load_pending()
    except Exception:
        old = []

    old_usernames = {p.get("username") for p in old if p}
    new_entries = [p for p in pending_list if p and p.get("username") not in old_usernames]

    # déterminer le chemin du fichier utilisé originellement par ce module
    try:
        path = PENDING_FILE  # si défini dans ce module
    except NameError:
        try:
            path = PENDING_PATH
        except NameError:
            # fallback : tentative de position relative (modifier si nécessaire)
            path = os.path.join(os.path.dirname(__file__), "..", "data", "pending.json")

    # écrire la nouvelle liste pending
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pending_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("save_pending write error:", e)
        return False

    # prévenir les admins pour chaque nouvel enregistrement
    try:
        from .mailer import send_new_pending_email
        for entry in new_entries:
            try:
                send_new_pending_email(entry.get("username"), entry.get("role"))
            except Exception as e:
                print("notification error for", entry.get("username"), e)
    except Exception as e:
        # si le module mailer n'est pas disponible, on continue silencieusement
        print("mailer import/send error:", e)

    return True

def load_reset_requests():
    try:
        if os.path.exists(RESET_PATH):
            with open(RESET_PATH, "r", encoding="utf-8") as f:
                return json.load(f) or []
    except Exception:
        logger.exception("load_reset_requests failed")
    return []

def save_reset_requests(reset_list):
    try:
        os.makedirs(os.path.dirname(RESET_PATH), exist_ok=True)
        with open(RESET_PATH, "w", encoding="utf-8") as f:
            json.dump(reset_list, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logger.exception("save_reset_requests failed")
        return False

def save_user_record(rec):
    users = load_users()
    if rec.get("username") in users:
        return False
    pw = rec.get("password", "")
    if not isinstance(pw, str):
        return False
    if not pw.startswith("pbkdf2:"):
        rec["password"] = generate_password_hash(pw)
    users[rec["username"]] = rec
    try:
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump(list(users.values()), f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        logger.exception("save_user_record failed")
        return False

def verify_scrypt_hash(stored_hash, password):
    """Vérifie un mot de passe contre un hash scrypt (DEPRECATED - migre vers pbkdf2)"""
    logger.warning("Using deprecated scrypt hash verification for hash: %s", stored_hash[:20])
    # Pour tous les anciens hashes scrypt, on considère qu'ils sont cassés
    # et on demande une réinitialisation
    return False

def migrate_user_to_pbkdf2(username, password):
    """Migre un utilisateur vers pbkdf2 avec un nouveau mot de passe"""
    from werkzeug.security import generate_password_hash
    try:
        users = load_users()
        if username not in users:
            return False
        
        # Générer un nouveau hash pbkdf2
        new_hash = generate_password_hash(password)
        users[username]["password"] = new_hash
        
        if save_users_dict(users):
            logger.info("Successfully migrated user %s to pbkdf2", username)
            return True
        else:
            logger.error("Failed to save migrated user %s", username)
            return False
    except Exception as e:
        logger.error("Error migrating user %s: %s", username, e)
        return False

def create_user(username, password, role="user", main_color="#4caf50"):
    """Créer un nouvel utilisateur avec un hash de mot de passe sécurisé"""
    try:
        # Charger les utilisateurs existants
        users = load_users()
        
        # Vérifier si l'utilisateur existe déjà
        if username in users:
            logger.warning("User '%s' already exists", username)
            return False
        
        # Créer le hash du mot de passe
        password_hash = generate_password_hash(password)
        
        # Créer l'enregistrement utilisateur
        user_record = {
            "username": username,
            "password": password_hash,
            "role": role,
            "main_color": main_color
        }
        
        # Ajouter à la liste des utilisateurs
        users[username] = user_record
        
        # Sauvegarder
        success = save_users_dict(users)
        if success:
            logger.info("User '%s' created successfully with role '%s'", username, role)
        else:
            logger.error("Failed to save user '%s'", username)
        
        return success
        
    except Exception as e:
        logger.exception("Error creating user '%s': %s", username, e)
        return False
