// home.js

// Initialiser le graphique
const ctx = document.getElementById('performanceChart').getContext('2d');
const performanceChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Les timestamps seront ajoutés dynamiquement
        datasets: [
            {
                label: 'CPU (%)',
                data: [],
                borderColor: '#4caf50',
                backgroundColor: 'rgba(76, 175, 80, 0.2)',
                fill: true,
            },
            {
                label: 'Mémoire (%)',
                data: [],
                borderColor: '#ffa500',
                backgroundColor: 'rgba(255, 165, 0, 0.2)',
                fill: true,
            },
            {
                label: 'Disque (%)',
                data: [],
                borderColor: '#f44336',
                backgroundColor: 'rgba(244, 67, 54, 0.2)',
                fill: true,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Temps',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Utilisation (%)',
                },
                min: 0,
                max: 100, // Limite à 100%
            },
        },
    },
});

// Fonction pour mettre à jour le graphique
function updateChart(data) {
    const timestamp = new Date().toLocaleTimeString();

    // Ajouter les nouvelles données
    performanceChart.data.labels.push(timestamp);
    performanceChart.data.datasets[0].data.push(data.cpu_percent);
    performanceChart.data.datasets[1].data.push(data.memory_percent);
    performanceChart.data.datasets[2].data.push(data.disk_percent);

    // Limiter le nombre de points affichés
    if (performanceChart.data.labels.length > 10) {
        performanceChart.data.labels.shift();
        performanceChart.data.datasets.forEach((dataset) => dataset.data.shift());
    }

    // Mettre à jour le graphique
    performanceChart.update();
}

// Initialiser le graphique du flux réseau
const networkCtx = document.getElementById('networkChart').getContext('2d');
const networkChart = new Chart(networkCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Entrée (KB/s)',
                data: [],
                borderColor: '#4caf50',
                backgroundColor: 'rgba(76, 175, 80, 0.2)',
                fill: true,
            },
            {
                label: 'Sortie (KB/s)',
                data: [],
                borderColor: '#f44336',
                backgroundColor: 'rgba(244, 67, 54, 0.2)',
                fill: true,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Temps',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Débit',
                },
                min: 0,
                max: 1000000, // 1 Go/s
                ticks: {
                    callback: function(value) {
                        if (value >= 1000000) {
                            return Math.round(value / 1000000) + ' Go/s';
                        } else if (value >= 1000) {
                            return Math.round(value / 1000) + ' Mo/s';
                        } else {
                            return Math.round(value) + ' Ko/s';
                        }
                    }
                }
            },
        },
    },
});

// Fonction pour mettre à jour le graphique du flux réseau
function updateNetworkChart(data) {
    const timestamp = new Date().toLocaleTimeString();

    // Ajouter les nouvelles données
    networkChart.data.labels.push(timestamp);
    networkChart.data.datasets[0].data.push(data.network_in);
    networkChart.data.datasets[1].data.push(data.network_out);

    // Limiter le nombre de points affichés
    if (networkChart.data.labels.length > 10) {
        networkChart.data.labels.shift();
        networkChart.data.datasets.forEach((dataset) => dataset.data.shift());
    }

    // Mettre à jour le graphique
    networkChart.update();
}

// Initialiser le graphique des threads CPU
const cpuThreadsCtx = document.getElementById('cpuThreadsChart').getContext('2d');
const cpuThreadsChart = new Chart(cpuThreadsCtx, {
    type: 'bar',
    data: {
        labels: [], // Les threads CPU seront ajoutés dynamiquement
        datasets: [
            {
                label: 'Utilisation (%)',
                data: [],
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
            },
        ],
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Threads CPU',
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Utilisation (%)',
                },
                min: 0,
                max: 100, // Limite à 100%
            },
        },
    },
});

// Fonction pour mettre à jour le graphique des threads CPU
function updateCpuThreadsChart(data) {
    if (!data.cpu_threads || !Array.isArray(data.cpu_threads)) {
        console.error('Les données des threads CPU sont invalides ou absentes.');
        return;
    }

    const threadLabels = data.cpu_threads.map((_, index) => `Thread ${index + 1}`);
    const threadData = data.cpu_threads;

    cpuThreadsChart.data.labels = threadLabels;
    cpuThreadsChart.data.datasets[0].data = threadData;

    cpuThreadsChart.update();
}

// Fonction pour mettre à jour les couleurs des barres
function updateBarColor(element, value) {
    if (value < 70) {
        element.className = 'progress-bar-fill normal';
    } else if (value < 90) {
        element.className = 'progress-bar-fill warning';
    } else {
        element.className = 'progress-bar-fill critical';
    }
}

