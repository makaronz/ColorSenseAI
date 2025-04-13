#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ColorSense Arduino Simulator
============================

Symulator mikrokontrolera Arduino z czujnikami:
- AS7262 - 6-kanałowy czujnik spektralny
- TSL2591 - Czujnik luminancji o wysokim zakresie dynamicznym
- DFRobot SEN0611 - Miernik CCT i ALS
- Moduł GPS NEO-6M

Symuluje warunki pogodowe w centrum Warszawy w pochmurny dzień 1 marca 2023 około 17:30.
"""

import time
import json
import random
import datetime
import math
import argparse
import threading
import socket
import logging
from typing import Dict, List, Tuple, Optional, Union, Any

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ArduinoSimulator")

# Stałe
DEFAULT_PORT = 8765
DEFAULT_HOST = "localhost"
DEFAULT_INTERVAL = 1.0  # sekundy
DEFAULT_DATE = "2023-03-01"
DEFAULT_TIME = "17:30:00"
DEFAULT_LATITUDE = 52.2297  # Warszawa, centrum
DEFAULT_LONGITUDE = 21.0122  # Warszawa, centrum
DEFAULT_WEATHER = "cloudy"  # pochmurno

# Parametry symulacji
SIMULATION_NOISE = 0.05  # 5% szumu
SIMULATION_DRIFT = 0.001  # 0.1% dryfu na godzinę
SIMULATION_TEMP_RANGE = (2.0, 5.0)  # Zakres temperatur w stopniach Celsjusza

class SensorAS7262:
    """Symulator czujnika spektralnego AS7262."""
    
    # Długości fal dla 6 kanałów (nm)
    WAVELENGTHS = [450, 500, 550, 570, 600, 650]
    
    # Typowe wartości dla różnych warunków pogodowych
    WEATHER_PROFILES = {
        "sunny": [0.8, 0.9, 1.0, 0.95, 0.9, 0.85],
        "cloudy": [0.4, 0.5, 0.6, 0.55, 0.5, 0.45],
        "rainy": [0.2, 0.3, 0.35, 0.3, 0.25, 0.2],
        "foggy": [0.3, 0.35, 0.4, 0.4, 0.35, 0.3],
        "night": [0.05, 0.04, 0.03, 0.02, 0.01, 0.01]
    }
    
    def __init__(self, weather: str = "cloudy"):
        """
        Inicjalizacja czujnika AS7262.
        
        Args:
            weather: Warunki pogodowe ("sunny", "cloudy", "rainy", "foggy", "night")
        """
        self.weather = weather
        self.base_values = self.WEATHER_PROFILES.get(weather, self.WEATHER_PROFILES["cloudy"])
        self.temperature = 25.0  # Temperatura czujnika w stopniach Celsjusza
        
    def read(self, time_of_day: datetime.datetime) -> Dict[str, float]:
        """
        Odczyt wartości z czujnika.
        
        Args:
            time_of_day: Czas odczytu
            
        Returns:
            Słownik z wartościami dla każdego kanału
        """
        # Współczynnik zależny od pory dnia (0.0 - 1.0)
        hour = time_of_day.hour + time_of_day.minute / 60.0
        
        # Symulacja zmian w ciągu dnia (maksimum około południa)
        day_factor = 1.0 - abs((hour - 12.0) / 12.0)
        
        # Dla pochmurnego dnia, zmniejszamy wpływ pory dnia
        if self.weather == "cloudy":
            day_factor = 0.3 + 0.3 * day_factor
        
        # Dodaj losowy szum
        noise = [random.uniform(-SIMULATION_NOISE, SIMULATION_NOISE) for _ in range(6)]
        
        # Oblicz wartości dla każdego kanału
        values = {}
        for i, wavelength in enumerate(self.WAVELENGTHS):
            base = self.base_values[i]
            value = base * day_factor * (1.0 + noise[i])
            values[f"{wavelength}nm"] = max(0.0, min(1.0, value))
            
        # Dodaj temperaturę czujnika
        values["temperature"] = self.temperature
        
        return values
        
    def update_temperature(self, ambient_temp: float):
        """
        Aktualizacja temperatury czujnika.
        
        Args:
            ambient_temp: Temperatura otoczenia w stopniach Celsjusza
        """
        # Symulacja nagrzewania się czujnika
        self.temperature = ambient_temp + random.uniform(1.0, 3.0)


class SensorTSL2591:
    """Symulator czujnika luminancji TSL2591."""
    
    # Typowe wartości luminancji (lux) dla różnych warunków pogodowych
    WEATHER_LUX = {
        "sunny": 20000.0,
        "cloudy": 5000.0,
        "rainy": 2000.0,
        "foggy": 1000.0,
        "night": 10.0
    }
    
    def __init__(self, weather: str = "cloudy"):
        """
        Inicjalizacja czujnika TSL2591.
        
        Args:
            weather: Warunki pogodowe ("sunny", "cloudy", "rainy", "foggy", "night")
        """
        self.weather = weather
        self.base_lux = self.WEATHER_LUX.get(weather, self.WEATHER_LUX["cloudy"])
        
    def read(self, time_of_day: datetime.datetime) -> Dict[str, Union[float, int]]:
        """
        Odczyt wartości z czujnika.
        
        Args:
            time_of_day: Czas odczytu
            
        Returns:
            Słownik z wartościami luminancji, IR i pełnego spektrum
        """
        # Współczynnik zależny od pory dnia (0.0 - 1.0)
        hour = time_of_day.hour + time_of_day.minute / 60.0
        
        # Symulacja zmian w ciągu dnia (maksimum około południa)
        day_factor = 1.0 - abs((hour - 12.0) / 12.0)
        
        # Dla pochmurnego dnia, zmniejszamy wpływ pory dnia
        if self.weather == "cloudy":
            day_factor = 0.3 + 0.3 * day_factor
        
        # Dodaj losowy szum
        noise = random.uniform(-SIMULATION_NOISE, SIMULATION_NOISE)
        
        # Oblicz luminancję
        lux = self.base_lux * day_factor * (1.0 + noise)
        
        # Symulacja wartości IR i pełnego spektrum
        ir = int(lux * 0.3 * (1.0 + random.uniform(-0.1, 0.1)))
        full = int(lux * 1.3 * (1.0 + random.uniform(-0.1, 0.1)))
        
        return {
            "lux": lux,
            "ir": ir,
            "full": full
        }


class SensorSEN0611:
    """Symulator miernika CCT i ALS DFRobot SEN0611."""
    
    # Typowe wartości CCT (K) dla różnych warunków pogodowych
    WEATHER_CCT = {
        "sunny": 5500.0,
        "cloudy": 6500.0,
        "rainy": 7000.0,
        "foggy": 6800.0,
        "night": 4000.0
    }
    
    # Typowe wartości ALS (lux) dla różnych warunków pogodowych
    WEATHER_ALS = {
        "sunny": 18000.0,
        "cloudy": 4500.0,
        "rainy": 1800.0,
        "foggy": 900.0,
        "night": 5.0
    }
    
    def __init__(self, weather: str = "cloudy"):
        """
        Inicjalizacja czujnika SEN0611.
        
        Args:
            weather: Warunki pogodowe ("sunny", "cloudy", "rainy", "foggy", "night")
        """
        self.weather = weather
        self.base_cct = self.WEATHER_CCT.get(weather, self.WEATHER_CCT["cloudy"])
        self.base_als = self.WEATHER_ALS.get(weather, self.WEATHER_ALS["cloudy"])
        
    def read(self, time_of_day: datetime.datetime) -> Dict[str, float]:
        """
        Odczyt wartości z czujnika.
        
        Args:
            time_of_day: Czas odczytu
            
        Returns:
            Słownik z wartościami CCT i ALS
        """
        # Współczynnik zależny od pory dnia (0.0 - 1.0)
        hour = time_of_day.hour + time_of_day.minute / 60.0
        
        # Symulacja zmian w ciągu dnia
        # CCT jest wyższe rano i wieczorem (bardziej niebieskie światło)
        # i niższe w południe (bardziej żółte światło)
        time_factor = abs((hour - 12.0) / 12.0)
        cct_factor = 1.0 + 0.2 * time_factor
        
        # ALS (luminancja) jest najwyższa w południe
        als_factor = 1.0 - abs((hour - 12.0) / 12.0)
        
        # Dla pochmurnego dnia, zmniejszamy wpływ pory dnia na ALS
        if self.weather == "cloudy":
            als_factor = 0.3 + 0.3 * als_factor
        
        # Dodaj losowy szum
        cct_noise = random.uniform(-SIMULATION_NOISE, SIMULATION_NOISE)
        als_noise = random.uniform(-SIMULATION_NOISE, SIMULATION_NOISE)
        
        # Oblicz wartości CCT i ALS
        cct = self.base_cct * cct_factor * (1.0 + cct_noise)
        als = self.base_als * als_factor * (1.0 + als_noise)
        
        return {
            "cct": cct,
            "als": als
        }


class GPSModuleNEO6M:
    """Symulator modułu GPS NEO-6M."""
    
    def __init__(self, latitude: float = DEFAULT_LATITUDE, longitude: float = DEFAULT_LONGITUDE):
        """
        Inicjalizacja modułu GPS.
        
        Args:
            latitude: Szerokość geograficzna
            longitude: Długość geograficzna
        """
        self.base_latitude = latitude
        self.base_longitude = longitude
        self.altitude = 110.0  # Wysokość w metrach (Warszawa, centrum)
        self.speed = 0.0  # Prędkość w km/h
        self.satellites = random.randint(8, 12)  # Liczba widocznych satelitów
        self.hdop = random.uniform(0.8, 1.5)  # Horizontal Dilution of Precision
        
    def read(self, time_of_day: datetime.datetime) -> Dict[str, Any]:
        """
        Odczyt danych z modułu GPS.
        
        Args:
            time_of_day: Czas odczytu
            
        Returns:
            Słownik z danymi GPS
        """
        # Dodaj losowy szum do pozycji (symulacja dryfu GPS)
        lat_noise = random.uniform(-0.0001, 0.0001)
        lon_noise = random.uniform(-0.0001, 0.0001)
        alt_noise = random.uniform(-1.0, 1.0)
        
        # Aktualizuj liczbę satelitów i HDOP
        if random.random() < 0.1:  # 10% szans na zmianę
            self.satellites = max(4, min(14, self.satellites + random.randint(-1, 1)))
            self.hdop = max(0.5, min(3.0, self.hdop + random.uniform(-0.1, 0.1)))
        
        # Formatuj czas w formacie NMEA
        nmea_time = time_of_day.strftime("%H%M%S.%f")[:-4]
        nmea_date = time_of_day.strftime("%d%m%y")
        
        return {
            "latitude": self.base_latitude + lat_noise,
            "longitude": self.base_longitude + lon_noise,
            "altitude": self.altitude + alt_noise,
            "speed": self.speed,
            "satellites": self.satellites,
            "hdop": self.hdop,
            "time": nmea_time,
            "date": nmea_date,
            "fix": 1 if self.satellites >= 4 else 0
        }


class ArduinoSimulator:
    """Symulator mikrokontrolera Arduino z czujnikami."""
    
    def __init__(self, 
                 date_str: str = DEFAULT_DATE,
                 time_str: str = DEFAULT_TIME,
                 latitude: float = DEFAULT_LATITUDE,
                 longitude: float = DEFAULT_LONGITUDE,
                 weather: str = DEFAULT_WEATHER,
                 interval: float = DEFAULT_INTERVAL):
        """
        Inicjalizacja symulatora.
        
        Args:
            date_str: Data symulacji (format: YYYY-MM-DD)
            time_str: Czas symulacji (format: HH:MM:SS)
            latitude: Szerokość geograficzna
            longitude: Długość geograficzna
            weather: Warunki pogodowe ("sunny", "cloudy", "rainy", "foggy", "night")
            interval: Interwał odczytu danych w sekundach
        """
        # Parsowanie daty i czasu
        date_time_str = f"{date_str} {time_str}"
        self.start_time = datetime.datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
        self.current_time = self.start_time
        
        # Inicjalizacja czujników
        self.as7262 = SensorAS7262(weather)
        self.tsl2591 = SensorTSL2591(weather)
        self.sen0611 = SensorSEN0611(weather)
        self.gps = GPSModuleNEO6M(latitude, longitude)
        
        # Parametry symulacji
        self.weather = weather
        self.interval = interval
        self.running = False
        self.simulation_thread = None
        self.server_socket = None
        self.clients = []
        
        # Temperatura otoczenia
        self.ambient_temperature = random.uniform(*SIMULATION_TEMP_RANGE)
        
        logger.info(f"Symulator zainicjalizowany: {date_time_str}, {weather}, {latitude}, {longitude}")
        
    def read_sensors(self) -> Dict[str, Any]:
        """
        Odczyt danych ze wszystkich czujników.
        
        Returns:
            Słownik z danymi ze wszystkich czujników
        """
        # Aktualizacja temperatury czujnika
        self.as7262.update_temperature(self.ambient_temperature)
        
        # Odczyt danych z czujników
        as7262_data = self.as7262.read(self.current_time)
        tsl2591_data = self.tsl2591.read(self.current_time)
        sen0611_data = self.sen0611.read(self.current_time)
        gps_data = self.gps.read(self.current_time)
        
        # Połącz dane w jeden słownik
        data = {
            "timestamp": self.current_time.isoformat(),
            "as7262": as7262_data,
            "tsl2591": tsl2591_data,
            "sen0611": sen0611_data,
            "gps": gps_data,
            "ambient_temperature": self.ambient_temperature
        }
        
        return data
        
    def update_time(self):
        """Aktualizacja czasu symulacji."""
        self.current_time += datetime.timedelta(seconds=self.interval)
        
        # Aktualizacja temperatury otoczenia (niewielkie zmiany w czasie)
        temp_change = random.uniform(-0.1, 0.1)
        self.ambient_temperature += temp_change
        
    def start_server(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        """
        Uruchomienie serwera TCP do przesyłania danych.
        
        Args:
            host: Adres hosta
            port: Numer portu
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((host, port))
            self.server_socket.listen(5)
            logger.info(f"Serwer uruchomiony na {host}:{port}")
            
            # Wątek akceptujący połączenia
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
        except Exception as e:
            logger.error(f"Błąd podczas uruchamiania serwera: {str(e)}")
            self.server_socket = None
            
    def _accept_connections(self):
        """Akceptowanie połączeń od klientów."""
        while self.running and self.server_socket:
            try:
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Nowe połączenie od {addr}")
                self.clients.append(client_socket)
            except Exception as e:
                if self.running:
                    logger.error(f"Błąd podczas akceptowania połączenia: {str(e)}")
                break
                
    def _send_data_to_clients(self, data: Dict[str, Any]):
        """
        Wysyłanie danych do klientów.
        
        Args:
            data: Dane do wysłania
        """
        if not self.clients:
            return
            
        # Konwersja danych do formatu JSON
        json_data = json.dumps(data) + "\n"
        data_bytes = json_data.encode('utf-8')
        
        # Lista klientów do usunięcia
        to_remove = []
        
        # Wysyłanie danych do każdego klienta
        for client in self.clients:
            try:
                client.sendall(data_bytes)
            except Exception as e:
                logger.warning(f"Błąd podczas wysyłania danych do klienta: {str(e)}")
                to_remove.append(client)
                
        # Usunięcie rozłączonych klientów
        for client in to_remove:
            try:
                client.close()
            except:
                pass
            self.clients.remove(client)
            
    def start(self):
        """Uruchomienie symulatora."""
        if self.running:
            logger.warning("Symulator już jest uruchomiony")
            return
            
        self.running = True
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        logger.info("Symulator uruchomiony")
        
    def stop(self):
        """Zatrzymanie symulatora."""
        self.running = False
        
        if self.simulation_thread:
            self.simulation_thread.join(timeout=2.0)
            self.simulation_thread = None
            
        # Zamknięcie połączeń
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients = []
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
            
        logger.info("Symulator zatrzymany")
        
    def _simulation_loop(self):
        """Główna pętla symulacji."""
        while self.running:
            # Odczyt danych z czujników
            data = self.read_sensors()
            
            # Wyświetlenie danych
            self._print_data(data)
            
            # Wysłanie danych do klientów
            self._send_data_to_clients(data)
            
            # Aktualizacja czasu
            self.update_time()
            
            # Poczekaj na następny odczyt
            time.sleep(self.interval)
            
    def _print_data(self, data: Dict[str, Any]):
        """
        Wyświetlenie danych z czujników.
        
        Args:
            data: Dane z czujników
        """
        print(f"\n=== Odczyt czujników: {data['timestamp']} ===")
        
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
    parser = argparse.ArgumentParser(description='Symulator Arduino z czujnikami')
    parser.add_argument('--date', type=str, default=DEFAULT_DATE, help='Data symulacji (YYYY-MM-DD)')
    parser.add_argument('--time', type=str, default=DEFAULT_TIME, help='Czas symulacji (HH:MM:SS)')
    parser.add_argument('--lat', type=float, default=DEFAULT_LATITUDE, help='Szerokość geograficzna')
    parser.add_argument('--lon', type=float, default=DEFAULT_LONGITUDE, help='Długość geograficzna')
    parser.add_argument('--weather', type=str, default=DEFAULT_WEATHER, 
                        choices=['sunny', 'cloudy', 'rainy', 'foggy', 'night'],
                        help='Warunki pogodowe')
    parser.add_argument('--interval', type=float, default=DEFAULT_INTERVAL, help='Interwał odczytu (sekundy)')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST, help='Adres hosta serwera')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port serwera')
    parser.add_argument('--no-server', action='store_true', help='Nie uruchamiaj serwera')
    
    args = parser.parse_args()
    
    # Utworzenie symulatora
    simulator = ArduinoSimulator(
        date_str=args.date,
        time_str=args.time,
        latitude=args.lat,
        longitude=args.lon,
        weather=args.weather,
        interval=args.interval
    )
    
    try:
        # Uruchomienie serwera
        if not args.no_server:
            simulator.start_server(host=args.host, port=args.port)
            
        # Uruchomienie symulatora
        simulator.start()
        
        # Pętla główna
        print("Naciśnij Ctrl+C, aby zakończyć...")
        while True:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nZatrzymywanie symulatora...")
    finally:
        simulator.stop()
        print("Symulator zatrzymany.")
        

if __name__ == "__main__":
    main()