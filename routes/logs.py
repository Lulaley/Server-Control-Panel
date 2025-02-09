import datetime
import os
import re
import subprocess
import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from rcon.source import Client
from .conf import MC_RCON_HOST, MC_RCON_PASSWORD, set_selected_folder, init_rcon_port, get_rcon_port

app = Flask(__name__)
socketio = SocketIO(app)

def remove_color_codes(text):
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', text)

def fetchPlayers():
    try:
        with Client(MC_RCON_HOST, get_rcon_port(), passwd=MC_RCON_PASSWORD) as client:
            response = client.run("list")
            # Typical response: "There are X of Y players online: Player1, Player2, ..."
            player_list = response.split(": ")[1] if ": " in response else ""
            players = player_list.split(", ") if player_list else []
            if not players:  # Si la liste des joueurs est vide
                return ["Aucun joueurs connecté"]  # Retourner le message indiquant qu'aucun joueur n'est connecté
            return players
    except Exception as e:
        return ["Aucun joueurs connecté"]  # Retourner le message en cas d'exception

@app.route('/api/players', methods=['GET'])
def get_players():
    players = fetchPlayers()
    return jsonify(players)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def update_players():
    global players
    new_players = fetchPlayers()
    for player in new_players:
        if player not in players:
            players.append(player)
            socketio.emit('player_connect', {'player': player})
    for player in players:
        if player not in new_players:
            players.remove(player)
            socketio.emit('player_disconnect', {'player': player})

def init_get_logs_routes(app):
    @app.route('/minecraft_log', methods=['POST'])
    def fetch_minecraft_log():
        data = request.get_json()
        log_path = data.get('log_path', '/home/chimea/Bureau/minecraft/logs')
        
        set_selected_folder(log_path.replace('/logs', ''))
        init_rcon_port()

        filter_type = data.get('filter_type', 'all')  # Get the filter type from the request

        logging.info(f'Fetching logs from {log_path} with filter type {filter_type}')

        latest_log_path = os.path.join(log_path, 'latest.log')
        filtered_log_path = os.path.join(log_path, 'filtered.log')

        # Si filtered.log n'existe pas, utiliser latest.log à la place
        if not os.path.exists(filtered_log_path):
            filtered_log_path = latest_log_path

        # Vérifier si "RCON" est présent dans les logs
        rcon_present_in_logs = False
        with open(latest_log_path, 'r') as latest_log:
            for line in latest_log:
                if 'RCON' in line:
                    rcon_present_in_logs = True
                    break
              
        # Si "RCON" n'est pas présent, ne pas traiter les logs pour "RCON"
        if rcon_present_in_logs:  
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

            with open(filtered_log_path, 'r') as log_file:
                log_lines = log_file.readlines()[-500:]  # Get the last 500 lines of the log
                # Filter out RCON listener and client messages based on the filter_type
                filtered_lines = []
                for line in log_lines:
                    if filter_type == 'errors' and '/ERROR]' in line:
                        filtered_lines.append(line)
                    elif filter_type == 'warnings' and '/WARN]' in line:
                        filtered_lines.append(line)
                    elif filter_type == 'discussion' and ('[Rcon]' in line or '<' in line and '>' in line):
                        # Find the first occurrence of <pseudo> or [Rcon] and remove everything before it
                        match = re.search(r'(<.*?>|\[Rcon\])', line)
                        if match:
                            # Extract the timestamp
                            timestamp_match = re.search(r'\[(\d{2}[A-Za-z]{3}\d{4} \d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}:\d{2})\]', line)
                            if timestamp_match:
                                timestamp_str = timestamp_match.group(1)
                                # Convert the timestamp to the desired format if necessary
                                try:
                                    if len(timestamp_str) > 8:  # Format is like [27Jul2024 23:28:48.567]
                                        timestamp = datetime.strptime(timestamp_str, '%d%b%Y %H:%M:%S.%f')
                                        formatted_timestamp = timestamp.strftime('%d-%m-%Y %H:%M:%S')
                                    else:  # Format is [23:40:48]
                                        formatted_timestamp = timestamp_str
                                    line = f'[{formatted_timestamp}] {line[match.start():]}'
                                except ValueError:
                                    # Handle the case where the timestamp format is incorrect
                                    line = line
                        filtered_lines.append(line)
                    elif filter_type == 'info' and '/INFO]' in line:
                        filtered_lines.append(line)
                    elif filter_type == 'all':
                        filtered_lines.append(line)

                # Write the filtered lines to filtered.log
                with open('filtered.log', 'w') as filtered_log_file:
                    for filtered_line in filtered_lines:
                        filtered_log_file.write(filtered_line)

                # Colorize and escape the log messages
                colored_lines = filtered_lines
                log_content = ''.join(colored_lines)
                return jsonify({'logs': log_content, 'online_players': online_players})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/palworld/logs', methods=['GET'])
    def fetch_palworld_logs():
        try:
            # Execute the journalctl command to fetch the logs for the PalWorld service
            result = subprocess.run(['journalctl', '-u', 'palworld.service', '--no-pager', '-n', '500'], capture_output=True, text=True)
            logs = result.stdout.splitlines()
            return jsonify({'logs': logs})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)