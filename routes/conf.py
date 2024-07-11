import os

MC_RCON_PASSWORD = 'minecraft'
MC_RCON_HOST = '0.0.0.0'
MC_RCON_PORT = 25575
LOG_PATH = '/home/chimea/Bureau/minecraft/logs'

def get_rcon_port_from_properties(app):
    # Récupérer le dossier sélectionné à partir de la configuration de l'application
    selected_folder = app.config.get('folders', '')
    if not selected_folder:
        return False

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
    if not rcon_port:
        MC_RCON_PORT = 25575
    else:
        MC_RCON_PORT = rcon_port
    print(f'RCON Port: {MC_RCON_PORT}')