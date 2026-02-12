document.addEventListener('DOMContentLoaded', function(){
    // Populate server selects (reuse existing server-select options if present)
    function copyOptions(srcId, destId){
        const src = document.getElementById(srcId);
        const dest = document.getElementById(destId);
        if (!src || !dest) return;
        dest.innerHTML = '';
        Array.from(src.options).forEach(opt => {
            const o = document.createElement('option');
            o.value = opt.value;
            o.text = opt.text;
            dest.appendChild(o);
        });
    }
    copyOptions('server-select', 'prop-server-select');

    const propSelect = document.getElementById('prop-server-select');
    const propertiesGrid = document.getElementById('properties-grid');
    const feedback = document.getElementById('props-feedback');

    // remplace buildTable et le handler de save pour gérer types
    function inferType(key, val){
        const s = String(val).trim();
        const low = s.toLowerCase();
        if (low === 'true' || low === 'false') return 'boolean';
        if (/^-?\d+$/.test(s)) return 'int';
        if (/^-?\d+\.\d+$/.test(s)) return 'float';
        // heuristiques sur le nom de la clé pour forcer numérique
        if (/(port|count|max|min|size|level|timeout|slots|rate|interval|threshold)/i.test(key) && /^-?\d+(\.\d+)?$/.test(s)) {
            return s.includes('.') ? 'float' : 'int';
        }
        return 'string';
    }

     function buildTable(props){
         propertiesGrid.innerHTML = '';
         const keys = Object.keys(props).sort();
         keys.forEach(k => {
             const raw = props[k];
             const type = inferType(k, raw);
             const item = document.createElement('div');
             item.className = 'prop-item';

             const label = document.createElement('label');
             label.textContent = k;
             item.appendChild(label);

             let input;
             if (type === 'boolean') {
                 input = document.createElement('input');
                 input.type = 'checkbox';
                 input.checked = String(raw).trim().toLowerCase() === 'true';
                 input.value = input.checked ? 'true' : 'false';
                 input.addEventListener('change', function(){ this.value = this.checked ? 'true' : 'false'; });
                 input.dataset.propType = 'boolean';
             } else if (type === 'int' || type === 'float') {
                 input = document.createElement('input');
                 input.type = 'number';
                 input.value = String(raw);
                 input.step = type === 'int' ? '1' : 'any';
                 input.dataset.propType = 'number';
             } else {
                 input = document.createElement('input');
                 input.type = 'text';
                 input.value = String(raw);
                 input.dataset.propType = 'string';
             }

             input.dataset.propKey = k;
             item.appendChild(input);
             propertiesGrid.appendChild(item);
         });
     }

     function loadPropertiesFor(server){
         if(!server) return;
         fetch(`/api/minecraft/server-properties/${encodeURIComponent(server)}`)
         .then(res => res.json())
         .then(data => {
             if(data.success){
                 const props = data.properties || {};
                 buildTable(props);
                 feedback.textContent = '';
             } else {
                 propertiesGrid.innerHTML = '<div class="error">Erreur: ' + (data.error||'non trouvé') + '</div>';
             }
         })
         .catch(err => {
             propertiesGrid.innerHTML = '<div class="error">Impossible de charger</div>';
         });
     }

    if(propSelect){
        // initial load
        loadPropertiesFor(propSelect.value || document.getElementById('server-select')?.value);
        propSelect.addEventListener('change', function(){ loadPropertiesFor(this.value); });
    }

    document.getElementById('reload-properties')?.addEventListener('click', function(){
        loadPropertiesFor(propSelect.value);
    });

    document.getElementById('save-properties')?.addEventListener('click', function(){
        const inputs = propertiesGrid.querySelectorAll('input[data-prop-key]');
        const payload = {};
        inputs.forEach(inp => {
            const key = inp.dataset.propKey;
            const t = inp.dataset.propType || 'string';
            if (t === 'boolean') {
                payload[key] = inp.checked ? 'true' : 'false';
            } else if (t === 'number') {
                // keep as string but ensure numeric format
                const val = inp.value;
                payload[key] = val === '' ? '' : String(val);
            } else {
                payload[key] = inp.value;
            }
        });
        fetch(`/api/minecraft/server-properties/${encodeURIComponent(propSelect.value)}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({properties: payload})
        })
        .then(res => res.json())
        .then(data => {
            if(data.success){
                feedback.style.color = '#080';
                feedback.textContent = 'Modifications enregistrées.';
            } else {
                feedback.style.color = '#d00';
                feedback.textContent = 'Erreur: ' + (data.error || 'échec');
            }
        })
        .catch(err => {
            feedback.style.color = '#d00';
            feedback.textContent = 'Erreur lors de la requête.';
        });
    });

    // Nouvelle logique : récupérer la liste des serveurs depuis l'API et remplir les deux selects
    function populateServerSelectsFromApi() {
        fetch('/api/minecraft/servers')
            .then(res => res.json())
            .then(data => { // <-- corrigé : ajout des parenthèses autour de 'data'
                const servers = Array.isArray(data) ? data : (Array.isArray(data?.servers) ? data.servers : (data?.servers || []));
                const serverSelect = document.getElementById('server-select');
                const propSelect = document.getElementById('prop-server-select');
                if (!servers || servers.length === 0) {
                    // si aucun serveur retourné, on laisse la logique existante (copie si présente)
                    copyOptions('server-select', 'prop-server-select');
                    return;
                }
                // Remplir server-select et prop-server-select
                if (serverSelect) {
                    serverSelect.innerHTML = '';
                    servers.forEach(s => {
                        const o = document.createElement('option');
                        o.value = s;
                        o.text = s;
                        serverSelect.appendChild(o);
                    });
                }
                if (propSelect) {
                    propSelect.innerHTML = '';
                    servers.forEach(s => {
                        const o = document.createElement('option');
                        o.value = s;
                        o.text = s;
                        propSelect.appendChild(o);
                    });
                }

                // Charger automatiquement les propriétés pour le serveur actuellement sélectionné
                const chosen = (propSelect && propSelect.value) || (serverSelect && serverSelect.value);
                if (chosen) loadPropertiesFor(chosen);
            })
            .catch(() => {
                // fallback : copier les options si le endpoint n'est pas disponible
                copyOptions('server-select', 'prop-server-select');
                const fallbackServer = document.getElementById('prop-server-select')?.value || document.getElementById('server-select')?.value;
                if (fallbackServer) loadPropertiesFor(fallbackServer);
            });
    }

    // Si l'utilisateur change le sélecteur principal, synchroniser le sélecteur de properties et recharger
    const mainServerSelect = document.getElementById('server-select');
    const propSelectElem = document.getElementById('prop-server-select');
    if (mainServerSelect && propSelectElem) {
        mainServerSelect.addEventListener('change', function(){
            // mettre à jour prop select si présent
            let found = Array.from(propSelectElem.options).some(opt => opt.value === this.value);
            if (!found) {
                // si prop-select n'a pas cette option, l'ajouter
                const o = document.createElement('option');
                o.value = this.value;
                o.text = this.value;
                propSelectElem.appendChild(o);
            }
            propSelectElem.value = this.value;
            loadPropertiesFor(this.value);
        });
    }

    // Lancer le remplissage depuis l'API
    populateServerSelectsFromApi();
});
