import re
import subprocess
import psutil
from flask import jsonify

def init_system_info_routes(app):
    @app.route('/system_info')
    def system_info():
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent

        try:
            try:
                java_version_output = subprocess.check_output(['java', '--version'], stderr=subprocess.STDOUT)
                java_version_match = re.search(r'openjdk (\d+\.\d+\.\d+)', java_version_output.decode('utf-8'))
            except:
                java_version_output = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
                java_version_match = re.search(r'openjdk version "(\d+\.\d+\.\d+_\d+)"', java_version_output.decode('utf-8'))
            java_version = java_version_match.group(1) if java_version_match else "Unknown"
        except Exception as e:
            java_version = str(e)

        total_ram = psutil.virtual_memory().total
        total_disk = psutil.disk_usage('/').total
        current_ram_used = psutil.virtual_memory().used
        current_disk_used = psutil.disk_usage('/').used

        return jsonify({
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'java_version': java_version,
            'total_ram': total_ram,
            'total_disk': total_disk,
            'current_ram_used': current_ram_used,
            'current_disk_used': current_disk_used
        })