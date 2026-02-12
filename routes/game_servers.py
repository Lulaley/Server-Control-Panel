from flask import Blueprint, render_template, current_app
import os
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

@game_servers_bp.route('/games')
def games():
    groups = {"minecraft": [], "satisfactory": [], "hytale": []}
    # Minecraft
    try:
        import routes.minecraft as mc
        mc_list = _call_and_json(mc.minecraft_servers)
        if mc_list and isinstance(mc_list, dict):
            for name in mc_list.get("servers", []):
                status_j = _call_and_json(mc.minecraft_status, name) or {}
                logs_j = _call_and_json(mc.minecraft_logs, name) or {}
                last_log = None
                # minecraft_logs returns {"logs": "..."}
                last_log = _last_line_from_logs_text(logs_j.get("logs") if isinstance(logs_j, dict) else None)
                groups["minecraft"].append({
                    "id": name,
                    "name": name,
                    "host": None,
                    "port": None,
                    "status": status_j.get("status", "unknown") if isinstance(status_j, dict) else "unknown",
                    "last_log": last_log,
                    "url": f"/server/{name}"
                })
    except Exception:
        current_app.logger.debug("Minecraft import failed: %s", traceback.format_exc())
    # Satisfactory
    try:
        import routes.satisfactory as sat
        sat_list = _call_and_json(sat.api_satisfactorys_list)
        if sat_list and isinstance(sat_list, dict):
            for name in sat_list.get("satisfactorys", []):
                status_j = _call_and_json(sat.api_satisfactorys_status, name) or {}
                logs_j = _call_and_json(sat.api_satisfactorys_logs, name) or {}
                last_log = _last_line_from_logs_text(logs_j.get("logs") if isinstance(logs_j, dict) else None)
                groups["satisfactory"].append({
                    "id": name,
                    "name": name,
                    "host": None,
                    "port": None,
                    "status": status_j.get("status", "unknown") if isinstance(status_j, dict) else "unknown",
                    "last_log": last_log,
                    "url": f"/server/{name}"
                })
    except Exception:
        current_app.logger.debug("Satisfactory import failed: %s", traceback.format_exc())
    # Hytale
    try:
        import routes.hytale as hyt
        hyt_list = _call_and_json(hyt.api_hytales_list)
        if hyt_list and isinstance(hyt_list, dict):
            for name in hyt_list.get("hytales", []):
                status_j = _call_and_json(hyt.api_hytales_status, name) or {}
                logs_j = _call_and_json(hyt.api_hytales_logs, name) or {}
                last_log = _last_line_from_logs_text(logs_j.get("logs") if isinstance(logs_j, dict) else None)
                groups["hytale"].append({
                    "id": name,
                    "name": name,
                    "host": None,
                    "port": None,
                    "status": status_j.get("status", "unknown") if isinstance(status_j, dict) else "unknown",
                    "last_log": last_log,
                    "url": f"/server/{name}"
                })
    except Exception:
        current_app.logger.debug("Hytale import failed: %s", traceback.format_exc())

    # Fallback: si aucun groupe rempli, utiliser SAMPLE_SERVERS (utile en dev)
    if not any(groups[g] for g in groups):
        for s in SAMPLE_SERVERS:
            g = (s.get("game") or "").lower()
            if g in groups:
                groups[g].append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "host": s.get("host"),
                    "port": s.get("port"),
                    "status": "online" if s.get("host") else "offline",
                    "last_log": None,
                    "url": s.get("url", f"/server/{s.get('id')}")
                })

    return render_template('games.html', groups=groups)
