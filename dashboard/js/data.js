/**
 * ColorSenseAI Dashboard - Sample Data
 * This file contains sample data for charts and visualizations
 */

// Time periods for x-axis
const timeLabels = {
    day: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
    week: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    month: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    year: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
};

// Raw sensor data - Sample readings from the three sensors
const rawSensorData = {
    // AS7262 - 6-channel spectral sensor data
    AS7262: {
        // Spectral channels (wavelengths in nm)
        violet: [28.5, 29.2, 30.1, 31.5, 32.8, 33.4, 34.2, 33.8, 32.5, 31.2, 30.5, 29.8], // 450nm
        blue: [32.1, 33.5, 34.8, 36.2, 37.5, 38.1, 38.9, 38.2, 37.1, 35.8, 34.2, 33.1],   // 500nm
        green: [45.2, 46.8, 48.3, 50.1, 52.4, 53.8, 54.5, 53.9, 52.1, 50.5, 48.9, 47.2],  // 550nm
        yellow: [51.8, 53.2, 55.1, 57.8, 59.5, 60.2, 61.1, 60.5, 58.9, 57.2, 55.8, 54.1], // 570nm
        orange: [48.5, 49.8, 51.2, 53.5, 55.1, 56.8, 57.5, 56.9, 55.2, 53.8, 52.1, 50.5], // 600nm
        red: [39.2, 40.5, 42.1, 44.8, 46.5, 47.9, 48.5, 47.8, 46.2, 44.5, 42.8, 41.2],    // 650nm
        // Temperature of the sensor in Celsius
        temperature: [22.5, 22.8, 23.2, 23.8, 24.5, 25.1, 25.8, 26.2, 26.5, 26.1, 25.5, 24.8]
    },
    
    // TSL2591 - Luminance sensor data
    TSL2591: {
        // Luminance in lux
        lux: [120, 150, 210, 350, 580, 820, 950, 880, 720, 450, 280, 180],
        // Infrared light level
        ir: [80, 95, 120, 180, 250, 320, 380, 350, 290, 210, 150, 110],
        // Full spectrum light level (visible + IR)
        fullSpectrum: [200, 245, 330, 530, 830, 1140, 1330, 1230, 1010, 660, 430, 290]
    },
    
    // DFRobot SEN0611 - CCT and ALS sensor data
    SEN0611: {
        // Correlated Color Temperature in Kelvin
        cct: [2700, 2850, 3100, 3450, 4200, 5100, 5800, 5600, 5200, 4500, 3800, 3200],
        // Ambient Light Sensor reading in lux
        als: [110, 140, 200, 340, 560, 790, 920, 850, 700, 430, 260, 170]
    },
    
    // Optional GPS module data
    GPS: {
        // Latitude
        latitude: [51.5074, 51.5075, 51.5076, 51.5077, 51.5078, 51.5079, 51.5080, 51.5081, 51.5082, 51.5083, 51.5084, 51.5085],
        // Longitude
        longitude: [-0.1278, -0.1279, -0.1280, -0.1281, -0.1282, -0.1283, -0.1284, -0.1285, -0.1286, -0.1287, -0.1288, -0.1289],
        // Altitude in meters
        altitude: [35, 35, 36, 36, 37, 37, 38, 38, 37, 37, 36, 36],
        // Number of satellites
        satellites: [8, 9, 9, 10, 10, 11, 11, 11, 10, 10, 9, 8],
        // Horizontal Dilution of Precision (lower is better)
        hdop: [1.2, 1.1, 1.0, 0.9, 0.8, 0.8, 0.7, 0.7, 0.8, 0.9, 1.0, 1.1]
    }
};

// Calculated color data based on sensor fusion
const calculatedColorData = {
    // White balance calculation results
    whiteBalance: {
        // Color temperature in Kelvin
        colorTemperature: [2800, 3000, 3400, 4100, 5000, 5600, 6200, 5900, 5400, 4600, 3800, 3200],
        // Tint value (green-magenta balance)
        tint: [-3, -2, -1, 0, 1, 2, 1, 0, -1, -2, -2, -3]
    },
    
    // Color accuracy metrics
    colorAccuracy: {
        // Delta E values (color difference)
        deltaE: [2.8, 2.5, 2.2, 1.8, 1.5, 1.2, 1.0, 1.3, 1.6, 2.0, 2.3, 2.6]
    }
};

// Dashboard Panel Data
const dashboardData = {
    // Color Readings Chart Data
    colorReadings: {
        labels: timeLabels.day,
        datasets: [
            {
                label: 'Color Temperature (K)',
                data: calculatedColorData.whiteBalance.colorTemperature,
                borderColor: 'rgba(231, 76, 60, 0.8)',
                backgroundColor: 'rgba(231, 76, 60, 0.2)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Tint',
                data: calculatedColorData.whiteBalance.tint,
                borderColor: 'rgba(46, 204, 113, 0.8)',
                backgroundColor: 'rgba(46, 204, 113, 0.2)',
                tension: 0.4,
                fill: true,
                yAxisID: 'y1'
            }
        ]
    },
    
    // Sensor Performance Chart Data
    sensorPerformance: {
        labels: ['AS7262', 'TSL2591', 'SEN0611'],
        datasets: [
            {
                label: 'Accuracy (%)',
                data: [95, 92, 97],
                backgroundColor: 'rgba(52, 152, 219, 0.8)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1
            },
            {
                label: 'Response Time (ms)',
                data: [120, 150, 110],
                backgroundColor: 'rgba(155, 89, 182, 0.8)',
                borderColor: 'rgba(155, 89, 182, 1)',
                borderWidth: 1
            }
        ]
    },
    
    // Sensor Map Data
    sensorMap: [
        { id: 1, name: 'AS7262', lat: 51.505, lng: -0.09, status: 'online', type: 'Spectral Sensor' },
        { id: 2, name: 'TSL2591', lat: 51.51, lng: -0.1, status: 'online', type: 'Luminance Sensor' },
        { id: 3, name: 'SEN0611', lat: 51.515, lng: -0.09, status: 'online', type: 'CCT & ALS Sensor' }
    ]
};

