document.getElementById('command-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const command = document.getElementById('command-input').value;

    try {
        const response = await fetch('/send_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `command=${encodeURIComponent(command)}`
        });

        const data = await response.json();

        if ('response' in data) {
            document.getElementById('console').innerText += '\n' + data.response;
            document.getElementById('command-error').innerText = '';
        } else if ('error' in data) {
            document.getElementById('command-error').innerText = data.error;
        } else {
            document.getElementById('command-error').innerText = 'Unknown error';
        }
    } catch (error) {
        document.getElementById('command-error').innerText = 'Error sending command: ' + error;
    }

    document.getElementById('command-input').value = '';
});
