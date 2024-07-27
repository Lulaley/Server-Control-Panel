let currentFilterType = 'all'; // Default filter type
let selectedButton = document.getElementById('all-tag-button');  // Par défaut, le bouton "Show All" est sélectionné
function updateFilterType(filterType) {
    localStorage.setItem('selectedFilterType', filterType);
    fetchMinecraftLogFiltered(filterType);

    // Supprimer la classe 'selected' du bouton précédemment sélectionné
    selectedButton.classList.remove('selected');

    // Ajouter la classe 'selected' au bouton actuellement sélectionné
    const buttonId = filterType + '-tag-button';
    selectedButton = document.getElementById(buttonId);
    selectedButton.classList.add('selected');
}

function highlightSelectedButton(filterType) {
    const buttons = document.querySelectorAll('#filter-buttons button');
    buttons.forEach(button => {
        if (button.getAttribute('data-filter') === filterType) {
            button.classList.add('selected');
        } else {
            button.classList.remove('selected');
        }
    });
}

async function fetchMinecraftLogFiltered() {
    if (document.getElementById('folder-select').value === "") {
        return;
    }

    // Retrieve the filter type from local storage or use a default
    let filterType = localStorage.getItem('selectedFilterType') || 'all';
    highlightSelectedButton(filterType);
    
    try {
        let data;
        try {
            const response = await fetch('/minecraft_log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ log_path: log_path, filter_type: filterType })
            });

            if (!response.ok) {
                // Gère les réponses HTTP non réussies
                throw new Error('La réponse du serveur n\'est pas OK. Statut: ' + response.status);
            }

            try {
                data = await response.json();
            } catch (jsonError) {
                console.error('Erreur lors de la conversion de la réponse en JSON:', jsonError);
                throw jsonError; // Optionnel, selon si vous voulez arrêter l'exécution ici
            }
        } catch (networkError) {
            console.error('Erreur réseau lors de la récupération des logs:', networkError);
        }

        const consoleElement = document.getElementById('console');
        consoleElement.innerHTML = ''; // Clear existing logs

        // Split the logs string into individual log entries
        try {
            let logEntries;
            if (data.logs) {
                logEntries = data.logs.split('\n').filter(entry => 
                    !entry.includes('Thread RCON Client ** started') && 
                    !entry.includes('Thread RCON Client ** shutting down')
                );
            } else {
                logEntries = data.logs;
            }
            logEntries.forEach(entry => {
                const span = document.createElement('span');
                span.textContent = entry;

                // Determine log level and apply CSS class
                if (entry.includes('/ERROR')) {
                    span.className = 'error-message';
                } else if (entry.includes('/WARN')) {
                    span.className = 'warning-message';
                } else if (entry.includes('<') || entry.includes('[Rcon]')) {
                    // This condition now also checks for entries containing [RCON]
                    span.className = 'discussion-message';
                } else if (entry.includes('/INFO')) {
                    span.className = 'info-message';
                } else {
                    // Default class for logs without a clear level, or you can add more conditions for other levels
                    span.className = 'any-message';
                }

                consoleElement.appendChild(span);
                consoleElement.appendChild(document.createElement('br')); // New line
            });
        } catch (processingError) {
            
            //console.info('Erreur lors du traitement des entrées de log:', processingError);
        }

        try {
            // Optionally, update the online players list if your API also returns this information            
            const playerList = document.getElementById('players-list');
            playerList.innerHTML = ''; // Clear existing list
            for (const player of data.online_players) {
                const div = document.createElement('div');
                div.textContent = player;

                const tellButton = document.createElement('button');
                tellButton.textContent = 'Tell';
                tellButton.className = 'modal';
                div.appendChild(tellButton);

                playerList.appendChild(div);
            }
        } catch (playerError) {
            console.info('Erreur lors de la récupération des joueurs:', playerError);
        }
        // Scroll to the bottom of the console
        consoleElement.scrollTop = consoleElement.scrollHeight;
    } catch (fetchError) {
        console.info('Erreur lors de la récupération des logs:', fetchError);
    }
}

// Call the fetchMinecraftLogFiltered function every 3800 milliseconds
setInterval(() => fetchMinecraftLogFiltered(), 1000);

document.addEventListener('DOMContentLoaded', function() {
    const filterType = localStorage.getItem('selectedFilterType') || 'all';
    highlightSelectedButton(filterType);
    fetchMinecraftLogFiltered(); // This will now use the filter type from local storage
});