/**
 * ColorSenseAI Dashboard - Charts
 * This file contains the chart initialization, data loading, and update logic.
 */

// --- Global Variables ---
let simulatedData = [];
let currentDataIndex = 0;
let chartInstances = {}; // To store chart instances for updates
const DATA_FILE_PATH = '../data/simulated_dashboard_data.csv'; // Relative path from js/ to data/
const UPDATE_INTERVAL = 500; // ms (2Hz refresh rate)
let updateIntervalId = null; // To store the interval ID
const dataFilter = new ColorScience.DataFilter(10); // Initialize data filter with window size 10
let targetCCT = 5600; // Default target CCT for camera calibration (5600K)

// --- Chart Configuration ---
const baseChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 500 // Smoother transitions
    },
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

// --- Data Loading and Processing ---

/**
 * Loads and parses CSV data using PapaParse.
 */
function loadAndProcessData() {
    console.log(`Attempting to load data from: ${DATA_FILE_PATH}`);
    showLoading(); // Show loading indicator from main.js

    Papa.parse(DATA_FILE_PATH, {
        download: true,
        header: true,
        dynamicTyping: true, // Automatically convert types
        skipEmptyLines: true,
        complete: (results) => {
            console.log("CSV data loaded and parsed successfully:", results.data.length, "rows");
            simulatedData = results.data;
            if (simulatedData && simulatedData.length > 0) {
                // Convert Timestamp string to Date object if needed (PapaParse might do this with dynamicTyping)
                // Example: simulatedData.forEach(row => row.Timestamp = new Date(row.Timestamp));
                initializeDashboardWithData(simulatedData[0]); // Initialize with the first row
                startDataUpdateLoop(); // Start the update loop
            } else {
                console.error("No data found in CSV file or failed to parse.");
                alert("Error: Could not load or parse simulation data.");
            }
            hideLoading();
        },
        error: (error) => {
            console.error("Error loading or parsing CSV:", error);
            alert(`Error loading data: ${error.message}. Please ensure the file ${DATA_FILE_PATH} exists and is accessible.`);
            hideLoading();
        }
    });
}

/**
 * Starts the interval timer to update the dashboard periodically.
 */
function startDataUpdateLoop() {
    if (updateIntervalId) {
        clearInterval(updateIntervalId); // Clear existing interval if any
    }
    console.log(`Starting data update loop with interval: ${UPDATE_INTERVAL}ms`);
    updateIntervalId = setInterval(updateDashboard, UPDATE_INTERVAL);
}

/**
 * Updates the dashboard with the next data row.
 */
function updateDashboard() {
    if (!simulatedData || simulatedData.length === 0) {
        // If no CSV data, use simulation.js to generate data
        const currentTime = new Date();
        const sunInfo = getSunInfo();
        const rawData = simulateSensorData(currentTime, sunInfo);
        
        // Process the simulated data
        processAndUpdateDashboard(rawData);
        return;
    }

    // Use CSV data if available
    currentDataIndex = (currentDataIndex + 1) % simulatedData.length; // Loop through data
    const currentRow = simulatedData[currentDataIndex];
    
    // Process the CSV data
    processAndUpdateDashboard(currentRow);
}

/**
 * Process raw data and update dashboard
 * @param {object} rawData - Raw data from simulation or CSV
 */
function processAndUpdateDashboard(rawData) {
    // Extract spectral data from AS7262 sensor
    const spectralData = {
        '450nm': rawData.AS7262 ? rawData.AS7262['450nm'] : rawData.Spectral_1,
        '500nm': rawData.AS7262 ? rawData.AS7262['500nm'] : rawData.Spectral_2,
        '550nm': rawData.AS7262 ? rawData.AS7262['550nm'] : rawData.Spectral_3,
        '570nm': rawData.AS7262 ? rawData.AS7262['570nm'] : rawData.Spectral_4,
        '600nm': rawData.AS7262 ? rawData.AS7262['600nm'] : rawData.Spectral_5,
        '650nm': rawData.AS7262 ? rawData.AS7262['650nm'] : rawData.Spectral_6,
        'temperature': rawData.AS7262 ? rawData.AS7262.temperature : rawData.Temperature
    };
    
    // Apply noise filtering to spectral data
    const filteredSpectralData = dataFilter.filterSpectralData(spectralData, 'kalman');
    
    // Calculate color temperature and tint
    const colorData = ColorScience.calculateColorTemperature(filteredSpectralData);
    
    // Calculate camera settings based on target CCT
    const cameraSettings = ColorScience.calculateCameraSettings(colorData.cct, colorData.tint, targetCCT);
    
    // Create processed data object
    const processedData = {
        ...rawData,
        // Add calculated values
        ColorTemperature_K: colorData.cct,
        Tint: colorData.tint,
        CameraSettings: cameraSettings,
        // Add filtered spectral data
        Spectral_1: filteredSpectralData['450nm'],
        Spectral_2: filteredSpectralData['500nm'],
        Spectral_3: filteredSpectralData['550nm'],
        Spectral_4: filteredSpectralData['570nm'],
        Spectral_5: filteredSpectralData['600nm'],
        Spectral_6: filteredSpectralData['650nm'],
        // Add timestamp if not present
        Timestamp: rawData.Timestamp || new Date().toISOString()
    };
    
    // Update dashboard components
    updateCharts(processedData);
    updateCalculationExplanation(processedData, colorData);
    updateStatusCards(processedData);
    updateRawDataDisplay(processedData);
    updateCameraCalibration(processedData, colorData, cameraSettings);
}

