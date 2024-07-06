from flask import request, jsonify
from rcon.source import Client

mc_rcon_password = "minecraft"
mc_rcon_host = "0.0.0.0"

def init_send_command(app):
    @app.route('/send_command', methods=['POST'])
    def send_command():
        command = request.form.get('command')
        try:
            with Client(mc_rcon_host, 25575, passwd=mc_rcon_password) as client:
                response = client.run(command)
                return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500