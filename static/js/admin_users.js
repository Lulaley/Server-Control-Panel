async function loadUsers(){
    const res = await fetch('/api/admin/users');
    if(!res.ok){
        document.getElementById('users-container').textContent = 'Erreur: ' + res.status;
        return;
    }
    const j = await res.json();
    const users = j.users || [];
    if(!users.length){
        document.getElementById('users-container').innerHTML = '<p>Aucun utilisateur.</p>';
        return;
    }
    const table = document.createElement('table');
    table.style.width = '100%';
    table.innerHTML = '<tr><th>Utilisateur</th><th>Rôle</th><th>Actions</th></tr>';
    users.forEach(u => {
        const tr = document.createElement('tr');
        const roleSelect = `<select data-user="${u.username}" class="role-select">
            <option value="user"${u.role==='user'?' selected':''}>Utilisateur</option>
            <option value="manager"${u.role==='manager'?' selected':''}>Manager</option>
            <option value="admin"${u.role==='admin'?' selected':''}>Admin</option>
        </select>`;
        tr.innerHTML = `<td>${u.username}</td><td>${roleSelect}</td><td>
            <button data-user="${u.username}" class="delete-btn">Supprimer</button>
        </td>`;
        table.appendChild(tr);
    });
    const container = document.getElementById('users-container');
    container.innerHTML = '';
    container.appendChild(table);

    Array.from(document.querySelectorAll('select.role-select')).forEach(sel=>{
        sel.onchange = async ()=> {
            const username = sel.dataset.user;
            const role = sel.value;
            const r = await fetch(`/api/admin/users/${encodeURIComponent(username)}/role`, {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({role})
            });
            if(!r.ok) alert('Échec changement rôle');
            else loadUsers();
        };
    });
    Array.from(document.querySelectorAll('button.delete-btn')).forEach(btn=>{
        btn.onclick = async ()=> {
            if(!confirm('Supprimer cet utilisateur ?')) return;
            const username = btn.dataset.user;
            const r = await fetch(`/api/admin/users/${encodeURIComponent(username)}`, {method:'DELETE'});
            if(!r.ok){
                const j = await r.json().catch(()=>({}));
                alert('Échec suppression: ' + (j.error || r.status));
            } else loadUsers();
        };
    });
}
document.addEventListener('DOMContentLoaded', loadUsers);
