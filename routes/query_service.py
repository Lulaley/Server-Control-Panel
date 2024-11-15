import socket
import json
from flask import Blueprint, jsonify

query_service_bp = Blueprint('query_service', __name__)

def load_services(filename):
    with open(filename, 'r') as file:
        return json.load(file)

services = load_services('services.json')

def query_satisfactory_server(ip, port):
    query = b'\xFF\xFF\xFF\xFFTSource Engine Query\x00'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    try:
        sock.sendto(query, (ip, port))
        data, _ = sock.recvfrom(4096)
        return {"status": "success", "data": data.decode('utf-8', errors='ignore')}
    except socket.timeout:
        return {"status": "error", "message": "No response from server"}
    finally:
        sock.close()

def query_minecraft_server(ip, port):
    # Implement Minecraft server query logic here
    return {"status": "success", "message": f"Querying Minecraft server at {ip}:{port}"}

@query_service_bp.route('/services', methods=['GET'])
def get_services():
    return jsonify(list(services.keys()))

@query_service_bp.route('/services/<service_name>/servers', methods=['GET'])
def get_servers(service_name):
    if service_name in services:
        return jsonify(services[service_name])
    else:
        return jsonify({"error": "Service not found"}), 404

@query_service_bp.route('/services/<service_name>/servers/<int:server_id>/query', methods=['GET'])
def query_server(service_name, server_id):
    if service_name in services:
        servers = services[service_name]
        if 0 <= server_id < len(servers):
            server = servers[server_id]
            ip = server["ip"]
            port = server["port"]
            if service_name == "Satisfactory":
                return jsonify(query_satisfactory_server(ip, port))
            elif service_name == "Minecraft":
                return jsonify(query_minecraft_server(ip, port))
            else:
                return jsonify({"error": "Unsupported service"}), 400
        else:
            return jsonify({"error": "Server not found"}), 404
    else:
        return jsonify({"error": "Service not found"}), 404