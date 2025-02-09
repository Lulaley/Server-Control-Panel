import subprocess
from flask import Blueprint, jsonify

update_bp = Blueprint('update', __name__)

@update_bp.route('/api/update_server', methods=['POST'])
def update_server():
    try:
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        subprocess.run(['sudo', 'apt-get', 'upgrade', '-y'], check=True)
        return jsonify(success=True)
    except subprocess.CalledProcessError as e:
        return jsonify(success=False, error=str(e))