// Fonction pour mettre à jour les barres de progression
function updateProgressBars(data) {
    const cpuBar = document.getElementById('cpu-bar');
    const memoryBar = document.getElementById('memory-bar');
    const diskBar = document.getElementById('disk-bar');

    // Mettre à jour la largeur et la couleur des barres
    cpuBar.style.width = `${data.cpu_percent}%`;
    cpuBar.textContent = `${data.cpu_percent}%`;
    updateBarColor(cpuBar, data.cpu_percent);

    memoryBar.style.width = `${data.memory_percent}%`;
    memoryBar.textContent = `${data.memory_percent}%`;
    updateBarColor(memoryBar, data.memory_percent);

    diskBar.style.width = `${data.disk_percent}%`;
    diskBar.textContent = `${data.disk_percent}%`;
    updateBarColor(diskBar, data.disk_percent);
}

function fetchSystemInfo() {
    fetch('/api/system-info')
        .then((response) => response.json())
        .then((data) => {
            // Mettre à jour les barres de progression
            updateProgressBars(data);

            // Mettre à jour le graphique des performances
            updateChart(data);

            // Mettre à jour le graphique du flux réseau
            updateNetworkChart(data);

            // Mettre à jour le graphique des threads CPU
            updateCpuThreadsChart(data);
        })
        .catch((error) => console.error('Erreur lors de la récupération des données système:', error));
}

// Actualiser les informations toutes les 2 secondes
setInterval(fetchSystemInfo, 2000);

// Appliquer une valeur de scale ('auto' ou numeric) à un chart Chart.js
function applyScaleToChart(chart, value) {
    if (!chart || !chart.options || !chart.options.scales) return;
    if (value === 'auto') {
        // remove explicit max/min
        if (chart.options.scales.y) {
            delete chart.options.scales.y.min;
            delete chart.options.scales.y.max;
        } else if (chart.options.scales['yAxes']) {
            // legacy fallback
            chart.options.scales['yAxes'].forEach(a => { delete a.ticks.min; delete a.ticks.max; });
        }
    } else {
        const n = Number(value);
        if (!isFinite(n)) return;
        if (!chart.options.scales.y) chart.options.scales.y = {};
        chart.options.scales.y.min = 0;
        chart.options.scales.y.max = n;
    }
    chart.update();
}

// Sauvegarder les preferences côté serveur
function saveChartScales(scales) {
    fetch('/api/user/chart-scales', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chart_scales: scales })
    }).then(r => r.json()).then(resp => {
        if (!resp.success) {
            console.warn('Failed saving chart scales', resp);
        }
    }).catch(err => console.error('Error saving chart scales', err));
}

// Charger preferences et appliquer
function loadAndApplyChartScales() {
    fetch('/api/user/chart-scales').then(r => {
        if (r.status === 401) return null;
        return r.json();
    }).then(obj => {
        if (!obj || !obj.chart_scales) return;
        const s = obj.chart_scales;
        if (s.performance) {
            document.getElementById('performance-scale').value = String(s.performance);
            applyScaleToChart(performanceChart, s.performance);
        }
        if (s.network) {
            document.getElementById('network-scale').value = String(s.network);
            applyScaleToChart(networkChart, s.network);
        }
        if (s.cpu_threads) {
            document.getElementById('cpu-threads-scale').value = String(s.cpu_threads);
            applyScaleToChart(cpuThreadsChart, s.cpu_threads);
        }
    }).catch(err => {
        console.debug('No chart-scales loaded (maybe unauthenticated)', err);
    });
}

// Attacher listeners aux selects
function setupScaleSelectors() {
    const perf = document.getElementById('performance-scale');
    const net = document.getElementById('network-scale');
    const cpu = document.getElementById('cpu-threads-scale');

    if (perf) perf.addEventListener('change', (e) => {
        const v = e.target.value;
        applyScaleToChart(performanceChart, v);
        saveChartScales({
            performance: v,
            network: document.getElementById('network-scale').value,
            cpu_threads: document.getElementById('cpu-threads-scale').value
        });
    });
    if (net) net.addEventListener('change', (e) => {
        const v = e.target.value;
        applyScaleToChart(networkChart, v);
        saveChartScales({
            performance: document.getElementById('performance-scale').value,
            network: v,
            cpu_threads: document.getElementById('cpu-threads-scale').value
        });
    });
    if (cpu) cpu.addEventListener('change', (e) => {
        const v = e.target.value;
        applyScaleToChart(cpuThreadsChart, v);
        saveChartScales({
            performance: document.getElementById('performance-scale').value,
            network: document.getElementById('network-scale').value,
            cpu_threads: v
        });
    });
}

// Après la création des charts, charger preferences et hooks
loadAndApplyChartScales();
setupScaleSelectors();