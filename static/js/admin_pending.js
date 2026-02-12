async function loadPending(){
    const res = await fetch('/api/admin/pending_users');
    if(!res.ok){
        document.getElementById('pending-container').textContent = 'Erreur: ' + res.status;
        return;
    }
    const j = await res.json();
    const pending = j.pending || [];
    if(!pending.length){
        document.getElementById('pending-container').innerHTML = '<p>Aucune demande en attente.</p>';
        return;
    }
    const table = document.createElement('table');
    table.style.width = '100%';
    table.innerHTML = '<tr><th>Utilisateur</th><th>Rôle demandé</th><th>Actions</th></tr>';
    pending.forEach(u => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${u.username}</td><td>${u.role}</td><td>
            <button data-user="${u.username}" class="approve">Valider</button>
            <button data-user="${u.username}" class="reject">Rejeter</button>
        </td>`;
        table.appendChild(tr);
    });
    const container = document.getElementById('pending-container');
    container.innerHTML = '';
    container.appendChild(table);
    // attach listeners
    Array.from(document.querySelectorAll('button.approve')).forEach(btn=>{
        btn.onclick = async ()=> {
            const u = btn.dataset.user;
            await fetch(`/api/admin/pending_users/${encodeURIComponent(u)}/approve`, {method:'POST'});
            loadPending();
        };
    });
    Array.from(document.querySelectorAll('button.reject')).forEach(btn=>{
        btn.onclick = async ()=> {
            const u = btn.dataset.user;
            await fetch(`/api/admin/pending_users/${encodeURIComponent(u)}/reject`, {method:'POST'});
            loadPending();
        };
    });
}

document.addEventListener('DOMContentLoaded', loadPending);
