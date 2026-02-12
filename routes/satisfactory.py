from flask import Blueprint, jsonify, render_template, request, session
import subprocess
import re
import os
import glob

# Créer un Blueprint pour les routes de la page home
satisfactory_bp = Blueprint('satisfactory', __name__)

# Make session available in templates for this blueprint
@satisfactory_bp.context_processor
def inject_user():
    return {
        'current_user': session.get('user'),
        'current_role': session.get('role'),
        'is_admin': session.get('role') == 'admin',
        'is_manager': session.get('role') == 'manager',
        'can_control_satisfactory': session.get('role') in ('admin', 'manager')
    }

# Liste des satisfactorys à surveiller (ajoutez ici les noms exacts des unités systemd)
MONITORED_SATISFACTORY_NAMES = [
    "satisfactory",  # exemple, ajoutez d'autres noms ici
]

@satisfactory_bp.route("/satisfactory")
def services_page():
    return render_template("satisfactory.html")

@satisfactory_bp.route("/api/satisfactorys/list")
def api_satisfactorys_list():
    # Recherche toutes les unités systemd contenant un nom de la liste
    found = []
    service_files = glob.glob("/etc/systemd/system/*.service")
    for f in service_files:
        name = os.path.basename(f).replace(".service", "")
        for pattern in MONITORED_SATISFACTORY_NAMES:
            if re.search(pattern, name, re.IGNORECASE):
                found.append(name)
    return jsonify({"satisfactorys": found})

@satisfactory_bp.route("/api/satisfactorys/status/<satisfactory>")
def api_satisfactorys_status(satisfactory):    
    satisfactory_name = f"{satisfactory}.service"
    
    # Try different paths for systemctl
    systemctl_paths = ["/usr/bin/systemctl", "/bin/systemctl", "systemctl"]
    systemctl_cmd = None
    
    for path in systemctl_paths:
        if os.path.exists(path) or path == "systemctl":
            systemctl_cmd = path
            break
    
    if not systemctl_cmd:
        return jsonify({
            "satisfactory": satisfactory,
            "status": "unknown",
            "error": "systemctl command not found",
            "can_control": session.get("role") in ("admin", "manager")
        })
    
    try:
        result = subprocess.run([systemctl_cmd, "is-active", satisfactory_name], 
                              capture_output=True, text=True, timeout=2,
                              env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
        status = result.stdout.strip()
                
        # Get service enabled status
        try:
            cmd_enabled = [systemctl_cmd, "is-enabled", satisfactory_name]
            result_enabled = subprocess.run(cmd_enabled, capture_output=True, text=True,
                                          env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
            is_enabled = result_enabled.stdout.strip()
        except Exception:
            is_enabled = "unknown"
        
        response_data = {
            "satisfactory": satisfactory,
            "status": status,
            "enabled": is_enabled,
            "can_control": session.get("role") in ("admin", "manager"),
            "debug_info": {
                "stdout": status,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "systemctl_path": systemctl_cmd
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"EXCEPTION OCCURRED: {e}")
        error_response = {
            "satisfactory": satisfactory,
            "status": "unknown",
            "error": str(e),
            "can_control": session.get("role") in ("admin", "manager")
        }
        print(f"Returning error JSON: {error_response}")
        return jsonify(error_response)

# --- Contrôle des satisfactory génériques ---
@satisfactory_bp.route("/api/satisfactorys/control/<satisfactory>", methods=["POST"])
def api_satisfactorys_control(satisfactory):
    data = request.get_json(force=True)
    action = data.get("action")
    satisfactory_name = f"{satisfactory}.service"
    if action not in ("start", "stop", "restart"):
        return jsonify({"success": False, "error": "Action invalide"}), 400
    # Permission: only manager or admin can control satisfactorys
    role = session.get("role")
    if role not in ("manager", "admin"):
        return jsonify({"success": False, "error": "forbidden"}), 403
    
    # Use full path for systemctl
    systemctl_paths = ["/usr/bin/systemctl", "/bin/systemctl", "systemctl"]
    systemctl_cmd = None
    
    for path in systemctl_paths:
        if os.path.exists(path) or path == "systemctl":
            systemctl_cmd = path
            break
            
    if not systemctl_cmd:
        print("SYSTEMCTL COMMAND NOT FOUND")
        return jsonify({"success": False, "error": "systemctl command not found"})
    
    try:
        result = subprocess.run(["sudo", systemctl_cmd, action, satisfactory_name], 
                              capture_output=True, text=True, timeout=5,
                              env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
        if result.returncode == 0:
            return jsonify({"success": True})
        else:
            print(f"SATISFACTORY CONTROL COMMAND FAILED: {result.stderr}")
            return jsonify({"success": False, "error": result.stderr})
    except Exception as e:
        print(f"EXCEPTION OCCURRED: {e}")
        return jsonify({"success": False, "error": str(e)})

@satisfactory_bp.route("/api/satisfactorys/logs/<satisfactory>")
def api_satisfactorys_logs(satisfactory):
    # Tente de lire les logs via journalctl
    try:
        result = subprocess.run([
            "journalctl", "-u", f"{satisfactory}.service", "-n", "100", "--no-pager", "--output=short"
        ], capture_output=True, text=True, timeout=3)
        logs = result.stdout[-5000:]
        return jsonify({"logs": logs})
    except Exception as e:
        print(f"EXCEPTION OCCURRED WHILE FETCHING LOGS: {e}")
        return jsonify({"logs": f"Erreur: {str(e)}"})
