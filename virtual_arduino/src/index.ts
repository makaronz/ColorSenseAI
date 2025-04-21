import { VirtualArduino } from './VirtualArduino';
import express from 'express';
import cors from 'cors';
import path from 'path';

// Konfiguracja serwera Express
const app = express();
const PORT = process.env.PORT || 3000;
const WS_PORT = process.env.WS_PORT || 8080;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

// Endpoint testowy
app.get('/api/status', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Virtual Arduino is running',
        timestamp: new Date().toISOString()
    });
});

// Uruchom serwer HTTP
app.listen(PORT, () => {
    console.log(`HTTP server running on port ${PORT}`);
});

// Uruchom wirtualne Arduino
const arduino = new VirtualArduino(Number(WS_PORT));

// Obsługa zamknięcia
process.on('SIGINT', () => {
    console.log('Shutting down...');
    arduino.stop();
    process.exit(0);
}); 