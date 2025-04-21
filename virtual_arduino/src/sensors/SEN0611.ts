import { SEN0611Data, SEN0611Config, EnvironmentalConditions } from '../interfaces/Sensors';

export class SEN0611Sensor {
    private config: SEN0611Config = {
        mode: 0,
        threshold: 10
    };

    private lastMeasurement: SEN0611Data = {
        cct: 5500,
        als: 0,
        accuracy: 100
    };

    // Stałe kalibracyjne dla różnych źródeł światła
    private readonly LIGHT_SOURCES = {
        sunlight: {
            baseCCT: 5500,
            variation: 500,
            accuracy: 95
        },
        incandescent: {
            baseCCT: 2700,
            variation: 200,
            accuracy: 90
        },
        fluorescent: {
            baseCCT: 4000,
            variation: 300,
            accuracy: 85
        },
        led: {
            baseCCT: 6500,
            variation: 400,
            accuracy: 92
        }
    };

    constructor() {
        this.initSensor();
    }

    private initSensor(): void {
        console.log('Initializing SEN0611 sensor...');
    }

    public configure(config: Partial<SEN0611Config>): void {
        this.config = { ...this.config, ...config };
    }

    public measure(env: EnvironmentalConditions): SEN0611Data {
        // Symulacja pomiaru
        const { cct, accuracy } = this.simulateCCT(env);
        const als = this.simulateALS(env);

        this.lastMeasurement = {
            cct,
            als,
            accuracy
        };

        return this.lastMeasurement;
    }

    private simulateCCT(env: EnvironmentalConditions): { cct: number, accuracy: number } {
        let baseCCT: number;
        let baseAccuracy: number;
        let variation: number;

        // Wybierz bazowe wartości w zależności od źródła światła
        if (env.artificialLight.type !== 'none') {
            const source = this.LIGHT_SOURCES[env.artificialLight.type];
            baseCCT = source.baseCCT;
            variation = source.variation;
            baseAccuracy = source.accuracy;
        } else {
            // Światło naturalne
            const source = this.LIGHT_SOURCES.sunlight;
            baseCCT = source.baseCCT;
            variation = source.variation;
            baseAccuracy = source.accuracy;

            // Modyfikuj CCT w zależności od pory dnia
            const timeEffect = Math.sin(Math.PI * env.timeOfDay / 24);
            baseCCT += timeEffect * 1000; // CCT zmienia się w ciągu dnia
        }

        // Uwzględnij zachmurzenie
        baseCCT += env.cloudCover * 500; // Zachmurzenie zwiększa CCT

        // Dodaj losową wariację
        const randomVariation = (Math.random() - 0.5) * 2 * variation;
        const finalCCT = Math.max(1000, Math.min(10000, baseCCT + randomVariation));

        // Oblicz dokładność
        let accuracy = baseAccuracy;
        
        // Zmniejsz dokładność przy słabym świetle
        if (env.lightIntensity < 0.1) {
            accuracy *= 0.7;
        }

        // Tryb wysokiej dokładności
        if (this.config.mode === 1) {
            accuracy = Math.min(100, accuracy * 1.1);
        }

        // Dodaj niewielką losową wariację do dokładności
        accuracy += (Math.random() - 0.5) * 2;
        accuracy = Math.max(0, Math.min(100, accuracy));

        return {
            cct: Math.round(finalCCT),
            accuracy: Math.round(accuracy)
        };
    }

    private simulateALS(env: EnvironmentalConditions): number {
        // Bazowa wartość ALS na podstawie intensywności światła
        let als = env.lightIntensity * 100000; // Maksymalna wartość 100k lux

        // Uwzględnij zachmurzenie
        als *= (1 - env.cloudCover * 0.7);

        // Uwzględnij sztuczne światło
        if (env.artificialLight.type !== 'none') {
            als += env.artificialLight.intensity * 1000;
        }

        // Dodaj szum
        const noise = (Math.random() - 0.5) * 0.05 * als; // 5% szumu
        als = Math.max(0, als + noise);

        // Zastosuj próg
        if (als < this.config.threshold) {
            als = 0;
        }

        return Math.round(als * 100) / 100; // Zaokrąglij do 2 miejsc po przecinku
    }

    public getLastMeasurement(): SEN0611Data {
        return this.lastMeasurement;
    }

    public getConfig(): SEN0611Config {
        return this.config;
    }
} 