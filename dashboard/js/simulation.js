function normalRandom(mean, deviation) {
    let u = 0, v = 0;
    while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
    while(v === 0) v = Math.random();
    let num = Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v );
    return num * deviation + mean;
}


// Simulation parameters (Warsaw, Poland - 2024-11-12 approximation)
const LATITUDE = 52.2297;
const LONGITUDE = 21.0122;
const ELEVATION = 110;
const TIMEZONE = "Europe/Warsaw"; // Not directly used in JS, but for reference
const DATE_STR = "2024-11-12";

// Approximate sunrise and sunset for Warsaw on 2024-11-12 (for simplicity)
const sunriseHour = 7;   // 7:00 AM
const sunsetHour = 17;  // 5:00 PM
const noonHour = 12;    // 12:00 PM

function getSunInfo() {
    const date = new Date(DATE_STR);
    const sunrise = new Date(date);
    sunrise.setHours(sunriseHour, 0, 0, 0);
    const sunset = new Date(date);
    sunset.setHours(sunsetHour, 0, 0, 0);
    const noon = new Date(date);
    noon.setHours(noonHour, 0, 0, 0);

    return { sunrise, sunset, noon };
}

function solarIntensityFactor(currentTime, sunrise, sunset, noon) {
    if (currentTime < sunrise || currentTime > sunset) {
        return 0.0;
    }
    // Sinusoidal model for intensity
    const totalDaylightSeconds = (sunset - sunrise) / 1000; // Convert milliseconds to seconds
    const timeSinceSunrise = (currentTime - sunrise) / 1000; // Convert milliseconds to seconds
    const factor = Math.sin(Math.PI * timeSinceSunrise / totalDaylightSeconds);
    return Math.max(0.0, factor); // Ensure it's not negative
}
function simulateSensorData(currentTime, sunInfo) {
    const intensityFactor = solarIntensityFactor(currentTime, sunInfo.sunrise, sunInfo.sunset, sunInfo.noon);

    // AS7262 data simulation
    const as7262Data = {
        '450nm': 100 * intensityFactor + normalRandom(0, 5),
        '500nm': 120 * intensityFactor + normalRandom(0, 5),
        '550nm': 150 * intensityFactor + normalRandom(0, 5),
        '570nm': 130 * intensityFactor + normalRandom(0, 5),
        '600nm': 110 * intensityFactor + normalRandom(0, 5),
        '650nm': 90 * intensityFactor + normalRandom(0, 5),
        'temperature': 25 + 5 * intensityFactor + normalRandom(0, 1)
    };

    // TSL2591 data simulation
    const tsl2591Data = {
        'lux': 1000 * intensityFactor + normalRandom(0, 50),
        'ir': 500 * intensityFactor + normalRandom(0, 25),
        'visible': 800 * intensityFactor + normalRandom(0, 40),
        'full_spectrum': 1500 * intensityFactor + normalRandom(0, 75)
    };

    // SEN0611 (CCT and ALS) data simulation
    const sen0611Data = {
        'cct': 5000 + 2000 * intensityFactor + normalRandom(0, 100),
        'als': 500 * intensityFactor + normalRandom(0, 25)
    };

    // Optional GPS module - always returns fixed data
    const gpsData = {
        'latitude': LATITUDE + normalRandom(0, 0.001),
        'longitude': LONGITUDE + normalRandom(0, 0.001),
        'altitude': ELEVATION + normalRandom(0, 1),
        'satellites': 8 + Math.floor(Math.random() * 3) - 1, // Equivalent of np.random.randint(-1, 2)
        'hdop': 1.0 + normalRandom(0, 0.1)
    };

    return {
        'timestamp': currentTime.toISOString(),
        'AS7262': as7262Data,
        'TSL2591': tsl2591Data,
        'SEN0611': sen0611Data,
        'GPS': gpsData
    };
}


// dashboard/js/simulation.js

// Placeholder for simulation functions, will be populated with translated Python logic