// Function to set a cookie
function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

// Function to get a cookie
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

window.onload = function() {
    // Get the selected service and tag button from cookies after the page reloads
    const serveurSelectIndex = getCookie('serveurSelectIndex');
    const selectedTagButton = getCookie('selectedTagButton');

    if (serveurSelectIndex !== "") {
        // Select the service
        const selectServeur = document.getElementById('folder-select');
        selectServeur.selectedIndex = Number(serveurSelectIndex);
    }

    if (selectedTagButton !== "") {
        // Select the tag button
        const button = document.getElementById(selectedTagButton);
        button.classList.add('selected');
    }
}

async function fetchServices() {
    try {
        const response = await fetch('/services');
        const services = await response.json();
        const servicesList = document.getElementById('services-list');
        services.forEach(service => {
        const li = document.createElement('li');
        li.textContent = service;
        servicesList.appendChild(li);
        });
    } catch (error) {
        console.error('Error fetching services:', error);
    }
}

  fetchServices();

function start_service(service) {
    fetch('/start_service', {
        method: 'POST',
        body: new URLSearchParams({service: service})
    }).then(() => {
        const serveurSelect = document.getElementById('folder-select');
        console.log(serveurSelect);
        setCookie('serveurSelectIndex', serveurSelect.selectedIndex, 1);
        setCookie('selectedTagButton', selectedButton.id, 1);
        setCookie('logPath', log_path, 1);
        setTimeout(() => {
            try {
                if(window.location.reload instanceof Function) {
                    window.location.reload(true);
                } else {
                    window.location.href = window.location.href;
                }
            } catch (error) {
                console.error('Error reloading the page:', error);
            }
        }, 100);
    });
}

function stop_service(service) {
    fetch('/stop_service', {
        method: 'POST',
        body: new URLSearchParams({service: service})
    }).then(() => {
        const serveurSelect = document.getElementById('folder-select');
        console.log(serveurSelect);
        setCookie('serveurSelectIndex', serveurSelect.selectedIndex, 1);
        setCookie('selectedTagButton', selectedButton.id, 1);
        setCookie('logPath', log_path, 1);
        setTimeout(() => {
            try {
                if(window.location.reload instanceof Function) {
                    window.location.reload(true);
                } else {
                    window.location.href = window.location.href;
                }
            } catch (error) {
                console.error('Error reloading the page:', error);
            }
        }, 100);
    });
}

function restart_service(service) {
    fetch('/restart_service', {
        method: 'POST',
        body: new URLSearchParams({service: service})
    }).then(() => {
        const serveurSelect = document.getElementById('folder-select');
        console.log(serveurSelect);
        setCookie('serveurSelectIndex', serveurSelect.selectedIndex, 1);
        setCookie('selectedTagButton', selectedButton.id, 1);
        setCookie('logPath', log_path, 1);
        setTimeout(() => {
            try {
                if(window.location.reload instanceof Function) {
                    window.location.reload(true);
                } else {
                    window.location.href = window.location.href;
                }
            } catch (error) {
                console.error('Error reloading the page:', error);
            }
        }, 100);
    });
}

function delete_service(serviceName) {
    if (confirm('Êtes-vous sûr de vouloir supprimer le service ' + serviceName + ' ?')) {
        fetch('/delete_service', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'service=' + encodeURIComponent(serviceName)
        })
        .then(response => {
            if (response.ok) {
                alert('Service ' + serviceName + ' supprimé avec succès.');
                window.location.reload(); // Recharger la page pour mettre à jour la liste des services
            } else {
                alert('Échec de la suppression du service ' + serviceName + '.');
            }
        })
        .catch(error => console.error('Erreur:', error));
    }
}

// Handle form submission
document.getElementById("new-service-form").onsubmit = function(event) {
    event.preventDefault();
    const serviceName = document.getElementById("service-name").value;
    const serviceDescription = document.getElementById("service-description").value;
    const serviceCommand = document.getElementById("service-command").value;
    
    // Préparer les données à envoyer
    const data = {
        serviceName: serviceName,
        serviceDescription: serviceDescription,
        serviceCommand: serviceCommand
    };
    
    // Utiliser fetch pour envoyer les données au serveur
    fetch('/create_service', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('La requête a échoué');
        }
        return response.json();
    })
    .then(data => {
        console.log('Service créé:', data);
        alert("Service créé avec succès");
        modal.style.display = "none";
        setTimeout(() => {
            try {
                if(window.location.reload instanceof Function) {
                    window.location.reload(true);
                } else {
                    window.location.href = window.location.href;
                }
            } catch (error) {
                console.error('Error reloading the page:', error);
            }
        }, 100);
    })
    .catch((error) => {
        console.error('Erreur:', error);
        alert("Erreur lors de la création du service \n", error);
    });
};
