import os
import logging

MC_RCON_PASSWORD = 'minecraft'
MC_RCON_HOST = '0.0.0.0'
MC_RCON_PORT = 25575
LOG_PATH = '/home/chimea/Bureau/minecraft/logs'
SELECTED_FOLDER = ''

def get_selected_folder():
    global SELECTED_FOLDER
    return SELECTED_FOLDER

def set_selected_folder(new_path):
    global SELECTED_FOLDER
    SELECTED_FOLDER = new_path

def get_rcon_port():
    global MC_RCON_PORT
    return MC_RCON_PORT

def set_rcon_port(new_port):
    global MC_RCON_PORT
    MC_RCON_PORT = new_port  

def get_rcon_port_from_properties():
    if not SELECTED_FOLDER:
        return False
    # Construire le chemin vers le fichier server.properties
    properties_file_path = os.path.join(get_selected_folder(), 'server.properties')

    # Lire le fichier server.properties et récupérer le port RCON
    try:
        with open(properties_file_path, 'r') as file:
            for line in file:
                if line.startswith('rcon.port='):
                    return line.split('=')[1].strip()
    except FileNotFoundError:
        logging.error(f'File not found: {properties_file_path}')
        return False

    return False

def init_rcon_port():
    rcon_port = get_rcon_port_from_properties()
    if rcon_port == False:
        set_rcon_port(25575)
    else:
        set_rcon_port(int(rcon_port))
    logging.info(f'RCON port set to {get_rcon_port()}')