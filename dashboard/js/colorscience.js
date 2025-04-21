/**
 * ColorSenseAI Dashboard - Color Science Module
 * This file contains algorithms for spectral analysis, CCT calculation, and tint calculation.
 */

// --- Color Science Algorithms ---

/**
 * Calculate XYZ values from spectral data using standard observer coefficients
 * @param {object} spectralData - Object containing spectral values at different wavelengths
 * @returns {object} - Object with x, y, z values
 */
function calculateXYZ(spectralData) {
    // CIE 1931 2° Standard Observer coefficients (approximated for AS7262 wavelengths)
    const xCoefficients = [0.0143, 0.0435, 0.1344, 0.2839, 0.3483, 0.3362];
    const yCoefficients = [0.0004, 0.0120, 0.0950, 0.3230, 0.5100, 0.1070];
    const zCoefficients = [0.0679, 0.2074, 0.2378, 0.1094, 0.0361, 0.0032];
    
    // Extract spectral values from AS7262 sensor
    const spectralValues = [
        spectralData['450nm'] || 0, // Violet
        spectralData['500nm'] || 0, // Blue
        spectralData['550nm'] || 0, // Green
        spectralData['570nm'] || 0, // Yellow
        spectralData['600nm'] || 0, // Orange
        spectralData['650nm'] || 0  // Red
    ];
    
    // Calculate XYZ values
    let X = 0, Y = 0, Z = 0;
    for (let i = 0; i < 6; i++) {
        X += spectralValues[i] * xCoefficients[i];
        Y += spectralValues[i] * yCoefficients[i];
        Z += spectralValues[i] * zCoefficients[i];
    }
    
    // Normalize
    const sum = X + Y + Z;
    if (sum === 0) return { X: 0, Y: 0, Z: 0 };
    
    return { X, Y, Z };
}

/**
 * Calculate chromaticity coordinates (x,y) from XYZ values
 * @param {object} xyz - Object with X, Y, Z values
 * @returns {object} - Object with x, y coordinates
 */
function calculateChromaticity(xyz) {
    const sum = xyz.X + xyz.Y + xyz.Z;
    if (sum === 0) return { x: 0, y: 0 };
    
    const x = xyz.X / sum;
    const y = xyz.Y / sum;
    
    return { x, y };
}

/**
 * Calculate CCT using McCamy's formula
 * CCT = 449*n³ + 3525*n² - 6823.3*n + 5520.33, where n = (x - 0.3320) / (y - 0.1858)
 * @param {object} chromaticity - Object with x, y coordinates
 * @returns {number} - Color temperature in Kelvin
 */
function calculateCCTMcCamy(chromaticity) {
    const { x, y } = chromaticity;
    
    // Check if values are valid
    if (x === 0 && y === 0) return 6500; // Default to 6500K
    
    // Calculate n
    const n = (x - 0.3320) / (y - 0.1858);
    
    // Calculate CCT using McCamy's formula
    let cct = 449 * Math.pow(n, 3) + 3525 * Math.pow(n, 2) - 6823.3 * n + 5520.33;
    
    // Limit to valid range (2000K-7000K)
    cct = Math.max(2000, Math.min(7000, cct));
    
    // Round to nearest 50K
    return Math.round(cct / 50) * 50;
}

/**
 * Calculate u'v' coordinates from x,y
 * @param {object} chromaticity - Object with x, y coordinates
 * @returns {object} - Object with u, v coordinates
 */
function calculateUV(chromaticity) {
    const { x, y } = chromaticity;
    
    // Calculate u'v' coordinates
    const u = 4 * x / (-2 * x + 12 * y + 3);
    const v = 9 * y / (-2 * x + 12 * y + 3);
    
    return { u, v };
}

/**
 * Calculate Planckian locus coordinates for a given CCT
 * @param {number} cct - Color temperature in Kelvin
 * @returns {object} - Object with u, v coordinates on Planckian locus
 */
function calculatePlanckianUV(cct) {
    // Approximation of Planckian locus in u'v' space
    const T = cct;
    const T2 = T * T;
    const T3 = T2 * T;
    
    // Calculate u'v' coordinates on Planckian locus
    let u, v;
    
    if (T <= 4000) {
        u = (0.179910 + 0.8776956E-4 * T - 0.2343589E-7 * T2 - 0.2661239E-10 * T3);
        v = (0.283593 - 0.10733E-4 * T + 0.99381E-8 * T2 - 0.3213E-11 * T3);
    } else {
        u = (0.1950439 + 0.2246008E-4 * T - 0.65471E-8 * T2 - 0.6358E-12 * T3);
        v = (0.2831483 - 0.4277005E-5 * T + 0.7573E-9 * T2 - 0.4956E-13 * T3);
    }
    
    return { u, v };
}