// --- Chart Initialization ---

/**
 * Initializes all dashboard components with the first row of data.
 * @param {object} initialDataRow - The first row of data from the CSV.
 */
function initializeDashboardWithData(initialDataRow) {
    console.log("Initializing dashboard with initial data:", initialDataRow);
    initDashboardCharts(initialDataRow);
    initSpectralCharts(initialDataRow);
    initExposureCharts(initialDataRow);
    initMLCharts(initialDataRow); // Assuming ML charts might also use some initial data
    initSensorMap(); // Map initialization might not depend on the first row
    updateCalculationExplanation(initialDataRow); // Update calculation example
    updateStatusCards(initialDataRow);
    updateRawDataDisplay(initialDataRow);
}

/**
 * Initializes charts on the main dashboard panel.
 * @param {object} dataRow - A single row of data.
 */
function initDashboardCharts(dataRow) {
    // Color Readings Chart
    const colorReadingsCtx = document.getElementById('colorReadingsChart')?.getContext('2d');
    if (colorReadingsCtx) {
        chartInstances.colorReadings = new Chart(colorReadingsCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp], // Start with one label
                datasets: [
                    {
                        label: 'Color Temperature (K)',
                        data: [dataRow.ColorTemperature_K],
                        borderColor: 'rgba(231, 76, 60, 0.8)',
                        backgroundColor: 'rgba(231, 76, 60, 0.2)',
                        tension: 0.4,
                        fill: true,
                        yAxisID: 'y'
                    },
                    // Tint data might not be directly in CSV, needs calculation or placeholder
                    // {
                    //     label: 'Tint',
                    //     data: [calculateTint(dataRow)], // Placeholder for tint calculation
                    //     borderColor: 'rgba(46, 204, 113, 0.8)',
                    //     backgroundColor: 'rgba(46, 204, 113, 0.2)',
                    //     tension: 0.4,
                    //     fill: true,
                    //     yAxisID: 'y1'
                    // }
                ]
            },
            options: {
                ...baseChartOptions,
                scales: {
                    x: {
                       title: { display: true, text: 'Time' }
                    },
                    y: {
                        beginAtZero: false,
                        title: { display: true, text: 'Color Temperature (K)' }
                    },
                    // y1: { // Tint axis
                    //     position: 'right', beginAtZero: true,
                    //     title: { display: true, text: 'Tint' },
                    //     min: -10, max: 10,
                    //     grid: { drawOnChartArea: false }
                    // }
                }
            }
        });
    } else {
        console.warn("Element with ID 'colorReadingsChart' not found.");
    }

    // Sensor Performance Chart (Static for now, or adapt if needed)
    const sensorPerformanceCtx = document.getElementById('sensorPerformanceChart')?.getContext('2d');
     if (sensorPerformanceCtx) {
        // This chart seems static based on original data.js, keep it or adapt if needed.
        const staticPerformanceData = {
            labels: ['AS7262', 'TSL2591', 'SEN0611'],
            datasets: [
                { label: 'Accuracy (%)', data: [95, 92, 97], backgroundColor: 'rgba(52, 152, 219, 0.8)' },
                { label: 'Response Time (ms)', data: [120, 150, 110], backgroundColor: 'rgba(155, 89, 182, 0.8)' }
            ]
        };
        chartInstances.sensorPerformance = new Chart(sensorPerformanceCtx, {
            type: 'bar',
            data: staticPerformanceData,
            options: { ...baseChartOptions, scales: { y: { beginAtZero: true } } }
        });
    } else {
         console.warn("Element with ID 'sensorPerformanceChart' not found.");
     }

    // Raw Sensor Data Charts
    initRawSensorCharts(dataRow);
}

/**
 * Initializes charts showing raw sensor data.
 * @param {object} dataRow - A single row of data.
 */
