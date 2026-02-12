from flask import Blueprint, jsonify, render_template, make_response, request, session
import subprocess
import os
import glob
import difflib
import json
from mcrcon import MCRcon
import shutil
import datetime

# Créer un Blueprint pour les routes de la page home
minecraft_bp = Blueprint('minecraft', __name__)

# Make session available in templates for this blueprint
@minecraft_bp.context_processor
def inject_user():
    return {
        'current_user': session.get('user'),
        'current_role': session.get('role'),
        'is_admin': session.get('role') == 'admin',
        'is_manager': session.get('role') == 'manager',
        'can_control_services': session.get('role') in ('admin', 'manager')
    }

@minecraft_bp.route("/minecraft")
def minecraft():
    return render_template("minecraft.html")

@minecraft_bp.route("/api/minecraft/servers")
def minecraft_servers():
    # Recherche les services systemd dont la description contient "minecraft" (insensible à la casse et aux espaces)
    service_files = glob.glob("/etc/systemd/system/*.service")
    servers = []
    for f in service_files:
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as file:
                for line in file:
                    # Nettoie la ligne pour ignorer espaces et casse
                    line_clean = line.strip().lower().replace(" ", "")
                    if line_clean.startswith("description=") and "minecraft" in line_clean:
                        servers.append(os.path.basename(f).replace(".service", ""))
                        break
        except Exception:
            continue
    return jsonify({"servers": servers})

