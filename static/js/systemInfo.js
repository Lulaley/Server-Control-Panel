function bytesToSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)), 10);
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
}

async function fetchSystemInfo() {
    try {
        const response = await fetch('/system_info');
        const data = await response.json();

        setProgressBar('#cpu-progress-bar', data.cpu_percent);
        setProgressBar('#memory-progress-bar', data.memory_percent);
        setProgressBar('#disk-progress-bar', data.disk_percent);

        document.getElementById('java-version').innerText = `Java Version: ${data.java_version}`;
        document.getElementById('cpu-percentage').innerText = `CPU: ${data.cpu_percent}%`;
        document.getElementById('memory-percentage').innerText = `Memory: ${data.memory_percent}% (${bytesToSize(data.current_ram_used)} used / ${bytesToSize(data.total_ram)} total)`;
        document.getElementById('disk-percentage').innerText = `Disk: ${data.disk_percent}% (${bytesToSize(data.current_disk_used)} used / ${bytesToSize(data.total_disk)} total)`;

    } catch (error) {
        console.error('Error fetching system info:', error);
    }
}

function setProgressBar(selector, percent) {
    const progressBarFill = document.querySelector(selector);
    progressBarFill.style.width = `${percent}%`;

    if (percent > 80) {
        progressBarFill.style.backgroundColor = 'red';
    } else if (percent > 60) {
        progressBarFill.style.backgroundColor = 'orange';
    } else {
        progressBarFill.style.backgroundColor = 'green';
    }
}

// Call the fetchSystemInfo function every minutes
setInterval(fetchSystemInfo, 3800);

// Call the fetchSystemInfo function once on page load
fetchSystemInfo();