function initRawSensorCharts(dataRow) {
    // AS7262 Spectral Sensor Chart
    const as7262ChartCtx = document.getElementById('as7262Chart')?.getContext('2d');
    if (as7262ChartCtx) {
        chartInstances.as7262 = new Chart(as7262ChartCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp],
                datasets: [
                    { label: 'Violet (450nm)', data: [dataRow.Spectral_1], borderColor: 'rgba(93, 63, 211, 1)', tension: 0.4 },
                    { label: 'Blue (500nm)', data: [dataRow.Spectral_2], borderColor: 'rgba(52, 152, 219, 1)', tension: 0.4 },
                    { label: 'Green (550nm)', data: [dataRow.Spectral_3], borderColor: 'rgba(46, 204, 113, 1)', tension: 0.4 },
                    { label: 'Yellow (570nm)', data: [dataRow.Spectral_4], borderColor: 'rgba(241, 196, 15, 1)', tension: 0.4 },
                    { label: 'Orange (600nm)', data: [dataRow.Spectral_5], borderColor: 'rgba(230, 126, 34, 1)', tension: 0.4 },
                    { label: 'Red (650nm)', data: [dataRow.Spectral_6], borderColor: 'rgba(231, 76, 60, 1)', tension: 0.4 }
                ]
            },
            options: { ...baseChartOptions, scales: { y: { beginAtZero: true, title: { display: true, text: 'Intensity' } }, x: { title: { display: true, text: 'Time' } } } }
        });
    } else {
        console.warn("Element with ID 'as7262Chart' not found.");
    }

    // TSL2591 Luminance Sensor Chart
    const tsl2591ChartCtx = document.getElementById('tsl2591Chart')?.getContext('2d');
    if (tsl2591ChartCtx) {
        chartInstances.tsl2591 = new Chart(tsl2591ChartCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp],
                datasets: [
                    { label: 'Lux', data: [dataRow.Luminance], borderColor: 'rgba(241, 196, 15, 1)', tension: 0.4, yAxisID: 'y' },
                    { label: 'IR', data: [dataRow.IR], borderColor: 'rgba(155, 89, 182, 1)', tension: 0.4, yAxisID: 'y1' },
                    { label: 'Full Spectrum', data: [dataRow.Full], borderColor: 'rgba(52, 152, 219, 1)', tension: 0.4, yAxisID: 'y1' }
                ]
            },
            options: {
                ...baseChartOptions,
                scales: {
                    y: { type: 'linear', position: 'left', beginAtZero: true, title: { display: true, text: 'Lux' } },
                    y1: { type: 'linear', position: 'right', beginAtZero: true, title: { display: true, text: 'Raw Counts (IR/Full)' }, grid: { drawOnChartArea: false } },
                    x: { title: { display: true, text: 'Time' } }
                }
            }
        });
    } else {
        console.warn("Element with ID 'tsl2591Chart' not found.");
    }

    // SEN0611 CCT and ALS Sensor Chart
    const sen0611ChartCtx = document.getElementById('sen0611Chart')?.getContext('2d');
    if (sen0611ChartCtx) {
        chartInstances.sen0611 = new Chart(sen0611ChartCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp],
                datasets: [
                    { label: 'CCT (K)', data: [dataRow.ColorTemperature_K], borderColor: 'rgba(231, 76, 60, 1)', tension: 0.4, yAxisID: 'y' },
                    { label: 'ALS (lux)', data: [dataRow.ALS], borderColor: 'rgba(46, 204, 113, 1)', tension: 0.4, yAxisID: 'y1' }
                ]
            },
            options: {
                ...baseChartOptions,
                scales: {
                    y: { type: 'linear', position: 'left', beginAtZero: false, title: { display: true, text: 'CCT (K)' } },
                    y1: { type: 'linear', position: 'right', beginAtZero: true, title: { display: true, text: 'ALS (lux)' }, grid: { drawOnChartArea: false } },
                    x: { title: { display: true, text: 'Time' } }
                }
            }
        });
    } else {
        console.warn("Element with ID 'sen0611Chart' not found.");
    }

    // Optional GPS Module Chart
    const gpsChartCtx = document.getElementById('gpsChart')?.getContext('2d');
    if (gpsChartCtx) {
        chartInstances.gps = new Chart(gpsChartCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp],
                datasets: [
                    { label: 'Satellites', data: [dataRow.Satellites], borderColor: 'rgba(52, 152, 219, 1)', tension: 0.4, yAxisID: 'y' },
                    { label: 'HDOP', data: [dataRow.HDOP], borderColor: 'rgba(231, 76, 60, 1)', tension: 0.4, yAxisID: 'y1' }
                ]
            },
            options: {
                ...baseChartOptions,
                scales: {
                    y: { type: 'linear', position: 'left', beginAtZero: true, title: { display: true, text: 'Satellites' } },
                    y1: { type: 'linear', position: 'right', beginAtZero: true, title: { display: true, text: 'HDOP' }, grid: { drawOnChartArea: false } },
                    x: { title: { display: true, text: 'Time' } }
                }
            }
        });
    } // No warning if GPS chart doesn't exist
}

/**
 * Initializes charts on the Spectral Analysis panel.
 * @param {object} dataRow - A single row of data.
 */
