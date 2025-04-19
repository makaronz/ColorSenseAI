/**
 * ColorSenseAI Dashboard - Charts
 * This file contains the chart initialization and configuration
 */

// Chart configuration options
const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
        },
        tooltip: {
            mode: 'index',
            intersect: false,
        }
    }
};

// Initialize Dashboard Charts
function initDashboardCharts() {
    // Color Readings Chart
    const colorReadingsCtx = document.getElementById('colorReadingsChart').getContext('2d');
    const colorReadingsChart = new Chart(colorReadingsCtx, {
        type: 'line',
        data: dashboardData.colorReadings,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Color Temperature (K)'
                    }
                },
                y1: {
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Tint'
                    },
                    min: -10,
                    max: 10,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                ...chartOptions.plugins,
                tooltip: {
                    ...chartOptions.plugins.tooltip,
                    callbacks: {
                        afterFooter: function(tooltipItems) {
                            return 'Color temperature and tint are calculated using sensor fusion from AS7262, TSL2591, and SEN0611 data.';
                        }
                    }
                }
            }
        }
    });

    // Sensor Performance Chart
    const sensorPerformanceCtx = document.getElementById('sensorPerformanceChart').getContext('2d');
    const sensorPerformanceChart = new Chart(sensorPerformanceCtx, {
        type: 'bar',
        data: dashboardData.sensorPerformance,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            }
        }
    });

    // Initialize Map
    initSensorMap();
    
    // Initialize Raw Sensor Data Charts
    initRawSensorCharts();
    
    // Initialize Calculation Explanation
    initCalculationExplanation();
}

