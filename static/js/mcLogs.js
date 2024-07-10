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
    const filterType = localStorage.getItem('selectedFilterType') || 'all';
    highlightSelectedButton(filterType);

    try {
        const response = await fetch('/minecraft_log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ log_path: log_path, filter_type: filterType })
        });
        const data = await response.json();

        const consoleElement = document.getElementById('console');
        consoleElement.innerHTML = ''; // Clear existing logs

        // Split the logs string into individual log entries
        const logEntries = data.logs.split('\n').filter(entry => 
            !entry.includes('Thread RCON Client ** started') && 
            !entry.includes('Thread RCON Client ** shutting down')
        );
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

        // Optionally, update the online players list if your API also returns this information            
        const playerList = document.getElementById('players-list');
        playerList.innerHTML = ''; // Clear existing list
        for (const player of data.online_players) {
            const li = document.createElement('li');
            li.textContent = player;
            playerList.appendChild(li);
        }

        // Scroll to the bottom of the console
        consoleElement.scrollTop = consoleElement.scrollHeight;
    } catch (error) {
        console.error('Error fetching Minecraft log:', error);
    }
}

// Call the fetchMinecraftLogFiltered function every 3800 milliseconds
setInterval(() => fetchMinecraftLogFiltered(), 1000);

document.addEventListener('DOMContentLoaded', function() {
    const filterType = localStorage.getItem('selectedFilterType') || 'all';
    highlightSelectedButton(filterType);
    fetchMinecraftLogFiltered(); // This will now use the filter type from local storage
});