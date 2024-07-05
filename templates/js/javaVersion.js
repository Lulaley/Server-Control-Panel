async function fetchJavaVersions() {
    try {
        const response = await fetch('/java_versions');
        const javaVersions = await response.json();
        const javaVersionSelect = document.getElementById('java-version-select');

        // Check if filtered.log exists and has a modified date of today for all Minecraft servers
        const logPaths = document.querySelectorAll('.log-path');
        let allLogsModifiedToday = true;
        for (const logPath of logPaths) {
            const path = logPath.textContent.trim();
            const logResponse = await fetch(path);
            if (logResponse.ok) {
                const logModifiedDate = new Date(logResponse.headers.get('Last-Modified')).setHours(0, 0, 0, 0);
                const today = new Date().setHours(0, 0, 0, 0);
                if (logModifiedDate !== today) {
                    allLogsModifiedToday = false;
                    break;
                }
            } else {
                console.log(`${path} does not exist`);
                allLogsModifiedToday = false;
                break;
            }
        }
        console.log(javaVersions);
        if (allLogsModifiedToday) {
            // Populate the java version select element with the available versions
            for (const version of javaVersions) {
                const option = document.createElement('option');
                option.value = version.path;
                option.textContent = version.version;
                if (javaVersionSelect) {
                    javaVersionSelect.appendChild(option);
                }
            }
        } else {
            console.log('Not all filtered.log files have a modified date of today');
        }
    } catch (error) {
        console.error('Error fetching Java versions:', error);
    }
}

fetchJavaVersions();

if (document.getElementById('java-version-select')) {
    document.getElementById('java-version-select').addEventListener('change', function(event) {
        const selectedVersion = event.target.value;
        console.log(`Java version wanted : ${selectedVersion}`);
        changeJavaVersion(selectedVersion);
    });
}

async function changeJavaVersion(selectedVersion) {
    try {
        const response = await fetch('/change_java_version', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `version=${encodeURIComponent(selectedVersion)}`
        });
        const data = await response.json();
        if (data.success) {
            console.log(`Java version changed to ${selectedVersion}`);
            // Reload the page to apply the changes
            location.reload();
        } else {
            console.error('Error changing Java version:', data.error);
        }
    } catch (error) {
        console.error('Error changing Java version:', error);
    }
}
