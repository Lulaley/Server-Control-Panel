from flask import request, jsonify, current_app
from rcon.source import Client

# Accéder aux variables globales
gbl_mc_rcon_password = current_app.config['MC_RCON_PASSWORD']
gbl_mc_rcon_host = current_app.config['MC_RCON_HOST']
gbl_mc_rcon_port = current_app.config['MC_RCON_PORT']
gbl_log_path = current_app.config['LOG_PATH']
print('global variable : ')
print('mc_rcon_host : ', gbl_mc_rcon_host,' mc_rcon_port : ', gbl_mc_rcon_port,' mc_rcon_password : ', gbl_mc_rcon_password)


def init_send_command(app):
    @app.route('/send_command', methods=['POST'])
    def send_command():
        command = request.form.get('command')
        try:
            with Client(gbl_mc_rcon_host, gbl_mc_rcon_port, passwd=gbl_mc_rcon_password) as client:
                response = client.run(command)
                return jsonify({'response': response})
        except Exception as e:
            return jsonify({'error': str(e)}), 500