function initSpectralCharts(dataRow) {
    // Spectral Distribution Chart (Bar chart might be better for single point)
    const spectralDistributionCtx = document.getElementById('spectralDistributionChart')?.getContext('2d');
    if (spectralDistributionCtx) {
        chartInstances.spectralDistribution = new Chart(spectralDistributionCtx, {
            type: 'bar', // Changed to bar for single point in time view
            data: {
                labels: ['450nm', '500nm', '550nm', '570nm', '600nm', '650nm'],
                datasets: [{
                    label: 'Current Reading',
                    data: [
                        dataRow.Spectral_1, dataRow.Spectral_2, dataRow.Spectral_3,
                        dataRow.Spectral_4, dataRow.Spectral_5, dataRow.Spectral_6
                    ],
                    backgroundColor: [
                        'rgba(93, 63, 211, 0.7)', 'rgba(52, 152, 219, 0.7)', 'rgba(46, 204, 113, 0.7)',
                        'rgba(241, 196, 15, 0.7)', 'rgba(230, 126, 34, 0.7)', 'rgba(231, 76, 60, 0.7)'
                    ]
                }]
            },
            options: { ...baseChartOptions, scales: { y: { beginAtZero: true, title: { display: true, text: 'Intensity' } } } }
        });
    } else {
        console.warn("Element with ID 'spectralDistributionChart' not found.");
    }

    // Color Accuracy Chart (Static for now)
    const colorAccuracyCtx = document.getElementById('colorAccuracyChart')?.getContext('2d');
    if (colorAccuracyCtx) {
        const staticAccuracyData = {
             labels: ['Violet (450nm)', 'Blue (500nm)', 'Green (550nm)', 'Yellow (570nm)', 'Orange (600nm)', 'Red (650nm)'],
             datasets: [{
                 label: 'Accuracy (%)', data: [95, 92, 97, 94, 91, 93], // Example static data
                 backgroundColor: [
                     'rgba(93, 63, 211, 0.8)', 'rgba(52, 152, 219, 0.8)', 'rgba(46, 204, 113, 0.8)',
                     'rgba(241, 196, 15, 0.8)', 'rgba(230, 126, 34, 0.8)', 'rgba(231, 76, 60, 0.8)'
                 ]
             }]
         };
        chartInstances.colorAccuracy = new Chart(colorAccuracyCtx, {
            type: 'radar',
            data: staticAccuracyData,
            options: { ...baseChartOptions, scales: { r: { beginAtZero: true, min: 80, max: 100 } } }
        });
    } else {
        console.warn("Element with ID 'colorAccuracyChart' not found.");
    }

    // Spectral Heatmap (Static or needs different logic for real-time)
    initSpectralHeatmap(); // Keep static heatmap for now
}

/**
 * Initializes charts on the Exposure Monitoring panel.
 * @param {object} dataRow - A single row of data.
 */
function initExposureCharts(dataRow) {
    // Exposure Trends Chart
    const exposureTrendsCtx = document.getElementById('exposureTrendsChart')?.getContext('2d');
    if (exposureTrendsCtx) {
        chartInstances.exposureTrends = new Chart(exposureTrendsCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp],
                datasets: [
                    { label: 'Light Exposure (lux)', data: [dataRow.Luminance], borderColor: 'rgba(241, 196, 15, 1)', tension: 0.4 },
                    { label: 'Ambient Light (lux)', data: [dataRow.ALS], borderColor: 'rgba(243, 156, 18, 1)', tension: 0.4 }
                ]
            },
            options: { ...baseChartOptions, scales: { y: { beginAtZero: true, title: { display: true, text: 'Light Exposure (lux)' } }, x: { title: { display: true, text: 'Time' } } } }
        });
    } else {
        console.warn("Element with ID 'exposureTrendsChart' not found.");
    }

    // Daily Exposure Pattern Chart (Shows CCT over time)
    const dailyExposureCtx = document.getElementById('dailyExposureChart')?.getContext('2d');
    if (dailyExposureCtx) {
        chartInstances.dailyExposure = new Chart(dailyExposureCtx, {
            type: 'line',
            data: {
                labels: [dataRow.Timestamp],
                datasets: [
                    { label: 'Color Temperature (K)', data: [dataRow.ColorTemperature_K], borderColor: 'rgba(241, 196, 15, 1)', tension: 0.4 }
                ]
            },
            options: { ...baseChartOptions, scales: { y: { beginAtZero: false, title: { display: true, text: 'Color Temperature (K)' } }, x: { title: { display: true, text: 'Time' } } } }
        });
    } else {
        console.warn("Element with ID 'dailyExposureChart' not found.");
    }
}

/**
 * Initializes charts on the Machine Learning panel.
 * @param {object} dataRow - A single row of data (might not be used if charts are static).
 */
function initMLCharts(dataRow) {
    // Model Performance Chart (Static for now)
    const modelPerformanceCtx = document.getElementById('modelPerformanceChart')?.getContext('2d');
    if (modelPerformanceCtx) {
         const staticPerformanceData = {
             labels: ['v2.1.0', 'v2.1.5', 'v2.2.0', 'v2.2.5', 'v2.3.0', 'v2.3.1'],
             datasets: [
                 { label: 'Accuracy (%)', data: [89.5, 91.2, 92.4, 92.8, 93.5, 94.7], borderColor: 'rgba(52, 152, 219, 1)', yAxisID: 'y' },
                 { label: 'Loss', data: [0.0612, 0.0542, 0.0498, 0.0412, 0.0389, 0.0342], borderColor: 'rgba(231, 76, 60, 1)', yAxisID: 'y1' }
             ]
         };
        chartInstances.modelPerformance = new Chart(modelPerformanceCtx, {
            type: 'line',
            data: staticPerformanceData,
            options: { ...baseChartOptions, scales: { y: { beginAtZero: false, min: 85, max: 100, title: { display: true, text: 'Accuracy (%)' } }, y1: { position: 'right', beginAtZero: true, max: 0.1, title: { display: true, text: 'Loss' }, grid: { drawOnChartArea: false } } } }
        });
    } else {
        console.warn("Element with ID 'modelPerformanceChart' not found.");
    }

    // Feature Importance Chart (Static for now)
    const featureImportanceCtx = document.getElementById('featureImportanceChart')?.getContext('2d');
    if (featureImportanceCtx) {
        const staticImportanceData = {
            labels: ['AS7262 Spectral', 'TSL2591 Luminance', 'SEN0611 CCT', 'Time of Day', 'Sensor Temperature'],
            datasets: [{
                label: 'Importance Score', data: [0.45, 0.25, 0.20, 0.06, 0.04],
                backgroundColor: ['rgba(52, 152, 219, 0.8)', 'rgba(231, 76, 60, 0.8)', 'rgba(241, 196, 15, 0.8)', 'rgba(46, 204, 113, 0.8)', 'rgba(155, 89, 182, 0.8)']
            }]
        };
        chartInstances.featureImportance = new Chart(featureImportanceCtx, {
            type: 'doughnut',
            data: staticImportanceData,
            options: { ...baseChartOptions, cutout: '50%' }
        });
    } else {
        console.warn("Element with ID 'featureImportanceChart' not found.");
    }
}