/**
 * Calculate tint (Duv) - distance from Planckian locus
 * @param {object} uv - Object with u, v coordinates
 * @param {number} cct - Color temperature in Kelvin
 * @returns {number} - Tint value (positive = green, negative = magenta)
 */
function calculateTint(uv, cct) {
    const planckianUV = calculatePlanckianUV(cct);
    
    // Calculate distance from Planckian locus
    // Positive = above locus (green), Negative = below locus (magenta)
    const deltaU = uv.u - planckianUV.u;
    const deltaV = uv.v - planckianUV.v;
    
    // Calculate perpendicular distance (Duv)
    // The factor 0.436 is an approximation for the slope of the perpendicular line
    const duv = deltaV - 0.436 * deltaU;
    
    // Scale to realistic tint range (-10 to +10)
    // First normalize to a smaller value (typical Duv values are very small, around 0.001-0.01)
    const normalizedDuv = duv * 0.01;
    
    // Then scale to the -10 to +10 range and clamp
    return Math.max(-10, Math.min(10, normalizedDuv * 100));
}

/**
 * Calculate CCT and Tint from spectral data
 * @param {object} spectralData - Object containing spectral values at different wavelengths
 * @returns {object} - Object with cct and tint values
 */
function calculateColorTemperature(spectralData) {
    // Calculate XYZ values
    const xyz = calculateXYZ(spectralData);
    
    // Calculate chromaticity coordinates
    const chromaticity = calculateChromaticity(xyz);
    
    // Calculate CCT using McCamy's formula
    const cct = calculateCCTMcCamy(chromaticity);
    
    // Calculate u'v' coordinates
    const uv = calculateUV(chromaticity);
    
    // Calculate tint (Duv)
    const tint = calculateTint(uv, cct);
    
    return {
        cct,
        tint,
        chromaticity,
        uv
    };
}

/**
 * Calculate camera white balance settings from CCT and tint
 * @param {number} cct - Color temperature in Kelvin
 * @param {number} tint - Tint value
 * @param {number} targetCCT - Target color temperature for camera (default: 5600K)
 * @returns {object} - Object with white balance settings
 */
function calculateCameraSettings(cct, tint, targetCCT = 5600) {
    // Calculate white balance multipliers
    const cctRatio = targetCCT / cct;
    
    // Basic RGB multipliers based on CCT ratio
    // These are simplified approximations
    let rMult, gMult, bMult;
    
    if (cctRatio > 1) {
        // Scene is cooler than target (add warmth)
        rMult = Math.min(2, Math.pow(cctRatio, 0.5));
        bMult = 1;
    } else {
        // Scene is warmer than target (add coolness)
        rMult = 1;
        bMult = Math.min(2, Math.pow(1/cctRatio, 0.5));
    }
    
    // Adjust for tint
    // Positive tint (green) requires magenta correction
    // Negative tint (magenta) requires green correction
    const tintAdjustment = Math.min(0.5, Math.abs(tint) / 20);
    
    if (tint > 0) {
        // Green tint, add magenta (increase red and blue)
        rMult *= (1 + tintAdjustment);
        bMult *= (1 + tintAdjustment);
        gMult = 1;
    } else {
        // Magenta tint, add green
        gMult = 1 + tintAdjustment;
        rMult = rMult;
        bMult = bMult;
    }
    
    // Calculate deviation from target
    const cctDeviation = cct - targetCCT;
    
    return {
        rMultiplier: rMult.toFixed(2),
        gMultiplier: gMult.toFixed(2),
        bMultiplier: bMult.toFixed(2),
        cctDeviation,
        cctRatio: cctRatio.toFixed(2)
    };
}

// --- Data Filtering ---

/**
 * Data filter class for noise reduction and smoothing
 */
class DataFilter {
    constructor(windowSize = 10) {
        this.windowSize = windowSize;
        this.dataBuffer = {};
    }
    
    /**
     * Apply moving average filter
     * @param {string} sensorId - Sensor identifier
     * @param {number} value - Current sensor value
     * @returns {number} - Filtered value
     */
    movingAverage(sensorId, value) {
        if (!this.dataBuffer[sensorId]) {
            this.dataBuffer[sensorId] = [];
        }
        
        const buffer = this.dataBuffer[sensorId];
        buffer.push(value);
        
        if (buffer.length > this.windowSize) {
            buffer.shift();
        }
        
        return buffer.reduce((sum, val) => sum + val, 0) / buffer.length;
    }
    
