import os
import logging

MC_RCON_PASSWORD = 'minecraft'
MC_RCON_HOST = '0.0.0.0'
MC_RCON_PORT = 25575
LOG_PATH = '/home/chimea/Bureau/minecraft/logs'

def get_rcon_port_from_properties(app):
    # Récupérer le dossier sélectionné à partir de la configuration de l'application
    selected_folder = app.config.get('folders', '')
    if not selected_folder:
        return False
    logging.warning(f'Selected folder: {selected_folder}')
    # Construire le chemin vers le fichier server.properties
    properties_file_path = os.path.join('/home/chimea/Bureau', selected_folder, 'server.properties')

    # Lire le fichier server.properties et récupérer le port RCON
    try:
        with open(properties_file_path, 'r') as file:
            for line in file:
                if line.startswith('rcon.port='):
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        return False

    return False

def init_rcon_port(app):
    global MC_RCON_PORT
    rcon_port = get_rcon_port_from_properties(app)
    logging.warning(f'RCON port from properties: {rcon_port}')
    if rcon_port == False:
        MC_RCON_PORT = 25575
    else:
        MC_RCON_PORT = rcon_port
    logging.info(f'RCON port set to {MC_RCON_PORT}')