# Démarre un thread qui surveille config/services_config.json et static/services_list.json
# et appelle les scripts appropriés lorsqu'ils changent.

import threading
import time
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'services_config.json')
STATIC_PATH = os.path.join(BASE_DIR, 'static', 'services_list.json')
GEN_SCRIPT = os.path.join(BASE_DIR, 'tools', 'generate_services_json.py')
SYNC_SCRIPT = os.path.join(BASE_DIR, 'tools', 'sync_static_to_config.py')


def run_script(path):
    if os.path.exists(path):
        try:
            subprocess.run([sys.executable, path], check=False)
        except Exception:
            pass


def watch(poll_interval=2):
    # Effectuer une génération initiale et une synchronisation initiale
    run_script(GEN_SCRIPT)
    run_script(SYNC_SCRIPT)

    last_mtimes = {
        'config': os.path.getmtime(CONFIG_PATH) if os.path.exists(CONFIG_PATH) else None,
        'static': os.path.getmtime(STATIC_PATH) if os.path.exists(STATIC_PATH) else None,
    }

    while True:
        try:
            cfg_exists = os.path.exists(CONFIG_PATH)
            st_exists = os.path.exists(STATIC_PATH)
            cfg_mtime = os.path.getmtime(CONFIG_PATH) if cfg_exists else None
            st_mtime = os.path.getmtime(STATIC_PATH) if st_exists else None

            if cfg_mtime != last_mtimes.get('config'):
                last_mtimes['config'] = cfg_mtime
                # si la config a changé, régénérer static à partir de la config
                run_script(GEN_SCRIPT)

            if st_mtime != last_mtimes.get('static'):
                last_mtimes['static'] = st_mtime
                # si le static a changé (ex: via l'UI), synchroniser vers config
                run_script(SYNC_SCRIPT)

        except Exception:
            pass

        time.sleep(poll_interval)


_thread = threading.Thread(target=watch, name='services_watcher', daemon=True)
_thread.start()
