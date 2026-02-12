let currentSelectedServer = null;
let currentPlayerForAction = null;

// Chargement initial
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page Minecraft chargée, initialisation...');
    loadServers();
    setupRconForm();
});

// Charger la liste des serveurs
function loadServers() {
    console.log('Chargement des serveurs...');
    fetch('/api/minecraft/servers')
        .then(response => {
            console.log('Réponse serveurs reçue:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Données serveurs:', data);
            const serverSelect = document.getElementById('server-select');
            if (!serverSelect) {
                console.error('Élément server-select non trouvé!');
                return;
            }
            
            serverSelect.innerHTML = '<option value="">-- Choisir un serveur --</option>';
            
            if (data.servers && data.servers.length > 0) {
                data.servers.forEach(server => {
                    const option = document.createElement('option');
                    option.value = server;
                    option.textContent = server;
                    serverSelect.appendChild(option);
                    console.log('Serveur ajouté:', server);
                });
            } else {
                console.log('Aucun serveur trouvé');
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'Aucun serveur disponible';
                serverSelect.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des serveurs:', error);
            const serverSelect = document.getElementById('server-select');
            if (serverSelect) {
                serverSelect.innerHTML = '<option value="">Erreur de chargement</option>';
            }
        });
}

// Gestion du changement de serveur
document.addEventListener('change', function(event) {
    if (event.target.id === 'server-select') {
        const selectedServer = event.target.value;
        console.log('Serveur sélectionné:', selectedServer);
        
        if (selectedServer) {
            currentSelectedServer = selectedServer;
            updateServerStatus(selectedServer);
            loadServerLogs(selectedServer);
            loadServerPlayers(selectedServer);
            setupBluemapButton(selectedServer);
        } else {
            currentSelectedServer = null;
            // Réinitialiser les affichages
            const statusEl = document.getElementById('server-status');
            const logsEl = document.getElementById('server-logs');
            const playersEl = document.getElementById('players-list');
            const noPlayersEl = document.getElementById('no-players');
            const bluemapEl = document.getElementById('btn-bluemap');
            
            if (statusEl) statusEl.textContent = '';
            if (logsEl) logsEl.textContent = '';
            if (playersEl) playersEl.innerHTML = '';
            if (noPlayersEl) noPlayersEl.style.display = 'block';
            if (bluemapEl) bluemapEl.style.display = 'none';
        }
    }
});

// Mettre à jour le statut du serveur
function updateServerStatus(server) {
    fetch(`/api/minecraft/status/${server}`)
        .then(response => response.json())
        .then(data => {
            // status dot + text (template: server-status-dot, server-status-text)
            const statusDot = document.getElementById('server-status-dot');
            const statusTextEl = document.getElementById('server-status-text');
            const statusContainer = document.getElementById('server-status'); // container .server-status
            if (statusDot && statusTextEl) {
                // reset dot classes
                statusDot.className = 'status-dot';
                if (data.status === 'running') {
                    statusDot.classList.add('online');
                    statusTextEl.textContent = 'En ligne';
                } else if (data.status === 'stopped') {
                    statusDot.classList.add('offline');
                    statusTextEl.textContent = 'Hors ligne';
                } else {
                    statusDot.classList.add('unknown');
                    statusTextEl.textContent = 'État inconnu';
                }
            }
            // apply a state class to the container so CSS can style both dot and text reliably
            if (statusContainer) {
                statusContainer.className = 'server-status';
                if (data.status === 'running') statusContainer.classList.add('status-online');
                else if (data.status === 'stopped') statusContainer.classList.add('status-offline');
                else statusContainer.classList.add('status-unknown');
            }

            // show/hide controls container (template id: server-controls)
            const controls = document.getElementById('server-controls');
            const btnStart = document.getElementById('mc-btn-start');
            const btnStop = document.getElementById('mc-btn-stop');
            const btnRestart = document.getElementById('mc-btn-restart');

            if (controls) {
                controls.style.display = (data.can_control === false) ? 'none' : 'inline-block';
            }

            // Update buttons visibility & disabled state based on normalized status
            if (btnStart && btnStop && btnRestart) {
                if (data.status === 'running') {
                    btnStart.style.display = 'none';
                    btnStop.style.display = 'inline-block';
                    btnRestart.style.display = 'inline-block';
                    btnStart.disabled = true;
                    btnStop.disabled = false;
                    btnRestart.disabled = false;
                } else if (data.status === 'stopped') {
                    btnStart.style.display = 'inline-block';
                    btnStop.style.display = 'none';
                    btnRestart.style.display = 'inline-block';
                    btnStart.disabled = false;
                    btnStop.disabled = true;
                    btnRestart.disabled = false;
                } else {
                    // unknown
                    btnStart.style.display = 'inline-block';
                    btnStop.style.display = 'inline-block';
                    btnRestart.style.display = 'inline-block';
                    btnStart.disabled = false;
                    btnStop.disabled = false;
                    btnRestart.disabled = false;
                }
            }
        })
        .catch(error => {
            console.error('Erreur lors de la vérification du statut:', error);
            const statusTextEl = document.getElementById('server-status-text');
            const statusContainer = document.getElementById('server-status');
            if (statusTextEl) statusTextEl.textContent = '❓ Erreur';
            const statusDot = document.getElementById('server-status-dot');
            if (statusDot) {
                statusDot.className = 'status-dot unknown';
            }
            if (statusContainer) {
                statusContainer.className = 'server-status status-unknown';
            }
        });
}

// Charger les logs du serveur
function loadServerLogs(server) {
    fetch(`/api/minecraft/logs/${server}`)
        .then(response => response.json())
        .then(data => {
            const logsElement = document.getElementById('server-logs');
            if (logsElement) {
                logsElement.textContent = data.logs || 'Aucun log disponible';
                logsElement.scrollTop = logsElement.scrollHeight;
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des logs:', error);
        });
}

// Charger la liste des joueurs connectés
function loadServerPlayers(server) {
    fetch(`/api/minecraft/players/${server}`)
        .then(response => response.json())
        .then(data => {
            const playersList = document.getElementById('players-list');
            const noPlayersMsg = document.getElementById('no-players');
            
            if (!playersList || !noPlayersMsg) return;
            
            playersList.innerHTML = '';
            
            if (data.players && data.players.length > 0) {
                noPlayersMsg.style.display = 'none';
                data.players.forEach(player => {
                    const li = document.createElement('li');
                    li.className = 'player-item';
                    
                    const playerName = document.createElement('span');
                    playerName.className = 'player-name';
                    playerName.textContent = player;
                    
                    const actions = document.createElement('div');
                    actions.className = 'player-actions';
                    
                    // Bouton Message (disponible pour tous)
                    const messageBtn = document.createElement('button');
                    messageBtn.textContent = 'Message';
                    messageBtn.className = 'player-action-btn btn-message';
                    messageBtn.onclick = () => openMessageModal(player);
                    actions.appendChild(messageBtn);
                    
                    // Vérifier le rôle de l'utilisateur pour les boutons admin
                    fetch('/api/whoami')
                        .then(res => res.json())
                        .then(userData => {
                            if (userData.role === 'admin') {
                                const kickBtn = document.createElement('button');
                                kickBtn.textContent = 'Kick';
                                kickBtn.className = 'player-action-btn btn-kick';
                                kickBtn.onclick = () => openKickModal(player);
                                
                                const banBtn = document.createElement('button');
                                banBtn.textContent = 'Ban';
                                banBtn.className = 'player-action-btn btn-ban';
                                banBtn.onclick = () => openBanModal(player);
                                
                                actions.appendChild(kickBtn);
                                actions.appendChild(banBtn);
                            }
                        });
                    
                    li.appendChild(playerName);
                    li.appendChild(actions);
                    playersList.appendChild(li);
                });
            } else {
                noPlayersMsg.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des joueurs:', error);
        });
}

// Contrôle du serveur (start/stop/restart)
function controlServer(action) {
    if (!currentSelectedServer) {
        alert('Aucun serveur sélectionné');
        return;
    }
    
    fetch(`/api/minecraft/control/${currentSelectedServer}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: action })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Action "${action}" exécutée avec succès`);
            // small delay to allow systemd to change status
            setTimeout(() => updateServerStatus(currentSelectedServer), 1500);
        } else {
            alert(`Erreur: ${data.error}`);
        }
    })
    .catch(error => {
        alert(`Erreur de connexion: ${error.message}`);
    });
}
// alias pour compatibilité avec les onclick du template
function controlMinecraft(action) {
    controlServer(action);
}

