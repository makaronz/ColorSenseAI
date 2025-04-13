import socket
import json
import logging
from datetime import datetime
import sys
import os

# Dodaj ścieżkę do katalogu src do PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.operations import save_sensor_reading
from database.db import init_db

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DatabaseClient")

class DatabaseClient:
    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Inicjalizacja klienta bazy danych.
        
        Args:
            host: Adres hosta symulatora
            port: Port symulatora
        """
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        
        # Inicjalizacja bazy danych
        init_db()
        logger.info("Baza danych zainicjalizowana")
        
    def connect(self):
        """Nawiązanie połączenia z symulatorem."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"Połączono z symulatorem na {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Błąd połączenia: {e}")
            return False
            
    def start(self):
        """Rozpoczęcie odbierania i zapisywania danych."""
        self.running = True
        logger.info("Rozpoczęto odbieranie danych")
        
        while self.running:
            try:
                # Odbierz dane
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                    
                # Przetwórz każdą linię osobno (może być kilka w jednym pakiecie)
                for line in data.strip().split('\n'):
                    try:
                        # Parsuj JSON
                        reading = json.loads(line)
                        
                        # Zapisz do bazy danych
                        save_sensor_reading(reading)
                        logger.debug(f"Zapisano odczyt: {reading['timestamp']}")
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Błąd parsowania JSON: {e}")
                    except KeyError as e:
                        logger.error(f"Brak wymaganego pola w danych: {e}")
                    except Exception as e:
                        logger.error(f"Błąd przetwarzania danych: {e}")
                        
            except Exception as e:
                logger.error(f"Błąd odbierania danych: {e}")
                break
                
        self.stop()
        
    def stop(self):
        """Zatrzymanie klienta."""
        self.running = False
        if self.socket:
            self.socket.close()
        logger.info("Zatrzymano klienta bazy danych")

def main():
    """Funkcja główna."""
    client = DatabaseClient()
    
    if client.connect():
        try:
            client.start()
        except KeyboardInterrupt:
            logger.info("Otrzymano sygnał przerwania")
        finally:
            client.stop()
    else:
        logger.error("Nie udało się połączyć z symulatorem")

if __name__ == "__main__":
    main() 