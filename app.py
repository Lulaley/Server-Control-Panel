import json
import logging
import os
import re
import subprocess
import psutil
import threading
from flask import Flask, request, render_template, jsonify
from rcon.source import Client
from apscheduler.schedulers.background import BackgroundScheduler
from routes.service import init_get_services, init_start_service_routes, init_stop_service_routes, init_restart_service_routes, init_delete_service_routes, init_create_service_routes

app = Flask(__name__)
mc_rcon_password = "minecraft"
mc_rcon_host = "0.0.0.0"
log_path = "/home/chimea/Bureau/minecraft/logs"

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialisez les routes
init_get_services(app)
init_start_service_routes(app)
init_stop_service_routes(app)
init_restart_service_routes(app)
init_delete_service_routes(app)
init_create_service_routes(app)

def remove_color_codes(text):
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', text)

def is_minecraft_server_running():
    logging.info("Checking if a Minecraft server is running...")
    for proc in psutil.process_iter(attrs=['cmdline']):
        cmdline = ' '.join(proc.info['cmdline']).lower()
        if 'java' in cmdline:
            logging.info("A Java process was found, assuming a Minecraft server is running.")
            return True
    logging.info("No Minecraft server found running.")
    return False

def fetchPlayers():
    try:
        with Client(mc_rcon_host, 25575, passwd=mc_rcon_password) as client:
            response = client.run("list")
            # Typical response: "There are X of Y players online: Player1, Player2, ..."
            player_list = response.split(": ")[1] if ": " in response else ""
            players = player_list.split(", ") if player_list else []
            return players
    except Exception as e:
        logging.error(f"Failed to fetch players: {e}")
        return []

# Assuming mc_rcon_password and mc_rcon_host are defined as shown in your excerpt
def send_welcome_message(new_player):
    try:
        with Client(mc_rcon_host, 25575, passwd=mc_rcon_password) as client:
            welcome_message = f"tell {new_player} Wesh tu geek encore ? Oublie pas de désactiver le spawn de mobs de mana & artifice via la quête ! Le serveur à peut-être restart ! Après peut-être que l'administrateur à régler le problème des mobs avec la modification en config serveur !."
            client.run(welcome_message)
            logging.info(f"Sent welcome message to {new_player}")
    except Exception as e:
        logging.error(f"Failed to send welcome message to {new_player}: {e}")

def monitor_for_new_players():
    known_players = load_known_players()  # Load the list of known players from a file or database
    with open(log_path + '/filtered.log', 'r') as file:
        for line in file:
            join_match = re.search(r'(\w+)\[.*\] logged in with entity id', line)
            if join_match:
                player_name = join_match.group(1)
                if player_name not in known_players:
                    send_welcome_message(player_name)
                    known_players.add(player_name)
                    save_known_players(known_players)  # Update the list of known players

# Global variable to store known players in-memory
known_players_set = set()

def load_known_players():
    # Return the global set of known players
    global known_players_set
    return known_players_set

def save_known_players(known_players):
    # Update the global set of known players, no actual saving since it's in-memory
    global known_players_set
    known_players_set = known_players

@app.route('/')
def index():
    services = get_services()
    minecraft_running = is_minecraft_server_running()
    return render_template('index.html', services=services, minecraft_running=minecraft_running)

@app.route('/api/minecraft_status')
def minecraft_status():
    minecraft_running = is_minecraft_server_running()
    return {'minecraft_running': minecraft_running}

@app.route('/system_info')
def system_info():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent

    try:
        try:
            java_version_output = subprocess.check_output(['java', '--version'], stderr=subprocess.STDOUT)
            java_version_match = re.search(r'openjdk (\d+\.\d+\.\d+)', java_version_output.decode('utf-8'))
        except:
            java_version_output = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
            java_version_match = re.search(r'openjdk version "(\d+\.\d+\.\d+_\d+)"', java_version_output.decode('utf-8'))
        java_version = java_version_match.group(1) if java_version_match else "Unknown"
    except Exception as e:
        java_version = str(e)

    total_ram = psutil.virtual_memory().total
    total_disk = psutil.disk_usage('/').total
    current_ram_used = psutil.virtual_memory().used
    current_disk_used = psutil.disk_usage('/').used

    return jsonify({
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'disk_percent': disk_percent,
        'java_version': java_version,
        'total_ram': total_ram,
        'total_disk': total_disk,
        'current_ram_used': current_ram_used,
        'current_disk_used': current_disk_used
    })

