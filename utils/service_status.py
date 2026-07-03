import os
import json
import psutil
import time

def get_services_status():
    """
    Retourne un dict {service_name: {running: bool, last_stopped: timestamp or None, pid: int or None}}
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'services_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            services = json.load(f)
    except Exception:
        services = []
    status = {}
    for svc in services:
        name = svc.get('name')
        port = svc.get('port')
        svc_type = svc.get('type')
        # Cherche un process qui écoute sur ce port
        found = False
        pid = None
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == port:
                if conn.status == psutil.CONN_LISTEN:
                    found = True
                    pid = conn.pid
                    break
        # Si pas trouvé, cherche un process par nom
        if not found:
            for proc in psutil.process_iter(['name', 'cmdline', 'create_time']):
                try:
                    if name and name in ' '.join(proc.info['cmdline']):
                        found = True
                        pid = proc.pid
                        break
                except Exception:
                    continue
        # Si trouvé, running, sinon, cherche le dernier arrêt
        last_stopped = None
        if not found:
            # On pourrait stocker un cache/état, mais ici on ne peut que None
            last_stopped = None
        status[name] = {
            'running': found,
            'last_stopped': None if found else last_stopped,
            'pid': pid
        }
    return status
