/* Base Scripts */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initThemeToggle();
    initFullscreenToggle();
    initTooltips();
});

/* Sidebar Toggle */
function initSidebar() {
    const toggleButton = document.querySelector('[data-sidebar-toggle]');
    const sidebar = document.getElementById('admin-sidebar');
    const wrapper = document.getElementById('admin-wrapper');
    const overlay = document.getElementById('sidebarOverlay');

    function isMobile() {
        return window.innerWidth < 992;
    }

    if (toggleButton && sidebar && wrapper) {
        // Set initial state
        if (!isMobile()) {
            const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
            if (isCollapsed) {
                wrapper.classList.add('sidebar-collapsed');
                toggleButton.classList.add('is-active');
            }
        }

        // Toggle click handler
        toggleButton.addEventListener('click', (e) => {
            e.stopPropagation();
            
            if (isMobile()) {
                // Mobile: slide sidebar and show overlay
                sidebar.classList.toggle('show');
                overlay.classList.toggle('show');
            } else {
                // Desktop: collapse sidebar
                const isCurrentlyCollapsed = wrapper.classList.contains('sidebar-collapsed');
                
                if (isCurrentlyCollapsed) {
                    wrapper.classList.remove('sidebar-collapsed');
                    toggleButton.classList.remove('is-active');
                    localStorage.setItem('sidebar-collapsed', 'false');
                } else {
                    wrapper.classList.add('sidebar-collapsed');
                    toggleButton.classList.add('is-active');
                    localStorage.setItem('sidebar-collapsed', 'true');
                }
            }
        });

        // Close sidebar when clicking overlay (mobile only)
        if (overlay) {
            overlay.addEventListener('click', () => {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            });
        }

        // Close sidebar when clicking a link (mobile only)
        const sidebarLinks = sidebar.querySelectorAll('.nav-link');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (isMobile()) {
                    sidebar.classList.remove('show');
                    overlay.classList.remove('show');
                }
            });
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (!isMobile()) {
                // Remove mobile classes on desktop
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            } else {
                // Remove desktop classes on mobile
                wrapper.classList.remove('sidebar-collapsed');
                toggleButton.classList.remove('is-active');
            }
        });
    }
}

/* Theme Toggle */
function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIconLight = document.getElementById('themeIconLight');
    const themeIconDark = document.getElementById('themeIconDark');
    const html = document.documentElement;

    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-bs-theme', savedTheme);
    
    if (savedTheme === 'dark') {
        themeIconLight.classList.add('d-none');
        themeIconDark.classList.remove('d-none');
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            if (newTheme === 'dark') {
                themeIconLight.classList.add('d-none');
                themeIconDark.classList.remove('d-none');
            } else {
                themeIconLight.classList.remove('d-none');
                themeIconDark.classList.add('d-none');
            }
        });
    }
}

/* Fullscreen Toggle */
function initFullscreenToggle() {
    const fullscreenToggle = document.getElementById('fullscreenToggle');
    
    if (fullscreenToggle) {
        fullscreenToggle.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                }
            }
        });
    }
}

/* Initialize Bootstrap Tooltips */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}