// --- Chart Update Logic ---

const MAX_CHART_POINTS = 100; // Limit the number of points shown on time-series charts

/**
 * Updates all relevant charts with new data.
 * @param {object} dataRow - The current row of data.
 */
function updateCharts(dataRow) {
    const timestamp = dataRow.Timestamp; // Assuming Timestamp is a string 'YYYY-MM-DD HH:MM:SS'

    // Function to update a time-series chart
    const updateTimeSeriesChart = (chartInstance, newData) => {
        if (!chartInstance) return;
        const labels = chartInstance.data.labels;
        const datasets = chartInstance.data.datasets;

        // Add new label
        labels.push(timestamp);

        // Add new data to each dataset
        Object.keys(newData).forEach((key, index) => {
            if (datasets[index]) {
                datasets[index].data.push(newData[key]);
            }
        });

        // Limit the number of data points
        if (labels.length > MAX_CHART_POINTS) {
            labels.shift();
            datasets.forEach(dataset => dataset.data.shift());
        }

        chartInstance.update();
    };

    // Update Color Readings Chart
    updateTimeSeriesChart(chartInstances.colorReadings, {
        ColorTemperature_K: dataRow.ColorTemperature_K
        // Tint: calculateTint(dataRow) // Add if tint calculation is implemented
    });

    // Update AS7262 Chart
    updateTimeSeriesChart(chartInstances.as7262, {
        Spectral_1: dataRow.Spectral_1, Spectral_2: dataRow.Spectral_2, Spectral_3: dataRow.Spectral_3,
        Spectral_4: dataRow.Spectral_4, Spectral_5: dataRow.Spectral_5, Spectral_6: dataRow.Spectral_6
    });

    // Update TSL2591 Chart
    updateTimeSeriesChart(chartInstances.tsl2591, {
        Luminance: dataRow.Luminance, IR: dataRow.IR, Full: dataRow.Full
    });

    // Update SEN0611 Chart
    updateTimeSeriesChart(chartInstances.sen0611, {
        ColorTemperature_K: dataRow.ColorTemperature_K, ALS: dataRow.ALS
    });

    // Update GPS Chart
    updateTimeSeriesChart(chartInstances.gps, {
        Satellites: dataRow.GPS_Valid ? dataRow.Satellites : null, // Show null if GPS invalid
        HDOP: dataRow.GPS_Valid ? dataRow.HDOP : null
    });

    // Update Spectral Distribution Chart (Bar chart - update data directly)
    if (chartInstances.spectralDistribution) {
        chartInstances.spectralDistribution.data.datasets[0].data = [
            dataRow.Spectral_1, dataRow.Spectral_2, dataRow.Spectral_3,
            dataRow.Spectral_4, dataRow.Spectral_5, dataRow.Spectral_6
        ];
        chartInstances.spectralDistribution.update();
    }

    // Update Exposure Trends Chart
    updateTimeSeriesChart(chartInstances.exposureTrends, {
        Luminance: dataRow.Luminance, ALS: dataRow.ALS
    });

    // Update Daily Exposure Pattern Chart (CCT over time)
    updateTimeSeriesChart(chartInstances.dailyExposure, {
        ColorTemperature_K: dataRow.ColorTemperature_K
    });

    // Note: Static charts (Sensor Performance, Color Accuracy, ML charts) are not updated here.
}


// --- Other UI Updates ---

/**
 * Updates the calculation explanation section.
 * @param {object} dataRow - The current row of data.
 */
/**
 * Update the calculation explanation section with detailed steps
 * @param {object} dataRow - Processed data row
 * @param {object} colorData - Color temperature calculation results
 */
