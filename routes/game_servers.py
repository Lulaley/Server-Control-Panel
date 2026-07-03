from flask import Blueprint, render_template, current_app
import traceback
import json

game_servers_bp = Blueprint('game_servers', __name__, template_folder='../templates')

SAMPLE_SERVERS = [
    {"id": "mc-1", "name": "MC Vanilla", "host": "127.0.0.1", "port": 25565, "game": "minecraft", "log_path": "/var/log/mc1/latest.log", "url": "/server/mc-1"},
    {"id": "sat-1", "name": "Satisfactory 1", "host": "127.0.0.1", "port": 15777, "game": "satisfactory", "log_path": "/var/log/sat1/latest.log", "url": "/server/sat-1"},
    {"id": "hyt-1", "name": "Hytale 1", "host": "127.0.0.1", "port": 25565, "game": "hytale", "log_path": "/var/log/hyt1/latest.log", "url": "/server/hyt-1"},
]

def _last_line_from_logs_text(logs_text):
    if not logs_text:
        return None
    lines = [l for l in logs_text.splitlines() if l.strip()]
    return lines[-1].strip() if lines else None

def _call_and_json(fn, *args, **kwargs):
    """Appelle une view/function de route et retourne dict JSON ou None."""
    try:
        res = fn(*args, **kwargs)
        # handle tuple responses (response, status, headers)
        if isinstance(res, tuple) and len(res) > 0:
            res = res[0]
        # Flask/Werkzeug Response object
        if hasattr(res, "get_json") or hasattr(res, "get_data"):
            try:
                # prefer built-in parser
                if hasattr(res, "get_json"):
                    j = res.get_json(silent=True)
                    if j is not None:
                        return j
                # fallback to raw body
                if hasattr(res, "get_data"):
                    body = res.get_data(as_text=True)
                    if body:
                        return json.loads(body)
            except Exception:
                current_app.logger.debug("Response parse failed: %s", traceback.format_exc())
                return None
        # already a dict/list
        if isinstance(res, (dict, list)):
            return res
        # string that might be JSON
        if isinstance(res, str):
            try:
                return json.loads(res)
            except Exception:
                return None
        return None
    except Exception:
        current_app.logger.debug("call error: %s", traceback.format_exc())
        return None


# --- Ajout utilitaire générique pour tous les jeux/services ---
def build_groups_from_services(service_sources):
    """
    service_sources: liste de tuples (game, list_of_services, status_fn, logs_fn)
    Chaque service doit avoir un champ 'id' unique et stable (utilisé par l'API du jeu)
    """
    groups = {}
    for game, service_list, status_fn, logs_fn in service_sources:
        game_key = game.lower()
        groups.setdefault(game_key, [])
        if service_list:
            for srv in service_list:
                srv_id = srv.get('id') or srv.get('name')
                status_j = _call_and_json(status_fn, srv_id) if status_fn else {}
                logs_j = _call_and_json(logs_fn, srv_id) if logs_fn else {}
                last_log = _last_line_from_logs_text(logs_j.get("logs") if isinstance(logs_j, dict) else None)
                groups[game_key].append({
                    "id": srv_id,
                    "name": srv.get('name', srv_id),
                    "host": srv.get('host'),
                    "port": srv.get('port'),
                    "status": status_j.get("status", "unknown") if isinstance(status_j, dict) else "unknown",
                    "last_log": last_log,
                    "url": srv.get('url', f"/server/{srv_id}")
                })
    return groups


@game_servers_bp.route('/games', methods=['GET'])
def games():
    try:
        # Construction générique
        service_sources = []
        try:
            import routes.minecraft as mc
            mc_list = _call_and_json(mc.minecraft_servers)
            mc_services = []
            if mc_list and isinstance(mc_list, dict):
                for name in mc_list.get("servers", []):
                    mc_services.append({"id": name, "name": name})
            service_sources.append(("minecraft", mc_services, mc.minecraft_status, mc.minecraft_logs))
        except Exception:
            current_app.logger.debug("Minecraft import failed: %s", traceback.format_exc())
        try:
            import routes.satisfactory as sat
            sat_list = _call_and_json(sat.api_satisfactorys_list)
            sat_services = []
            if sat_list and isinstance(sat_list, dict):
                for name in sat_list.get("satisfactorys", []):
                    sat_services.append({"id": name, "name": name})
            service_sources.append(("satisfactory", sat_services, sat.api_satisfactorys_status, sat.api_satisfactorys_logs))
        except Exception:
            current_app.logger.debug("Satisfactory import failed: %s", traceback.format_exc())
        try:
            import routes.hytale as hyt
            hyt_list = _call_and_json(hyt.api_hytales_list)
            hyt_services = []
            if hyt_list and isinstance(hyt_list, dict):
                for name in hyt_list.get("hytales", []):
                    hyt_services.append({"id": name, "name": name})
            service_sources.append(("hytale", hyt_services, hyt.api_hytales_status, hyt.api_hytales_logs))
        except Exception:
            current_app.logger.debug("Hytale import failed: %s", traceback.format_exc())

        # Fallback: si aucun groupe rempli, utiliser SAMPLE_SERVERS (utile en dev)
        if not service_sources or not any(len(services) > 0 for (_, services, *_ ) in service_sources):
            for s in SAMPLE_SERVERS:
                service_sources.append((s.get("game", "minecraft"), [s], None, None))

        groups = build_groups_from_services(service_sources)
        return render_template('games.html', groups=groups)
    except Exception as e:
        # Affiche l'erreur dans la page pour debug
        return f"<h1>Erreur interne</h1><pre>{traceback.format_exc()}</pre>", 500
