document.addEventListener('click', function(e){
  const t = e.target;
  if(t.classList.contains('btn-open')){
    // lien déjà target="_blank"; hook pour extensions éventuelles
  }
});

// fetch user color and apply to page
(function(){
  function hexToRgb(hex){
    if(!hex) return null;
    hex = hex.replace('#','').trim();
    if(hex.length === 3){
      hex = hex.split('').map(c=>c+c).join('');
    }
    if(hex.length !== 6) return null;
    const r = parseInt(hex.slice(0,2),16);
    const g = parseInt(hex.slice(2,4),16);
    const b = parseInt(hex.slice(4,6),16);
    return {r,g,b};
  }
  function rgbaString(hex, alpha){
    const rgb = hexToRgb(hex);
    if(!rgb) return null;
    return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
  }
  function luminance(rgb){
    if(!rgb) return 0;
    // relative luminance approximation
    const [r,g,b] = [rgb.r, rgb.g, rgb.b].map(v=>{
      v /= 255;
      return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
    });
    return 0.2126*r + 0.7152*g + 0.0722*b;
  }

  fetch('/api/user/main-color').then(r => {
    if(!r.ok) return null;
    return r.json();
  }).then(data => {
    if(!data || !data.main_color) return;
    const col = data.main_color;
    const rgb = hexToRgb(col);
    // page title color (dark text on light colors)
    let titleColor = '#0b1726';
    if(rgb){
      const lum = (0.299*rgb.r + 0.587*rgb.g + 0.114*rgb.b)/255;
      titleColor = lum > 0.6 ? '#071126' : '#ffffff';
    }
    // Only adjust page-level title color; do not set variables that affect cards.
    if(titleColor) document.documentElement.style.setProperty('--page-title-color', titleColor);
  }).catch(()=>{ /* silent */ });
})();
