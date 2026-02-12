#!/usr/bin/env python3
"""
Synchronise static/services_list.json -> config/services_config.json.
Le fichier de config généré contient une liste d'objets minimalistes (name,type,port,domain) et est écrit
seulement si le contenu diffère.
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_PATH = os.path.join(BASE_DIR, 'static', 'services_list.json')
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'services_config.json')


def load_static():
    if not os.path.exists(STATIC_PATH):
        return None
    try:
        with open(STATIC_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def build_config_from_static(static_json):
    services = static_json.get('services') if isinstance(static_json, dict) else None
    if not services:
        return []
    out = []
    for s in services:
        entry = {
            'name': s.get('name'),
            'type': s.get('type'),
            'port': s.get('port'),
            'domain': s.get('domain')
        }
        out.append(entry)
    return out


def write_config(config_list, path=CONFIG_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = config_list
    new_content = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)

    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                existing = f.read()
            existing_json = json.loads(existing) if existing.strip() else None
            new_json = json.loads(new_content)
            if existing_json == new_json:
                return path
        except Exception:
            pass

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return path


def main():
    static = load_static()
    if not static:
        print('No static/services_list.json found')
        return
    cfg = build_config_from_static(static)
    out = write_config(cfg)
    print(f'Wrote config to {out}')


if __name__ == '__main__':
    main()
