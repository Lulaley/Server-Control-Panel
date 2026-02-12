document.addEventListener('DOMContentLoaded', function() {
    function applyMainColor(color) {
        document.documentElement.style.setProperty('--main-color', color);
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

        const styleId = 'user-main-color-style';
        let styleTag = document.getElementById(styleId);
        const css = `:root { --main-color: ${color}; }`;
        if (!styleTag) {
            styleTag = document.createElement('style');
            styleTag.id = styleId;
            const head = document.head || document.getElementsByTagName('head')[0];
            if (head.firstChild) head.insertBefore(styleTag, head.firstChild);
            else head.appendChild(styleTag);
        }
        styleTag.textContent = css;
        let meta = document.querySelector('meta[name="theme-color"]');
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('name', 'theme-color');
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', color);
        if (document.body) document.body.style.setProperty('--main-color', color);

        // Remplacement dynamique des couleurs hexes dans CSS et inline
        (function replaceHexColors(newColor){
            const hexRegex = /#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b/g;
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
                } catch (e) {}
            }
            for (const el of Array.from(document.querySelectorAll('[style]'))) {
                const s = el.getAttribute('style');
                if (!s) continue;
                if (hexRegex.test(s)) el.setAttribute('style', s.replace(hexRegex, newColor));
            }
            for (const svgEl of Array.from(document.querySelectorAll('[fill],[stroke]'))) {
                const fill = svgEl.getAttribute('fill');
                if (fill && hexRegex.test(fill)) svgEl.setAttribute('fill', newColor);
                const stroke = svgEl.getAttribute('stroke');
                if (stroke && hexRegex.test(stroke)) svgEl.setAttribute('stroke', newColor);
            }
        })(color);
    }

    fetch('/api/user')
        .then(res => {
            if (!res.ok) throw new Error('no /api/user');
            return res.json();
        })
        .then(userData => {
            const color = userData.main_color || '#4caf50';
            applyMainColor(color);
        })
        .catch(() => {
            applyMainColor('#4caf50');
        });
});
