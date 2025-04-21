import { TSL2591Data, TSL2591Config, EnvironmentalConditions } from '../interfaces/Sensors';

export class TSL2591Sensor {
    private config: TSL2591Config = {
        gain: 1,
        integrationTime: 100,
        enabled: true
    };

    private lastMeasurement: TSL2591Data = {
        visible: 0,
        ir: 0,
        full: 0,
        lux: 0
    };

    // Stałe kalibracyjne
    private readonly LUX_DF = 408.0;    // Współczynnik skali luksów
    private readonly CH0_COEFF = 1.00;   // Współczynnik kanału 0 (pełne spektrum)
    private readonly CH1_COEFF = 1.64;   // Współczynnik kanału 1 (IR)

    constructor() {
        this.initSensor();
    }

    private initSensor(): void {
        console.log('Initializing TSL2591 sensor...');
    }

    public configure(config: Partial<TSL2591Config>): void {
        this.config = { ...this.config, ...config };
    }

    public measure(env: EnvironmentalConditions): TSL2591Data {
        if (!this.config.enabled) {
            return this.lastMeasurement;
        }

        // Symulacja pomiaru
        const rawValues = this.simulateRawValues(env);
        const gainAdjusted = this.applyGain(rawValues);
        const withNoise = this.addNoise(gainAdjusted);

        // Oblicz wartości końcowe
        const full = withNoise.ch0;
        const ir = withNoise.ch1;
        const visible = Math.max(0, full - ir);
        const lux = this.calculateLux(full, ir);

        this.lastMeasurement = {
            visible,
            ir,
            full,
            lux
        };

        return this.lastMeasurement;
    }

    private simulateRawValues(env: EnvironmentalConditions): { ch0: number, ch1: number } {
        // Symulacja surowych wartości ADC na podstawie warunków środowiskowych
        const baseIntensity = env.lightIntensity * (1 - env.cloudCover * 0.7);
        
        let ch0Base = baseIntensity * 65535; // Pełna skala 16-bit
        let ch1Ratio = 0.25; // Bazowy stosunek IR

        // Modyfikuj stosunek IR w zależności od źródła światła
        if (env.artificialLight.type !== 'none') {
            switch (env.artificialLight.type) {
                case 'incandescent':
                    ch1Ratio = 0.4;
                    break;
                case 'fluorescent':
                    ch1Ratio = 0.2;
                    break;
                case 'led':
                    ch1Ratio = 0.15;
                    break;
            }
        }

        // Uwzględnij porę dnia
        const timeEffect = Math.sin(Math.PI * env.timeOfDay / 24);
        ch1Ratio += (timeEffect * 0.1); // IR zmienia się w ciągu dnia

        return {
            ch0: ch0Base,
            ch1: ch0Base * ch1Ratio
        };
    }

    private applyGain(values: { ch0: number, ch1: number }): { ch0: number, ch1: number } {
        // Zastosuj wzmocnienie
        const gainFactors = {
            1: 1,
            25: 25,
            428: 428,
            9876: 9876
        };
        const gainFactor = gainFactors[this.config.gain] || 1;
        const maxValue = 65535;

        return {
            ch0: Math.min(values.ch0 * gainFactor, maxValue),
            ch1: Math.min(values.ch1 * gainFactor, maxValue)
        };
    }

    private addNoise(values: { ch0: number, ch1: number }): { ch0: number, ch1: number } {
        // Dodaj realistyczny szum do pomiarów
        const addNoiseToValue = (value: number): number => {
            const noise = (Math.random() - 0.5) * 0.02 * value; // 2% szumu
            return Math.max(0, Math.min(65535, value + noise));
        };

        return {
            ch0: addNoiseToValue(values.ch0),
            ch1: addNoiseToValue(values.ch1)
        };
    }

    private calculateLux(ch0: number, ch1: number): number {
        // Implementacja rzeczywistego algorytmu obliczania luksów TSL2591
        if (ch0 === 0) {
            return 0;
        }

        const ch0_calc = ch0 * this.CH0_COEFF;
        const ch1_calc = ch1 * this.CH1_COEFF;

        if (ch0_calc < ch1_calc) {
            return 0;
        }

        const ratio = ch1_calc / ch0_calc;
        let lux: number;

        if (ratio <= 0.50) {
            lux = (0.0304 * ch0_calc) - (0.062 * ch0_calc * Math.pow(ratio, 1.4));
        } else if (ratio <= 0.61) {
            lux = (0.0224 * ch0_calc) - (0.031 * ch1_calc);
        } else if (ratio <= 0.80) {
            lux = (0.0128 * ch0_calc) - (0.0153 * ch1_calc);
        } else if (ratio <= 1.30) {
            lux = (0.00146 * ch0_calc) - (0.00112 * ch1_calc);
        } else {
            lux = 0;
        }

        // Zastosuj współczynnik skali
        lux *= this.LUX_DF;
        
        return Math.max(0, lux);
    }

    public getLastMeasurement(): TSL2591Data {
        return this.lastMeasurement;
    }

    public getConfig(): TSL2591Config {
        return this.config;
    }
} 