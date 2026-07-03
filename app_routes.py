from flask import Blueprint, render_template, jsonify, request, redirect, session
from app_utils import _get_machine_info
from app_config import logger
import psutil
from utils.service_status import get_services_status

routes_bp = Blueprint('routes_bp', __name__)

@routes_bp.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

@routes_bp.route("/_ping", methods=["GET"])
def _ping():
    return "ok", 200

@routes_bp.route('/api/machine', methods=['GET'])
def api_machine():
    info = _get_machine_info()
    if info is None:
        return jsonify({"error": "server_error"}), 500
    return jsonify(info)

@routes_bp.app_errorhandler(404)
def not_found_error(e):
    logger.warning("404 error: %s for path %s", e, request.path)
    if request.path in ['/signup', '/reset-password']:
        return redirect('/login')
    return "Page not found", 404

@routes_bp.app_errorhandler(500)
def internal_server_error(e):
    logger.error("Internal server error: %s", e)
    logger.error("Request path: %s", request.path)
    logger.error("Request method: %s", request.method)
    logger.error("Traceback: %s", e, exc_info=True)
    return "Internal server error - check logs for details", 500

# --- Ports admin monitoring ---
def _is_admin():
    return session.get('role') == 'admin'

PORTS_CONFIG = [
    {"name": "WireGuard", "status": "USED", "wan": 45376, "lan": 45376},
    {"name": "Domain", "status": "USED", "wan": 49000, "lan": 49000},
    {"name": "SSH", "status": "USED", "wan": 33696, "lan": 22},
    {"name": "Panel Control Web", "status": "USED", "wan": 35555, "lan": 443},
    {"name": "Chimea Love", "status": "USED", "wan": 36969, "lan": 6969},
    {"name": "Tools", "status": "DELETE", "wan": 33939, "lan": 3939},
    {"name": "PalWorld", "status": "", "wan": 33965, "lan": 8211},
    {"name": "Satisfactory", "status": "", "p1": 35002, "p2": 35001, "p3": "35001/udp"},
    {"name": "Hytale 1", "status": "", "wan": 35520, "lan": 5520},
    {"name": "Hytale 2", "status": "", "wan": 35521, "lan": 5521},
    {"name": "Hytale 3", "status": "", "wan": 35522, "lan": 5522},
    {"name": "Minecraft 1", "status": "USED", "wan": 32769, "lan": 32769, "rcon": 32771, "desc": "vanilla laura"},
    {"name": "Minecraft 2", "status": "USED", "wan": 32772, "lan": 32772, "rcon": 32773, "desc": "contrebande"},
    {"name": "Minecraft 3", "status": "USED", "wan": 32774, "lan": 32774, "rcon": 32775, "desc": "osr"},
    {"name": "Minecraft 4", "status": "USED", "wan": 32776, "lan": 32776, "rcon": 32777, "desc": "atm10"},
]

def _check_port(port, proto='tcp'):
    try:
        conns = psutil.net_connections(kind=proto)
        for c in conns:
            if c.laddr and c.laddr.port == port:
                return True
    except Exception:
        pass
    return False

@routes_bp.route('/admin/ports', methods=['GET'])
def admin_ports():
    if not _is_admin():
        return redirect('/login')
    return render_template('admin_ports.html')

@routes_bp.route('/admin/ports/status', methods=['GET'])
def admin_ports_status():
    if not _is_admin():
        return jsonify({"error": "unauthorized"}), 403
    service_status = get_services_status()
    status_list = []
    for entry in PORTS_CONFIG:
        item = entry.copy()
        # Associe le service par nom si possible
        svc_name = entry.get('name')
        svc_info = service_status.get(svc_name, {})
        item['service_running'] = svc_info.get('running', None)
        item['service_last_stopped'] = svc_info.get('last_stopped', None)
        for key in ["wan", "lan", "p1", "p2", "p3", "rcon"]:
            if key in entry:
                port = entry[key]
                proto = 'udp' if isinstance(port, str) and '/udp' in str(port) else 'tcp'
                port_num = int(str(port).replace('/udp', ''))
                item[f"{key}_used"] = _check_port(port_num, proto)
        status_list.append(item)
    return jsonify(status_list)
