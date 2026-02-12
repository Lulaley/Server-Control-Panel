from flask import Blueprint, jsonify, request, session
import json, os, re
from flask_login import current_user

bp = Blueprint('user_api', __name__)

USERS_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'config', 'users.json'))

def load_users():
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    tmp = USERS_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    os.replace(tmp, USERS_FILE)

def get_username():
    try:
        if current_user and getattr(current_user, 'is_authenticated', False):
            return getattr(current_user, 'username', None)
    except Exception:
        pass
    return session.get('username')

@bp.route('/api/user', methods=['GET'])
def api_user():
    username = get_username()
    if not username:
        return jsonify({'error': 'unauthenticated'}), 401
    users = load_users()
    user = next((u for u in users if u.get('username') == username), None)
    if not user:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({'username': user.get('username'), 'main_color': user.get('main_color'), 'role': user.get('role')})

@bp.route('/api/user/main-color', methods=['GET'])
def get_main_color():
    username = get_username()
    if not username:
        return jsonify({'error': 'unauthenticated'}), 401
    users = load_users()
    user = next((u for u in users if u.get('username') == username), None)
    if not user:
        return jsonify({'error': 'not_found'}), 404
    return jsonify({'username': user.get('username'), 'main_color': user.get('main_color')})

@bp.route('/api/user/main-color', methods=['POST'])
def set_main_color():
    username = get_username()
    if not username:
        return jsonify({'success': False, 'error': 'unauthenticated'}), 401
    data = request.get_json(silent=True) or {}
    color = data.get('main_color')
    if not color or not re.match(r'^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$', color):
        return jsonify({'success': False, 'error': 'invalid_color'}), 400
    users = load_users()
    for u in users:
        if u.get('username') == username:
            u['main_color'] = color
            save_users(users)
            return jsonify({'success': True, 'main_color': color})
    return jsonify({'success': False, 'error': 'not_found'}), 404
