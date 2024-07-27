let currentPlayer = '';

function showMessageBox(playerName) {
    currentPlayer = playerName;
    document.getElementById('message-box').style.display = 'block';
}

function closeMessageBox() {
    document.getElementById('message-box').style.display = 'none';
}

function sendMessage() {
    const message = document.getElementById('message-input').value;
    // Send message via Rcon
    sendRconCommand(`/tell ${currentPlayer} ${message}`);
    closeMessageBox();
}

function showKickBanBox(playerName) {
    currentPlayer = playerName;
    document.getElementById('kick-ban-box').style.display = 'block';
}

function closeKickBanBox() {
    document.getElementById('kick-ban-box').style.display = 'none';
}

function performAction() {
    const action = document.getElementById('action-select').value;
    const reason = document.getElementById('reason-input').value;
    // Send kick/ban command via Rcon
    sendRconCommand(`/${action} ${currentPlayer} ${reason}`);
    closeKickBanBox();
}

function sendRconCommand(command) {
    // Implement the function to send the command via Rcon
    console.log(`Sending Rcon command: ${command}`);
}