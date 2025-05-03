/**
 * EventLink - glavna JavaScript datoteka
 * Vsebuje funkcionalnosti za animacije, validacije in interakcije uporabniških vmesnikov
 */

document.addEventListener('DOMContentLoaded', function() {
    // Animate cards on hover
    const eventCards = document.querySelectorAll('.card');
    eventCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
            this.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.2)';
            this.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
            this.style.transition = 'all 0.3s ease';
        });
    });
    
    // Add fade-in effect for flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        message.style.opacity = '0';
        message.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            message.style.opacity = '1';
        }, 100);
        
        // Auto-dismiss flash messages after 5 seconds
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
    });
    
    // Form validation for registration and profile editing
    const passwordForm = document.querySelector('form');
    
    if (passwordForm) {
        // Preveri, če obrazec vsebuje polja za geslo
        const passwordField = document.getElementById('password') || document.getElementById('new_password');
        const confirmField = document.getElementById('confirm_password');
        
        if (passwordField && confirmField) {
            passwordForm.addEventListener('submit', function(event) {
                if (passwordField.value && confirmField.value) {
                    if (passwordField.value !== confirmField.value) {
                        event.preventDefault();
                        
                        // Create password mismatch alert
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'alert alert-danger';
                        alertDiv.textContent = 'Gesli se ne ujemata!';
                        alertDiv.role = 'alert';
                        
                        // Insert alert before form
                        this.parentNode.insertBefore(alertDiv, this);
                        
                        // Highlight password fields
                        passwordField.classList.add('is-invalid');
                        confirmField.classList.add('is-invalid');
                        
                        // Auto-dismiss alert after 5 seconds
                        setTimeout(() => {
                            alertDiv.style.opacity = '0';
                            alertDiv.style.transition = 'opacity 0.5s ease';
                            setTimeout(() => {
                                alertDiv.remove();
                            }, 500);
                        }, 5000);
                    }
                }
            });
        }
    }
    
    // Add date validation - prevent future dates for date of birth
    const dateOfBirthField = document.getElementById('date_of_birth');
    if (dateOfBirthField) {
        const today = new Date().toISOString().split('T')[0];
        dateOfBirthField.setAttribute('max', today);
        
        // Add tooltip for date field
        dateOfBirthField.setAttribute('title', 'Izberite svoj datum rojstva');
        dateOfBirthField.setAttribute('data-bs-toggle', 'tooltip');
        dateOfBirthField.setAttribute('data-bs-placement', 'top');
        
        // Initialize tooltip for this element
        try {
            new bootstrap.Tooltip(dateOfBirthField);
        } catch (e) {
            console.warn('Bootstrap Tooltip ni na voljo, ignoriramo:', e);
        }
    }
    
    // Initialize all tooltips if Bootstrap is available
    try {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
        }
    } catch (e) {
        console.warn('Bootstrap Tooltips ni na voljo:', e);
    }
    
    // Add smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            
            // Skip if targeting just '#'
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add loading animation for form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                // Save original button text
                const originalText = submitButton.innerHTML;
                
                // Change to loading spinner
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Nalaganje...';
                submitButton.disabled = true;
                
                // Restore original state if form submission takes too long (for demo purposes)
                setTimeout(() => {
                    if (submitButton.disabled) {
                        submitButton.innerHTML = originalText;
                        submitButton.disabled = false;
                    }
                }, 10000);
            }
        });
    });
    
    // Add confirmation for logout
    const logoutLink = document.querySelector('a[href*="logout"]');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            const confirmLogout = confirm('Ali ste prepričani, da se želite odjaviti?');
            if (!confirmLogout) {
                e.preventDefault();
            }
        });
    }
    
    // Invoke the background color update function
    updateBackgroundColor();
});

// Add dynamic background color change based on time of day
function updateBackgroundColor() {
    const hour = new Date().getHours();
    const body = document.body;
    
    // Night mode (8 PM - 6 AM)
    if (hour >= 20 || hour < 6) {
        body.style.backgroundColor = '#f0f4f8';
        body.style.transition = 'background-color 1s ease';
    } 
    // Morning (6 AM - 12 PM)
    else if (hour >= 6 && hour < 12) {
        body.style.backgroundColor = '#f8f9fa';
        body.style.transition = 'background-color 1s ease';
    } 
    // Afternoon (12 PM - 5 PM)
    else if (hour >= 12 && hour < 17) {
        body.style.backgroundColor = '#fff';
        body.style.transition = 'background-color 1s ease';
    } 
    // Evening (5 PM - 8 PM)
    else {
        body.style.backgroundColor = '#f5f5f5';
        body.style.transition = 'background-color 1s ease';
    }
}

// Run on page load and then every hour
setInterval(updateBackgroundColor, 3600000); // Update every hour (3600000 ms)