// Spectral Analysis Panel Data
const spectralData = {
    // Spectral Distribution Chart Data
    spectralDistribution: {
        labels: ['450nm', '500nm', '550nm', '570nm', '600nm', '650nm'],
        datasets: [
            {
                label: 'Current Reading',
                data: [rawSensorData.AS7262.violet[6], rawSensorData.AS7262.blue[6], 
                       rawSensorData.AS7262.green[6], rawSensorData.AS7262.yellow[6], 
                       rawSensorData.AS7262.orange[6], rawSensorData.AS7262.red[6]],
                borderColor: 'rgba(52, 152, 219, 1)',
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                tension: 0.4,
                fill: true
            }
        ]
    },
    
    // Color Accuracy Chart Data
    colorAccuracy: {
        labels: ['Violet (450nm)', 'Blue (500nm)', 'Green (550nm)', 'Yellow (570nm)', 'Orange (600nm)', 'Red (650nm)'],
        datasets: [
            {
                label: 'Accuracy (%)',
                data: [95, 92, 97, 94, 91, 93],
                backgroundColor: [
                    'rgba(93, 63, 211, 0.8)', // Violet
                    'rgba(52, 152, 219, 0.8)', // Blue
                    'rgba(46, 204, 113, 0.8)', // Green
                    'rgba(241, 196, 15, 0.8)', // Yellow
                    'rgba(230, 126, 34, 0.8)', // Orange
                    'rgba(231, 76, 60, 0.8)'   // Red
                ],
                borderColor: [
                    'rgba(93, 63, 211, 1)',
                    'rgba(52, 152, 219, 1)',
                    'rgba(46, 204, 113, 1)',
                    'rgba(241, 196, 15, 1)',
                    'rgba(230, 126, 34, 1)',
                    'rgba(231, 76, 60, 1)'
                ],
                borderWidth: 1
            }
        ]
    },
    
    // Spectral Heatmap Data
    spectralHeatmap: {
        // Sample data for heatmap
        // This would typically be a 2D array of values
        data: Array.from({ length: 24 }, () => 
            Array.from({ length: 24 }, () => Math.floor(Math.random() * 100))
        )
    }
};

// Exposure Monitoring Panel Data
const exposureData = {
    // Exposure Trends Chart Data
    exposureTrends: {
        labels: timeLabels.day,
        datasets: [
            {
                label: 'Light Exposure (lux)',
                data: rawSensorData.TSL2591.lux,
                borderColor: 'rgba(241, 196, 15, 1)',
                backgroundColor: 'rgba(241, 196, 15, 0.2)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Ambient Light (lux)',
                data: rawSensorData.SEN0611.als,
                borderColor: 'rgba(243, 156, 18, 1)',
                backgroundColor: 'rgba(243, 156, 18, 0.2)',
                tension: 0.4,
                fill: true
            }
        ]
    },
    
    // Daily Exposure Pattern Chart Data
    dailyExposure: {
        labels: timeLabels.day,
        datasets: [
            {
                label: 'Color Temperature (K)',
                data: rawSensorData.SEN0611.cct,
                borderColor: 'rgba(241, 196, 15, 1)',
                backgroundColor: 'rgba(241, 196, 15, 0.2)',
                tension: 0.4,
                fill: true
            }
        ]
    }
};

// Machine Learning Panel Data
const mlData = {
    // Model Performance Chart Data
    modelPerformance: {
        labels: ['v2.1.0', 'v2.1.5', 'v2.2.0', 'v2.2.5', 'v2.3.0', 'v2.3.1'],
        datasets: [
            {
                label: 'Accuracy (%)',
                data: [89.5, 91.2, 92.4, 92.8, 93.5, 94.7],
                borderColor: 'rgba(52, 152, 219, 1)',
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                tension: 0.4,
                fill: true
            },
            {
                label: 'Loss',
                data: [0.0612, 0.0542, 0.0498, 0.0412, 0.0389, 0.0342],
                borderColor: 'rgba(231, 76, 60, 1)',
                backgroundColor: 'rgba(231, 76, 60, 0.2)',
                tension: 0.4,
                fill: true,
                yAxisID: 'y1'
            }
        ]
    },
    
    // Feature Importance Chart Data
    featureImportance: {
        labels: ['AS7262 Spectral', 'TSL2591 Luminance', 'SEN0611 CCT', 'Time of Day', 'Sensor Temperature'],
        datasets: [
            {
                label: 'Importance Score',
                data: [0.45, 0.25, 0.20, 0.06, 0.04],
                backgroundColor: [
                    'rgba(52, 152, 219, 0.8)',
                    'rgba(231, 76, 60, 0.8)',
                    'rgba(241, 196, 15, 0.8)',
                    'rgba(46, 204, 113, 0.8)',
                    'rgba(155, 89, 182, 0.8)'
                ],
                borderColor: [
                    'rgba(52, 152, 219, 1)',
                    'rgba(231, 76, 60, 1)',
                    'rgba(241, 196, 15, 1)',
                    'rgba(46, 204, 113, 1)',
                    'rgba(155, 89, 182, 1)'
                ],
                borderWidth: 1
            }
        ]
    }
};