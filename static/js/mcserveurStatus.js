async function fetchServerStatus() {
    const selectedFolder = document.getElementById('folder-select').value;

    try {
        const response = await fetch('/server_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ folder: selectedFolder })
        });
        const data = await response.json();

        console.log("Minecraft server is running: ", data.is_running);
        return data.is_running;
    } catch (error) {
        console.error('Error fetching minecraft server status:', error);
        return false;
    }
}
