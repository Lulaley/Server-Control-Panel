(function(){
  const INTERVAL = 1000; // 1s polling interval

  let timer = null;

  async function fetchAndUpdate(){
    const card = document.getElementById('machine-card');
    if(!card) return;
    try{
      const res = await fetch('/api/machine', { cache: 'no-store' });
      if(!res.ok) return;
      const data = await res.json();

      // CPU
      const cpuVal = card.querySelector('#cpu-value');
      const cpuBar = card.querySelector('.progress-bar[data-metric="cpu"]');
      if(typeof data.cpu_percent !== 'undefined'){
        if(cpuVal) cpuVal.textContent = data.cpu_percent + '%';
        if(cpuBar){ cpuBar.style.width = data.cpu_percent + '%'; cpuBar.style.background = data.cpu_percent < 60 ? '#1b7a1b' : (data.cpu_percent < 85 ? '#b26900' : '#c62828'); }
      }

      // RAM
      const ramVal = card.querySelector('#ram-value');
      const ramBar = card.querySelector('.progress-bar[data-metric="ram"]');
      if(typeof data.ram_percent !== 'undefined'){
        if(ramVal){
          if(typeof data.ram_used !== 'undefined' && typeof data.ram_total !== 'undefined') ramVal.textContent = `${data.ram_used} / ${data.ram_total} (${data.ram_percent}%)`;
          else ramVal.textContent = data.ram_percent + '%';
        }
        if(ramBar){ ramBar.style.width = data.ram_percent + '%'; ramBar.style.background = data.ram_percent < 60 ? '#1b7a1b' : (data.ram_percent < 85 ? '#b26900' : '#c62828'); }
      }

      // Disk
      const diskVal = card.querySelector('#disk-value');
      const diskBar = card.querySelector('.progress-bar[data-metric="disk"]');
      if(typeof data.disk_percent !== 'undefined'){
        if(diskVal){
          if(typeof data.disk_used !== 'undefined' && typeof data.disk_total !== 'undefined') diskVal.textContent = `${data.disk_used} / ${data.disk_total} (${data.disk_percent}%)`;
          else diskVal.textContent = data.disk_percent + '%';
        }
        if(diskBar){ diskBar.style.width = data.disk_percent + '%'; diskBar.style.background = data.disk_percent < 60 ? '#1b7a1b' : (data.disk_percent < 85 ? '#b26900' : '#c62828'); }
      }
    }catch(e){
      // silent
    }
  }

  function startPolling(){
    fetchAndUpdate();
    if(timer) clearInterval(timer);
    timer = setInterval(fetchAndUpdate, INTERVAL);
  }

  document.addEventListener('DOMContentLoaded', startPolling);
  window.startMachineCardPolling = startPolling;
})();
