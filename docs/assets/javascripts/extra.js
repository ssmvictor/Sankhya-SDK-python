/* Custom JavaScript for Sankhya SDK Python Documentation */

document.addEventListener('DOMContentLoaded', function () {
    console.log('Sankhya SDK Documentation loaded - Enhanced Version');

    // Initialize custom features
    initScrollProgress();
    
    // Reveal animations on scroll
    // Add 'reveal' class to major blocks
    const articles = document.querySelectorAll('article > *');
    articles.forEach((el, index) => {
        if (index < 5) { // Animate first few elements immediately
             el.classList.add('reveal');
             el.style.animationDelay = `${index * 0.1}s`;
        } else {
             // Others will be triggered by scroll
             el.classList.add('reveal-on-scroll');
             // Initially hide them via CSS or just let the observer handle opacity if we had one
             // For simplicity, we'll reuse the PHP logic
             el.classList.add('reveal'); // Just add reveal for now as simple fade-in
        }
    });

    // MkDocs specific: Hook into copy button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.md-clipboard')) {
            showToast('Code copied to clipboard!', 'success');
        }
    });
});

// Scroll Progress Bar
function initScrollProgress() {
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress';
    document.body.appendChild(progressBar);
    
    window.addEventListener('scroll', () => {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight - windowHeight;
        const scrolled = window.scrollY;
        
        // Prevent division by zero
        if (documentHeight <= 0) {
            progressBar.style.width = '0%';
            return;
        }

        const progress = (scrolled / documentHeight) * 100;
        progressBar.style.width = `${progress}%`;
    });
}

// Toast Notification System
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    // Using simple SVG icons since we might not have Lucide loaded
    let iconSvg = '';
    if (type === 'success') {
        iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
    } else {
        iconSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
    }

    toast.innerHTML = `
        <div style="width: 20px; height: 20px; color: ${type === 'success' ? '#4EC9B0' : '#FF5555'}">${iconSvg}</div>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}