def check_systemctl_service(service):
    """Vérifie rapidement le statut d'un service systemd (service sans suffixe .service).
    Retourne dict: { is_active: bool, state: str, systemctl_status: str, debug: {...} }"""
    service_name = f"{service}.service"
    systemctl_paths = ["/usr/bin/systemctl", "/bin/systemctl", "systemctl"]
    systemctl_cmd = None
    for path in systemctl_paths:
        if os.path.exists(path) or path == "systemctl":
            systemctl_cmd = path
            break

    debug = {"systemctl_path": systemctl_cmd}
    if not systemctl_cmd:
        return {"is_active": False, "state": "unknown", "systemctl_status": "", "debug": debug}

    try:
        proc = subprocess.run([systemctl_cmd, "is-active", service_name],
                              capture_output=True, text=True, timeout=3,
                              env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
        status = (proc.stdout or proc.stderr or "").strip()
        debug.update({"stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode})
    except Exception as e:
        debug.update({"error": str(e)})
        return {"is_active": False, "state": "unknown", "systemctl_status": "", "debug": debug}

    state = "unknown"
    is_active = False
    if status == "active":
        state = "active"
        is_active = True
    elif status in ("inactive", "failed", "dead"):
        state = "inactive"
        is_active = False
    else:
        state = status or "unknown"

    return {"is_active": is_active, "state": state, "systemctl_status": status, "debug": debug}

# Route pour l'état du serveur Minecraft (doit être après la déclaration de minecraft_bp)
@minecraft_bp.route("/api/minecraft/status/<server>")
def minecraft_status(server):    
    # Vérifie l'état du service systemd
    service_name = f"{server}.service"
    
    # Try different paths for systemctl
    systemctl_paths = ["/usr/bin/systemctl", "/bin/systemctl", "systemctl"]
    systemctl_cmd = None
    
    for path in systemctl_paths:
        if os.path.exists(path) or path == "systemctl":
            systemctl_cmd = path
            break
    
    if not systemctl_cmd:
        return jsonify({
            "service": server,
            "status": "unknown",
            "error": "systemctl command not found",
            "can_control": session.get("role") in ("admin", "manager")
        })
    
    # use shared helper
    info = check_systemctl_service(server)
    status_map = "unknown"
    if info["state"] == "active":
        status_map = "running"
    elif info["state"] == "inactive":
        status_map = "stopped"
    return jsonify({
        "service": server,
        "status": status_map,
        "systemctl_status": info.get("systemctl_status"),
        "can_control": session.get("role") in ("admin", "manager"),
        "debug_info": info.get("debug", {})
    })

# --- Contrôle des services Minecraft ---
@minecraft_bp.route("/api/minecraft/control/<server>", methods=["POST"])
def minecraft_control(server):
    data = request.get_json(force=True)
    action = data.get("action")
    service_name = f"{server}.service"
    if action not in ("start", "stop", "restart"):
        return jsonify({"success": False, "error": "Action invalide"}), 400
    # Permission: only manager or admin can control server services
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
        return jsonify({"success": False, "error": "systemctl command not found"})
    
    try:
        result = subprocess.run(["sudo", systemctl_cmd, action, service_name], 
                              capture_output=True, text=True, timeout=5,
                              env=dict(os.environ, PATH="/usr/bin:/bin:/usr/sbin:/sbin"))
        if result.returncode == 0:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": result.stderr})
    except Exception as e:
        print(f"EXCEPTION OCCURRED: {e}")
        return jsonify({"success": False, "error": str(e)})

@minecraft_bp.route("/api/minecraft/logs/<server>")
def minecraft_logs(server):
    # Chemin du fichier de log Minecraft
    log_path = f"/var/log/{server}.log"
    logs = ""
    purged = False
    removed_count = 0

    def _read_and_clean(path):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            cleaned = [l for l in lines if "Can't keep up!" not in l]
            return lines, cleaned
        except Exception as e:
            return None, None

    if os.path.exists(log_path):
        orig_lines, cleaned_lines = _read_and_clean(log_path)
        if orig_lines is None:
            logs = ""
        else:
            removed_count = len(orig_lines) - len(cleaned_lines)
            logs = ''.join(cleaned_lines[-5000:]) if len(cleaned_lines) > 5000 else ''.join(cleaned_lines)

            # Si purge demandée et utilisateur admin, sauvegarder et réécrire le fichier sans les lignes indésirables
            purge_req = str(request.args.get('purge', '')).lower() in ('1', 'true', 'yes')
            if purge_req and session.get('role') == 'admin' and removed_count > 0:
                try:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    backup_path = f"{log_path}.bak.{timestamp}"
                    shutil.copy2(log_path, backup_path)
                    tmp_path = f"{log_path}.tmp"
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.writelines(cleaned_lines)
                    os.replace(tmp_path, log_path)
                    purged = True
                except Exception as e:
                    # Ne pas échouer la lecture si la purge échoue ; log côté serveur possible
                    print(f"Error purging log file {log_path}: {e}")
    else:
        logs = ""
        # Essayer autres emplacements (comme avant) et appliquer même logique de nettoyage + purge si trouvé
        alternative_paths = [
            f"/home/chimea/Bureau/{server}/logs/latest.log",
            f"/home/chimea/Bureau/{server}/server.log",
            f"/opt/minecraft/{server}/logs/latest.log",
            f"/var/minecraft/{server}/logs/latest.log"
        ]
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                orig_lines, cleaned_lines = _read_and_clean(alt_path)
                if orig_lines is None:
                    continue
                removed_count = len(orig_lines) - len(cleaned_lines)
                logs = ''.join(cleaned_lines[-5000:]) if len(cleaned_lines) > 5000 else ''.join(cleaned_lines)
                purge_req = str(request.args.get('purge', '')).lower() in ('1', 'true', 'yes')
                if purge_req and session.get('role') == 'admin' and removed_count > 0:
                    try:
                        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                        backup_path = f"{alt_path}.bak.{timestamp}"
                        shutil.copy2(alt_path, backup_path)
                        tmp_path = f"{alt_path}.tmp"
                        with open(tmp_path, "w", encoding="utf-8") as f:
                            f.writelines(cleaned_lines)
                        os.replace(tmp_path, alt_path)
                        purged = True
                    except Exception as e:
                        print(f"Error purging log file {alt_path}: {e}")
                break

    response = make_response(jsonify({
        "logs": logs,
        "log_path": log_path,
        "purged": purged,
        "removed_lines": removed_count
    }))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@minecraft_bp.route("/api/minecraft/players/<server>")
def minecraft_players(server):    
    log_path = f"/var/log/{server}.log"
    
    print(f"DEBUG: Checking players for server {server}")
    print(f"DEBUG: Log path: {log_path}")
    print(f"DEBUG: Log file exists: {os.path.exists(log_path)}")

    players = set()
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                print(f"DEBUG: Total lines in log: {len(lines)}")
                
                # Prendre seulement les dernières 1000 lignes pour la performance
                recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                
                for line in recent_lines:
                    line = line.strip()
                    
                    # Patterns plus robustes pour détecter les connexions/déconnexions
                    if "joined the game" in line.lower():
                        # Exemples: [12:34:56] [Server thread/INFO]: PlayerName joined the game
                        #          [12:34:56] [User Authenticator #1/INFO] [minecraft/DedicatedServer]: PlayerName joined the game
                        parts = line.split("joined the game")
                        if len(parts) >= 2:
                            before_join = parts[0]
                            # Extraire le nom du joueur (généralement le dernier mot avant "joined")
                            words = before_join.split()
                            if words:
                                # Le nom du joueur est souvent le dernier mot ou avant-dernier
                                for i in range(len(words)-1, -1, -1):
                                    word = words[i]
                                    # Éviter les mots qui ne sont pas des noms de joueurs
                                    if word and not any(x in word.lower() for x in ['info', 'thread', 'server', ':', '[', ']']):
                                        if len(word) >= 3 and len(word) <= 16:  # Longueur typique d'un nom Minecraft
                                            players.add(word)
                                            print(f"DEBUG: Player joined: {word}")
                                            break
                    
                    elif "left the game" in line.lower():
                        # Même logique pour les déconnexions
                        parts = line.split("left the game")
                        if len(parts) >= 2:
                            before_left = parts[0]
                            words = before_left.split()
                            if words:
                                for i in range(len(words)-1, -1, -1):
                                    word = words[i]
                                    if word and not any(x in word.lower() for x in ['info', 'thread', 'server', ':', '[', ']']):
                                        if len(word) >= 3 and len(word) <= 16:
                                            players.discard(word)
                                            print(f"DEBUG: Player left: {word}")
                                            break
                
                print(f"DEBUG: Final players list: {list(players)}")
                
        except Exception as e:
            print(f"DEBUG: Error reading log file: {e}")
            return jsonify({"players": [], "error": f"Erreur lecture logs: {e}"})
    else:
        print(f"DEBUG: Log file not found at {log_path}")
        # Essayer d'autres emplacements possibles
        alternative_paths = [
            f"/home/chimea/Bureau/{server}/logs/latest.log",
            f"/home/chimea/Bureau/{server}/server.log",
            f"/opt/minecraft/{server}/logs/latest.log",
            f"/var/minecraft/{server}/logs/latest.log"
        ]
        
        for alt_path in alternative_paths:
            print(f"DEBUG: Trying alternative path: {alt_path}")
            if os.path.exists(alt_path):
                print(f"DEBUG: Found log at: {alt_path}")
                # Répéter la même logique avec le nouveau chemin
                try:
                    with open(alt_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        recent_lines = lines[-1000:] if len(lines) > 1000 else lines
                        
                        for line in recent_lines:
                            if "joined the game" in line.lower():
                                parts = line.split("joined the game")
                                if len(parts) >= 2:
                                    words = parts[0].split()
                                    for i in range(len(words)-1, -1, -1):
                                        word = words[i]
                                        if word and not any(x in word.lower() for x in ['info', 'thread', 'server', ':', '[', ']']):
                                            if len(word) >= 3 and len(word) <= 16:
                                                players.add(word)
                                                break
                            elif "left the game" in line.lower():
                                parts = line.split("left the game")
                                if len(parts) >= 2:
                                    words = parts[0].split()
                                    for i in range(len(words)-1, -1, -1):
                                        word = words[i]
                                        if word and not any(x in word.lower() for x in ['info', 'thread', 'server', ':', '[', ']']):
                                            if len(word) >= 3 and len(word) <= 16:
                                                players.discard(word)
                                                break
                    break
                except Exception as e:
                    print(f"DEBUG: Error reading alternative log: {e}")
                    continue
    
    return jsonify({"players": list(players), "log_path_used": log_path})

@minecraft_bp.route("/api/minecraft/command/<server>", methods=["POST"])
def minecraft_command(server):
    # Récupère le chemin du .service
    service_file = f"/etc/systemd/system/{server}.service"
    server_dir = None

    if os.path.exists(service_file):
        with open(service_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Cherche le WorkingDirectory
                if line.strip().startswith("WorkingDirectory="):
                    server_dir = line.strip().split("=", 1)[1]
                    break
        # Si WorkingDirectory non trouvé, fallback sur ExecStart
        if not server_dir:
            with open(service_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().startswith("ExecStart="):
                        exec_cmd = line.strip().split("=", 1)[1]
                        path_parts = exec_cmd.strip().split()
                        if path_parts:
                            exec_path = path_parts[0]
                            if ".sh" in exec_path:
                                server_dir = os.path.dirname(exec_path)
                            else:
                                server_dir = exec_path
                            break

    # Fallback si le chemin n'est pas trouvé via le .service
    if not server_dir:
        base_dir = "/home/chimea/Bureau/"
        possible_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
        match = difflib.get_close_matches(server.lower(), [d.lower() for d in possible_dirs], n=1)
        if not match:
            return jsonify({"success": False, "error": "Serveur introuvable"}), 404
        real_dir = next(d for d in possible_dirs if d.lower() == match[0])
        server_dir = os.path.join(base_dir, real_dir)

    # Lire server.properties pour récupérer port et mot de passe RCON
    properties_path = os.path.join(server_dir, "server.properties")
    if not os.path.exists(properties_path):
        return jsonify({"success": False, "error": "server.properties introuvable"}), 404

    # Lire les propriétés RCON
    rcon_port = None
    rcon_password = None
    with open(properties_path, "r") as f:
        for line in f:
            if line.startswith("rcon.port"):
                rcon_port = int(line.strip().split("=")[1])
            elif line.startswith("rcon.password"):
                rcon_password = line.strip().split("=")[1]
    if not rcon_port or not rcon_password:
        return jsonify({"success": False, "error": "RCON non configuré"}), 400

    # Récupérer la commande à exécuter
    command = (json.loads(request.data)).get("command")
    if not command:
        return jsonify({"success": False, "error": "Commande manquante"}), 400

    # Permission: admin can run all commands, manager can only use tell command
    role = session.get("role")
    if role == "manager":
        # Manager can only use tell command
        if not command.startswith("tell "):
            return jsonify({"success": False, "error": "Les managers ne peuvent utiliser que la commande 'tell'"}), 403
    elif role != "admin":
        return jsonify({"success": False, "error": "forbidden"}), 403
    
    # Get current user for command attribution
    current_user = session.get("user", "Admin")
    
    # Envoyer la commande via mcrcon
    try:
        with MCRcon("127.0.0.1", rcon_password, port=rcon_port) as mcr:
            # Add user identification to certain commands
            if command.startswith(('tell ', 'kick ', 'ban ')):
                # For player actions, add user signature
                parts = command.split(' ', 2)
                if len(parts) >= 3 and command.startswith('tell '):
                    # tell player message -> tell player [Admin: message]
                    player, message = parts[1], parts[2]
                    command = f"tell {player} [{current_user}] {message}"
                elif len(parts) >= 2 and command.startswith(('kick ', 'ban ')):
                    # kick/ban player reason -> kick/ban player [reason - by Admin]
                    action, player = parts[0], parts[1]
                    reason = parts[2] if len(parts) > 2 else ""
                    if reason:
                        command = f"{action} {player} {reason} - par {current_user}"
                    else:
                        command = f"{action} {player} Action effectuée par {current_user}"
            
            response = mcr.command(command)
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Helper: trouver le dossier du serveur (réutilise la logique déjà présente plus bas)
def find_server_dir(server):
    # 1) tenter via le .service systemd
    service_file = f"/etc/systemd/system/{server}.service"
    server_dir = None
    if os.path.exists(service_file):
        try:
            with open(service_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip().startswith("WorkingDirectory="):
                        server_dir = line.strip().split("=", 1)[1]
                        break
            if not server_dir:
                with open(service_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.strip().startswith("ExecStart="):
                            exec_cmd = line.strip().split("=", 1)[1]
                            path_parts = exec_cmd.strip().split()
                            if path_parts:
                                exec_path = path_parts[0]
                                if ".sh" in exec_path:
                                    server_dir = os.path.dirname(exec_path)
                                else:
                                    server_dir = exec_path
                                break
        except Exception:
            server_dir = None

    # 2) fallback : rechercher dans base_dir
    if not server_dir:
        base_dir = "/home/chimea/Bureau/"
        try:
            possible_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            match = difflib.get_close_matches(server.lower(), [d.lower() for d in possible_dirs], n=1)
            if match:
                real_dir = next(d for d in possible_dirs if d.lower() == match[0])
                server_dir = os.path.join(base_dir, real_dir)
        except Exception:
            server_dir = None

    return server_dir

# Helpers pour parser et écrire server.properties
def read_server_properties(path):
    props = {}
    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            if "=" in line_stripped:
                k, v = line_stripped.split("=", 1)
                props[k.strip()] = v.strip()
    except Exception:
        return None
    return props

def write_server_properties(path, new_props):
    # backup original
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{path}.bak.{timestamp}"
    shutil.copy2(path, backup_path)
    # Read original to preserve comments/order where possible
    out_lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            orig_lines = f.readlines()
    except Exception:
        orig_lines = []
    seen = set()
    for line in orig_lines:
        if "=" in line and not line.strip().startswith("#"):
            k = line.split("=",1)[0].strip()
            if k in new_props:
                out_lines.append(f"{k}={new_props[k]}\n")
                seen.add(k)
            else:
                out_lines.append(line)
        else:
            out_lines.append(line)
    # append any new keys not in original
    for k, v in new_props.items():
        if k not in seen:
            out_lines.append(f"{k}={v}\n")
    # write atomically
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(out_lines)
    os.replace(tmp, path)
    return True

# --- NEW: endpoints pour server.properties (admin only for POST) ---
@minecraft_bp.route("/api/minecraft/server-properties/<server>", methods=["GET"])
def get_server_properties(server):
    server_dir = find_server_dir(server)
    candidates = []
    if server_dir:
        candidates.append(os.path.join(server_dir, "server.properties"))
    # common fallback paths
    candidates.extend([
        f"/home/chimea/Bureau/{server}/server.properties",
        f"/home/chimea/Bureau/{server}/logs/server.properties",
        f"/opt/minecraft/{server}/server.properties",
        f"/var/minecraft/{server}/server.properties"
    ])
    for path in candidates:
        if path and os.path.exists(path):
            props = read_server_properties(path)
            if props is None:
                return jsonify({"success": False, "error": "failed_to_read"}), 500
            return jsonify({"success": True, "path": path, "properties": props})
    return jsonify({"success": False, "error": "not_found"}), 404

@minecraft_bp.route("/api/minecraft/server-properties/<server>", methods=["POST"])
def set_server_properties(server):
    # only admin allowed to overwrite server.properties via this endpoint
    if session.get("role") != "admin":
        return jsonify({"success": False, "error": "forbidden"}), 403
    data = request.get_json(silent=True) or {}
    new_props = data.get("properties")
    if not isinstance(new_props, dict):
        return jsonify({"success": False, "error": "invalid_payload"}), 400

    server_dir = find_server_dir(server)
    candidates = []
    if server_dir:
        candidates.append(os.path.join(server_dir, "server.properties"))
    candidates.extend([
        f"/home/chimea/Bureau/{server}/server.properties",
        f"/home/chimea/Bureau/{server}/logs/server.properties",
        f"/opt/minecraft/{server}/server.properties",
        f"/var/minecraft/{server}/server.properties"
    ])
    for path in candidates:
        if path and os.path.exists(path):
            try:
                write_server_properties(path, new_props)
                return jsonify({"success": True, "path": path})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "not_found"}), 404
