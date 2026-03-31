import os
import logging
import traceback
from logging.handlers import RotatingFileHandler

# Constantes globales
TRACEBACK_MSG = "Traceback: %s"
LOGIN_PATH = "/login"

# Initialisation du logger
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            os.path.join(log_dir, 'controlWeb.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

# Configuration Flask
SECRET = os.getenv("FLASK_SECRET")
if not SECRET or SECRET == "change-me-in-production":
    logger.critical("FLASK_SECRET environment variable is not set or uses the default value. Refusing to start for security reasons.")
    raise RuntimeError("FLASK_SECRET environment variable must be set to a strong random value in production.")

FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