// Initialize Raw Sensor Data Charts
function initRawSensorCharts() {
    // AS7262 Spectral Sensor Chart
    const as7262ChartCtx = document.getElementById('as7262Chart').getContext('2d');
    const as7262Chart = new Chart(as7262ChartCtx, {
        type: 'line',
        data: {
            labels: timeLabels.day,
            datasets: [
                {
                    label: 'Violet (450nm)',
                    data: rawSensorData.AS7262.violet,
                    borderColor: 'rgba(93, 63, 211, 1)',
                    backgroundColor: 'rgba(93, 63, 211, 0.2)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Blue (500nm)',
                    data: rawSensorData.AS7262.blue,
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Green (550nm)',
                    data: rawSensorData.AS7262.green,
                    borderColor: 'rgba(46, 204, 113, 1)',
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Yellow (570nm)',
                    data: rawSensorData.AS7262.yellow,
                    borderColor: 'rgba(241, 196, 15, 1)',
                    backgroundColor: 'rgba(241, 196, 15, 0.2)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Orange (600nm)',
                    data: rawSensorData.AS7262.orange,
                    borderColor: 'rgba(230, 126, 34, 1)',
                    backgroundColor: 'rgba(230, 126, 34, 0.2)',
                    tension: 0.4,
                    fill: false
                },
                {
                    label: 'Red (650nm)',
                    data: rawSensorData.AS7262.red,
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.2)',
                    tension: 0.4,
                    fill: false
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Intensity'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });
    
    // TSL2591 Luminance Sensor Chart
    const tsl2591ChartCtx = document.getElementById('tsl2591Chart').getContext('2d');
    const tsl2591Chart = new Chart(tsl2591ChartCtx, {
        type: 'line',
        data: {
            labels: timeLabels.day,
            datasets: [
                {
                    label: 'Lux',
                    data: rawSensorData.TSL2591.lux,
                    borderColor: 'rgba(241, 196, 15, 1)',
                    backgroundColor: 'rgba(241, 196, 15, 0.2)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'IR',
                    data: rawSensorData.TSL2591.ir,
                    borderColor: 'rgba(155, 89, 182, 1)',
                    backgroundColor: 'rgba(155, 89, 182, 0.2)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Full Spectrum',
                    data: rawSensorData.TSL2591.fullSpectrum,
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });
    
    // SEN0611 CCT and ALS Sensor Chart
    const sen0611ChartCtx = document.getElementById('sen0611Chart').getContext('2d');
    const sen0611Chart = new Chart(sen0611ChartCtx, {
        type: 'line',
        data: {
            labels: timeLabels.day,
            datasets: [
                {
                    label: 'CCT (K)',
                    data: rawSensorData.SEN0611.cct,
                    borderColor: 'rgba(231, 76, 60, 1)',
                    backgroundColor: 'rgba(231, 76, 60, 0.2)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'ALS (lux)',
                    data: rawSensorData.SEN0611.als,
                    borderColor: 'rgba(46, 204, 113, 1)',
                    backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'CCT (K)'
                    },
                    position: 'left'
                },
                y1: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'ALS (lux)'
                    },
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            }
        }
    });
    
    // Optional GPS Module Chart
    if (document.getElementById('gpsChart')) {
        const gpsChartCtx = document.getElementById('gpsChart').getContext('2d');
        const gpsChart = new Chart(gpsChartCtx, {
            type: 'line',
            data: {
                labels: timeLabels.day,
                datasets: [
                    {
                        label: 'Satellites',
                        data: rawSensorData.GPS.satellites,
                        borderColor: 'rgba(52, 152, 219, 1)',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y'
                    },
                    {
                        label: 'HDOP',
                        data: rawSensorData.GPS.hdop,
                        borderColor: 'rgba(231, 76, 60, 1)',
                        backgroundColor: 'rgba(231, 76, 60, 0.2)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Satellites'
                        },
                        position: 'left'
                    },
                    y1: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'HDOP'
                        },
                        position: 'right',
                        grid: {
                            drawOnChartArea: false
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    }
}

// Initialize Calculation Explanation
function initCalculationExplanation() {
    // Get the current data point (using the middle of the day for example)
    const dataIndex = 6; // Noon
    
    // Get values from each sensor for the calculation example
    const as7262Data = {
        violet: rawSensorData.AS7262.violet[dataIndex],
        blue: rawSensorData.AS7262.blue[dataIndex],
        green: rawSensorData.AS7262.green[dataIndex],
        yellow: rawSensorData.AS7262.yellow[dataIndex],
        orange: rawSensorData.AS7262.orange[dataIndex],
        red: rawSensorData.AS7262.red[dataIndex],
        temperature: rawSensorData.AS7262.temperature[dataIndex]
    };
    
    const tsl2591Data = {
        lux: rawSensorData.TSL2591.lux[dataIndex],
        ir: rawSensorData.TSL2591.ir[dataIndex],
        fullSpectrum: rawSensorData.TSL2591.fullSpectrum[dataIndex]
    };
    
    const sen0611Data = {
        cct: rawSensorData.SEN0611.cct[dataIndex],
        als: rawSensorData.SEN0611.als[dataIndex]
    };
    
    // Calculate the color temperature and tint
    const calculatedCCT = calculatedColorData.whiteBalance.colorTemperature[dataIndex];
    const calculatedTint = calculatedColorData.whiteBalance.tint[dataIndex];
    
    // Update the calculation explanation in the DOM
    const calculationContainer = document.getElementById('calculation-steps');
    if (calculationContainer) {
        // Create the calculation explanation HTML
        let calculationHTML = `
            <h4>Step 1: Gather Raw Sensor Data</h4>
            <div class="calculation-data">
                <p><strong>AS7262 Spectral Data:</strong></p>
                <ul>
                    <li>Violet (450nm): ${as7262Data.violet}</li>
                    <li>Blue (500nm): ${as7262Data.blue}</li>
                    <li>Green (550nm): ${as7262Data.green}</li>
                    <li>Yellow (570nm): ${as7262Data.yellow}</li>
                    <li>Orange (600nm): ${as7262Data.orange}</li>
                    <li>Red (650nm): ${as7262Data.red}</li>
                    <li>Sensor Temperature: ${as7262Data.temperature}°C</li>
                </ul>
                
                <p><strong>TSL2591 Luminance Data:</strong></p>
                <ul>
                    <li>Luminance: ${tsl2591Data.lux} lux</li>
                    <li>IR: ${tsl2591Data.ir}</li>
                    <li>Full Spectrum: ${tsl2591Data.fullSpectrum}</li>
                </ul>
                
                <p><strong>SEN0611 CCT & ALS Data:</strong></p>
                <ul>
                    <li>CCT: ${sen0611Data.cct}K</li>
                    <li>ALS: ${sen0611Data.als} lux</li>
                </ul>
            </div>
            
            <h4>Step 2: Calculate Spectral Ratios</h4>
            <div class="calculation-formula">
                <p>Red/Blue Ratio = Red / Blue = ${as7262Data.red.toFixed(2)} / ${as7262Data.blue.toFixed(2)} = ${(as7262Data.red / as7262Data.blue).toFixed(3)}</p>
                <p>Green/Red Ratio = Green / Red = ${as7262Data.green.toFixed(2)} / ${as7262Data.red.toFixed(2)} = ${(as7262Data.green / as7262Data.red).toFixed(3)}</p>
                <p>Blue/Green Ratio = Blue / Green = ${as7262Data.blue.toFixed(2)} / ${as7262Data.green.toFixed(2)} = ${(as7262Data.blue / as7262Data.green).toFixed(3)}</p>
            </div>
            
            <h4>Step 3: Apply CCT Calculation Formula</h4>
            <div class="calculation-formula">
                <p>The CCT is calculated using the McCamy's formula based on the chromaticity coordinates derived from spectral data:</p>
                <p>CCT = 449 * (Red/Blue Ratio)^3 + 3525 * (Red/Blue Ratio)^2 - 6823.3 * (Red/Blue Ratio) + 5520.33</p>
                <p>CCT = 449 * (${(as7262Data.red / as7262Data.blue).toFixed(3)})^3 + 3525 * (${(as7262Data.red / as7262Data.blue).toFixed(3)})^2 - 6823.3 * (${(as7262Data.red / as7262Data.blue).toFixed(3)}) + 5520.33</p>
                <p>The SEN0611 CCT reading (${sen0611Data.cct}K) is used as a reference to validate and calibrate this calculation.</p>
            </div>
            
            <h4>Step 4: Calculate Tint Value</h4>
            <div class="calculation-formula">
                <p>Tint is calculated based on the Green/Red and Blue/Green ratios:</p>
                <p>Tint = 100 * (Green/Red Ratio - Blue/Green Ratio) / (Green/Red Ratio + Blue/Green Ratio)</p>
                <p>Tint = 100 * ((${(as7262Data.green / as7262Data.red).toFixed(3)}) - (${(as7262Data.blue / as7262Data.green).toFixed(3)})) / ((${(as7262Data.green / as7262Data.red).toFixed(3)}) + (${(as7262Data.blue / as7262Data.green).toFixed(3)}))</p>
                <p>Tint = 100 * (${((as7262Data.green / as7262Data.red) - (as7262Data.blue / as7262Data.green)).toFixed(3)}) / (${((as7262Data.green / as7262Data.red) + (as7262Data.blue / as7262Data.green)).toFixed(3)})</p>
                <p>Tint = 100 * (${((as7262Data.green / as7262Data.red) - (as7262Data.blue / as7262Data.green)).toFixed(3)} / ${((as7262Data.green / as7262Data.red) + (as7262Data.blue / as7262Data.green)).toFixed(3)})</p>
            </div>
            
            <h4>Step 5: Apply Sensor Fusion Algorithm</h4>
            <div class="calculation-formula">
                <p>The final CCT and Tint values are calculated using a weighted average of all sensor data:</p>
                <p>Final CCT = (0.6 * AS7262_CCT) + (0.1 * TSL2591_CCT_Estimate) + (0.3 * SEN0611_CCT)</p>
                <p>Final Tint = Tint_from_AS7262 * (1 + Correction_Factor)</p>
                <p>Where Correction_Factor is derived from the luminance readings of TSL2591 and SEN0611.</p>
            </div>
            
            <h4>Final Result</h4>
            <div class="calculation-result">
                <p>Color Temperature: <strong>${calculatedCCT}K</strong></p>
                <p>Tint: <strong>${calculatedTint}</strong> (negative values indicate magenta, positive values indicate green)</p>
            </div>
        `;
        
        calculationContainer.innerHTML = calculationHTML;
    }
}

// Initialize Spectral Analysis Charts
function initSpectralCharts() {
    // Spectral Distribution Chart
    const spectralDistributionCtx = document.getElementById('spectralDistributionChart').getContext('2d');
    const spectralDistributionChart = new Chart(spectralDistributionCtx, {
        type: 'line',
        data: spectralData.spectralDistribution,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Intensity'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Wavelength (nm)'
                    }
                }
            }
        }
    });

    // Color Accuracy Chart
    const colorAccuracyCtx = document.getElementById('colorAccuracyChart').getContext('2d');
    const colorAccuracyChart = new Chart(colorAccuracyCtx, {
        type: 'radar',
        data: spectralData.colorAccuracy,
        options: {
            ...chartOptions,
            scales: {
                r: {
                    beginAtZero: true,
                    min: 80,
                    max: 100,
                    ticks: {
                        stepSize: 5
                    }
                }
            }
        }
    });

    // Spectral Heatmap
    initSpectralHeatmap();
}

// Initialize Exposure Monitoring Charts
function initExposureCharts() {
    // Exposure Trends Chart
    const exposureTrendsCtx = document.getElementById('exposureTrendsChart').getContext('2d');
    const exposureTrendsChart = new Chart(exposureTrendsCtx, {
        type: 'line',
        data: exposureData.exposureTrends,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Light Exposure (lux)'
                    }
                }
            }
        }
    });

    // Daily Exposure Pattern Chart
    const dailyExposureCtx = document.getElementById('dailyExposureChart').getContext('2d');
    const dailyExposureChart = new Chart(dailyExposureCtx, {
        type: 'line',
        data: exposureData.dailyExposure,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Color Temperature (K)'
                    }
                }
            }
        }
    });
}

