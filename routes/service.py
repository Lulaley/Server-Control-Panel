import json
import re
import subprocess
from flask import request, jsonify

def init_get_services(app):
    def get_services():
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        services = {}
        services_list = []
        try:
            with open('services.json', 'r') as f:
                services_list = json.load(f)['services']
        except FileNotFoundError:
            return {'error': 'Le fichier services.json est introuvable', 'status': 'not_found'}
        except json.JSONDecodeError:
            return {'error': 'Erreur de décodage JSON dans services.json', 'status': 'error'}

        for service in services_list:
            process = subprocess.Popen(['systemctl', 'show', f'{service}.service'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if error:
                services[service] = {'status': 'not_found'}  # Service fichier n'existe pas
            else:
                output = output.decode('utf-8').strip().split('\n')
                status = None
                for line in output:
                    if line.startswith('ActiveState='):
                        status = line.split('=')[1]
                if status == 'inactive':
                    services[service] = {'status': 'inactive'}  # Service existe mais est inactif
                elif status:
                    services[service] = {'status': 'active'}  # Service actif
                else:
                    services[service] = {'status': 'not_found'}  # Service fichier n'existe pas
        return services
    pass

def init_start_service_routes(app):
    @app.route('/start_service', methods=['POST'])
    def start_service():
        service = request.form.get('service')
        subprocess.run(['sudo', 'systemctl', 'start', service])
        return 'Service '+service+' started'
    pass

def init_stop_service_routes(app):
    @app.route('/stop_service', methods=['POST'])
    def stop_service():
        service = request.form.get('service')
        subprocess.run(['sudo', 'systemctl', 'stop', service])
        return 'Service '+service+' stopped'
    pass

def init_restart_service_routes(app):
    @app.route('/restart_service', methods=['POST'])
    def restart_service():
        service = request.form.get('service')
        subprocess.run(['sudo', 'systemctl', 'restart', service])
        return 'Service '+service+' restarted'
    pass

def init_delete_service_routes(app):
    @app.route('/delete_service', methods=['POST'])
    def delete_service():
        service = request.form.get('service')
        if not is_valid_name(service):
            return 'Invalid service name', 400

        # Vérifier si le service est inactif
        process = subprocess.Popen(['systemctl', 'is-active', f'{service}.service'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if output.decode('utf-8').strip() == 'inactive':
            # Supprimer le service du fichier JSON
            # Supprimer le service du fichier JSON
            try:
                with open('services.json', 'r') as f:
                    services = json.load(f)
            except FileNotFoundError:
                return 'Fichier services.json non trouvé', 500
            except json.JSONDecodeError:
                return 'Erreur de décodage JSON dans services.json', 500

            # Vérifier si le service existe
            if service in services['services']:
                services['services'].remove(service)  # Supprimer le service de la liste
                # Écrire les services mis à jour dans le fichier JSON
                with open('services.json', 'w') as f:
                    json.dump(services, f, indent=4)
                # Supprimer le service via systemctl
                subprocess.run(['sudo', 'systemctl', 'stop', service])
                subprocess.run(['sudo', 'systemctl', 'disable', service])
                subprocess.run(['systemctl', 'daemon-reload'], check=True)
                return f'Service {service} deleted successfully'
            else:
                return 'Service not found in JSON', 400
        else:
            return 'Service is not inactive or not found', 400
    pass
        
def is_valid_name(name):
    # Simple validation to ensure name is safe
    return re.match("^[a-zA-Z0-9_-]+$", name) is not None

def init_create_service_routes(app):
    @app.route('/create_service', methods=['POST'])
    def create_service():
        data = request.json
        service_name = data.get('serviceName')
        service_description = data.get('serviceDescription', 'No description provided')
        service_command = data.get('serviceCommand')

        # Validation
        if not service_name or not is_valid_name(service_name):
            return jsonify(error='Invalid service name'), 400
        if not service_command:
            return jsonify(error='Service command is required'), 400

        # Load existing services from JSON
        try:
            with open('services.json', 'r') as f:
                services = json.load(f)
        except FileNotFoundError:
            services = {"services": []}
        except json.JSONDecodeError:
            return jsonify(error='Erreur de décodage JSON dans services.json'), 500

        # Check if service already exists in JSON
        if service_name in services['services']:
            return jsonify(error='Service name already exists'), 400
        else:
            services['services'].append(service_name)

        # Write updated services to JSON
        with open('services.json', 'w') as f:
            json.dump(services, f, indent=4)

        service_file_path = f'/etc/systemd/system/{service_name}.service'
        service_content = f'[Unit]\nDescription={service_description}\n\n[Service]\nExecStart={service_command}\n'

        # Create or overwrite the service file
        try:
            with open(service_file_path, 'w') as f:
                f.write(service_content)
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', service_name], check=True)
            subprocess.run(['systemctl', 'start', service_name], check=True)
        except Exception as e:
            return jsonify(error=f'Failed to create service: {e}'), 500

        return jsonify(message='Service créé'), 200
    pass