from flask import Blueprint, render_template, current_app, url_for
import socket
import os

bp = Blueprint('game_servers', __name__, template_folder='../../templates')

SAMPLE_SERVERS = [
	# ...exemple minimal à remplacer par votre source réelle...
	{"id": "mc-1", "name": "MC Vanilla", "host": "127.0.0.1", "port": 25565, "game": "minecraft", "log_path": "/var/log/mc1/latest.log", "url": "/server/mc-1"},
	{"id": "sat-1", "name": "Satisfactory 1", "host": "127.0.0.1", "port": 15777, "game": "satisfactory", "log_path": "/var/log/sat1/latest.log", "url": "/server/sat-1"},
	{"id": "hyt-1", "name": "Hytale 1", "host": "127.0.0.1", "port": 25565, "game": "hytale", "log_path": "/var/log/hyt1/latest.log", "url": "/server/hyt-1"},
]

def check_port(host, port, timeout=0.8):
	try:
		with socket.create_connection((host, int(port)), timeout=timeout):
			return True
	except Exception:
		return False

def tail_last_line(path):
	try:
		if not path or not os.path.isfile(path):
			return None
		with open(path, "rb") as f:
			f.seek(0, os.SEEK_END)
			pos = f.tell() - 1
			if pos < 0:
				return ""
			line = b""
			while pos >= 0:
				f.seek(pos)
				ch = f.read(1)
				if ch == b'\n' and line:
					break
				line = ch + line
				pos -= 1
			return line.decode('utf-8', errors='replace').strip()
	except Exception:
		return None

@bp.route('/games')
def games():
	servers = current_app.config.get('SERVERS', SAMPLE_SERVERS)
	groups = {"minecraft": [], "satisfactory": [], "hytale": []}
	for s in servers:
		game = (s.get("game") or "").lower()
		if game not in groups:
			continue
		status = check_port(s.get("host", "127.0.0.1"), s.get("port", 0))
		last_log = tail_last_line(s.get("log_path")) if s.get("log_path") else None
		item = {
			"id": s.get("id"),
			"name": s.get("name"),
			"host": s.get("host"),
			"port": s.get("port"),
			"status": "online" if status else "offline",
			"last_log": last_log,
			"url": s.get("url", f"/server/{s.get('id')}")
		}
		groups[game].append(item)
	return render_template('games.html', groups=groups)
