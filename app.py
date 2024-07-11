import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template

app = Flask(__name__)


def get_rcon_port_from_properties(app):
    # Récupérer le dossier sélectionné à partir de la configuration de l'application
    selected_folder = app.config.get('folders', '')
    if not selected_folder:
        return "Aucun dossier sélectionné."

    # Construire le chemin vers le fichier server.properties
    properties_file_path = os.path.join('/home/chimea/Bureau', selected_folder, 'server.properties')

    # Lire le fichier server.properties et récupérer le port RCON
    try:
        with open(properties_file_path, 'r') as file:
            for line in file:
                if line.startswith('rcon.port='):
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        return "Le fichier server.properties n'a pas été trouvé."

    return "Le port RCON n'a pas été trouvé dans le fichier."
# Variables globales pour stocker les informations de configuration
global MC_RCON_PASSWORD
global MC_RCON_HOST
global MC_RCON_PORT
global LOG_PATH
MC_RCON_PASSWORD = 'minecraft'
MC_RCON_HOST = '0.0.0.0'
MC_RCON_PORT = get_rcon_port_from_properties(app) or 25575
LOG_PATH = '/home/chimea/Bureau/minecraft/logs'

from routes.service import get_services, init_start_service_routes, init_stop_service_routes, init_restart_service_routes, init_delete_service_routes, init_create_service_routes
from routes.logs import init_get_logs_routes
from routes.commandMcServer import init_send_command, init_globals
from routes.welcomeMessage import monitor_for_new_players
from routes.statusMcServer import init_get_mc_folders_routes, init_minecraft_status_routes, init_server_status_routes, is_minecraft_server_running
from routes.systemInfo import init_system_info_routes
from routes.javaGestion import init_get_java_versions_routes, init_change_java_version_routes

# Créez un contexte d'application et initialisez les variables globales
with app.app_context():
    init_globals()

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialisez les routes pour démarrer, arrêter, redémarrer et supprimer les services
init_start_service_routes(app)
init_stop_service_routes(app)
init_restart_service_routes(app)
init_delete_service_routes(app)
init_create_service_routes(app)

# Initialisez la route pour récupérer les logs du serveur Minecraft sélectionné
init_get_logs_routes(app)

# Initialisez la route pour envoyer une commande au serveur Minecraft sélectionné
init_send_command(app)

# Initialisez la route pour récupérer les dossiers de serveur Minecraft disponibles
init_get_mc_folders_routes(app)
# Initialisez les routes pour récupérer le status du serveur Minecraft sélectionné
init_minecraft_status_routes(app)
init_server_status_routes(app)

# Initialisez la route pour récupérer les informations de la machine
init_system_info_routes(app)

# Initialisez les routes pour récupérer les versions de Java installées et pour changer la version de Java
init_get_java_versions_routes(app)
init_change_java_version_routes(app)


@app.route('/')
def index():
    services = get_services()
    minecraft_running = is_minecraft_server_running()
    return render_template('index.html', services=services, minecraft_running=minecraft_running)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(monitor_for_new_players, 'interval', minutes=1)
    scheduler.start()
    # Important to use use_reloader=False to avoid duplicate scheduler instances
    app.run(host='0.0.0.0', port=5000, use_reloader=False, debug=True)