from flask import Blueprint, jsonify, request, render_template
from werkzeug.security import generate_password_hash
import secrets
from app_utils import _get_session_username, _load_users_list, _save_users_list, COLOR_RE, _allowed_filename, _delete_user_avatar, _save_user_avatar_file

user_api_bp = Blueprint('user_api_bp', __name__)

@user_api_bp.route('/api/user', methods=['GET'])
def api_user():
    username = _get_session_username()
    if not username:
        return jsonify({'error': 'unauthenticated'}), 401
    try:
        users = _load_users_list()
        user = next((u for u in users if u.get('username') == username), None)
        if not user:
            return jsonify({'error': 'not_found'}), 404
        return jsonify({
            'username': user.get('username'),
            'main_color': user.get('main_color'),
            'role': user.get('role')
        })
    except Exception as e:
        return jsonify({'error': 'server_error'}), 500

@user_api_bp.route('/api/user/main-color', methods=['GET'])
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
        return jsonify({'error': 'server_error'}), 500

@user_api_bp.route('/api/user/main-color', methods=['POST'])
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
        return jsonify({'success': False, 'error': 'server_error'}), 500

@user_api_bp.route('/api/user/avatar/delete', methods=['POST'])
def user_avatar_delete():
    username = _get_session_username()
    if not username:
        return jsonify({'success': False, 'error': 'unauthenticated'}), 401
    ok, err = _delete_user_avatar(username)
    if ok:
        return jsonify({'success': True})
    elif err == 'not_found':
        return jsonify({'success': False, 'error': 'not_found'}), 404
    else:
        return jsonify({'success': False, 'error': 'server_error'}), 500

@user_api_bp.route('/api/user/avatar', methods=['POST'])
def user_avatar_upload():
    username = _get_session_username()
    if not username:
        return jsonify({'success': False, 'error': 'unauthenticated'}), 401
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'no_file'}), 400
    file = request.files['avatar']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'empty_filename'}), 400
    if not _allowed_filename(file.filename):
        return jsonify({'success': False, 'error': 'invalid_extension'}), 400
    ok, err, avatar_url = _save_user_avatar_file(username, file)
    if ok:
        return jsonify({'success': True, 'avatar_url': avatar_url})
    elif err == 'not_found':
        return jsonify({'success': False, 'error': 'not_found'}), 404
    else:
        return jsonify({'success': False, 'error': 'server_error'}), 500

@user_api_bp.route('/migrate-password', methods=['GET'])
def migrate_password_get():
    try:
        return render_template('migrate_password.html')
    except Exception:
        return "Migrate password page", 200

@user_api_bp.route('/migrate-password', methods=['POST'])
def migrate_password_post():
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
        return jsonify({'success': False, 'error': 'server_error'}), 500

@user_api_bp.route('/reset-password', methods=['GET'])
def reset_password_get():
    try:
        return render_template('reset_password.html')
    except Exception:
        return "Reset password page", 200

@user_api_bp.route('/reset-password', methods=['POST'])
def reset_password_post():
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
        return jsonify({'success': False, 'error': 'server_error'}), 500
