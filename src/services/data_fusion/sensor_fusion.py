import numpy as np
from typing import Dict, List, Optional, Tuple
import time

class KalmanFilter:
    """
    Implementacja filtru Kalmana dla fuzji danych z czujników.
    """
    def __init__(self, state_dim: int, measurement_dim: int):
        # Wymiary stanu i pomiarów
        self.state_dim = state_dim
        self.measurement_dim = measurement_dim
        
        # Inicjalizacja macierzy stanu
        self.x = np.zeros((state_dim, 1))  # Stan
        self.P = np.eye(state_dim)  # Kowariancja stanu
        self.F = np.eye(state_dim)  # Model przejścia stanu
        self.Q = np.eye(state_dim) * 0.01  # Szum procesu
        
        # Inicjalizacja macierzy pomiarów
        self.H = np.zeros((measurement_dim, state_dim))  # Model pomiarów
        for i in range(min(measurement_dim, state_dim)):
            self.H[i, i] = 1.0
        self.R = np.eye(measurement_dim) * 0.1  # Szum pomiarów
        
        # Inicjalizacja czasu
        self.last_time = time.time()
        
    def predict(self) -> np.ndarray:
        """
        Krok predykcji filtru Kalmana.
        """
        # Oblicz delta czasu
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Aktualizacja macierzy przejścia stanu dla ciągłego czasu
        if self.state_dim >= 6:  # Jeśli mamy pozycję, prędkość i przyspieszenie
            # Dla każdej pary wymiarów (x, y, z)
            for i in range(0, self.state_dim, 3):
                if i + 2 < self.state_dim:
                    self.F[i, i+1] = dt
                    self.F[i+1, i+2] = dt
        
        # Predykcja stanu
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.x
        
    def update(self, z: np.ndarray, R: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Krok aktualizacji filtru Kalmana.
        
        Args:
            z: Wektor pomiarów
            R: Opcjonalna macierz kowariancji szumu pomiarów
        """
        if R is not None:
            self.R = R
            
        # Obliczenie innowacji
        y = z - self.H @ self.x
        
        # Obliczenie kowariancji innowacji
        S = self.H @ self.P @ self.H.T + self.R
        
        # Obliczenie wzmocnienia Kalmana
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Aktualizacja stanu
        self.x = self.x + K @ y
        self.P = (np.eye(self.state_dim) - K @ self.H) @ self.P
        
        return self.x
        
    def get_state(self) -> np.ndarray:
        """
        Zwraca aktualny stan.
        """
        return self.x


class SensorFusion:
    """
    Klasa odpowiedzialna za fuzję danych z różnych czujników.
    """
    def __init__(self):
        # Inicjalizacja filtrów Kalmana dla różnych parametrów
        self.cct_filter = KalmanFilter(state_dim=2, measurement_dim=1)  # Stan: [CCT, dCCT/dt]
        self.luminance_filter = KalmanFilter(state_dim=2, measurement_dim=1)  # Stan: [Luminance, dLuminance/dt]
        self.spectral_filter = KalmanFilter(state_dim=6, measurement_dim=6)  # Stan: 6 kanałów spektralnych
        
        # Ostatnie przetworzone dane
        self.last_processed_data = None
        
    def process_data(self, sensor_data: Dict, confidence_weights: Optional[Dict] = None) -> Dict:
        """
        Przetwarza dane z czujników i wykonuje fuzję danych.
        
        Args:
            sensor_data: Słownik zawierający dane z czujników
            confidence_weights: Opcjonalny słownik zawierający wagi pewności dla każdego czujnika
            
        Returns:
            Słownik zawierający przetworzone dane
        """
        # Domyślne wagi pewności
        if confidence_weights is None:
            confidence_weights = {
                'as7262': 1.0,
                'tsl2591': 1.0,
                'sen0611': 1.0
            }
            
        # Przygotuj wynikowy słownik
        result = {}
        
        # Przetwarzanie CCT
        if 'cct' in sensor_data:
            # Przygotuj pomiar i macierz kowariancji
            cct_measurement = np.array([[sensor_data['cct']]])
            cct_confidence = confidence_weights.get('sen0611', 1.0)
            cct_R = np.array([[1.0 / cct_confidence]])
            
            # Wykonaj predykcję i aktualizację
            self.cct_filter.predict()
            self.cct_filter.update(cct_measurement, cct_R)
            
            # Zapisz wynik
            result['cct'] = float(self.cct_filter.get_state()[0, 0])
            result['cct_velocity'] = float(self.cct_filter.get_state()[1, 0])
            
        # Przetwarzanie luminancji
        if 'luminance' in sensor_data and 'als' in sensor_data:
            # Oblicz średnią ważoną luminancji z dwóch czujników
            tsl_confidence = confidence_weights.get('tsl2591', 1.0)
            sen_confidence = confidence_weights.get('sen0611', 1.0)
            
            weighted_luminance = (
                sensor_data['luminance'] * tsl_confidence + 
                sensor_data['als'] * sen_confidence
            ) / (tsl_confidence + sen_confidence)
            
            # Przygotuj pomiar i macierz kowariancji
            lum_measurement = np.array([[weighted_luminance]])
            lum_R = np.array([[1.0 / (tsl_confidence + sen_confidence)]])
            
            # Wykonaj predykcję i aktualizację
            self.luminance_filter.predict()
            self.luminance_filter.update(lum_measurement, lum_R)
            
            # Zapisz wynik
            result['luminance'] = float(self.luminance_filter.get_state()[0, 0])
            result['luminance_velocity'] = float(self.luminance_filter.get_state()[1, 0])
            
        # Przetwarzanie danych spektralnych
        if 'spectral' in sensor_data and isinstance(sensor_data['spectral'], list):
            # Przygotuj pomiar
            spectral_measurement = np.array(sensor_data['spectral']).reshape(-1, 1)
            spectral_confidence = confidence_weights.get('as7262', 1.0)
            spectral_R = np.eye(len(sensor_data['spectral'])) * (1.0 / spectral_confidence)
            
            # Wykonaj predykcję i aktualizację
            self.spectral_filter.predict()
            self.spectral_filter.update(spectral_measurement, spectral_R)
            
            # Zapisz wynik
            result['spectral'] = [float(x) for x in self.spectral_filter.get_state()[:len(sensor_data['spectral']), 0]]
            
        # Dodaj oryginalne dane dla porównania
        result['original'] = sensor_data
        
        # Zapisz przetworzone dane
        self.last_processed_data = result
        
        return result
        
    def detect_outliers(self, sensor_data: Dict, threshold: float = 3.0) -> Dict:
        """
        Wykrywa wartości odstające w danych z czujników.
        
        Args:
            sensor_data: Słownik zawierający dane z czujników
            threshold: Próg dla wykrywania wartości odstających (w odchyleniach standardowych)
            
        Returns:
            Słownik zawierający flagi dla wykrytych wartości odstających
        """
        outliers = {}
        
        # Sprawdź CCT
        if 'cct' in sensor_data and self.last_processed_data is not None and 'cct' in self.last_processed_data:
            cct_diff = abs(sensor_data['cct'] - self.last_processed_data['cct'])
            cct_std = np.sqrt(self.cct_filter.P[0, 0])
            outliers['cct'] = (cct_diff > threshold * cct_std)
            
        # Sprawdź luminancję
        if 'luminance' in sensor_data and self.last_processed_data is not None and 'luminance' in self.last_processed_data:
            lum_diff = abs(sensor_data['luminance'] - self.last_processed_data['luminance'])
            lum_std = np.sqrt(self.luminance_filter.P[0, 0])
            outliers['luminance'] = (lum_diff > threshold * lum_std)
            
        # Sprawdź dane spektralne
        if 'spectral' in sensor_data and isinstance(sensor_data['spectral'], list) and self.last_processed_data is not None and 'spectral' in self.last_processed_data:
            spectral_outliers = []
            for i, (measured, filtered) in enumerate(zip(sensor_data['spectral'], self.last_processed_data['spectral'])):
                diff = abs(measured - filtered)
                std = np.sqrt(self.spectral_filter.P[i, i])
                spectral_outliers.append(diff > threshold * std)
            outliers['spectral'] = spectral_outliers
            
        return outliers
        
    def calculate_confidence(self, sensor_data: Dict, outliers: Dict) -> Dict:
        """
        Oblicza wagi pewności dla każdego czujnika na podstawie wykrytych wartości odstających.
        
        Args:
            sensor_data: Słownik zawierający dane z czujników
            outliers: Słownik zawierający flagi dla wykrytych wartości odstających
            
        Returns:
            Słownik zawierający wagi pewności dla każdego czujnika
        """
        confidence = {
            'as7262': 1.0,
            'tsl2591': 1.0,
            'sen0611': 1.0
        }
        
        # Aktualizuj pewność na podstawie wartości odstających
        if 'spectral' in outliers and any(outliers['spectral']):
            # Zmniejsz pewność AS7262 proporcjonalnie do liczby wartości odstających
            outlier_ratio = sum(outliers['spectral']) / len(outliers['spectral'])
            confidence['as7262'] = max(0.1, 1.0 - outlier_ratio)
            
        if 'luminance' in outliers and outliers['luminance']:
            # Zmniejsz pewność TSL2591
            confidence['tsl2591'] = 0.5
            
        if 'cct' in outliers and outliers['cct']:
            # Zmniejsz pewność SEN0611
            confidence['sen0611'] = 0.5
            
        # Dodatkowe reguły dla poprawy pewności
        
        # Sprawdź spójność między luminancją a danymi spektralnymi
        if 'luminance' in sensor_data and 'spectral' in sensor_data and isinstance(sensor_data['spectral'], list):
            spectral_sum = sum(sensor_data['spectral'])
            if spectral_sum > 0:
                luminance_ratio = sensor_data['luminance'] / spectral_sum
                if luminance_ratio < 0.1 or luminance_ratio > 10.0:
                    # Dane są niespójne, zmniejsz pewność obu czujników
                    confidence['as7262'] *= 0.8
                    confidence['tsl2591'] *= 0.8
                    
        # Sprawdź spójność między CCT a danymi spektralnymi
        if 'cct' in sensor_data and 'spectral' in sensor_data and isinstance(sensor_data['spectral'], list) and len(sensor_data['spectral']) >= 6:
            # Prosta heurystyka: stosunek niebieskiego do czerwonego powinien korelować z CCT
            blue_red_ratio = sensor_data['spectral'][0] / (sensor_data['spectral'][5] + 1e-6)
            expected_ratio = 0.5 + sensor_data['cct'] / 10000.0  # Prosta aproksymacja
            
            ratio_diff = abs(blue_red_ratio - expected_ratio) / expected_ratio
            if ratio_diff > 0.5:  # Jeśli różnica jest większa niż 50%
                confidence['as7262'] *= 0.8
                confidence['sen0611'] *= 0.8
                
        return confidence


def fuse_sensor_data(sensor_data: Dict, previous_data: Optional[List[Dict]] = None) -> Dict:
    """
    Główna funkcja do fuzji danych z czujników.
    
    Args:
        sensor_data: Słownik zawierający dane z czujników
        previous_data: Opcjonalna lista poprzednich danych z czujników
        
    Returns:
        Słownik zawierający przetworzone dane
    """
    # Utwórz obiekt fuzji danych
    fusion = SensorFusion()
    
    # Jeśli mamy poprzednie dane, przetwórz je najpierw
    if previous_data is not None:
        for data in previous_data:
            fusion.process_data(data)
    
    # Wykryj wartości odstające
    outliers = fusion.detect_outliers(sensor_data)
    
    # Oblicz wagi pewności
    confidence = fusion.calculate_confidence(sensor_data, outliers)
    
    # Wykonaj fuzję danych
    result = fusion.process_data(sensor_data, confidence)
    
    # Dodaj informacje o wartościach odstających i pewności
    result['outliers'] = outliers
    result['confidence'] = confidence
    
    return result