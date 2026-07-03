// JS pour rafraîchir dynamiquement l'état des ports
function statusLabel(status) {
    if (status === 'USED') return '<span class="status-used">UTILISÉ</span>';
    if (status === 'DELETE') return '<span class="status-delete">À SUPPRIMER</span>';
    return '<span class="status-free">LIBRE</span>';
}

function portBadge(port, used, proto) {
    if (port === undefined) return '';
    let cls = used === true ? 'port-used' : 'port-free';
    let label = port + (proto === 'udp' ? '/udp' : '');
    return `<span class="port-badge ${cls}">${label}</span>`;
}

function fillPortsTable(data) {
    const tbody = document.getElementById('ports-table-body');
    tbody.innerHTML = '';
    data.forEach(item => {
        let wan = item.wan !== undefined ? portBadge(item.wan, item.wan_used, 'tcp') : '';
        let lan = item.lan !== undefined ? portBadge(item.lan, item.lan_used, 'tcp') : '';
        let rcon = item.rcon !== undefined ? portBadge(item.rcon, item.rcon_used, 'tcp') : '';
        let autres = '';
        if (item.p1) autres += portBadge(item.p1, item.p1_used, 'tcp');
        if (item.p2) autres += portBadge(item.p2, item.p2_used, 'tcp');
        if (item.p3) autres += portBadge(item.p3, item.p3_used, item.p3 && item.p3.toString().includes('udp') ? 'udp' : 'tcp');
        let desc = item.desc ? `<br><small>${item.desc}</small>` : '';
        let service = '';
        if (item.service_running === true) {
            service = '<span style="color:#4caf50;font-weight:bold">Service actif</span>';
        } else if (item.service_running === false) {
            let since = item.service_last_stopped ? `depuis ${item.service_last_stopped}` : '(inactif)';
            service = `<span style="color:#ff9800;font-weight:bold">Service arrêté</span> <small>${since}</small>`;
        } else {
            service = '<span style="color:#bbb">N/A</span>';
        }
        tbody.innerHTML += `<tr>
            <td>${item.name}${desc}</td>
            <td>${statusLabel(item.status)}</td>
            <td>${wan}</td>
            <td>${lan}</td>
            <td>${rcon}</td>
            <td>${autres}</td>
            <td>${service}</td>
        </tr>`;
    });
}

function showPortsError(msg) {
    const tbody = document.getElementById('ports-table-body');
    tbody.innerHTML = `<tr><td colspan="6" style="color:#f44336;font-weight:bold;text-align:center;">${msg}</td></tr>`;
}

function refreshPorts() {
    fetch('/admin/ports/status')
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                showPortsError('Erreur : ' + (data.error === 'unauthorized' ? 'Accès refusé, connecte-toi en admin.' : data.error));
            } else {
                fillPortsTable(data);
            }
        })
        .catch(() => showPortsError('Erreur de connexion au serveur.'));
}

document.addEventListener('DOMContentLoaded', function() {
    refreshPorts();
    setInterval(refreshPorts, 4000); // rafraîchit toutes les 4s
});
