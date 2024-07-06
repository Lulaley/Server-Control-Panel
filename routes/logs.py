import os
import re
import subprocess
from flask import request, jsonify
from rcon.source import Client

mc_rcon_password = "minecraft"
mc_rcon_host = "0.0.0.0"

def remove_color_codes(text):
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', text)

def fetchPlayers():
    try:
        with Client(mc_rcon_host, 25575, passwd=mc_rcon_password) as client:
            response = client.run("list")
            # Typical response: "There are X of Y players online: Player1, Player2, ..."
            player_list = response.split(": ")[1] if ": " in response else ""
            players = player_list.split(", ") if player_list else []
            return players
    except Exception as e:
        return []

def init_get_logs_routes(app):
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
                return jsonify({'logs': log_content, 'online_players': online_players})
        except Exception as e:
            return jsonify({'error': str(e)}), 500