@app.route('/minecraft_log', methods=['POST'])
def fetch_minecraft_log():
    data = request.get_json()
    global log_path
    log_path = data.get('log_path', '/home/chimea/Bureau/minecraft/logs')
    filter_type = data.get('filter_type', 'all')  # Get the filter type from the request

    latest_log_path = os.path.join(log_path, 'latest.log')
    filtered_log_path = os.path.join(log_path, 'filtered.log')

    # Get the last line of latest.log and filtered.log that does not contain "RCON"
    last_line_latest = None
    last_line_filtered = None
    with open(latest_log_path, 'r') as latest_log, open(filtered_log_path, 'r') as filtered_log:
        for line in latest_log:
            if 'RCON' not in line:
                last_line_latest = line
        for line in filtered_log:
            if 'RCON' not in line:
                last_line_filtered = line

    # If the last lines are different, execute the command
    if last_line_latest != last_line_filtered:
        subprocess.Popen('cat ' + latest_log_path + ' | grep -v RCON > ' + filtered_log_path, shell=True)

    try:
        # Fetch the list of online players
        online_players = fetchPlayers()

        with open(os.path.join(log_path, 'filtered.log'), 'r') as log_file:
            log_lines = log_file.readlines()[-500:]  # Get the last 50 lines of the log
            # Filter out RCON listener and client messages based on the filter_type
            filtered_lines = []
            for line in log_lines:
                if filter_type == 'errors' and '/ERROR]' in line:
                    filtered_lines.append(line)
                elif filter_type == 'warnings' and '/WARN]' in line:
                    filtered_lines.append(line)
                elif filter_type == 'discussion' and ('[Rcon]' in line or '<' in line and '>' in line) and ('[net.minecraft.server.dedicated.DedicatedServer/]') in line:
                    # Find the first occurrence of <pseudo> or [Rcon] and remove everything before it
                    match = re.search(r'(<.*?>|\[Rcon\])', line)
                    if match:
                        line = line[match.start():]
                    filtered_lines.append(line)
                elif filter_type == 'info' and '/INFO]' in line and ('[net.minecraft.server.dedicated.DedicatedServer/]') in line and not ('[Rcon]' in line or '<' in line and '>' in line):
                    filtered_lines.append(line)
                elif filter_type == 'all':
                    filtered_lines.append(line)

            # Colorize and escape the log messages
            colored_lines = filtered_lines
            log_content = ''.join(colored_lines)
            logging.debug(log_content)
            return jsonify({'logs': log_content, 'online_players': online_players})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_command', methods=['POST'])
def send_command():
    command = request.form.get('command')
    try:
        with Client(mc_rcon_host, 25575, passwd=mc_rcon_password) as client:
            response = client.run(command)
            return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/folders')
def get_folders():
    folders = []
    path = "/home/chimea/Bureau"
    for entry in os.scandir(path):
        if entry.is_dir():
            server_properties_path = os.path.join(entry.path, "server.properties")
            if os.path.isfile(server_properties_path):
                folders.append(entry.name)
                logging.info("Find : "+entry.name+".")
    return jsonify({'folders': folders})

def check_server_status(selected_folder):
    session_lock_file = os.path.join('/home/chimea/Bureau', selected_folder, 'world/session.lock')

    if os.path.isfile(session_lock_file):
        return True
    else:
        return False

@app.route('/server_status', methods=['POST'])
def server_status():
    data = request.get_json()
    selected_folder = data.get('folder', None)

    if selected_folder is not None:
        app.config['SELECTED_FOLDER'] = selected_folder

    is_running = check_server_status(app.config.get('SELECTED_FOLDER', ''))
    return jsonify({'is_running': is_running})

@app.route('/java_versions')
def get_java_versions():
    try:
        result = subprocess.run(['update-java-alternatives', '-l'], stdout=subprocess.PIPE)
        output = result.stdout.decode().strip()

        # Diviser la sortie en lignes
        lines = output.split('\n')

        java_versions = []

        # Parcourir les lignes et extraire les informations de version et de chemin
        for line in lines:
            # Ignorer les lignes vides
            if not line:
                continue

            # Diviser la ligne en éléments
            elements = line.split()

            # Extraire le chemin et la version
            path = elements[0]
            version_number = elements[0].split('-')[1]
            version = f"Java {version_number}"

            # Ajouter la version de Java et son chemin à la liste
            java_versions.append({'version': version, 'path': path})

        # Renvoie la liste des versions de Java installées avec leur chemin
        return jsonify(java_versions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/change_java_version', methods=['POST'])
def change_java_version():
    version = request.form.get('version')
    print(version)
    try:
        subprocess.check_call(['sudo', 'update-java-alternatives', '-s', version])
        return jsonify({'success': True})
    except subprocess.CalledProcessError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(monitor_for_new_players, 'interval', minutes=1)
    scheduler.start()
    # Important to use use_reloader=False to avoid duplicate scheduler instances
    app.run(host='0.0.0.0', port=5000, use_reloader=False, debug=True)