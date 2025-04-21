import WebSocket, { WebSocketServer } from 'ws';
import { AS7262Sensor } from './sensors/AS7262';
import { TSL2591Sensor } from './sensors/TSL2591';
import { SEN0611Sensor } from './sensors/SEN0611';
import { EnvironmentalConditions } from './interfaces/Sensors';

export class VirtualArduino {
    private wss: WebSocketServer;
    private clients: WebSocket[] = [];
    private updateInterval: NodeJS.Timeout | null = null;
    private running: boolean = false;

    // Czujniki
    private as7262: AS7262Sensor;
    private tsl2591: TSL2591Sensor;
    private sen0611: SEN0611Sensor;

    // Warunki środowiskowe
    private environment: EnvironmentalConditions = {
        temperature: 25,
        humidity: 50,
        lightIntensity: 0.8,
        timeOfDay: 12,
        cloudCover: 0,
        artificialLight: {
            type: 'none',
            intensity: 0
        }
    };

    constructor(port: number = 8080) {
        // Inicjalizacja czujników
        this.as7262 = new AS7262Sensor();
        this.tsl2591 = new TSL2591Sensor();
        this.sen0611 = new SEN0611Sensor();

        // Konfiguracja WebSocket
        this.wss = new WebSocketServer({ port });
        this.setupWebSocket();
        
        // Rozpoczęcie symulacji
        this.start();
    }

    private setupWebSocket(): void {
        this.wss.on('connection', (ws: WebSocket) => {
            console.log('New client connected');
            this.clients.push(ws);

            ws.on('message', (message: string) => {
                try {
                    const data = JSON.parse(message.toString());
                    this.handleMessage(data, ws);
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            });

            ws.on('close', () => {
                this.clients = this.clients.filter(client => client !== ws);
                console.log('Client disconnected');
            });
        });
    }

    private handleMessage(message: any, ws: WebSocket): void {
        switch (message.type) {
            case 'config':
                this.handleConfig(message);
                break;
            case 'command':
                this.handleCommand(message);
                break;
            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    private handleConfig(message: any): void {
        if (!message.sensor || !message.data) return;

        switch (message.sensor) {
            case 'as7262':
                this.as7262.configure(message.data);
                break;
            case 'tsl2591':
                this.tsl2591.configure(message.data);
                break;
            case 'sen0611':
                this.sen0611.configure(message.data);
                break;
        }
    }

    private handleCommand(message: any): void {
        if (!message.data?.command) return;

        switch (message.data.command) {
            case 'setEnvironment':
                this.environment = {
                    ...this.environment,
                    ...message.data.environment
                };
                break;
            case 'reset':
                this.resetSimulation();
                break;
        }
    }

    private updateEnvironment(): void {
        // Aktualizacja czasu
        this.environment.timeOfDay = (this.environment.timeOfDay + 0.1) % 24;

        // Losowe zmiany zachmurzenia
        if (Math.random() < 0.1) {
            this.environment.cloudCover = Math.min(1, Math.max(0,
                this.environment.cloudCover + (Math.random() - 0.5) * 0.2
            ));
        }

        // Aktualizacja temperatury
        const timeEffect = Math.sin(Math.PI * this.environment.timeOfDay / 24);
        this.environment.temperature = 20 + timeEffect * 5 + (Math.random() - 0.5);
    }

    private broadcastData(): void {
        if (!this.running) return;

        // Aktualizacja środowiska
        this.updateEnvironment();

        // Pomiary z czujników
        const data = {
            timestamp: new Date().toISOString(),
            as7262: this.as7262.measure(this.environment),
            tsl2591: this.tsl2591.measure(this.environment),
            sen0611: this.sen0611.measure(this.environment),
            environment: this.environment
        };

        // Wysłanie danych do wszystkich klientów
        const message = JSON.stringify({
            type: 'data',
            data: data
        });

        this.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        });
    }

    private resetSimulation(): void {
        this.environment = {
            temperature: 25,
            humidity: 50,
            lightIntensity: 0.8,
            timeOfDay: 12,
            cloudCover: 0,
            artificialLight: {
                type: 'none',
                intensity: 0
            }
        };
    }

    public start(): void {
        if (this.running) return;
        
        this.running = true;
        this.updateInterval = setInterval(() => this.broadcastData(), 1000);
        console.log('Virtual Arduino started');
    }

    public stop(): void {
        if (!this.running) return;

        this.running = false;
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        this.wss.close();
        console.log('Virtual Arduino stopped');
    }
} 