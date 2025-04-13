#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Przykładowy klient dla symulatora Arduino
=========================================

Ten skrypt demonstruje, jak połączyć się z symulatorem Arduino
i odbierać dane z czujników w czasie rzeczywistym.
"""

import socket
import json
import time
import argparse
import threading
import logging
import os
import sys
import datetime
from typing import Dict, Any, Optional, List

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("client.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArduinoClient")

# Stałe
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8765
DEFAULT_OUTPUT_DIR = "data"
DEFAULT_SAVE_INTERVAL = 60  # sekundy

class ArduinoClient:
    """Klient do komunikacji z symulatorem Arduino."""
    
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Inicjalizacja klienta.
        
        Args:
            host: Adres hosta symulatora
            port: Port symulatora
        """
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.running = False
        self.receive_thread = None
        self.data_buffer = []
        self.last_data = None
        self.data_callbacks = []
        
    def connect(self) -> bool:
        """
        Połączenie z symulatorem.
        
        Returns:
            True, jeśli połączenie się powiodło, False w przeciwnym razie
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info(f"Połączono z symulatorem na {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas łączenia z symulatorem: {str(e)}")
            self.socket = None
            self.connected = False
            return False
            
    def disconnect(self):
        """Rozłączenie z symulatorem."""
        self.running = False
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
            self.receive_thread = None
            
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            
        self.connected = False
        logger.info("Rozłączono z symulatorem")
        
    def start_receiving(self):
        """Rozpoczęcie odbierania danych."""
        if not self.connected:
            logger.error("Nie można rozpocząć odbierania danych - brak połączenia")
            return False
            
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        logger.info("Rozpoczęto odbieranie danych")
        return True
        
    def _receive_loop(self):
        """Główna pętla odbierania danych."""
        buffer = ""
        
        while self.running and self.socket:
            try:
                # Odbierz dane
                data = self.socket.recv(4096)
                
                if not data:
                    logger.warning("Połączenie zostało zamknięte przez serwer")
                    break
                    
                # Dodaj dane do bufora
                buffer += data.decode('utf-8')
                
                # Przetwórz kompletne linie
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    
                    try:
                        # Parsuj JSON
                        json_data = json.loads(line)
                        
                        # Zapisz dane
                        self.last_data = json_data
                        self.data_buffer.append(json_data)
                        
                        # Wywołaj callbacki
                        for callback in self.data_callbacks:
                            try:
                                callback(json_data)
                            except Exception as e:
                                logger.error(f"Błąd w callbacku: {str(e)}")
                                
                    except json.JSONDecodeError as e:
                        logger.error(f"Błąd parsowania JSON: {str(e)}")
                        
            except Exception as e:
                if self.running:
                    logger.error(f"Błąd podczas odbierania danych: {str(e)}")
                break
                
        self.running = False
        logger.info("Zakończono odbieranie danych")
        
    def add_data_callback(self, callback):
        """
        Dodanie callbacku wywoływanego przy odbiorze nowych danych.
        
        Args:
            callback: Funkcja przyjmująca jeden argument (dane w formacie JSON)
        """
        self.data_callbacks.append(callback)
        
    def get_last_data(self) -> Optional[Dict[str, Any]]:
        """
        Pobranie ostatnich odebranych danych.
        
        Returns:
            Ostatnie odebrane dane lub None, jeśli brak danych
        """
        return self.last_data
        
    def get_data_buffer(self) -> List[Dict[str, Any]]:
        """
        Pobranie bufora danych.
        
        Returns:
            Lista odebranych danych
        """
        return self.data_buffer.copy()
        
    def clear_data_buffer(self):
        """Wyczyszczenie bufora danych."""
        self.data_buffer = []
        

class DataSaver:
    """Klasa do zapisywania danych z symulatora."""
    
    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR, save_interval: int = DEFAULT_SAVE_INTERVAL):
        """
        Inicjalizacja zapisywacza danych.
        
        Args:
            output_dir: Katalog do zapisywania danych
            save_interval: Interwał zapisywania danych w sekundach
        """
        self.output_dir = output_dir
        self.save_interval = save_interval
        self.data_buffer = []
        self.running = False
        self.save_thread = None
        self.last_save_time = time.time()
        
        # Utwórz katalog wyjściowy, jeśli nie istnieje
        os.makedirs(output_dir, exist_ok=True)
        
    def add_data(self, data: Dict[str, Any]):
        """
        Dodanie danych do bufora.
        
        Args:
            data: Dane do dodania
        """
        self.data_buffer.append(data)
        
    def start(self):
        """Rozpoczęcie zapisywania danych."""
        self.running = True
        self.save_thread = threading.Thread(target=self._save_loop)
        self.save_thread.daemon = True
        self.save_thread.start()
        
        logger.info(f"Rozpoczęto zapisywanie danych (interwał: {self.save_interval}s)")
        
    def stop(self):
        """Zatrzymanie zapisywania danych."""
        self.running = False
        
        if self.save_thread:
            self.save_thread.join(timeout=2.0)
            self.save_thread = None
            
        # Zapisz pozostałe dane
        self._save_data()
        
        logger.info("Zatrzymano zapisywanie danych")
        
    def _save_loop(self):
        """Główna pętla zapisywania danych."""
        while self.running:
            current_time = time.time()
            
            # Sprawdź, czy minął interwał zapisywania
            if current_time - self.last_save_time >= self.save_interval:
                self._save_data()
                self.last_save_time = current_time
                
            # Poczekaj chwilę
            time.sleep(1.0)
            
    def _save_data(self):
        """Zapisanie danych do pliku."""
        if not self.data_buffer:
            return
            
        # Utwórz nazwę pliku na podstawie aktualnego czasu
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"sensor_data_{timestamp}.json")
        
        try:
            # Zapisz dane do pliku
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data_buffer, f, indent=2)
                
            logger.info(f"Zapisano {len(self.data_buffer)} rekordów do pliku {filename}")
            
            # Wyczyść bufor
            self.data_buffer = []
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania danych: {str(e)}")
            

def print_sensor_data(data: Dict[str, Any]):
    """
    Wyświetlenie danych z czujników.
    
    Args:
        data: Dane z czujników
    """
    print(f"\n=== Odebrano dane: {data['timestamp']} ===")
    
    # AS7262
    print("\nAS7262 (Czujnik spektralny):")
    for wavelength, value in sorted(data['as7262'].items()):
        if wavelength != 'temperature':
            print(f"  {wavelength}: {value:.4f}")
    print(f"  Temperatura: {data['as7262']['temperature']:.2f}°C")
    
    # TSL2591
    print("\nTSL2591 (Czujnik luminancji):")
    print(f"  Luminancja: {data['tsl2591']['lux']:.2f} lux")
    print(f"  IR: {data['tsl2591']['ir']}")
    print(f"  Pełne spektrum: {data['tsl2591']['full']}")
    
    # SEN0611
    print("\nSEN0611 (Miernik CCT i ALS):")
    print(f"  CCT: {data['sen0611']['cct']:.2f} K")
    print(f"  ALS: {data['sen0611']['als']:.2f} lux")
    
    # GPS
    print("\nGPS (NEO-6M):")
    print(f"  Pozycja: {data['gps']['latitude']:.6f}, {data['gps']['longitude']:.6f}")
    print(f"  Wysokość: {data['gps']['altitude']:.2f} m")
    print(f"  Satelity: {data['gps']['satellites']}")
    print(f"  HDOP: {data['gps']['hdop']:.2f}")
    print(f"  Czas GPS: {data['gps']['time']}")
    
    # Temperatura otoczenia
    print(f"\nTemperatura otoczenia: {data['ambient_temperature']:.2f}°C")
    

def main():
    """Funkcja główna."""
    parser = argparse.ArgumentParser(description='Klient symulatora Arduino')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='Adres hosta symulatora')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port symulatora')
    parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR, help='Katalog do zapisywania danych')
    parser.add_argument('--save-interval', type=int, default=DEFAULT_SAVE_INTERVAL, help='Interwał zapisywania danych (sekundy)')
    parser.add_argument('--no-save', action='store_true', help='Nie zapisuj danych')
    parser.add_argument('--quiet', action='store_true', help='Nie wyświetlaj danych')
    
    args = parser.parse_args()
    
    # Utworzenie klienta
    client = ArduinoClient(host=args.host, port=args.port)
    
    # Utworzenie zapisywacza danych
    data_saver = None
    if not args.no_save:
        data_saver = DataSaver(output_dir=args.output_dir, save_interval=args.save_interval)
        
    try:
        # Połączenie z symulatorem
        if not client.connect():
            logger.error("Nie można połączyć się z symulatorem")
            return 1
            
        # Dodanie callbacków
        if not args.quiet:
            client.add_data_callback(print_sensor_data)
            
        if data_saver:
            client.add_data_callback(data_saver.add_data)
            data_saver.start()
            
        # Rozpoczęcie odbierania danych
        client.start_receiving()
        
        # Pętla główna
        print("Naciśnij Ctrl+C, aby zakończyć...")
        while client.running:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nZatrzymywanie klienta...")
    finally:
        # Zatrzymanie zapisywania danych
        if data_saver:
            data_saver.stop()
            
        # Rozłączenie z symulatorem
        client.disconnect()
        
    return 0
    

if __name__ == "__main__":
    sys.exit(main())