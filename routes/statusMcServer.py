import os
import psutil
from flask import request, jsonify

def is_minecraft_server_running():
    for proc in psutil.process_iter(attrs=['cmdline']):
        cmdline = ' '.join(proc.info['cmdline']).lower()
        if 'java' in cmdline:
            return True
    return False

def check_server_status(selected_folder):
    session_lock_file = os.path.join('/home/chimea/Bureau', selected_folder, 'world/session.lock')

    if os.path.isfile(session_lock_file):
        return True
    else:
        return False
    
def init_get_mc_folders_routes(app):
    @app.route('/folders')
    def get_folders():
        folders = []
        path = "/home/chimea/Bureau"
        for entry in os.scandir(path):
            if entry.is_dir():
                server_properties_path = os.path.join(entry.path, "server.properties")
                if os.path.isfile(server_properties_path):
                    folders.append(entry.name)
        return jsonify({'folders': folders})

def init_minecraft_status_routes(app):
    @app.route('/api/minecraft_status')
    def minecraft_status():
        minecraft_running = is_minecraft_server_running()
        return {'minecraft_running': minecraft_running}
    
def init_server_status_routes(app):
    @app.route('/server_status', methods=['POST'])
    def server_status():
        data = request.get_json()
        selected_folder = data.get('folder', None)

        if selected_folder is not None:
            app.config['SELECTED_FOLDER'] = selected_folder

        is_running = check_server_status(app.config.get('SELECTED_FOLDER', ''))
        return jsonify({'is_running': is_running})