function updateCalculationExplanation(dataRow, colorData) {
    const calculationContainer = document.getElementById('calculation-steps');
    if (!calculationContainer || !dataRow) return;

    // Format values with proper precision
    const spectral = {
        v: dataRow.Spectral_1?.toFixed(2) || 'N/A',
        b: dataRow.Spectral_2?.toFixed(2) || 'N/A',
        g: dataRow.Spectral_3?.toFixed(2) || 'N/A',
        y: dataRow.Spectral_4?.toFixed(2) || 'N/A',
        o: dataRow.Spectral_5?.toFixed(2) || 'N/A',
        r: dataRow.Spectral_6?.toFixed(2) || 'N/A'
    };
    
    const luminance = dataRow.Luminance?.toFixed(2) || 'N/A';
    const ir = dataRow.IR || 'N/A';
    const full = dataRow.Full || 'N/A';
    const cct = dataRow.ColorTemperature_K?.toFixed(0) || 'N/A';
    const als = dataRow.ALS?.toFixed(2) || 'N/A';
    const tint = dataRow.Tint?.toFixed(2) || 'N/A';
    
    // Create detailed calculation explanation
    let calculationHTML = `
        <h4>Step 1: Gather Raw Sensor Data</h4>
        <div class="calculation-data">
            <p><strong>AS7262:</strong> V:${spectral.v} B:${spectral.b} G:${spectral.g} Y:${spectral.y} O:${spectral.o} R:${spectral.r}</p>
            <p><strong>TSL2591:</strong> Lum:${luminance} IR:${ir} Full:${full}</p>
            <p><strong>SEN0611:</strong> CCT:${cct}K ALS:${als} lux</p>
        </div>
        
        <h4>Step 2: Apply Noise Filtering</h4>
        <p>Kalman filtering applied to reduce sensor noise and improve measurement stability.</p>
        
        <h4>Step 3: Calculate XYZ Color Space Values</h4>
        <div class="calculation-data">
            <p>Using CIE 1931 2° Standard Observer coefficients:</p>
            <p>X = ${colorData?.xyz?.X?.toFixed(2) || 'N/A'}</p>
            <p>Y = ${colorData?.xyz?.Y?.toFixed(2) || 'N/A'}</p>
            <p>Z = ${colorData?.xyz?.Z?.toFixed(2) || 'N/A'}</p>
        </div>
        
        <h4>Step 4: Calculate Chromaticity Coordinates</h4>
        <div class="calculation-data">
            <p>x = X / (X + Y + Z) = ${colorData?.chromaticity?.x?.toFixed(4) || 'N/A'}</p>
            <p>y = Y / (X + Y + Z) = ${colorData?.chromaticity?.y?.toFixed(4) || 'N/A'}</p>
        </div>
        
        <h4>Step 5: Apply McCamy's Formula for CCT</h4>
        <div class="calculation-data">
            <p>n = (x - 0.3320) / (y - 0.1858) = ${((colorData?.chromaticity?.x - 0.3320) / (colorData?.chromaticity?.y - 0.1858))?.toFixed(4) || 'N/A'}</p>
            <p>CCT = 449*n³ + 3525*n² - 6823.3*n + 5520.33</p>
            <p>CCT = ${cct}K (rounded to nearest 50K)</p>
        </div>
        
        <h4>Step 6: Calculate Tint (Duv)</h4>
        <div class="calculation-data">
            <p>Convert to u'v' coordinates</p>
            <p>Calculate distance from Planckian locus</p>
            <p>Tint = ${tint} (positive = green, negative = magenta)</p>
        </div>
        
        <h4>Final Result</h4>
        <div class="calculation-result">
            <p>Color Temperature: <strong>${cct}K</strong></p>
            <p>Tint: <strong>${tint}</strong></p>
        </div>
    `;
    calculationContainer.innerHTML = calculationHTML;
}

/**
 * Updates the status cards.
 * @param {object} dataRow - The current row of data.
 */
function updateStatusCards(dataRow) {
    // Example: Update Avg. Temperature card (assuming AS7262 temp is not in CSV, use placeholder)
    const avgTempElement = document.querySelector('.status-card:nth-child(2) .card-value');
    if (avgTempElement) avgTempElement.textContent = `~${(Math.random()*5 + 22).toFixed(1)}°C`; // Placeholder

    // Example: Update Light Exposure card
    const lightExposureElement = document.querySelector('.status-card:nth-child(3) .card-value');
    if (lightExposureElement) {
        if (dataRow.Luminance > 50000) lightExposureElement.textContent = 'Very High';
        else if (dataRow.Luminance > 10000) lightExposureElement.textContent = 'High';
        else if (dataRow.Luminance > 1000) lightExposureElement.textContent = 'Medium';
        else if (dataRow.Luminance > 100) lightExposureElement.textContent = 'Low';
        else lightExposureElement.textContent = 'Very Low';
    }
     // Update Sensor Status (Simplified - assumes all are online if data is valid)
    const sensorStatusElement = document.querySelector('.status-card:nth-child(1) .card-value');
    if (sensorStatusElement) sensorStatusElement.textContent = dataRow.IsValid ? '3/3' : 'Check!';

    // Update Alerts (Simplified - based on confidence)
    const alertsElement = document.querySelector('.status-card:nth-child(4) .card-value');
    if (alertsElement) alertsElement.textContent = dataRow.Confidence < 0.8 ? 'Check!' : 'OK';


}

/**
 * Updates the raw data display section (if one exists).
 * @param {object} dataRow - The current row of data.
 */
function updateRawDataDisplay(dataRow) {
    // Find elements where raw data should be displayed (e.g., tables, text fields)
    // Example:
    // const rawLuxElement = document.getElementById('raw-lux-value');
    // if (rawLuxElement) rawLuxElement.textContent = dataRow.Luminance?.toFixed(2);
    // const rawCctElement = document.getElementById('raw-cct-value');
    // if (rawCctElement) rawCctElement.textContent = dataRow.ColorTemperature_K?.toFixed(0);
    // ... update other raw data displays
}


