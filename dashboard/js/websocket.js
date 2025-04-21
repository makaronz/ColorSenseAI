// Konfiguracja WebSocket
const WS_HOST = 'localhost';
const WS_PORT = 8765;

class ArduinoConnection {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // 2 sekundy
        this.onDataCallbacks = [];
    }

    connect() {
        try {
            this.ws = new WebSocket(`ws://${WS_HOST}:${WS_PORT}`);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Błąd podczas tworzenia połączenia WebSocket:', error);
            this.handleConnectionError();
        }
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('Połączono z symulatorem Arduino');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            document.getElementById('connection-status').textContent = 'Połączono';
            document.getElementById('connection-status').className = 'badge badge-success';
        };

        this.ws.onclose = () => {
            console.log('Rozłączono z symulatorem Arduino');
            this.isConnected = false;
            document.getElementById('connection-status').textContent = 'Rozłączono';
            document.getElementById('connection-status').className = 'badge badge-error';
            this.handleConnectionError();
        };

        this.ws.onerror = (error) => {
            console.error('Błąd WebSocket:', error);
            this.handleConnectionError();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.onDataCallbacks.forEach(callback => callback(data));
            } catch (error) {
                console.error('Błąd podczas przetwarzania danych:', error);
            }
        };
    }

    handleConnectionError() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Próba ponownego połączenia ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            console.error('Przekroczono maksymalną liczbę prób połączenia');
        }
    }

    onData(callback) {
        this.onDataCallbacks.push(callback);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Eksportuj klasę do użycia w innych plikach
window.ArduinoConnection = ArduinoConnection; 