// Initialize Machine Learning Charts
function initMLCharts() {
    // Model Performance Chart
    const modelPerformanceCtx = document.getElementById('modelPerformanceChart').getContext('2d');
    const modelPerformanceChart = new Chart(modelPerformanceCtx, {
        type: 'line',
        data: mlData.modelPerformance,
        options: {
            ...chartOptions,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Accuracy (%)'
                    },
                    min: 85,
                    max: 100
                },
                y1: {
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Loss'
                    },
                    min: 0,
                    max: 0.1,
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });

    // Feature Importance Chart
    const featureImportanceCtx = document.getElementById('featureImportanceChart').getContext('2d');
    const featureImportanceChart = new Chart(featureImportanceCtx, {
        type: 'doughnut',
        data: mlData.featureImportance,
        options: {
            ...chartOptions,
            cutout: '50%'
        }
    });
}

// Initialize Sensor Map
function initSensorMap() {
    // Create map
    const map = L.map('sensorMap').setView([51.505, -0.09], 13);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    
    // Add markers for each sensor
    dashboardData.sensorMap.forEach(sensor => {
        const markerColor = sensor.status === 'online' ? '#2ECC71' : '#E74C3C';
        const markerIcon = L.divIcon({
            className: 'sensor-marker',
            html: `<div style="background-color: ${markerColor}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
            iconSize: [12, 12],
            iconAnchor: [6, 6]
        });
        
        const marker = L.marker([sensor.lat, sensor.lng], { icon: markerIcon }).addTo(map);
        marker.bindPopup(`
            <div class="map-popup">
                <h3>${sensor.name}</h3>
                <p>Type: ${sensor.type}</p>
                <p>Status: <span style="color: ${markerColor}">${sensor.status}</span></p>
            </div>
        `);
    });
}

// Initialize Spectral Heatmap
function initSpectralHeatmap() {
    const spectralHeatmapCtx = document.getElementById('spectralHeatmapChart').getContext('2d');
    
    // Create a custom heatmap using canvas
    const width = spectralHeatmapCtx.canvas.width;
    const height = spectralHeatmapCtx.canvas.height;
    const data = spectralData.spectralHeatmap.data;
    const cellWidth = width / data[0].length;
    const cellHeight = height / data.length;
    
    // Draw heatmap
    for (let y = 0; y < data.length; y++) {
        for (let x = 0; x < data[y].length; x++) {
            const value = data[y][x];
            const intensity = value / 100;
            
            // Create a color gradient from blue (cold) to red (hot)
            const r = Math.floor(255 * Math.min(1, intensity * 2));
            const g = Math.floor(255 * Math.min(1, 2 - intensity * 2));
            const b = Math.floor(255 * Math.max(0, 1 - intensity * 2));
            
            spectralHeatmapCtx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            spectralHeatmapCtx.fillRect(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
        }
    }
    
    // Add legend
    spectralHeatmapCtx.fillStyle = '#2C3E50';
    spectralHeatmapCtx.font = '14px Roboto';
    spectralHeatmapCtx.fillText('Spectral Intensity', 20, 20);
    
    // Draw legend gradient
    const gradientWidth = 200;
    const gradientHeight = 20;
    const gradient = spectralHeatmapCtx.createLinearGradient(width - gradientWidth - 20, height - gradientHeight - 20, width - 20, height - gradientHeight - 20);
    gradient.addColorStop(0, 'rgb(0, 0, 255)');
    gradient.addColorStop(0.5, 'rgb(0, 255, 0)');
    gradient.addColorStop(1, 'rgb(255, 0, 0)');
    
    spectralHeatmapCtx.fillStyle = gradient;
    spectralHeatmapCtx.fillRect(width - gradientWidth - 20, height - gradientHeight - 20, gradientWidth, gradientHeight);
    
    // Add legend labels
    spectralHeatmapCtx.fillStyle = '#2C3E50';
    spectralHeatmapCtx.font = '12px Roboto';
    spectralHeatmapCtx.fillText('Low', width - gradientWidth - 20, height - 5);
    spectralHeatmapCtx.fillText('High', width - 20, height - 5);
}

// Initialize all charts when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts for the active panel
    const activePanel = document.querySelector('.panel.active');
    if (activePanel) {
        const panelId = activePanel.id;
        
        if (panelId === 'dashboard-panel') {
            initDashboardCharts();
        } else if (panelId === 'spectral-panel') {
            initSpectralCharts();
        } else if (panelId === 'exposure-panel') {
            initExposureCharts();
        } else if (panelId === 'ml-panel') {
            initMLCharts();
        }
    }
    
    // Initialize charts when switching panels
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const panelId = this.getAttribute('data-panel');
            
            if (panelId === 'dashboard') {
                initDashboardCharts();
            } else if (panelId === 'spectral') {
                initSpectralCharts();
            } else if (panelId === 'exposure') {
                initExposureCharts();
            } else if (panelId === 'ml') {
                initMLCharts();
            }
        });
    });
});