// --- Map and Heatmap Initialization (Mostly Static) ---

/**
 * Initializes the Leaflet map for sensor locations.
 */
function initSensorMap() {
    const mapElement = document.getElementById('sensorMap');
    if (!mapElement || mapElement._leaflet_id) return; // Check if map already initialized

    try {
        const map = L.map('sensorMap').setView([51.505, -0.09], 13); // Default view
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Add markers based on static data or potentially GPS data if available
        const sensorLocations = [ // Example static locations
             { id: 1, name: 'AS7262', lat: 51.505, lng: -0.09, status: 'online', type: 'Spectral Sensor' },
             { id: 2, name: 'TSL2591', lat: 51.51, lng: -0.1, status: 'online', type: 'Luminance Sensor' },
             { id: 3, name: 'SEN0611', lat: 51.515, lng: -0.09, status: 'online', type: 'CCT & ALS Sensor' }
         ];

        sensorLocations.forEach(sensor => {
            const markerColor = sensor.status === 'online' ? '#2ECC71' : '#E74C3C';
            const markerIcon = L.divIcon({
                className: 'sensor-marker',
                html: `<div style="background-color: ${markerColor}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
                iconSize: [12, 12], iconAnchor: [6, 6]
            });
            const marker = L.marker([sensor.lat, sensor.lng], { icon: markerIcon }).addTo(map);
            marker.bindPopup(`<div class="map-popup"><h3>${sensor.name}</h3><p>Type: ${sensor.type}</p><p>Status: <span style="color: ${markerColor}">${sensor.status}</span></p></div>`);
        });
        chartInstances.map = map; // Store map instance if needed later
    } catch (e) {
        console.error("Error initializing Leaflet map:", e);
        if (mapElement) mapElement.innerHTML = "<p>Error loading map. Leaflet library might be missing or failed to initialize.</p>";
    }
}

/**
 * Initializes the spectral heatmap (static example).
 */
function initSpectralHeatmap() {
    const spectralHeatmapCtx = document.getElementById('spectralHeatmapChart')?.getContext('2d');
    if (!spectralHeatmapCtx) {
        console.warn("Element with ID 'spectralHeatmapChart' not found.");
        return;
    }

    // Static heatmap example
    const width = spectralHeatmapCtx.canvas.width;
    const height = spectralHeatmapCtx.canvas.height;
    const data = Array.from({ length: 24 }, () => Array.from({ length: 24 }, () => Math.floor(Math.random() * 100))); // Example data
    const cellWidth = width / data[0].length;
    const cellHeight = height / data.length;

    for (let y = 0; y < data.length; y++) {
        for (let x = 0; x < data[y].length; x++) {
            const value = data[y][x];
            const intensity = value / 100;
            const r = Math.floor(255 * Math.min(1, intensity * 2));
            const g = Math.floor(255 * Math.min(1, 2 - intensity * 2));
            const b = Math.floor(255 * Math.max(0, 1 - intensity * 2));
            spectralHeatmapCtx.fillStyle = `rgb(${r}, ${g}, ${b})`;
            spectralHeatmapCtx.fillRect(x * cellWidth, y * cellHeight, cellWidth, cellHeight);
        }
    }
    // Add legend (optional)
}

/**
 * Update the camera calibration panel
 * @param {object} dataRow - Processed data row
 * @param {object} colorData - Color temperature calculation results
 * @param {object} cameraSettings - Camera white balance settings
 */
function updateCameraCalibration(dataRow, colorData, cameraSettings) {
    // Find camera calibration elements
    const cctValueElement = document.getElementById('camera-cct-value');
    const tintValueElement = document.getElementById('camera-tint-value');
    const targetCctElement = document.getElementById('target-cct-value');
    const cctDeviationElement = document.getElementById('cct-deviation-value');
    const cctScaleElement = document.getElementById('cct-deviation-scale');
    const tintScaleElement = document.getElementById('tint-scale');
    const rMultElement = document.getElementById('r-multiplier');
    const gMultElement = document.getElementById('g-multiplier');
    const bMultElement = document.getElementById('b-multiplier');
    
    // Update elements if they exist
    if (cctValueElement) cctValueElement.textContent = `${dataRow.ColorTemperature_K}K`;
    if (tintValueElement) tintValueElement.textContent = dataRow.Tint?.toFixed(2) || 'N/A';
    if (targetCctElement) targetCctElement.textContent = `${targetCCT}K`;
    
    if (cctDeviationElement) {
        const deviation = cameraSettings.cctDeviation;
        const sign = deviation > 0 ? '+' : '';
        cctDeviationElement.textContent = `${sign}${deviation}K`;
        
        // Set color based on deviation
        if (Math.abs(deviation) < 100) {
            cctDeviationElement.style.color = '#2ecc71'; // Green for small deviation
        } else if (Math.abs(deviation) < 300) {
            cctDeviationElement.style.color = '#f39c12'; // Orange for medium deviation
        } else {
            cctDeviationElement.style.color = '#e74c3c'; // Red for large deviation
        }
    }
    
    // Update CCT deviation scale
    if (cctScaleElement) {
        const deviation = cameraSettings.cctDeviation;
        const maxDeviation = 1000; // Maximum deviation to show on scale
        const percentage = Math.min(100, Math.abs(deviation) / maxDeviation * 100);
        const direction = deviation > 0 ? 'right' : 'left';
        
        // Create gradient based on deviation
        if (direction === 'right') {
            cctScaleElement.style.background = `linear-gradient(to right, #3498db ${50-percentage/2}%, #e74c3c ${50+percentage/2}%)`;
        } else {
            cctScaleElement.style.background = `linear-gradient(to left, #e74c3c ${50-percentage/2}%, #3498db ${50+percentage/2}%)`;
        }
        
        // Position indicator
        const indicator = cctScaleElement.querySelector('.scale-indicator');
        if (indicator) {
            indicator.style.left = `${50 + (deviation / maxDeviation * 50)}%`;
        }
    }
    
    // Update tint scale
    if (tintScaleElement) {
        const tint = dataRow.Tint || 0;
        const maxTint = 20; // Maximum tint to show on scale
        const percentage = Math.min(100, Math.abs(tint) / maxTint * 100);
        const direction = tint > 0 ? 'right' : 'left';
        
        // Create gradient based on tint
        if (direction === 'right') {
            tintScaleElement.style.background = `linear-gradient(to right, #9b59b6 ${50-percentage/2}%, #2ecc71 ${50+percentage/2}%)`;
        } else {
            tintScaleElement.style.background = `linear-gradient(to left, #2ecc71 ${50-percentage/2}%, #9b59b6 ${50+percentage/2}%)`;
        }
        
        // Position indicator
        const indicator = tintScaleElement.querySelector('.scale-indicator');
        if (indicator) {
            indicator.style.left = `${50 + (tint / maxTint * 50)}%`;
        }
    }
    
    // Update multiplier values
    if (rMultElement) rMultElement.textContent = cameraSettings.rMultiplier;
    if (gMultElement) gMultElement.textContent = cameraSettings.gMultiplier;
    if (bMultElement) bMultElement.textContent = cameraSettings.bMultiplier;
}

/**
 * Set target CCT for camera calibration
 * @param {number} cct - Target color temperature in Kelvin
 */
function setTargetCCT(cct) {
    targetCCT = cct;
    
    // Update target CCT display
    const targetCctElement = document.getElementById('target-cct-value');
    if (targetCctElement) targetCctElement.textContent = `${targetCCT}K`;
    
    // Update camera calibration with new target
    const currentData = simulatedData[currentDataIndex];
    if (currentData) {
        const spectralData = {
            '450nm': currentData.Spectral_1,
            '500nm': currentData.Spectral_2,
            '550nm': currentData.Spectral_3,
            '570nm': currentData.Spectral_4,
            '600nm': currentData.Spectral_5,
            '650nm': currentData.Spectral_6
        };
        
        const colorData = ColorScience.calculateColorTemperature(spectralData);
        const cameraSettings = ColorScience.calculateCameraSettings(colorData.cct, colorData.tint, targetCCT);
        
        updateCameraCalibration(currentData, colorData, cameraSettings);
    }
}

// --- Initial Load Trigger ---
document.addEventListener('DOMContentLoaded', function() {
    // Load data and initialize dashboard when the DOM is ready
    loadAndProcessData();

    // Re-initialize charts when switching panels
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const panelId = this.getAttribute('data-panel');
            // Small delay to allow panel transition
            setTimeout(() => {
                if (simulatedData.length > 0 || true) { // Always update, even with simulated data
                    // Get current data
                    let currentData;
                    if (simulatedData.length > 0) {
                        currentData = simulatedData[currentDataIndex];
                    } else {
                        const currentTime = new Date();
                        const sunInfo = getSunInfo();
                        currentData = simulateSensorData(currentTime, sunInfo);
                    }
                    
                    // Process and update
                    processAndUpdateDashboard(currentData);
                    
                    // Re-init map if needed
                    if (panelId === 'dashboard' && !chartInstances.map) initSensorMap();
                    // Re-init heatmap if needed
                    if (panelId === 'spectral' && !document.getElementById('spectralHeatmapChart').hasChildNodes()) initSpectralHeatmap();
                }
            }, 50);
        });
    });
    
    // Set up target CCT input handler
    const targetCctInput = document.getElementById('target-cct-input');
    if (targetCctInput) {
        targetCctInput.addEventListener('change', function() {
            const newCCT = parseInt(this.value);
            if (!isNaN(newCCT) && newCCT >= 2000 && newCCT <= 10000) {
                setTargetCCT(newCCT);
            }
        });
    }
    
    // Set up preset CCT buttons
    const cctPresetButtons = document.querySelectorAll('.cct-preset-btn');
    cctPresetButtons.forEach(button => {
        button.addEventListener('click', function() {
            const presetCCT = parseInt(this.getAttribute('data-cct'));
            if (!isNaN(presetCCT)) {
                setTargetCCT(presetCCT);
                // Update input field
                const targetCctInput = document.getElementById('target-cct-input');
                if (targetCctInput) targetCctInput.value = presetCCT;
            }
        });
    });
});