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

        data.logs.forEach(log => {
            const logEntry = document.createElement('div');
            logEntry.textContent = log;
            consoleElement.appendChild(logEntry);
        });

        const playerList = document.getElementById('players-list');
        playerList.innerHTML = ''; // Clear existing list
        data.online_players.forEach(player => {
            const playerEntry = document.createElement('div');
            playerEntry.textContent = player;
            playerList.appendChild(playerEntry);
        });

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