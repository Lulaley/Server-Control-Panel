from flask import request, jsonify
from rcon.source import Client

def init_send_command(app):
    @app.route('/send_command', methods=['POST'])
    def send_command():
        command = request.form.get('command')
        try:
            with Client(mc_rcon_host, mc_rcon_port, passwd=mc_rcon_password) as client:
                response = client.run(command)
                return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500