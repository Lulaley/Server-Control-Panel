async function fetchFolders() {
    try {
        const response = await fetch('/folders');
        const data = await response.json();

        const folderSelect = document.getElementById('folder-select');

        data.folders.forEach(folder => {
            const option = document.createElement('option');
            option.value = folder;
            option.textContent = folder;
            folderSelect.appendChild(option);
        });

        // Get the selected service from cookies after the page reloads
        const serveurSelectIndex = getCookie('serveurSelectIndex');

        if (serveurSelectIndex !== "") {
            // Select the service
            const selectServeur = document.getElementById('folder-select');
            selectServeur.selectedIndex = Number(serveurSelectIndex);
        }

        // Get the path log from cookies after the page reloads
        const logPath = getCookie('logPath');

        if (logPath !== "") {
            log_path = logPath;
        }
    } catch (error) {
        console.error('Error fetching folders:', error);
    }
}
fetchFolders();
document.getElementById('folder-select').addEventListener('change', function(event) {
    const selectedFolder = event.target.value;
    log_path = `/home/chimea/Bureau/${selectedFolder}/logs`;
    console.log(`Log path changed to: ${log_path}`);
    fetchMinecraftLogFiltered('all');
});
