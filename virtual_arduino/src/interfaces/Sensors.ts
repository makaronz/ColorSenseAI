// Interfejs dla AS7262 - 6-kanałowy czujnik spektralny
export interface AS7262Data {
    violet: number;   // 450nm
    blue: number;     // 500nm
    green: number;    // 550nm
    yellow: number;   // 570nm
    orange: number;   // 600nm
    red: number;      // 650nm
    temperature: number;
}

export interface AS7262Config {
    gain: number;           // Wzmocnienie (1x, 3.7x, 16x, 64x)
    integrationTime: number; // Czas integracji (2.8ms - 714ms)
    ledDrive: number;       // Prąd diody LED (0-3)
    ledMode: number;        // Tryb LED (0: wyłączony, 1: włączony, 2: tylko podczas pomiaru)
}

// Interfejs dla TSL2591 - Czujnik luminancji
export interface TSL2591Data {
    visible: number;    // Światło widzialne
    ir: number;        // Podczerwień
    full: number;      // Pełne spektrum
    lux: number;       // Obliczona wartość lux
}

export interface TSL2591Config {
    gain: number;           // Wzmocnienie (1x, 25x, 428x, 9876x)
    integrationTime: number; // Czas integracji (100ms - 600ms)
    enabled: boolean;       // Stan czujnika
}

// Interfejs dla SEN0611 - Miernik CCT i ALS
export interface SEN0611Data {
    cct: number;       // Skorelowana temperatura barwowa (K)
    als: number;       // Czujnik światła otoczenia (lux)
    accuracy: number;  // Dokładność pomiaru (0-100%)
}

export interface SEN0611Config {
    mode: number;      // Tryb pracy (0: normalny, 1: wysoka dokładność)
    threshold: number; // Próg wyzwalania
}

// Interfejs dla całego zestawu czujników
export interface SensorSet {
    as7262: {
        data: AS7262Data;
        config: AS7262Config;
    };
    tsl2591: {
        data: TSL2591Data;
        config: TSL2591Config;
    };
    sen0611: {
        data: SEN0611Data;
        config: SEN0611Config;
    };
    timestamp: number;
}

// Typy komunikatów WebSocket
export type WSMessage = {
    type: 'config' | 'data' | 'command' | 'error';
    sensor?: 'as7262' | 'tsl2591' | 'sen0611' | 'all';
    data?: any;
    error?: string;
}

// Interfejs dla generatora danych środowiskowych
export interface EnvironmentalConditions {
    temperature: number;     // Temperatura otoczenia (°C)
    humidity: number;       // Wilgotność (%)
    lightIntensity: number; // Intensywność światła (%)
    timeOfDay: number;      // Czas dnia (0-24h)
    cloudCover: number;     // Zachmurzenie (0-1)
    artificialLight: {      // Sztuczne źródła światła
        type: 'none' | 'incandescent' | 'fluorescent' | 'led';
        intensity: number;  // 0-1
    };
} 