    /**
     * Apply median filter
     * @param {string} sensorId - Sensor identifier
     * @param {number} value - Current sensor value
     * @returns {number} - Filtered value
     */
    medianFilter(sensorId, value) {
        if (!this.dataBuffer[sensorId]) {
            this.dataBuffer[sensorId] = [];
        }
        
        const buffer = this.dataBuffer[sensorId];
        buffer.push(value);
        
        if (buffer.length > this.windowSize) {
            buffer.shift();
        }
        
        const sortedBuffer = [...buffer].sort((a, b) => a - b);
        const mid = Math.floor(sortedBuffer.length / 2);
        
        return sortedBuffer.length % 2 === 0
            ? (sortedBuffer[mid - 1] + sortedBuffer[mid]) / 2
            : sortedBuffer[mid];
    }
    
    /**
     * Apply exponential smoothing filter
     * @param {string} sensorId - Sensor identifier
     * @param {number} value - Current sensor value
     * @param {number} alpha - Smoothing factor (0-1)
     * @returns {number} - Filtered value
     */
    exponentialSmoothing(sensorId, value, alpha = 0.2) {
        if (!this.dataBuffer[sensorId]) {
            this.dataBuffer[sensorId] = [value];
            return value;
        }
        
        const lastValue = this.dataBuffer[sensorId][this.dataBuffer[sensorId].length - 1];
        const smoothedValue = alpha * value + (1 - alpha) * lastValue;
        
        this.dataBuffer[sensorId].push(smoothedValue);
        if (this.dataBuffer[sensorId].length > this.windowSize) {
            this.dataBuffer[sensorId].shift();
        }
        
        return smoothedValue;
    }
    
    /**
     * Apply Kalman filter for more sophisticated noise reduction
     * This is a simplified implementation of a Kalman filter
     * @param {string} sensorId - Sensor identifier
     * @param {number} value - Current sensor value
     * @param {number} processNoise - Process noise (Q)
     * @param {number} measurementNoise - Measurement noise (R)
     * @returns {number} - Filtered value
     */
    kalmanFilter(sensorId, value, processNoise = 0.01, measurementNoise = 1) {
        // Initialize state if not exists
        if (!this.dataBuffer[sensorId]) {
            this.dataBuffer[sensorId] = {
                estimate: value,
                errorCovariance: 1
            };
            return value;
        }
        
        const state = this.dataBuffer[sensorId];
        
        // Prediction step
        const predictedCovariance = state.errorCovariance + processNoise;
        
        // Update step
        const kalmanGain = predictedCovariance / (predictedCovariance + measurementNoise);
        const newEstimate = state.estimate + kalmanGain * (value - state.estimate);
        const newCovariance = (1 - kalmanGain) * predictedCovariance;
        
        // Update state
        state.estimate = newEstimate;
        state.errorCovariance = newCovariance;
        
        return newEstimate;
    }
    
    /**
     * Filter spectral data object
     * @param {object} spectralData - Object with spectral values
     * @param {string} filterType - Type of filter to apply
     * @returns {object} - Filtered spectral data
     */
    filterSpectralData(spectralData, filterType = 'movingAverage') {
        const filteredData = {};
        
        for (const key in spectralData) {
            if (typeof spectralData[key] === 'number') {
                switch (filterType) {
                    case 'median':
                        filteredData[key] = this.medianFilter(`spectral_${key}`, spectralData[key]);
                        break;
                    case 'exponential':
                        filteredData[key] = this.exponentialSmoothing(`spectral_${key}`, spectralData[key]);
                        break;
                    case 'kalman':
                        filteredData[key] = this.kalmanFilter(`spectral_${key}`, spectralData[key]);
                        break;
                    case 'movingAverage':
                    default:
                        filteredData[key] = this.movingAverage(`spectral_${key}`, spectralData[key]);
                        break;
                }
            } else {
                filteredData[key] = spectralData[key];
            }
        }
        
        return filteredData;
    }
}

// Export functions for use in other modules
window.ColorScience = {
    calculateXYZ,
    calculateChromaticity,
    calculateCCTMcCamy,
    calculateUV,
    calculatePlanckianUV,
    calculateTint,
    calculateColorTemperature,
    calculateCameraSettings,
    DataFilter
};