let currentSatisfactory = null;
let lastLogs = null;
let lastSatisfactoryStatus = null;

// Variables pour la gestion intelligente du polling
let statusCheckInterval = 5000; // 5 secondes par défaut
let unchangedCount = 0;
let maxUnchangedBeforeSlowdown = 3;
let slowInterval = 3600000; // 1 heure en millisecondes
let normalInterval = 5000; // 5 secondes
let statusCheckTimer = null;

// Récupère la liste des satisfactorys
(function(){
  const sel = document.getElementById('satisfactory-select');
  if(!sel) return;
  fetch('/api/satisfactorys/list')
      .then(res => res.json())
      .then(data => {
          data.satisfactorys.forEach(s => {
              const opt = document.createElement('option');
              opt.value = s;
              opt.textContent = s;
              sel.appendChild(opt);
          });
          if (data.satisfactorys.length > 0) {
              sel.value = data.satisfactorys[0];
              updateSatisfactoryInfo(data.satisfactorys[0]);
          }
      })
      .catch(()=>{});
  sel.addEventListener('change', function() {
      updateSatisfactoryInfo(this.value);
  });
})();

function updateSatisfactoryInfo(satisfactory) {
    currentSatisfactory = satisfactory;
    // Reset polling logic when satisfactory changes
    resetPollingLogic();
    fetchSatisfactoryStatus(satisfactory);
    fetchSatisfactoryLogs();
}

function resetPollingLogic() {
    unchangedCount = 0;
    statusCheckInterval = normalInterval;
    lastSatisfactoryStatus = null;
    
    // Clear existing timer and start fresh
    if (statusCheckTimer) {
        clearInterval(statusCheckTimer);
    }
    startStatusPolling();
}

function startStatusPolling() {
    if (statusCheckTimer) {
        clearInterval(statusCheckTimer);
    }
    
    statusCheckTimer = setInterval(() => {
        if (currentSatisfactory) {
            fetchSatisfactoryStatus(currentSatisfactory);
        }
    }, statusCheckInterval);
    
    console.log(`Status polling started with interval: ${statusCheckInterval}ms`);
}

// NEW: role-aware UI
let CURRENT_ROLE = null;
fetch('/api/whoami').then(r => {
  if (r.ok) return r.json();
  throw new Error('no user');
}).then(j => {
  CURRENT_ROLE = j.role;
}).catch(()=>{ CURRENT_ROLE = null; });

function fetchSatisfactoryStatus(satisfactory) {
    console.log(`DEBUG: fetchSatisfactoryStatus appelé pour: ${satisfactory}`);
    const statusElem = document.getElementById('satisfactory-status');
    const controlsElem = document.getElementById('satisfactory-controls');
    if(!statusElem) {
        console.log('DEBUG: statusElem non trouvé');
        return;
    }
    
    const url = `/api/satisfactorys/status/${satisfactory}`;
    console.log(`DEBUG: URL appelée: ${url}`);
    
    fetch(url)
        .then(res => {
            console.log(`DEBUG: Response status: ${res.status}`);
            console.log(`DEBUG: Response ok: ${res.ok}`);
            return res.json();
        })
        .then(data => {
            console.log('DEBUG: Data reçue:', data);
            
            // Check if status has changed
            if (data.status === lastSatisfactoryStatus) {
                unchangedCount++;
                console.log(`Status unchanged (${unchangedCount}/${maxUnchangedBeforeSlowdown}): ${data.status}`);
                
                // If status hasn't changed for 3 times, switch to hourly polling
                if (unchangedCount >= maxUnchangedBeforeSlowdown && statusCheckInterval !== slowInterval) {
                    statusCheckInterval = slowInterval;
                    console.log('Switching to slow polling (1 hour interval)');
                    startStatusPolling();
                }
            } else {
                // Status changed, reset to normal polling
                if (lastSatisfactoryStatus !== null) { // Don't log on first load
                    console.log(`Status changed from ${lastSatisfactoryStatus} to ${data.status}`);
                }
                unchangedCount = 0;
                lastSatisfactoryStatus = data.status;
                
                if (statusCheckInterval !== normalInterval) {
                    statusCheckInterval = normalInterval;
                    console.log('Switching back to normal polling (5 second interval)');
                    startStatusPolling();
                }
            }
            
            // Update UI based on status
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
            
            // toggle controls based on status and permissions
            const controls = document.getElementById('satisfactory-controls');
            const btnStart = document.getElementById('sf-btn-start');
            const btnStop = document.getElementById('sf-btn-stop');
            const btnRestart = document.getElementById('sf-btn-restart');
            if (controls) {
                controls.style.display = (data.can_control === false) ? 'none' : 'inline-block';
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
        .catch((error) => {
            console.error('DEBUG: Error fetching satisfactory status:', error);
            statusElem.textContent = '⚪ Erreur récupération status';
            statusElem.style.color = '#888';
            
            // Reset to normal polling on error
            if (statusCheckInterval !== normalInterval) {
                statusCheckInterval = normalInterval;
                unchangedCount = 0;
                startStatusPolling();
            }
        });
}

function controlSatisfactory(action) {
    if (!currentSatisfactory) return;
    if (!(CURRENT_ROLE === 'admin' || CURRENT_ROLE === 'manager')) {
        alert('Action interdite: vous n\'avez pas les droits');
        return;
    }
    fetch(`/api/satisfactorys/control/${currentSatisfactory}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action})
    })
    .then(res => res.json())
    .then(data => {
        console.log('Control response:', data);
        if (data.success) {
            alert(`Action ${action} réussie`);
            // Force immediate status check after control action
            resetPollingLogic();
            fetchSatisfactoryStatus(currentSatisfactory);
        } else {
            alert('Erreur: ' + (data.error || 'Action impossible'));
        }
    })
    .catch((error) => {
        console.error('Error controlling satisfactory:', error);
        alert('Erreur réseau');
    });
}

function fetchSatisfactoryLogs() {
    if (!currentSatisfactory) return;
    const logsElem = document.getElementById('satisfactory-logs');
    if (logsElem) {
        fetch(`/api/satisfactorys/logs/${currentSatisfactory}`)
            .then(res => res.json())
            .then(data => {
                const logs = data.logs || 'Aucun log trouvé.';
                if (logs !== lastLogs) {
                    logsElem.textContent = logs;
                    logsElem.scrollTop = logsElem.scrollHeight;
                    lastLogs = logs;
                }
            })
            .catch(()=>{ if(logsElem) logsElem.textContent = 'Erreur lors de la récupération des logs.'; });
    }
}

// Start polling when page loads
document.addEventListener('DOMContentLoaded', function() {
    startStatusPolling();
    
    // Keep logs polling at normal interval (5 seconds)
    setInterval(() => {
        fetchSatisfactoryLogs();
    }, 5000);
});
