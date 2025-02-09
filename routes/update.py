import subprocess
from flask import Blueprint, jsonify, request
from flask_socketio import emit
from socketio_instance import socketio  # Import socketio from the new file

update_bp = Blueprint('update', __name__)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        socketio.emit('update_status', {'message': line.strip()})
    process.wait()
    if process.returncode != 0:
        for line in process.stderr:
            socketio.emit('update_status', {'message': line.strip()})
        raise subprocess.CalledProcessError(process.returncode, command)

@update_bp.route('/api/aaction_server', methods=['POST'])
def aaction_server():
    data = request.get_json()
    action = data.get('action')

    try:
        if action == 'update':
            run_command(['sudo', 'apt-get', 'update'])
            run_command(['sudo', 'apt-get', 'upgrade', '-y'])
        elif action == 'restart':
            run_command(['sudo', 'reboot'])
        else:
            return jsonify(success=False, error='Invalid action'), 400

        return jsonify(success=True)
    except subprocess.CalledProcessError as e:
        return jsonify(success=False, error=str(e))