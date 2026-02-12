async function loadResetRequests() {
    try {
        const response = await fetch('/api/admin/reset_requests');
        const data = await response.json();
        
        const container = document.getElementById('reset-requests-list');
        
        if (!data.reset_requests || data.reset_requests.length === 0) {
            container.innerHTML = '<p>Aucune demande de reset en cours.</p>';
            return;
        }
        
        const table = document.createElement('table');
        table.innerHTML = '<tr><th>Utilisateur</th><th>Actions</th></tr>';
        
        data.reset_requests.forEach(req => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${req.username}</strong></td>
                <td>
                    <button class="btn-approve" data-user="${req.username}">Approuver</button>
                    <button class="btn-reject" data-user="${req.username}">Rejeter</button>
                </td>
            `;
            table.appendChild(tr);
        });
        
        container.innerHTML = '';
        container.appendChild(table);
        
        // Attach event listeners
        Array.from(document.querySelectorAll('.btn-approve')).forEach(btn => {
            btn.onclick = async () => {
                await approveReset(btn.dataset.user);
            };
        });
        
        Array.from(document.querySelectorAll('.btn-reject')).forEach(btn => {
            btn.onclick = async () => {
                await rejectReset(btn.dataset.user);
            };
        });
        
    } catch (error) {
        console.error('Erreur lors du chargement des demandes:', error);
        document.getElementById('reset-requests-list').textContent = 'Erreur: ' + error.message;
    }
}

async function approveReset(username) {
    try {
        const response = await fetch(`/api/admin/reset_requests/${username}/approve`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (response.ok) {
            alert(`Reset approuvé pour ${username}.\nNouveau mot de passe: ${data.new_password}`);
            loadResetRequests(); // Recharger la liste
        } else {
            alert('Erreur: ' + (data.error || 'Erreur inconnue'));
        }
    } catch (error) {
        alert('Erreur lors de l\'approbation: ' + error.message);
    }
}

async function rejectReset(username) {
    if (!confirm(`Êtes-vous sûr de vouloir rejeter la demande de ${username} ?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/admin/reset_requests/${username}/reject`, {
            method: 'POST'
        });
        
        if (response.ok) {
            loadResetRequests(); // Recharger la liste
        } else {
            const data = await response.json();
            alert('Erreur: ' + (data.error || 'Erreur inconnue'));
        }
    } catch (error) {
        alert('Erreur lors du rejet: ' + error.message);
    }
}

// Charger les demandes au chargement de la page
document.addEventListener('DOMContentLoaded', loadResetRequests);
