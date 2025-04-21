/**
 * ColorSenseAI Dashboard - Main JavaScript
 * This file contains the main interaction logic for the dashboard
 */

// Debounce helper function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Error handling wrapper
function handleError(fn) {
    return function wrapper(...args) {
        try {
            return fn.apply(this, args);
        } catch (error) {
            console.error('Error in event handler:', error);
            // You might want to show this to the user in a more friendly way
            showError('An error occurred. Please try again or contact support if the problem persists.');
        }
    };
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    let isDarkMode = false;
    let currentPanel = 'dashboard';
    let eventListeners = new Map(); // Store event listeners for cleanup
    
    // Toggle sidebar
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    
    const toggleSidebar = handleError(() => {
        sidebar.classList.toggle('collapsed');
        document.querySelector('.content').classList.toggle('expanded');
    });
    
    menuToggle.addEventListener('click', toggleSidebar);
    eventListeners.set(menuToggle, { event: 'click', handler: toggleSidebar });
    
    // Toggle right sidebar
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const rightSidebar = document.getElementById('right-sidebar');
    
    const toggleRightSidebar = handleError(function() {
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
    
    sidebarToggleBtn.addEventListener('click', toggleRightSidebar);
    eventListeners.set(sidebarToggleBtn, { event: 'click', handler: toggleRightSidebar });
    
    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const panels = document.querySelectorAll('.panel');
    
    navItems.forEach(item => {
        const navHandler = handleError((e) => {
            e.preventDefault();
            
            // Remove active class from all elements
            navItems.forEach(nav => nav.classList.remove('active'));
            
            // Add active class to clicked element
            item.classList.add('active');
            
            // Update active panel
            const panelId = item.querySelector('a').getAttribute('href').substring(1);
            switchPanel(panelId);
        });
        
        item.addEventListener('click', navHandler);
        eventListeners.set(item, { event: 'click', handler: navHandler });
    });
    
    // Time filter buttons
    const timeButtons = document.querySelectorAll('.time-filter .btn');
    
    timeButtons.forEach(button => {
        const timeHandler = handleError(() => {
            timeButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            updateCharts(button.textContent.toLowerCase());
        });
        
        button.addEventListener('click', timeHandler);
        eventListeners.set(button, { event: 'click', handler: timeHandler });
    });
    
    // Notification handling
    const notificationBtn = document.querySelector('.notification-btn');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    
    const toggleNotification = handleError((e) => {
        e.stopPropagation();
        notificationDropdown.style.display = notificationDropdown.style.display === 'block' ? 'none' : 'block';
    });
    
    const closeNotification = handleError((e) => {
        if (!notificationBtn.contains(e.target) && !notificationDropdown.contains(e.target)) {
            notificationDropdown.style.display = 'none';
        }
    });
    
    notificationBtn.addEventListener('click', toggleNotification);
    document.addEventListener('click', closeNotification);
    
    eventListeners.set(notificationBtn, { event: 'click', handler: toggleNotification });
    eventListeners.set(document, { event: 'click', handler: closeNotification });
    
    // Mobile navigation with debounce
    const handleResize = debounce(() => {
        if (window.innerWidth <= 767) {
            sidebar.classList.add('collapsed');
            sidebar.classList.remove('active');
        } else {
            sidebar.classList.remove('active');
        }
    }, 250); // 250ms debounce
    
    window.addEventListener('resize', handleResize);
    eventListeners.set(window, { event: 'resize', handler: handleResize });
    
    // Card action buttons
    const cardActionBtns = document.querySelectorAll('.card-action-btn');
    
    cardActionBtns.forEach(btn => {
        const cardHandler = handleError(function() {
            // Implement card actions like export, refresh, etc.
            console.log('Card action clicked');
        });
        
        btn.addEventListener('click', cardHandler);
        eventListeners.set(btn, { event: 'click', handler: cardHandler });
    });
    
    // Sensor action buttons
    const sensorActionBtns = document.querySelectorAll('.sensor-action-btn');
    
    sensorActionBtns.forEach(btn => {
        const sensorHandler = handleError(function() {
            // Implement sensor actions like configure, restart, etc.
            console.log('Sensor action clicked');
        });
        
        btn.addEventListener('click', sensorHandler);
        eventListeners.set(btn, { event: 'click', handler: sensorHandler });
    });
    
    // Initialize tooltips
    initTooltips();
    
    // Cleanup function
    function cleanup() {
        eventListeners.forEach((value, element) => {
            element.removeEventListener(value.event, value.handler);
        });
        eventListeners.clear();
    }
    
    // Helper functions
    function switchPanel(panelId) {
        const panels = document.querySelectorAll('.panel');
        panels.forEach(panel => {
            panel.classList.remove('active');
            panel.style.display = 'none';
        });
        
        const activePanel = document.getElementById(`${panelId}-panel`);
        if (activePanel) {
            activePanel.style.display = 'block';
            setTimeout(() => {
                activePanel.classList.add('active');
            }, 10);
        }
        
        currentPanel = panelId;
        updateCharts();
    }
    
    // Single updateSensorData function
    function updateSensorData(data) {
        try {
            // Update sensor readings
            document.getElementById('temperature').textContent = data.temperature ? `${data.temperature}°C` : 'N/A';
            document.getElementById('humidity').textContent = data.humidity ? `${data.humidity}%` : 'N/A';
            document.getElementById('light').textContent = data.light ? `${data.light} lux` : 'N/A';
            document.getElementById('color-temp').textContent = data.colorTemp ? `${data.colorTemp}K` : 'N/A';
            
            // Update status indicators
            updateStatusIndicators(data);
            
            // Update charts if they exist
            if (window.colorTempChart && data.colorTemp) {
                updateColorTempChart(data);
            }
            if (window.lightExposureChart && data.light) {
                updateLightExposureChart(data);
            }
        } catch (error) {
            console.error('Error updating sensor data:', error);
            showError('Failed to update sensor data');
        }
    }
    
    function showError(message) {
        // Implement error display logic here
        console.error(message);
        // You might want to show this in a toast or notification
    }
    
    // Attach cleanup to window unload
    window.addEventListener('unload', cleanup);
    eventListeners.set(window, { event: 'unload', handler: cleanup });
    
    // Initialize charts
    initCharts();
});

// Function to update ML insights data
function updateMLInsights(data) {
    document.getElementById('ml-cct-prediction').textContent = data.ml_cct_prediction || 'N/A';
    document.getElementById('ml-illuminance-prediction').textContent = data.ml_illuminance_prediction || 'N/A';
    document.getElementById('ml-color-category').textContent = data.ml_color_category || 'N/A';
}

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

function updateSensorData(sensorData) {
    // Update sensor data for charts and raw data display
    updateRawDataDisplay(sensorData);
    updateSpectralCharts(sensorData);
    updateExposureIndicators(sensorData);

    // Update ML insights if available
    if (sensorData.ml_insights) {
        updateMLInsights(sensorData.ml_insights);
    }
}

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