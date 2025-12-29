document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const hamburgerButton = document.getElementById('hamburger-button');
    const overlay = document.getElementById('overlay');
    const closeSidebarButton = document.getElementById('close-sidebar-button');

    // This function only controls the "mobile" open/closed state by toggling classes
    function setMobileSidebar(isOpen) {
        if (isOpen) {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
            if (hamburgerButton) hamburgerButton.setAttribute('aria-expanded', 'true');
        } else {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
            if (hamburgerButton) hamburgerButton.setAttribute('aria-expanded', 'false');
        }
    }

    // --- Event Listeners ---

    // Toggle sidebar on hamburger button click
    if (hamburgerButton) {
        hamburgerButton.addEventListener('click', function (e) {
            e.stopPropagation();
            const isCurrentlyClosed = sidebar.classList.contains('-translate-x-full');
            setMobileSidebar(isCurrentlyClosed);
        });
    }

    // Close sidebar with the close button inside it
    if (closeSidebarButton) {
        closeSidebarButton.addEventListener('click', function(e) {
            e.stopPropagation();
            setMobileSidebar(false);
        });
    }

    // Close sidebar when clicking on the overlay
    if (overlay) {
        overlay.addEventListener('click', () => setMobileSidebar(false));
    }

    // Close sidebar with the Escape key on mobile
    document.addEventListener('keydown', (e) => {
        // Only handle Escape key on mobile view when the sidebar is open
        if (window.innerWidth < 1024 && e.key === 'Escape' && !sidebar.classList.contains('-translate-x-full')) {
            setMobileSidebar(false);
        }
    });

    // Reset sidebar state on window resize to prevent weird states
    window.addEventListener('resize', () => {
        // If resizing to desktop, ensure the mobile overlay is hidden.
        // The sidebar visibility is handled by Tailwind's `lg:` variants.
        if (window.innerWidth >= 1024) {
            overlay.classList.add('hidden');
        }
        // If resizing and the sidebar is open, close it to avoid visual glitches
        else if (!sidebar.classList.contains('-translate-x-full')) {
            setMobileSidebar(false);
        }
    });

    // --- Initial State ---
    
    // Set ARIA attributes for accessibility
    if (hamburgerButton) {
        hamburgerButton.setAttribute('aria-controls', 'sidebar');
        hamburgerButton.setAttribute('aria-expanded', 'false');
    }
});