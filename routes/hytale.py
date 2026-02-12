from flask import Blueprint, jsonify, render_template, request, session
import subprocess
import re
import os
import glob

hytale_bp = Blueprint('hytale', __name__)

@hytale_bp.context_processor
def inject_user():
    return {
        'current_user': session.get('user'),
        'current_role': session.get('role'),
        'is_admin': session.get('role') == 'admin',
        'is_manager': session.get('role') == 'manager',
        'can_control_hytale': session.get('role') in ('admin', 'manager')
    }

MONITORED_HYTALE_NAMES = [
    "hytale",
]

@hytale_bp.route("/hytale")
def services_page():
    return render_template("hytale.html")

@hytale_bp.route("/api/hytales/list")
def api_hytales_list():
    found = []
    search_phrase = "Service to start a server hytale at the boot of the computer"
    service_dirs = ["/etc/systemd/system", "/lib/systemd/system", "/usr/lib/systemd/system"]
    seen = set()
    for d in service_dirs:
        if not os.path.isdir(d):
            continue
        pattern = os.path.join(d, "*.service")
        for f in glob.glob(pattern):
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                m = re.search(r'^[ \t]*Description\s*=\s*(.*)$', content, flags=re.IGNORECASE | re.MULTILINE)
                if m:
                    desc = m.group(1).strip()
                    if search_phrase.lower() in desc.lower() or "hytale" in desc.lower():
                        name = os.path.basename(f).replace(".service", "")
                        if name not in seen:
                            found.append(name)
                            seen.add(name)
            except Exception:
                continue
    # fallback: search by service filename if nothing found by description
    if not found:
        service_files = glob.glob("/etc/systemd/system/*.service")
        for f in service_files:
            name = os.path.basename(f).replace(".service", "")
            for pattern in MONITORED_HYTALE_NAMES:
                if re.search(pattern, name, re.IGNORECASE):
                    if name not in seen:
                        found.append(name)
                        seen.add(name)
    return jsonify({"hytales": found})

@hytale_bp.route("/api/hytales/status/<hytale>")
def api_hytales_status(hytale):
    hytale_name = f"{hytale}.service"
    systemctl_paths = ["/usr/bin/systemctl", "/bin/systemctl", "systemctl"]
    systemctl_cmd = None
    for path in systemctl_paths:
        if os.path.exists(path) or path == "systemctl":
            systemctl_cmd = path
            break
    if not systemctl_cmd:
        return jsonify({
            "hytale": hytale,
            "status": "unknown",
            "error": "systemctl command not found",
            "can_control": session.get("role") in ("admin", "manager")
        })
    try:
        result = subprocess.run([systemctl_cmd, "is-active", hytale_name],
                              capture_output=True, text=True, timeout=2,
                              env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
        status = result.stdout.strip()
        try:
            cmd_enabled = [systemctl_cmd, "is-enabled", hytale_name]
            result_enabled = subprocess.run(cmd_enabled, capture_output=True, text=True,
                                          env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
            is_enabled = result_enabled.stdout.strip()
        except Exception:
            is_enabled = "unknown"
        response_data = {
            "hytale": hytale,
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
        return jsonify({
            "hytale": hytale,
            "status": "unknown",
            "error": str(e),
            "can_control": session.get("role") in ("admin", "manager")
        })

@hytale_bp.route("/api/hytales/control/<hytale>", methods=["POST"])
def api_hytales_control(hytale):
    data = request.get_json(force=True)
    action = data.get("action")
    hytale_name = f"{hytale}.service"
    if action not in ("start", "stop", "restart"):
        return jsonify({"success": False, "error": "Action invalide"}), 400
    role = session.get("role")
    if role not in ("manager", "admin"):
        return jsonify({"success": False, "error": "forbidden"}), 403
    systemctl_paths = ["/usr/bin/systemctl", "/bin/systemctl", "systemctl"]
    systemctl_cmd = None
    for path in systemctl_paths:
        if os.path.exists(path) or path == "systemctl":
            systemctl_cmd = path
            break
    if not systemctl_cmd:
        return jsonify({"success": False, "error": "systemctl command not found"})
    try:
        result = subprocess.run(["sudo", systemctl_cmd, action, hytale_name],
                              capture_output=True, text=True, timeout=5,
                              env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
        if result.returncode == 0:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": result.stderr})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@hytale_bp.route("/api/hytales/logs/<hytale>")
def api_hytales_logs(hytale):
    # Logs now placed per-service under /home/hytale/{service}/Server/logs
    safe_name = os.path.basename(hytale)
    logs_dir = os.path.join("/home/hytale", safe_name, "Server", "logs")
    # fallback to legacy location if per-service path not present
    if not os.path.isdir(logs_dir):
        legacy = "/home/hytale/Server/logs"
        if os.path.isdir(legacy):
            logs_dir = legacy
        else:
            return jsonify({"logs": "Erreur: aucun fichier de log trouvé", "players": []})

    max_bytes = 5000  # max bytes to return for display
    try:
        pattern = os.path.join(logs_dir, "*.log")
        files = glob.glob(pattern)
        if not files:
            return jsonify({"logs": "Erreur: aucun fichier de log trouvé", "players": []})

        # Sort files oldest first to replay chronologically
        files.sort(key=lambda p: os.path.getmtime(p))

        all_texts = []
        players = []

        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
                    all_texts.append(content)
                    # parse entire file lines in order to maintain players state
                    for line in content.splitlines():
                        m_add = re.search(r"Adding player\s+'([^']+)'", line, re.IGNORECASE)
                        if m_add:
                            name = m_add.group(1).strip()
                            if name and name not in players:
                                players.append(name)
                            continue
                        m_rm = re.search(r"Removing player\s+'([^']+)'", line, re.IGNORECASE)
                        if m_rm:
                            name = m_rm.group(1).strip()
                            if name in players:
                                players.remove(name)
                            continue
                        m_add2 = re.search(r"Adding player\s+([A-Za-z0-9_\-]+)", line, re.IGNORECASE)
                        if m_add2:
                            name = m_add2.group(1).strip()
                            if name and name not in players:
                                players.append(name)
                            continue
                        m_rm2 = re.search(r"Removing player\s+([A-Za-z0-9_\-]+)", line, re.IGNORECASE)
                        if m_rm2:
                            name = m_rm2.group(1).strip()
                            if name in players:
                                players.remove(name)
            except Exception:
                # skip unreadable files but continue processing others
                continue

        # build truncated logs for display (take last max_bytes of concatenated logs)
        concat = "".join(all_texts)
        logs = concat[-max_bytes:]

        return jsonify({"logs": logs, "players": players})
    except Exception as e:
        return jsonify({"logs": f"Erreur: {str(e)}", "players": []})
