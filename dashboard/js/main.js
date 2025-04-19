/**
 * ColorSenseAI Dashboard - Main JavaScript
 * This file contains the main interaction logic for the dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    
    menuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        document.querySelector('.content').classList.toggle('sidebar-collapsed');
    });
    
    // Toggle right sidebar
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const rightSidebar = document.getElementById('right-sidebar');
    
    sidebarToggleBtn.addEventListener('click', function() {
        rightSidebar.classList.toggle('collapsed');
        
        // Change icon direction
        const icon = this.querySelector('i');
        if (rightSidebar.classList.contains('collapsed')) {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-left');
        } else {
            icon.classList.remove('fa-chevron-left');
            icon.classList.add('fa-chevron-right');
        }
    });
    
    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const panels = document.querySelectorAll('.panel');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all nav items
            navItems.forEach(navItem => {
                navItem.classList.remove('active');
            });
            
            // Add active class to clicked nav item
            this.classList.add('active');
            
            // Get panel id
            const panelId = this.getAttribute('data-panel');
            
            // Hide all panels
            panels.forEach(panel => {
                panel.classList.remove('active');
            });
            
            // Show selected panel
            if (panelId) {
                const panel = document.getElementById(`${panelId}-panel`);
                if (panel) {
                    panel.classList.add('active');
                }
            }
            
            // On mobile, close sidebar after navigation
            if (window.innerWidth <= 767) {
                sidebar.classList.remove('active');
            }
        });
    });
    
    // Time filter buttons
    const timeButtons = document.querySelectorAll('.time-btn');
    
    timeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all time buttons in the same filter
            const parentFilter = this.closest('.time-filter');
            parentFilter.querySelectorAll('.time-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Here you would update the charts based on the selected time period
            // For this prototype, we'll just log the selected period
            console.log('Selected time period:', this.textContent);
        });
    });
    
    // Notification dropdown
    const notificationBtn = document.querySelector('.notification-btn');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    
    notificationBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationDropdown.style.display = notificationDropdown.style.display === 'block' ? 'none' : 'block';
    });
    
    // Close notification dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!notificationBtn.contains(e.target) && !notificationDropdown.contains(e.target)) {
            notificationDropdown.style.display = 'none';
        }
    });
    
    // Mobile navigation
    if (window.innerWidth <= 767) {
        sidebar.classList.add('collapsed');
        
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }
    
    // Responsive adjustments
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 767) {
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('active');
        } else {
            sidebar.classList.remove('active');
        }
    });
    
    // Card action buttons
    const cardActionBtns = document.querySelectorAll('.card-action-btn');
    
    cardActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Here you would implement card actions like export, refresh, etc.
            console.log('Card action clicked');
        });
    });
    
    // Sensor action buttons
    const sensorActionBtns = document.querySelectorAll('.sensor-action-btn');
    
    sensorActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Here you would implement sensor actions like configure, restart, etc.
            console.log('Sensor action clicked');
        });
    });
    
    // Initialize tooltips (if needed)
    initTooltips();
});

// Initialize tooltips
function initTooltips() {
    // This is a placeholder for tooltip initialization
    // You could use a library like Tippy.js or implement custom tooltips
    console.log('Tooltips initialized');
}

// Handle errors gracefully
window.addEventListener('error', function(e) {
    console.error('An error occurred:', e.error);
    // You could implement a more user-friendly error handling here
});

// Add a simple loading indicator
function showLoading() {
    // Create loading element if it doesn't exist
    if (!document.getElementById('loading-indicator')) {
        const loading = document.createElement('div');
        loading.id = 'loading-indicator';
        loading.innerHTML = '<div class="spinner"></div>';
        loading.style.position = 'fixed';
        loading.style.top = '0';
        loading.style.left = '0';
        loading.style.width = '100%';
        loading.style.height = '100%';
        loading.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
        loading.style.display = 'flex';
        loading.style.justifyContent = 'center';
        loading.style.alignItems = 'center';
        loading.style.zIndex = '9999';
        
        const spinner = loading.querySelector('.spinner');
        spinner.style.width = '40px';
        spinner.style.height = '40px';
        spinner.style.border = '4px solid #f3f3f3';
        spinner.style.borderTop = '4px solid #3498db';
        spinner.style.borderRadius = '50%';
        spinner.style.animation = 'spin 1s linear infinite';
        
        // Add keyframes for spinner animation
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(loading);
    } else {
        document.getElementById('loading-indicator').style.display = 'flex';
    }
}

function hideLoading() {
    const loading = document.getElementById('loading-indicator');
    if (loading) {
        loading.style.display = 'none';
    }
}

// Example of how to use the loading indicator
// showLoading();
// setTimeout(hideLoading, 2000);