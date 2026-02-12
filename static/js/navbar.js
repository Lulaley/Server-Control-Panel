function toggleDropdown(event) {
    event.preventDefault();
    event.stopPropagation();
    
    const dropdown = event.target.closest('.dropdown');
    const content = dropdown.querySelector('.dropdown-content');
    
    // Fermer tous les autres dropdowns
    document.querySelectorAll('.dropdown-content.show').forEach(function(openDropdown) {
        if (openDropdown !== content) {
            openDropdown.classList.remove('show');
            openDropdown.closest('.dropdown').classList.remove('active');
        }
    });
    
    // Toggle le dropdown actuel
    if (content.classList.contains('show')) {
        content.classList.remove('show');
        dropdown.classList.remove('active');
    } else {
        content.classList.add('show');
        dropdown.classList.add('active');
    }
}

// Fermer le dropdown si on clique en dehors
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown-content.show').forEach(function(dropdown) {
            dropdown.classList.remove('show');
            dropdown.closest('.dropdown').classList.remove('active');
        });
    }
});

// Fermer le dropdown avec la touche Echap
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('.dropdown-content.show').forEach(function(dropdown) {
            dropdown.classList.remove('show');
            dropdown.closest('.dropdown').classList.remove('active');
        });
    }
});
