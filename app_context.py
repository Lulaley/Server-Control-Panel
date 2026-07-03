from flask import session
import psutil
from app_utils import _safe_url_for, _get_avatar_url

# Context processors

def inject_user():
    username = session.get('user')
    return {
        'current_user': username,
        'current_role': session.get('role'),
        'is_admin': session.get('role') == 'admin',
        'is_manager': session.get('role') == 'manager',
        'can_control_services': session.get('role') in ('admin', 'manager'),
        'safe_url_for': _safe_url_for,
        'url_for': _safe_url_for,
        'avatar_url': _get_avatar_url(username)
    }

def inject_machine_info():
    try:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        machine_info = {
            "cpu_percent": round(cpu, 1),
            "ram_percent": round(mem.percent, 1),
            "ram_used": f"{mem.used / (1024 ** 3):.2f} GB",
            "ram_total": f"{mem.total / (1024 ** 3):.2f} GB",
            "disk_percent": round(disk.percent, 1),
            "disk_used": f"{disk.used / (1024 ** 3):.2f} GB",
            "disk_total": f"{disk.total / (1024 ** 3):.2f} GB"
        }
    except Exception:
        machine_info = None
    return {"machine_info": machine_info}
