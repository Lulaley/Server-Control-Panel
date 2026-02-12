// Remplacer la logique de chargement et de soumission pour supporter une préférence par utilisateur

// Ajout : fonction globale accessible partout dans ce fichier (mise à jour pour injecter une règle CSS dans <head>)
function applyMainColor(color) {
    // Affecte la variable CSS via JS (inline style sur l'élément root)
    document.documentElement.style.setProperty('--main-color', color);

    // Met à jour l'attribut inline "style" de <html> sans écraser les autres déclarations
    (function setHtmlInlineVar(varName, value){
        const el = document.documentElement;
        const prev = el.getAttribute('style') || '';
        const decls = {};
        prev.split(';').map(s => s.trim()).filter(Boolean).forEach(d => {
            const idx = d.indexOf(':');
            if (idx === -1) return;
            const k = d.slice(0, idx).trim();
            const v = d.slice(idx + 1).trim();
            if (k) decls[k] = v;
        });
        decls[varName] = value;
        const styleStr = Object.entries(decls).map(([k,v]) => `${k}: ${v}`).join('; ');
        el.setAttribute('style', styleStr);
    })('--main-color', color);

    // Met à jour (ou crée) une balise <style> dédiée qui place la variable en tête du <head>
    const styleId = 'user-main-color-style';
    let styleTag = document.getElementById(styleId);
    const css = `:root { --main-color: ${color}; }`;
    if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = styleId;
        // on prepend pour maximiser la priorité (si nécessaire)
        const head = document.head || document.getElementsByTagName('head')[0];
        if (head.firstChild) head.insertBefore(styleTag, head.firstChild);
        else head.appendChild(styleTag);
    }
    styleTag.textContent = css;

    // Met à jour meta theme-color si présent ou le crée
    let meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute('name', 'theme-color');
        document.head.appendChild(meta);
    }
    meta.setAttribute('content', color);

    // Optionnel : applique également sur body pour compatibilité avec certains styles inline
    if (document.body) document.body.style.setProperty('--main-color', color);

    // Remplace dynamiquement les couleurs hex dans les feuilles de style et styles inline
    (function replaceHexColors(newColor){
        const hexRegex = /#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g;

        // Feuilles de style CSS
        for (const sheet of Array.from(document.styleSheets)) {
            try {
                const rules = sheet.cssRules || sheet.rules;
                if (!rules) continue;
                for (const rule of Array.from(rules)) {
                    if (!rule.style) continue;
                    const cssText = rule.style.cssText;
                    if (hexRegex.test(cssText)) {
                        rule.style.cssText = cssText.replace(hexRegex, newColor);
                    }
                }
            } catch (e) {
                // feuille cross-origin ou inaccessible -> ignorer
            }
        }

        // Styles inline des éléments
        for (const el of Array.from(document.querySelectorAll('[style]'))) {
            const s = el.getAttribute('style');
            if (!s) continue;
            if (hexRegex.test(s)) {
                el.setAttribute('style', s.replace(hexRegex, newColor));
            }
        }

        // SVG fill/stroke attributes
        for (const svgEl of Array.from(document.querySelectorAll('[fill],[stroke]'))) {
            const fill = svgEl.getAttribute('fill');
            if (fill && hexRegex.test(fill)) svgEl.setAttribute('fill', newColor);
            const stroke = svgEl.getAttribute('stroke');
            if (stroke && hexRegex.test(stroke)) svgEl.setAttribute('stroke', newColor);
        }
    })(color);
}

document.addEventListener('DOMContentLoaded', function() {
    // Récupérer l'utilisateur courant depuis l'API et appliquer sa couleur serveur
    fetch('/api/user')
        .then(res => {
            if (!res.ok) throw new Error('no /api/user');
            return res.json();
        })
        .then(data => {
            const color = data.main_color || '#4caf50';
            const colorInput = document.getElementById('main-color');
            if (colorInput) colorInput.value = color;
            applyMainColor(color);
        })
        .catch(error => {
            console.error('Erreur lors du chargement de la couleur:', error);
            applyMainColor('#4caf50');
        });
});

// Soumission du formulaire : sauvegarde UNIQUEMENT sur le serveur
const colorForm = document.getElementById('color-form');
if (colorForm) {
    colorForm.addEventListener('submit', function(e){
        e.preventDefault();
        const colorInput = document.getElementById('main-color');
        if (!colorInput) return;
        const color = colorInput.value;

        fetch('/api/user/main-color', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({main_color: color})
        })
        .then(res => res.json())
        .then(data => {
            if (data && data.success) {
                applyMainColor(color);
                showMessage('Couleur sauvegardée sur le serveur !', 'success');
            } else {
                showMessage('Erreur lors de la sauvegarde serveur', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showMessage('Erreur lors de la sauvegarde serveur', 'error');
        });
    });
}

// Fonction pour afficher des messages de feedback
function showMessage(message, type) {
    // Supprimer tout message existant
    const existingMessage = document.querySelector('.feedback-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Créer le nouveau message
    const messageDiv = document.createElement('div');
    messageDiv.className = `feedback-message ${type}`;
    messageDiv.textContent = message;
    messageDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 10px 20px;
        border-radius: 5px;
        color: white;
        background-color: ${type === 'success' ? '#4caf50' : '#f44336'};
        z-index: 1000;
        transition: opacity 0.3s;
    `;
    
    document.body.appendChild(messageDiv);
    
    // Supprimer le message après 3 secondes
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}