# Server-Control-Panel

Server-Control-Panel est un site permettant de monitorer une machine de serveurs.
Il permet de visualiser les métriques CPU, RAM, disque, réseau et threads CPU,
de visionner et contrôler différents services de jeux, avec une gestion de comptes
utilisateurs et des configurations individuelles.

## Fonctionnalités

- Monitoring de la machine hôte (CPU, RAM, disque, réseau, threads CPU)
- Visualisation et contrôle des services de jeux
- Gestion des comptes utilisateurs
- Paramétrage individuel par utilisateur

## Stack technique

- Backend Python avec Flask
- Frontend HTML/CSS/JavaScript
- Configuration via fichiers JSON

## Lancer le projet en local

1. Cloner le dépôt puis ouvrir le dossier dans VS Code.
2. Créer et activer un environnement virtuel Python.
3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. (Optionnel) Installer les dépendances de développement :

```bash
pip install -r dev-requirements.txt
```

5. Lancer l'application :

```bash
python controlWeb.py
```

## Notes de configuration

- Les fichiers sensibles dans `config/` (comptes, reset, mail, etc.) ne doivent pas être commit.
- Utiliser `config/services_config.example.json` comme base pour la configuration locale.
