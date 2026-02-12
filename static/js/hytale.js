let currentHytale = null;
let lastLogs = null;
let lastHytaleStatus = null;
let lastPlayers = null;

// Variables pour la gestion intelligente du polling
let statusCheckInterval = 5000;
let unchangedCount = 0;
let maxUnchangedBeforeSlowdown = 3;
let slowInterval = 3600000;
let normalInterval = 5000;
let statusCheckTimer = null;

// Récupère la liste des hytales
(function(){
  const sel = document.getElementById('hytale-select');
  if(!sel) return;
  fetch('/api/hytales/list')
      .then(res => res.json().catch(() => ({hytales: []})))
      .then(data => {
          (data.hytales || []).forEach(s => {
              const opt = document.createElement('option');
              opt.value = s;
              opt.textContent = s;
              sel.appendChild(opt);
          });
          if (sel.options.length > 0) {
              sel.value = sel.options[0].value;
              updateHytaleInfo(sel.value);
          }
      })
      .catch(()=>{});
  sel.addEventListener('change', function() {
      updateHytaleInfo(this.value);
  });
})();

function updateHytaleInfo(hytale) {
    currentHytale = hytale;
    // force refresh logs/players for the newly selected server
    lastLogs = null;
    lastPlayers = null; // reset because switched server
    resetPollingLogic();
    fetchHytaleStatus(hytale);
    // clear previous logs display immediately
    const logsElem = document.getElementById('hytale-logs');
    if (logsElem) logsElem.textContent = 'Chargement des logs...';
    fetchHytaleLogs();
}

function resetPollingLogic() {
    unchangedCount = 0;
    statusCheckInterval = normalInterval;
    lastHytaleStatus = null;
    if (statusCheckTimer) {
        clearInterval(statusCheckTimer);
        statusCheckTimer = null;
    }
    startStatusPolling();
}

function startStatusPolling() {
    if (statusCheckTimer) {
        clearInterval(statusCheckTimer);
    }
    statusCheckTimer = setInterval(() => {
        if (currentHytale) {
            fetchHytaleStatus(currentHytale);
        }
    }, statusCheckInterval);
}

let CURRENT_ROLE = null;
fetch('/api/whoami').then(r => {
  if (r.ok) return r.json();
  throw new Error('no user');
}).then(j => {
  CURRENT_ROLE = j.role;
}).catch(()=>{ CURRENT_ROLE = null; });

function fetchHytaleStatus(hytale) {
    const statusElem = document.getElementById('hytale-status');
    if(!statusElem) return;
    const url = `/api/hytales/status/${encodeURIComponent(hytale)}`;
    fetch(url)
        .then(res => res.json().catch(() => ({})))
        .then(data => {
            if (data.status === lastHytaleStatus) {
                unchangedCount++;
                if (unchangedCount >= maxUnchangedBeforeSlowdown && statusCheckInterval !== slowInterval) {
                    statusCheckInterval = slowInterval;
                    startStatusPolling();
                }
            } else {
                unchangedCount = 0;
                lastHytaleStatus = data.status;
                if (statusCheckInterval !== normalInterval) {
                    statusCheckInterval = normalInterval;
                    startStatusPolling();
                }
            }
            if (data.status === 'active') {
                statusElem.textContent = '🟢 En ligne';
                statusElem.style.color = '#4caf50';
            } else if (data.status === 'inactive' || data.status === 'failed' || data.status === 'dead') {
                statusElem.textContent = '🔴 Hors ligne';
                statusElem.style.color = '#f44336';
            } else {
                statusElem.textContent = '⚪ Inconnu';
                statusElem.style.color = '#888';
            }

            // toggle control buttons based on status and permissions
            const controls = document.getElementById('hytale-controls');
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');
            const btnRestart = document.getElementById('btn-restart');
            if (controls) {
                if (data.can_control === false) {
                    controls.style.display = 'none';
                } else {
                    controls.style.display = 'inline-block';
                }
            }
            if (btnStart && btnStop && btnRestart) {
                if (data.status === 'active') {
                    btnStart.style.display = 'none';
                    btnStop.style.display = 'inline-block';
                    btnRestart.style.display = 'inline-block';
                    btnStart.disabled = true;
                    btnStop.disabled = false;
                    btnRestart.disabled = false;
                } else if (data.status === 'inactive' || data.status === 'failed' || data.status === 'dead') {
                    btnStart.style.display = 'inline-block';
                    btnStop.style.display = 'none';
                    btnRestart.style.display = 'inline-block';
                    btnStart.disabled = false;
                    btnStop.disabled = true;
                    btnRestart.disabled = true;
                } else {
                    btnStart.style.display = 'inline-block';
                    btnStop.style.display = 'none';
                    btnRestart.style.display = 'none';
                    btnStart.disabled = false;
                    btnRestart.disabled = true;
                }
            }
        })
        .catch(() => {
            statusElem.textContent = '⚪ Erreur récupération status';
            statusElem.style.color = '#888';
            if (statusCheckInterval !== normalInterval) {
                statusCheckInterval = normalInterval;
                unchangedCount = 0;
                startStatusPolling();
            }
        });
}

