from flask import request, jsonify, current_app
from rcon.source import Client

# Accéder aux variables globales
try:
    mc_rcon_password = current_app.config['MC_RCON_PASSWORD']
    mc_rcon_host = current_app.config['MC_RCON_HOST']
    mc_rcon_port = current_app.config['MC_RCON_PORT']
    log_path = current_app.config['LOG_PATH']
except Exception as e:
    print(e)

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