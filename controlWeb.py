

from flask import Flask
from app_config import logger, SECRET, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
from app_context import inject_user, inject_machine_info

from app_routes import routes_bp
from app_user_api import user_api_bp

# Import des blueprints métiers
from routes.home import home_bp
from routes.minecraft import minecraft_bp
from routes.satisfactory import satisfactory_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.hytale import hytale_bp
from routes.game_servers import game_servers_bp

controlWeb = Flask(__name__)
controlWeb.secret_key = SECRET
controlWeb.logger.setLevel(logger.level)

# Enregistrement des context processors
controlWeb.context_processor(inject_user)
controlWeb.context_processor(inject_machine_info)

# Enregistrement des blueprints génériques
controlWeb.register_blueprint(routes_bp)
controlWeb.register_blueprint(user_api_bp)

# Enregistrement des blueprints métiers
controlWeb.register_blueprint(home_bp)
controlWeb.register_blueprint(minecraft_bp)
controlWeb.register_blueprint(satisfactory_bp)
controlWeb.register_blueprint(auth_bp)
controlWeb.register_blueprint(admin_bp)
controlWeb.register_blueprint(api_bp)
controlWeb.register_blueprint(hytale_bp)
controlWeb.register_blueprint(game_servers_bp)

if __name__ == '__main__':
    logger.info("Starting Flask app...")
    cert_path = "/home/web_server/certs/certificate.crt"
    key_path = "/home/web_server/certs/private.key"
    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"Using SSL context: cert={cert_path}, key={key_path}")
        controlWeb.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, ssl_context=(cert_path, key_path))
    else:
        logger.warning("Certificat SSL ou clé privée manquants, lancement sans HTTPS !")
        controlWeb.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)


# Protection contre l'exécution multiple
if __name__ == '__main__':
    logger.info("Starting Flask app...")
    cert_path = "/home/web_server/certs/certificate.crt"
    key_path = "/home/web_server/certs/private.key"
    # Par défaut, ne pas binder sur 0.0.0.0 sauf si explicitement demandé
    flask_host = os.getenv("FLASK_HOST", "127.0.0.1")
    flask_port = int(os.getenv("FLASK_PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    if os.path.exists(cert_path) and os.path.exists(key_path):
        logger.info(f"Using SSL context: cert={cert_path}, key={key_path}")
        controlWeb.run(debug=debug_mode, host=flask_host, port=flask_port, ssl_context=(cert_path, key_path))
    else:
        logger.warning("Certificat SSL ou clé privée manquants, lancement sans HTTPS !")
        controlWeb.run(debug=debug_mode, host=flask_host, port=flask_port)