function controlHytale(action) {
    if (!currentHytale) return;
    if (!(CURRENT_ROLE === 'admin' || CURRENT_ROLE === 'manager')) {
        alert('Action interdite: vous n\'avez pas les droits');
        return;
    }
    fetch(`/api/hytales/control/${encodeURIComponent(currentHytale)}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action})
    })
    .then(res => res.json().catch(() => ({})))
    .then(data => {
        if (data && data.success) {
            alert(`Action ${action} réussie`);
            resetPollingLogic();
            fetchHytaleStatus(currentHytale);
        } else {
            alert('Erreur: ' + (data && data.error ? data.error : 'Action impossible'));
        }
    })
    .catch(() => {
        alert('Erreur réseau');
    });
}

function fetchHytaleLogs() {
    if (!currentHytale) return;
    const logsElem = document.getElementById('hytale-logs');
    const playersContainer = document.getElementById('hytale-players');
    if (!logsElem && !playersContainer) return;

    const url = `/api/hytales/logs/${encodeURIComponent(currentHytale)}?t=${Date.now()}`;
    fetch(url)
        .then(res => res.json().catch(() => ({})))
        .then(data => {
            const logs = (typeof data.logs === 'string') ? data.logs : (data.logs ? String(data.logs) : 'Aucun log trouvé.');
            if (logs !== lastLogs) {
                if (logsElem) {
                    logsElem.textContent = logs;
                    logsElem.scrollTop = logsElem.scrollHeight;
                }
                lastLogs = logs;
            }
            // players handling: prefer authoritative full list if provided
            if (playersContainer) {
                if (Array.isArray(data.players)) {
                    // server provided full current players list -> use it
                    lastPlayers = data.players.slice();
                } else {
                    // fallback to delta merging if server returns recent_adds/recent_removes
                    const recentAdds = Array.isArray(data.recent_adds) ? data.recent_adds : [];
                    const recentRemoves = Array.isArray(data.recent_removes) ? data.recent_removes : [];
                    if (lastPlayers === null) {
                        if (recentAdds.length > 0) {
                            lastPlayers = Array.from(new Set(recentAdds));
                        } else {
                            lastPlayers = [];
                        }
                    } else {
                        recentAdds.forEach(p => { if (!lastPlayers.includes(p)) lastPlayers.push(p); });
                        recentRemoves.forEach(p => {
                            const idx = lastPlayers.indexOf(p);
                            if (idx !== -1) lastPlayers.splice(idx, 1);
                        });
                    }
                }

                // render playersContainer based on lastPlayers
                const players = lastPlayers || [];
                let html = '<h3>Joueurs connectés</h3>';
                if (players.length === 0) {
                    html += '<div class="no-players">Aucun joueur</div>';
                } else {
                    html += '<ul class="player-list">';
                    players.forEach(p => { html += `<li>${p}</li>`; });
                    html += '</ul>';
                }
                playersContainer.innerHTML = html;
            }
        })
        .catch(() => {
            if (logsElem) logsElem.textContent = 'Erreur lors de la récupération des logs.';
        });
}

document.addEventListener('DOMContentLoaded', function() {
    startStatusPolling();
    setInterval(() => {
        fetchHytaleLogs();
    }, 5000);
});
