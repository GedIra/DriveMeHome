document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const hamburgerButton = document.getElementById('hamburger-button');
    const overlay = document.getElementById('overlay');

    function setSidebarOpen(open) {
        if (!sidebar || !overlay) return;
        if (open) {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
            if (hamburgerButton) hamburgerButton.setAttribute('aria-expanded', 'true');
        } else {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
            if (hamburgerButton) hamburgerButton.setAttribute('aria-expanded', 'false');
        }
    }

    function toggleSidebar() {
        if (!sidebar || !overlay) return;
        const isOpen = !sidebar.classList.contains('-translate-x-full');
        setSidebarOpen(!isOpen);
    }

    if (hamburgerButton) {
        hamburgerButton.setAttribute('aria-controls', 'sidebar');
        hamburgerButton.setAttribute('aria-expanded', 'false');
        hamburgerButton.addEventListener('click', function (event) {
            event.stopPropagation();
            toggleSidebar();
        });
    }

    if (overlay) {
        overlay.addEventListener('click', function () {
            toggleSidebar();
        });
    }

    const closeSidebarButton = document.getElementById('close-sidebar-button');
    if (closeSidebarButton) {
        closeSidebarButton.addEventListener('click', function (e) {
            e.stopPropagation();
            setSidebarOpen(false);
        });
    }

    // Close sidebar on Escape
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (sidebar && !sidebar.classList.contains('-translate-x-full')) {
                setSidebarOpen(false);
            }
        }
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (e) {
        if (!sidebar || !hamburgerButton || !overlay) return;
        const clickedInside = sidebar.contains(e.target) || hamburgerButton.contains(e.target) || !overlay.classList.contains('hidden') && overlay.contains(e.target);
        if (!clickedInside && !overlay.classList.contains('hidden')) {
            setSidebarOpen(false);
        }
    });

    function checkScreenSize() {
        if (window.innerWidth >= 1024) {
            // Ensure sidebar visible on large screens
            if (sidebar) sidebar.classList.remove('-translate-x-full');
            if (overlay) overlay.classList.add('hidden');
            if (hamburgerButton) hamburgerButton.setAttribute('aria-expanded', 'true');
        } else {
            // Ensure sidebar hidden by default on small screens
            if (sidebar) sidebar.classList.add('-translate-x-full');
            if (overlay) overlay.classList.add('hidden');
            if (hamburgerButton) hamburgerButton.setAttribute('aria-expanded', 'false');
        }
    }

    // Initial check
    checkScreenSize();

    // Update on resize
    window.addEventListener('resize', checkScreenSize);
});
