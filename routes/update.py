import subprocess
from flask import Blueprint, jsonify, request

update_bp = Blueprint('update', __name__)

@update_bp.route('/api/aaction_server', methods=['POST'])
def aaction_server():
    data = request.get_json()
    action = data.get('action')

    try:
        if action == 'update':
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'upgrade', '-y'], check=True)
        elif action == 'restart':
            subprocess.run(['sudo', 'reboot'], check=True)
        else:
            return jsonify(success=False, error='Invalid action'), 400

        return jsonify(success=True)
    except subprocess.CalledProcessError as e:
        return jsonify(success=False, error=str(e))