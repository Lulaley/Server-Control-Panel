from flask import abort, Blueprint, jsonify, render_template, make_response, request, session
import subprocess
import re
import psutil
import time
import os
import glob
import difflib
import json
from mcrcon import MCRcon

# Créer un Blueprint pour les routes de la page home
home_bp = Blueprint('home', __name__)

# Variables globales pour calculer le débit réseau
previous_net_io = psutil.net_io_counters()
previous_time = time.time()

# Chemin vers le fichier de configuration des couleurs
COLOR_FILE = "static/main_color.json"

# Fonction pour obtenir la couleur principale depuis le fichier JSON
def get_main_color():
    try:
        with open(COLOR_FILE, "r") as f:
            data = json.load(f)
            return data.get("main_color", "#4caf50")
    except Exception:
        return "#4caf50"
    
# Fonction pour définir la couleur principale dans le fichier JSON
def set_main_color(color):
    with open(COLOR_FILE, "w") as f:
        json.dump({"main_color": color}, f)

@home_bp.route("/")
def home():
    global previous_net_io, previous_time

    # Récupérer les informations système
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_threads = psutil.cpu_percent(interval=1, percpu=True)  # Utilisation par thread
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Calculer le débit réseau
    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    elapsed_time = current_time - previous_time

    network_in = (current_net_io.bytes_recv - previous_net_io.bytes_recv) / 1024 / elapsed_time  # KB/s
    network_out = (current_net_io.bytes_sent - previous_net_io.bytes_sent) / 1024 / elapsed_time  # KB/s

    # Mettre à jour les valeurs précédentes
    previous_net_io = current_net_io
    previous_time = current_time

    # Préparer les données pour le rendu
    system_info = {
        "cpu_percent": cpu_percent,
        "cpu_threads": cpu_threads,
        "memory_percent": memory.percent,
        "memory_used": f"{memory.used / (1024 ** 3):.2f} GB",
        "memory_total": f"{memory.total / (1024 ** 3):.2f} GB",
        "disk_percent": disk.percent,
        "disk_used": f"{disk.used / (1024 ** 3):.2f} GB",
        "disk_total": f"{disk.total / (1024 ** 3):.2f} GB",
        "network_in": f"{network_in:.2f} KB/s",
        "network_out": f"{network_out:.2f} KB/s"
    }
    return render_template("home.html", system_info=system_info)

@home_bp.route("/api/system-info")
def api_system_info():
    global previous_net_io, previous_time

    # Récupérer les informations système
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_threads = psutil.cpu_percent(interval=1, percpu=True)  # Utilisation par thread
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Calculer le débit réseau
    current_net_io = psutil.net_io_counters()
    current_time = time.time()
    elapsed_time = current_time - previous_time

    network_in = (current_net_io.bytes_recv - previous_net_io.bytes_recv) / 1024 / elapsed_time  # KB/s
    network_out = (current_net_io.bytes_sent - previous_net_io.bytes_sent) / 1024 / elapsed_time  # KB/s

    # Mettre à jour les valeurs précédentes
    previous_net_io = current_net_io
    previous_time = current_time

    # Retourner les données au format JSON
    return jsonify({
        "cpu_percent": cpu_percent,
        "cpu_threads": cpu_threads,  # Liste des threads CPU
        "memory_percent": memory.percent,
        "memory_used": memory.used / (1024 ** 3),  # En GB
        "memory_total": memory.total / (1024 ** 3),  # En GB
        "disk_percent": disk.percent,
        "disk_used": disk.used / (1024 ** 3),  # En GB
        "disk_total": disk.total / (1024 ** 3),  # En GB
        "network_in": network_in,  # KB/s
        "network_out": network_out  # KB/s
    })

@home_bp.route("/api/main-color", methods=["POST"])
def api_set_main_color():
    # Only admin can change main color
    role = session.get("role")
    if role != "admin":
        return jsonify({"success": False, "error": "forbidden"}), 403
    color = (json.loads(request.data)).get("main_color")
    if color:
        set_main_color(color)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@home_bp.route("/api/main-color", methods=["GET"])
def api_get_main_color():
    return jsonify({"main_color": get_main_color()})

@home_bp.route("/settings")
def settings():
    return render_template("settings.html")

@home_bp.context_processor
def inject_system_info():
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        machine_info = {
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(memory.percent, 1),
            "ram_used": f"{memory.used / (1024 ** 3):.2f} GB",
            "ram_total": f"{memory.total / (1024 ** 3):.2f} GB",
            "disk_percent": round(disk.percent, 1),
            "disk_used": f"{disk.used / (1024 ** 3):.2f} GB",
            "disk_total": f"{disk.total / (1024 ** 3):.2f} GB"
        }
    except Exception:
        machine_info = None
    return {"machine_info": machine_info}
