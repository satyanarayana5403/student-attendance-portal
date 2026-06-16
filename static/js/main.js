// Page loader
window.addEventListener('load', () => {
    setTimeout(() => {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.classList.add('gone');
            setTimeout(() => loader.remove(), 600);
        }
    }, 400);
});

// Flash message close buttons & auto-dismiss
document.querySelectorAll('.flash').forEach(flash => {
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
        if (document.body.contains(flash)) {
            flash.classList.add('flash-dismissing');
            setTimeout(() => flash.remove(), 300);
        }
    }, 4000);
    
    const btn = flash.querySelector('.flash-close');
    if (btn) {
        btn.addEventListener('click', () => {
            flash.classList.add('flash-dismissing');
            setTimeout(() => flash.remove(), 300);
        });
    }
});

// Global theme toggle function
function toggleTheme() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    if (isLight) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
    }
    // Dispatch event for other scripts to update
    window.dispatchEvent(new Event('theme_changed'));
    
    // If the toggle element exists, update it visually (mostly for settings page)
    const toggle = document.querySelector('[data-setting="dark_mode"]');
    if (toggle) {
        if (!isLight) toggle.classList.add('on');
        else toggle.classList.remove('on');
    }
    
    // Update simple dark mode buttons dynamically
    document.querySelectorAll('.dark-mode-btn').forEach(btn => {
        btn.textContent = !isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
    });
}