// Configuration du formulaire RCON
function setupRconForm() {
    const rconForm = document.getElementById('rcon-form');
    if (rconForm) {
        rconForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Empêcher le rafraîchissement de la page
            
            const commandInput = document.getElementById('rcon-command');
            const responseElement = document.getElementById('rcon-response');
            
            if (!commandInput || !responseElement) {
                console.error('Éléments RCON non trouvés');
                return;
            }
            
            if (!currentSelectedServer) {
                responseElement.textContent = 'Erreur: Aucun serveur sélectionné';
                responseElement.style.color = '#dc3545';
                return;
            }
            
            const command = commandInput.value.trim();
            if (!command) {
                responseElement.textContent = 'Erreur: Commande vide';
                responseElement.style.color = '#dc3545';
                return;
            }
            
            // Afficher un indicateur de chargement
            responseElement.textContent = 'Envoi de la commande...';
            responseElement.style.color = '#666';
            
            // Envoyer la commande via AJAX
            fetch(`/api/minecraft/command/${currentSelectedServer}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: command })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    responseElement.textContent = data.response || 'Commande exécutée avec succès';
                    responseElement.style.color = '#28a745';
                    commandInput.value = ''; // Vider le champ de commande
                    
                    // Recharger les joueurs si c'est une commande qui peut affecter la liste
                    if (command.includes('kick') || command.includes('ban') || command.includes('op')) {
                        setTimeout(() => loadServerPlayers(currentSelectedServer), 1000);
                    }
                } else {
                    responseElement.textContent = `Erreur: ${data.error}`;
                    responseElement.style.color = '#dc3545';
                }
            })
            .catch(error => {
                responseElement.textContent = `Erreur de connexion: ${error.message}`;
                responseElement.style.color = '#dc3545';
                console.error('Erreur RCON:', error);
            });
        });
    }
}

// Configuration du bouton Bluemap
function setupBluemapButton(server) {
    const bluemapBtn = document.getElementById('btn-bluemap');
    if (bluemapBtn) {
        const bluemapPort = 8100; // Port par défaut Bluemap
        bluemapBtn.style.display = 'inline-block';
        bluemapBtn.onclick = function() {
            const bluemapUrl = `http://${window.location.hostname}:${bluemapPort}`;
            window.open(bluemapUrl, '_blank');
        };
    }
}

