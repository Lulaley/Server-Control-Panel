#!/usr/bin/env python3
"""
Découvre les serveurs Minecraft en cherchant des fichiers server.properties
sous des chemins configurés (config/minecraft_paths.json) ou chemins par défaut.
Extrait le port (server-port) pour chaque serveur et met à jour
config/services_config.json (fusionne les entrées Minecraft par nom), puis
lance tools/generate_services_json.py pour mettre à jour static/services_list.json.
"""

import os
import json
import sys
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATHS_CONFIG = os.path.join(BASE_DIR, 'config', 'minecraft_paths.json')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'services_config.json')
GEN_SCRIPT = os.path.join(BASE_DIR, 'tools', 'generate_services_json.py')

DEFAULT_PATHS = [
    os.path.join(BASE_DIR, 'servers'),
    '/srv/minecraft',
    '/opt/minecraft',
    '/var/minecraft',
    os.path.expanduser('~/minecraft_servers'),
    os.path.expanduser('~/servers'),
]


def load_paths():
    if os.path.exists(PATHS_CONFIG):
        try:
            with open(PATHS_CONFIG, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                return [os.path.expanduser(p) for p in data]
        except Exception:
            pass
    return DEFAULT_PATHS


def find_server_properties(paths):
    found = []
    for base in paths:
        if not base:
            continue
        # Support glob patterns
        for root in glob.glob(base):
            if not os.path.exists(root):
                continue
            # Walk and find server.properties files
            for dirpath, dirnames, filenames in os.walk(root):
                if 'server.properties' in filenames:
                    found.append(os.path.join(dirpath, 'server.properties'))
    return found


def parse_server_properties(path):
    port = None
    name = None
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip()
                if k == 'server-port' or k == 'server_port':
                    try:
                        port = int(v)
                    except Exception:
                        pass
                if k == 'motd' and not name:
                    # Try use motd as a fallback name, sanitize
                    name = v.strip().split('\n')[0][:50]
    except Exception:
        pass

    # If no name found, use parent directory name
    if not name:
        name = os.path.basename(os.path.dirname(path))
    if not port:
        port = 25565
    return name, port


def load_existing_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f) or []
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def write_config(data):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def main():
    paths = load_paths()
    props = find_server_properties(paths)
    discovered = []
    for p in props:
        name, port = parse_server_properties(p)
        entry = {'name': name, 'type': 'minecraft', 'port': port, 'domain': f"{name}.chimea.fr"}
        discovered.append(entry)

    if not discovered:
        print('No minecraft servers discovered')
        return

    existing = load_existing_config()
    # Keep non-minecraft entries, merge minecraft by name
    non_mc = [e for e in existing if not (isinstance(e, dict) and e.get('type') == 'minecraft')]
    mc_by_name = {e.get('name'): e for e in existing if isinstance(e, dict) and e.get('type') == 'minecraft'}

    for d in discovered:
        name = d['name']
        mc_by_name[name] = {**mc_by_name.get(name, {}), **d}

    final = non_mc + list(mc_by_name.values())

    if write_config(final):
        print(f'Wrote {len(discovered)} minecraft entries to {CONFIG_PATH}')
        # Call generator to update static file
        try:
            if os.path.exists(GEN_SCRIPT):
                import subprocess
                subprocess.run([sys.executable, GEN_SCRIPT], check=False)
        except Exception:
            pass
    else:
        print('Failed to write config')


if __name__ == '__main__':
    main()
