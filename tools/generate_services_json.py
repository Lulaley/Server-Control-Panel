#!/usr/bin/env python3
"""
Génère un fichier JSON listant les services (minecraft, web, ssh, ...).
- Lit une configuration optionnelle dans ../config/services_config.json (liste d'objets).
- Écrit le résultat dans ../static/services_list.json avec les entrées rcon pour les services minecraft
  et ajoute systématiquement l'entrée SSH remote.chimea.fr.
"""

import os
import json
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # chemin vers flask-template
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'services_config.json')
OUTPUT_PATH = os.path.join(BASE_DIR, 'static', 'services_list.json')


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erreur en lisant la config {CONFIG_PATH}: {e}", file=sys.stderr)
    return None


def build_services(config=None):
    services = []
    if config and isinstance(config, list):
        for s in config:
            name = s.get('name') or s.get('service') or ''
            stype = s.get('type', 'generic')
            port = s.get('port')
            domain = s.get('domain') or (f"{name}.chimea.fr" if name else None)
            entry = {"name": name, "domain": domain, "port": port, "type": stype}
            if stype and stype.lower() == 'minecraft':
                entry['rcon_domain'] = f"{name}-rcon.chimea.fr"
            services.append(entry)
    else:
        # Exemple par défaut si aucune config fournie
        services = [
            {"name": "minecraft-1", "domain": "minecraft-1.chimea.fr", "port": 25565, "type": "minecraft", "rcon_domain": "minecraft-1-rcon.chimea.fr"},
            {"name": "web-1", "domain": "web-1.chimea.fr", "port": 8080, "type": "web"}
        ]

    # Ajoute l'entrée SSH remote.chimea.fr si elle n'existe pas
    ssh_entry = {"name": "remote", "domain": "remote.chimea.fr", "port": 22, "type": "ssh"}
    if not any(s.get('name') == 'remote' for s in services):
        services.append(ssh_entry)

    return services


def write_output(services, path=OUTPUT_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"services": services}
    # Serialize with sorted keys for stable comparison
    new_content = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)

    # Compare with existing file to éviter d'écraser si identique
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing = f.read()
            # Normaliser les deux contenus pour comparaison
            # On compare les JSON parsés pour être robustes aux différences de format
            existing_json = json.loads(existing) if existing.strip() else None
            new_json = json.loads(new_content)
            if existing_json == new_json:
                return path
        except Exception:
            # En cas d'erreur de lecture, on continue et on réécrit
            pass

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return path


def main():
    config = load_config()
    services = build_services(config)
    out = write_output(services)
    print(f"Wrote services JSON to {out}")


if __name__ == '__main__':
    main()
