document.addEventListener('DOMContentLoaded', function() {
    const usernameForm = document.getElementById('username-form');
    if (usernameForm) {
        usernameForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = {
                new_username: formData.get('new_username'),
                current_password: formData.get('current_password')
            };
            const messageEl = document.getElementById('username-message');
            try {
                const response = await fetch('/api/user/change-username', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                if (response.ok) {
                    messageEl.className = 'message success';
                    messageEl.textContent = result.message;
                    document.getElementById('current-username').textContent = data.new_username;
                    e.target.reset();
                } else {
                    messageEl.className = 'message error';
                    messageEl.textContent = result.error || 'Erreur';
                }
            } catch (error) {
                messageEl.className = 'message error';
                messageEl.textContent = 'Erreur de connexion';
            }
        });
    }

    const passwordForm = document.getElementById('password-form');
    if (passwordForm) {
        passwordForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            const messageDiv = document.getElementById('password-message');
            
            // Validation côté client
            if (newPassword !== confirmPassword) {
                showMessage(messageDiv, 'Les nouveaux mots de passe ne correspondent pas', 'error');
                return;
            }
            
            if (newPassword.length < 6) {
                showMessage(messageDiv, 'Le nouveau mot de passe doit contenir au moins 6 caractères', 'error');
                return;
            }
            
            // Envoi de la requête
            fetch('/api/user/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                    confirm_password: confirmPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(messageDiv, data.message || 'Mot de passe modifié avec succès', 'success');
                    // Réinitialiser le formulaire
                    document.getElementById('password-form').reset();
                } else {
                    showMessage(messageDiv, data.error || 'Erreur lors de la modification', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage(messageDiv, 'Erreur de communication avec le serveur', 'error');
            });
        });
    }
});

function showMessage(element, message, type) {
    element.textContent = message;
    element.className = 'message ' + type;
    element.style.display = 'block';
    
    // Masquer le message après 5 secondes
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}
