let currentFilterType = 'all'; // Default filter type
let selectedButton = document.getElementById('all-tag-button');  // Par défaut, le bouton "Show All" est sélectionné
let serverType = 'minecraft'; // Default server type

function updateFilterType(filterType) {
    currentFilterType = filterType;
    localStorage.setItem('selectedFilterType', filterType);
    highlightSelectedButton(filterType);
    fetchLogs();
}

function highlightSelectedButton(filterType) {
    if (selectedButton) {
        selectedButton.classList.remove('selected');
    }
    selectedButton = document.getElementById(`${filterType}-tag-button`);
    if (selectedButton) {
        selectedButton.classList.add('selected');
    }
}

async function fetchLogs() {
    try {
        let response;
        if (serverType === 'minecraft') {
            response = await fetch(`/minecraft_log`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filter_type: currentFilterType })
            });
        } else if (serverType === 'palworld') {
            response = await fetch('/palworld/logs');
        }

        if (!response.ok) {
            throw new Error(`La réponse du serveur n'est pas OK. Statut: ${response.status}`);
        }

        const data = await response.json();

        const consoleElement = document.getElementById('console');
        consoleElement.innerHTML = ''; // Clear existing logs

        try {
            const logEntries = data.logs.split('\n');
            logEntries.forEach(entry => {
                const span = document.createElement('span');
                span.textContent = entry;

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
            console.info('Erreur lors du traitement des entrées de log:', processingError);
        }

        try {
            // Optionally, update the online players list if your API also returns this information            
            const playerList = document.getElementById('players-list');
            playerList.innerHTML = ''; // Clear existing list
            for (const player of data.online_players) {
                const div = document.createElement('div');
                div.textContent = player;

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

// Call the fetchLogs function every 1000 milliseconds
setInterval(() => fetchLogs(), 1000);

document.addEventListener('DOMContentLoaded', function() {
    const filterType = localStorage.getItem('selectedFilterType') || 'all';
    highlightSelectedButton(filterType);
    fetchLogs(); // This will now use the filter type from local storage
});