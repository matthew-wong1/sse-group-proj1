const popup = document.getElementById('alert-popup');
    function hidePopup() {
        popup.classList.remove('opacity-100'); // Remove opacity class
        popup.classList.add('opacity-0'); // Add class to fade out
        setTimeout(() => {
            popup.style.display = 'none';
        }, 500);
    }

    if (show_alert) {
        setTimeout(hidePopup, 5000)
    }