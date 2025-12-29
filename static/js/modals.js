document.addEventListener('DOMContentLoaded', function() {
    function showModalById(id) {
        const modal = document.getElementById(id);
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('overflow-hidden');
    }

    function hideModalById(id) {
        const modal = document.getElementById(id);
        if (!modal) return;
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('overflow-hidden');
    }

    // Toggle buttons
    document.querySelectorAll('[data-modal-toggle]').forEach(btn => {
        const target = btn.getAttribute('data-modal-target') || btn.getAttribute('data-modal-toggle');
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!target) return;
            const modal = document.getElementById(target);
            if (!modal) return;
            if (modal.classList.contains('hidden')) showModalById(target); else hideModalById(target);
        });
    });

    // Hide buttons
    document.querySelectorAll('[data-modal-hide]').forEach(btn => {
        const target = btn.getAttribute('data-modal-hide');
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!target) return;
            hideModalById(target);
        });
    });

    // Click outside to close: if click target is the modal container itself
    document.querySelectorAll('[id^="review-modal-"]').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.add('hidden');
                modal.setAttribute('aria-hidden', 'true');
                document.body.classList.remove('overflow-hidden');
            }
        });
    });

    // Escape key closes any open modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('[id^="review-modal-"], [id^="ride-modal-"]').forEach(modal => {
                if (!modal.classList.contains('hidden')) {
                    modal.classList.add('hidden');
                    modal.setAttribute('aria-hidden', 'true');
                }
            });
            document.body.classList.remove('overflow-hidden');
        }
    });

    // Try to initialize Flowbite Modal instances (if Flowbite exposes a constructor) to avoid console warnings
    try {
        if (window.Modal && typeof window.Modal === 'function') {
            document.querySelectorAll('[id^="review-modal-"], [id^="ride-modal-"]').forEach(modalEl => {
                try {
                    // If Flowbite's Modal accepts (element, options)
                    new window.Modal(modalEl);
                } catch (innerErr) {
                    // ignore if constructor signature differs
                }
            });
        }
    } catch (err) {
        // ignore
    }

});