// Modals pour actions sur les joueurs
function openMessageModal(playerName) {
    currentPlayerForAction = playerName;
    const playerNameEl = document.getElementById('message-player-name');
    const messageTextEl = document.getElementById('message-text');
    const modalEl = document.getElementById('message-modal');
    
    if (playerNameEl) playerNameEl.textContent = playerName;
    if (messageTextEl) messageTextEl.value = '';
    if (modalEl) modalEl.style.display = 'block';
}

function openKickModal(playerName) {
    currentPlayerForAction = playerName;
    const playerNameEl = document.getElementById('kick-player-name');
    const kickReasonEl = document.getElementById('kick-reason');
    const modalEl = document.getElementById('kick-modal');
    
    if (playerNameEl) playerNameEl.textContent = playerName;
    if (kickReasonEl) kickReasonEl.value = '';
    if (modalEl) modalEl.style.display = 'block';
}

function openBanModal(playerName) {
    currentPlayerForAction = playerName;
    const playerNameEl = document.getElementById('ban-player-name');
    const banReasonEl = document.getElementById('ban-reason');
    const modalEl = document.getElementById('ban-modal');
    
    if (playerNameEl) playerNameEl.textContent = playerName;
    if (banReasonEl) banReasonEl.value = '';
    if (modalEl) modalEl.style.display = 'block';
}

