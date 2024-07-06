import logging
import subprocess
from flask import  request, jsonify

def init_get_java_versions_routes(app):
    @app.route('/java_versions')
    def get_java_versions():
        try:
            result = subprocess.run(['update-java-alternatives', '-l'], stdout=subprocess.PIPE)
            output = result.stdout.decode().strip()

            # Diviser la sortie en lignes
            lines = output.split('\n')

            java_versions = []

            # Parcourir les lignes et extraire les informations de version et de chemin
            for line in lines:
                # Ignorer les lignes vides
                if not line:
                    continue

                # Diviser la ligne en éléments
                elements = line.split()

                # Extraire le chemin et la version
                path = elements[0]
                version_number = elements[0].split('-')[1]
                version = f"Java {version_number}"

                # Ajouter la version de Java et son chemin à la liste
                java_versions.append({'version': version, 'path': path})

            # Renvoie la liste des versions de Java installées avec leur chemin
            return jsonify(java_versions)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

def init_change_java_version_routes(app):
    @app.route('/change_java_version', methods=['POST'])
    def change_java_version():
        version = request.form.get('version')
        print(version)
        try:
            subprocess.check_call(['sudo', 'update-java-alternatives', '-s', version])
            return jsonify({'success': True})
        except subprocess.CalledProcessError as e:
            return jsonify({'success': False, 'error': str(e)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
