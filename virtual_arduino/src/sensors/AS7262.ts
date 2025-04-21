import { AS7262Data, AS7262Config, EnvironmentalConditions } from '../interfaces/Sensors';

export class AS7262Sensor {
    private config: AS7262Config = {
        gain: 1,
        integrationTime: 100,
        ledDrive: 0,
        ledMode: 0
    };

    private lastMeasurement: AS7262Data = {
        violet: 0,
        blue: 0,
        green: 0,
        yellow: 0,
        orange: 0,
        red: 0,
        temperature: 25
    };

    // Charakterystyki spektralne różnych źródeł światła
    private readonly LIGHT_PROFILES = {
        sunlight: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        incandescent: [0.3, 0.5, 0.7, 0.9, 1.0, 1.0],
        fluorescent: [0.8, 1.0, 0.9, 0.7, 0.5, 0.4],
        led: [0.9, 1.0, 0.8, 0.6, 0.5, 0.4]
    };

    constructor() {
        this.initSensor();
    }

    private initSensor(): void {
        // Symulacja inicjalizacji sprzętowej
        console.log('Initializing AS7262 sensor...');
    }

    public configure(config: Partial<AS7262Config>): void {
        this.config = { ...this.config, ...config };
    }

    public measure(env: EnvironmentalConditions): AS7262Data {
        // Symulacja pomiaru z uwzględnieniem warunków środowiskowych
        const baseValues = this.calculateBaseValues(env);
        const noisyValues = this.addNoise(baseValues);
        const gainAdjusted = this.applyGain(noisyValues);

        this.lastMeasurement = {
            violet: gainAdjusted[0],
            blue: gainAdjusted[1],
            green: gainAdjusted[2],
            yellow: gainAdjusted[3],
            orange: gainAdjusted[4],
            red: gainAdjusted[5],
            temperature: this.simulateTemperature(env)
        };

        return this.lastMeasurement;
    }

    private calculateBaseValues(env: EnvironmentalConditions): number[] {
        // Wybierz profil światła na podstawie warunków
        let profile: number[];
        if (env.artificialLight.type !== 'none') {
            profile = this.LIGHT_PROFILES[env.artificialLight.type];
        } else {
            profile = this.LIGHT_PROFILES.sunlight;
        }

        // Uwzględnij intensywność światła i zachmurzenie
        const intensity = env.lightIntensity * (1 - env.cloudCover * 0.7);
        return profile.map(v => v * intensity * 100); // Skalowanie do realistycznych wartości
    }

    private addNoise(values: number[]): number[] {
        // Dodaj realistyczny szum do pomiarów
        return values.map(v => {
            const noise = (Math.random() - 0.5) * 0.05 * v; // 5% szumu
            return Math.max(0, v + noise);
        });
    }

    private applyGain(values: number[]): number[] {
        // Zastosuj wzmocnienie i symuluj saturację
        const gainFactors = {
            1: 1,
            3.7: 3.7,
            16: 16,
            64: 64
        };
        const gainFactor = gainFactors[this.config.gain] || 1;
        const maxValue = 65535; // 16-bit ADC

        return values.map(v => Math.min(v * gainFactor, maxValue));
    }

    private simulateTemperature(env: EnvironmentalConditions): number {
        // Symuluj temperaturę czujnika na podstawie temperatury otoczenia
        const selfHeating = this.config.ledMode > 0 ? 2 : 0;
        const noise = (Math.random() - 0.5) * 0.2;
        return env.temperature + selfHeating + noise;
    }

    public getLastMeasurement(): AS7262Data {
        return this.lastMeasurement;
    }

    public getConfig(): AS7262Config {
        return this.config;
    }
} 