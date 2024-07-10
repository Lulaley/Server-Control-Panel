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
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Erreur lors de la conversion de la réponse en JSON:', jsonError);
            throw jsonError; // Optionnel, selon si vous voulez arrêter l'exécution ici
        }

        const consoleElement = document.getElementById('console');
        consoleElement.innerHTML = ''; // Clear existing logs

        try {
            const logEntries = data.logs.split('\n').filter(entry => 
                !entry.includes('Thread RCON Client ** started') && 
                !entry.includes('Thread RCON Client ** shutting down')
            );
            logEntries.forEach(entry => {
                // Votre code pour traiter chaque entrée de log
            });
        } catch (processingError) {
            console.error('Erreur lors du traitement des entrées de log:', processingError);
        }
    } catch (fetchError) {
        console.error('Erreur lors de la récupération des logs:', fetchError);
    }
}

// Call the fetchMinecraftLogFiltered function every 3800 milliseconds
setInterval(() => fetchMinecraftLogFiltered(), 1000);

document.addEventListener('DOMContentLoaded', function() {
    const filterType = localStorage.getItem('selectedFilterType') || 'all';
    highlightSelectedButton(filterType);
    fetchMinecraftLogFiltered(); // This will now use the filter type from local storage
});