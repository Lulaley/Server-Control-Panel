from flask import request, jsonify
from rcon.source import Client
from .conf import MC_RCON_HOST, MC_RCON_PASSWORD, init_rcon_port, get_rcon_port

def init_send_command(app):
    @app.route('/send_command', methods=['POST'])
    def send_command():
        init_rcon_port()
        command = request.form.get('command')
        try:
            with Client(MC_RCON_HOST, get_rcon_port(), passwd=MC_RCON_PASSWORD) as client:
                response = client.run(command)
                return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500