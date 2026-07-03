# Ajout de la fonction _get_machine_info pour fournir les infos machine
import psutil
from flask import url_for, session
import logging
import os
import json
import re
from werkzeug.utils import secure_filename

from app_config import logger

# Helpers
def _get_machine_info():
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
    
def _delete_user_avatar(username):
    """Supprime l’avatar de l’utilisateur si présent."""
    if not username:
        return False, 'not_found'
    avatar_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'avatars')
    found = False
    for ext in ALLOWED_EXT:
        avatar_path = os.path.join(avatar_dir, f"{username}.{ext}")
        if os.path.exists(avatar_path):
            try:
                os.remove(avatar_path)
                found = True
            except Exception:
                return False, 'server_error'
    if found:
        return True, None
    else:
        return False, 'not_found'
    
def _safe_url_for(endpoint, **values):
    try:
        return url_for(endpoint, **values)
    except Exception:
        if '.' not in endpoint:
            try:
                return url_for(f'auth.{endpoint}', **values)
            except Exception:
                pass
        logger.warning("Could not build URL for endpoint '%s', using fallback", endpoint)
        return f"/{endpoint}"

def _get_avatar_url(username):
    try:
        if username:
            users = _load_users_list()
            u = next((x for x in users if x.get('username') == username), None)
            if u:
                return u.get('avatar_url')
    except Exception:
        logger.debug("Could not resolve avatar_url for user in context processor")
    try:
        return url_for('static', filename='images/utilisateur.png')
    except Exception:
        return '/static/images/utilisateur.png'

def _get_session_username():
    return session.get('user')

def _load_users_list():
    CONFIG_USERS = os.path.normpath(os.path.join(os.path.dirname(__file__), 'config', 'users.json'))
    with open(CONFIG_USERS, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_users_list(users):
    CONFIG_USERS = os.path.normpath(os.path.join(os.path.dirname(__file__), 'config', 'users.json'))
    tmp = CONFIG_USERS + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    os.replace(tmp, CONFIG_USERS)

COLOR_RE = re.compile(r'^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$')
STATIC_IMAGES = os.path.join(os.path.dirname(__file__), 'static', 'images')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def _allowed_filename(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def _save_user_avatar_file(username, file_storage):
    """Enregistre le fichier avatar pour l'utilisateur."""
    if not username or not file_storage:
        return False, 'invalid'
    ext = file_storage.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return False, 'invalid_ext'
    avatar_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'avatars')
    os.makedirs(avatar_dir, exist_ok=True)
    avatar_path = os.path.join(avatar_dir, f"{username}.{ext}")
    try:
        file_storage.save(avatar_path)
        return True, None
    except Exception:
        return False, 'server_error'