function closeModal(modalId) {
    const modalEl = document.getElementById(modalId);
    if (modalEl) modalEl.style.display = 'none';
    currentPlayerForAction = null;
}

// Actions sur les joueurs
function sendPlayerMessage() {
    const messageEl = document.getElementById('message-text');
    const message = messageEl ? messageEl.value.trim() : '';
    
    if (!message || !currentPlayerForAction) return;
    
    const command = `tell ${currentPlayerForAction} ${message}`;
    sendRconCommand(command, () => {
        closeModal('message-modal');
    });
}

function kickPlayer() {
    const reasonEl = document.getElementById('kick-reason');
    const reason = reasonEl ? reasonEl.value.trim() : '';
    
    if (!currentPlayerForAction) return;
    
    const command = reason ? 
        `kick ${currentPlayerForAction} ${reason}` : 
        `kick ${currentPlayerForAction}`;
    
    sendRconCommand(command, () => {
        closeModal('kick-modal');
        setTimeout(() => loadServerPlayers(currentSelectedServer), 1000);
    });
}

function banPlayer() {
    const reasonEl = document.getElementById('ban-reason');
    const reason = reasonEl ? reasonEl.value.trim() : '';
    
    if (!currentPlayerForAction) return;
    
    const command = reason ? 
        `ban ${currentPlayerForAction} ${reason}` : 
        `ban ${currentPlayerForAction}`;
    
    sendRconCommand(command, () => {
        closeModal('ban-modal');
        setTimeout(() => loadServerPlayers(currentSelectedServer), 1000);
    });
}

// Fonction utilitaire pour envoyer des commandes RCON
function sendRconCommand(command, successCallback) {
    if (!currentSelectedServer) {
        alert('Aucun serveur sélectionné');
        return;
    }
    
    fetch(`/api/minecraft/command/${currentSelectedServer}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command: command })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (successCallback) successCallback();
            // Optionnel: afficher la réponse dans les logs RCON
            const rconResponse = document.getElementById('rcon-response');
            if (rconResponse) {
                rconResponse.textContent = data.response || 'Commande exécutée avec succès';
                rconResponse.style.color = '#28a745';
            }
        } else {
            alert(`Erreur: ${data.error}`);
        }
    })
    .catch(error => {
        alert(`Erreur de connexion: ${error.message}`);
        console.error('Erreur RCON:', error);
    });
}

// Fermer les modals en cliquant en dehors
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Auto-refresh des données (optionnel)
setInterval(() => {
    if (currentSelectedServer) {
        updateServerStatus(currentSelectedServer);
        loadServerPlayers(currentSelectedServer);
    }
}, 30000); // Refresh toutes les 30 secondes

// Fonction de debug pour diagnostiquer les problèmes
function debugMinecraft() {
    console.log('=== DEBUG MINECRAFT ===');
    console.log('currentSelectedServer:', currentSelectedServer);
    console.log('server-select element:', document.getElementById('server-select'));
    console.log('rcon-form element:', document.getElementById('rcon-form'));
    console.log('server-status element:', document.getElementById('server-status'));
    console.log('======================');
}

// Exposer la fonction debug globalement
window.debugMinecraft = debugMinecraft;
