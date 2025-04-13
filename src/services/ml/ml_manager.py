from typing import Dict, Optional, List, Tuple, Any
from .ml_feature_manager import MLFeatureManager
from .color_correction import ColorCorrectionModel
from .anomaly_detection import AnomalyDetectionSystem
from .sensor_optimization import SensorOptimizationAgent
from .adaptive_calibration import AdaptiveCalibrationSystem
import numpy as np
import os
import json
import time
from datetime import datetime
import logging
from ..data_fusion.sensor_fusion import fuse_sensor_data

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/ml_manager.log'
)
logger = logging.getLogger('MLManager')

class MLManager:
    def __init__(self, config_path: str = "config/ml_features.json"):
        self.config_path = config_path
        self.feature_manager = MLFeatureManager(config_path)
        self.color_correction: Optional[ColorCorrectionModel] = None
        self.anomaly_detection: Optional[AnomalyDetectionSystem] = None
        self.sensor_optimization: Optional[SensorOptimizationAgent] = None
        self.adaptive_calibration: Optional[AdaptiveCalibrationSystem] = None
        
        # Statystyki wydajności
        self.performance_stats = {
            'color_correction': {'inference_time': [], 'memory_usage': []},
            'anomaly_detection': {'inference_time': [], 'memory_usage': []},
            'sensor_optimization': {'inference_time': [], 'memory_usage': []},
            'adaptive_calibration': {'inference_time': [], 'memory_usage': []}
        }
        
        # Historia danych
        self.data_history = []
        self.max_history_size = 100
        
        # Inicjalizacja modeli
        self.initialize_models()
        def initialize_models(self):
            """
            Inicjalizuje modele ML na podstawie włączonych funkcji.
            """
            try:
                logger.info("Inicjalizacja modeli ML")
                
                if self.feature_manager.is_feature_enabled("color_correction"):
                    logger.info("Inicjalizacja modelu korekcji kolorów")
                    self.color_correction = ColorCorrectionModel()
                    
                if self.feature_manager.is_feature_enabled("anomaly_detection"):
                    logger.info("Inicjalizacja systemu wykrywania anomalii")
                    self.anomaly_detection = AnomalyDetectionSystem()
                    
                if self.feature_manager.is_feature_enabled("sensor_optimization"):
                    logger.info("Inicjalizacja agenta optymalizacji czujników")
                    self.sensor_optimization = SensorOptimizationAgent()
                    
                if self.feature_manager.is_feature_enabled("adaptive_calibration"):
                    logger.info("Inicjalizacja systemu adaptacyjnej kalibracji")
                    self.adaptive_calibration = AdaptiveCalibrationSystem()
                    
                logger.info("Inicjalizacja modeli ML zakończona")
            except Exception as e:
                logger.error(f"Błąd podczas inicjalizacji modeli ML: {str(e)}")
                raise
                
            def process_sensor_data(self, sensor_data: np.ndarray, env_data: np.ndarray) -> Dict:
                """
                Przetwarza dane z czujników przez wszystkie włączone modele ML.
                Mierzy czas wykonania i zużycie pamięci dla każdego modelu.
                
                Args:
                    sensor_data: Dane z czujników
                    env_data: Dane środowiskowe (temperatura, wilgotność, itp.)
                    
                Returns:
                    Słownik zawierający wyniki przetwarzania
                """
                results = {
                    'color_correction': None,
                    'anomaly_detection': None,
                    'sensor_optimization': None,
                    'adaptive_calibration': None,
                    'fused_data': None,
                    'performance': {},
                    'timestamp': datetime.now().isoformat()
                }
                
                try:
                    # Dodaj dane do historii
                    self._update_data_history(sensor_data, env_data)
                    
                    # Fuzja danych z czujników
                    if len(self.data_history) > 0:
                        sensor_dict = {
                            'spectral': sensor_data[:6].tolist() if len(sensor_data) >= 6 else [],
                            'luminance': float(sensor_data[6]) if len(sensor_data) > 6 else 0.0,
                            'als': float(sensor_data[7]) if len(sensor_data) > 7 else 0.0,
                            'cct': float(sensor_data[8]) if len(sensor_data) > 8 else 0.0
                        }
                        
                        previous_data = [
                            {
                                'spectral': d['sensor_data'][:6].tolist() if len(d['sensor_data']) >= 6 else [],
                                'luminance': float(d['sensor_data'][6]) if len(d['sensor_data']) > 6 else 0.0,
                                'als': float(d['sensor_data'][7]) if len(d['sensor_data']) > 7 else 0.0,
                                'cct': float(d['sensor_data'][8]) if len(d['sensor_data']) > 8 else 0.0
                            }
                            for d in self.data_history[-5:]  # Użyj ostatnich 5 pomiarów
                        ]
                        
                        start_time = time.time()
                        fused_data = fuse_sensor_data(sensor_dict, previous_data)
                        results['fused_data'] = fused_data
                        results['performance']['fusion'] = {
                            'time': time.time() - start_time
                        }
                    
                    # Korekcja koloru
                    if self.color_correction:
                        start_time = time.time()
                        memory_before = self._get_memory_usage()
                        
                        results['color_correction'] = self.color_correction.predict_correction(
                            sensor_data, env_data
                        )
                        
                        inference_time = time.time() - start_time
                        memory_usage = self._get_memory_usage() - memory_before
                        
                        self.performance_stats['color_correction']['inference_time'].append(inference_time)
                        self.performance_stats['color_correction']['memory_usage'].append(memory_usage)
                        
                        results['performance']['color_correction'] = {
                            'time': inference_time,
                            'memory': memory_usage
                        }
                        
                    # Wykrywanie anomalii
                    if self.anomaly_detection:
                        start_time = time.time()
                        memory_before = self._get_memory_usage()
                        
                        results['anomaly_detection'] = self.anomaly_detection.detect_anomalies(
                            sensor_data
                        )
                        
                        inference_time = time.time() - start_time
                        memory_usage = self._get_memory_usage() - memory_before
                        
                        self.performance_stats['anomaly_detection']['inference_time'].append(inference_time)
                        self.performance_stats['anomaly_detection']['memory_usage'].append(memory_usage)
                        
                        results['performance']['anomaly_detection'] = {
                            'time': inference_time,
                            'memory': memory_usage
                        }
                        
                    # Optymalizacja sensorów
                    if self.sensor_optimization:
                        start_time = time.time()
                        memory_before = self._get_memory_usage()
                        
                        results['sensor_optimization'] = self.sensor_optimization.optimize_settings(
                            sensor_data
                        )
                        
                        inference_time = time.time() - start_time
                        memory_usage = self._get_memory_usage() - memory_before
                        
                        self.performance_stats['sensor_optimization']['inference_time'].append(inference_time)
                        self.performance_stats['sensor_optimization']['memory_usage'].append(memory_usage)
                        
                        results['performance']['sensor_optimization'] = {
                            'time': inference_time,
                            'memory': memory_usage
                        }
                        
                    # Adaptacyjna kalibracja
                    if self.adaptive_calibration:
                        start_time = time.time()
                        memory_before = self._get_memory_usage()
                        
                        results['adaptive_calibration'] = self.adaptive_calibration.update_calibration(
                            sensor_data, env_data[0]  # Zakładamy, że temperatura jest pierwszym elementem
                        )
                        
                        inference_time = time.time() - start_time
                        memory_usage = self._get_memory_usage() - memory_before
                        
                        self.performance_stats['adaptive_calibration']['inference_time'].append(inference_time)
                        self.performance_stats['adaptive_calibration']['memory_usage'].append(memory_usage)
                        
                        results['performance']['adaptive_calibration'] = {
                            'time': inference_time,
                            'memory': memory_usage
                        }
                        
                    # Oblicz średnie czasy wnioskowania i zużycie pamięci
                    results['performance']['average'] = self._calculate_average_performance()
                    
                    logger.info(f"Przetworzono dane z czujników: {results['performance']['average']}")
                    
                    return results
                except Exception as e:
                    logger.error(f"Błąd podczas przetwarzania danych z czujników: {str(e)}")
                    results['error'] = str(e)
                    return results
                
        def train_models(self, training_data: Dict):
            """
            Trenuje wszystkie modele ML na podstawie dostarczonych danych treningowych.
            
            Args:
                training_data: Słownik zawierający dane treningowe dla każdego modelu
            """
            try:
                logger.info("Rozpoczęcie treningu modeli ML")
                
                if self.color_correction and 'color_correction' in training_data:
                    logger.info("Trening modelu korekcji kolorów")
                    
                    # Optymalizacja hiperparametrów, jeśli dostępne dane walidacyjne
                    if 'validation' in training_data['color_correction']:
                        self.color_correction.optimize_hyperparameters(
                            training_data['color_correction']['X'],
                            training_data['color_correction']['y']
                        )
                    else:
                        # Standardowy trening
                        self.color_correction.train(
                            training_data['color_correction']['X'],
                            training_data['color_correction']['y'],
                            validation_split=0.2
                        )
                    
                    # Kwantyzacja modelu
                    self.color_correction.quantize_model()
                    
                if self.anomaly_detection and 'anomaly_detection' in training_data:
                    logger.info("Trening systemu wykrywania anomalii")
                    
                    # Optymalizacja hiperparametrów, jeśli dostępne dane walidacyjne
                    if 'validation_data' in training_data['anomaly_detection']:
                        self.anomaly_detection.optimize_hyperparameters(
                            training_data['anomaly_detection']['normal_data'],
                            training_data['anomaly_detection']['validation_data']
                        )
                    else:
                        # Standardowy trening
                        self.anomaly_detection.train(
                            training_data['anomaly_detection']['normal_data'],
                            epochs=50,
                            batch_size=32,
                            validation_split=0.2
                        )
                    
                if self.sensor_optimization and 'sensor_optimization' in training_data:
                    logger.info("Trening agenta optymalizacji czujników")
                    
                    # Optymalizacja hiperparametrów, jeśli dostępne dane walidacyjne
                    if 'validation_data' in training_data['sensor_optimization']:
                        self.sensor_optimization.optimize_hyperparameters(
                            training_data['sensor_optimization']['validation_data']
                        )
                    
                    # Standardowy trening
                    self.sensor_optimization.train(
                        training_data['sensor_optimization']['episodes'],
                        training_data['sensor_optimization']['batch_size'],
                        training_data['sensor_optimization'].get('validation_data')
                    )
                    
                if self.adaptive_calibration and 'adaptive_calibration' in training_data:
                    logger.info("Trening systemu adaptacyjnej kalibracji")
                    
                    # Optymalizacja hiperparametrów, jeśli dostępne dane walidacyjne
                    if 'validation_split' in training_data['adaptive_calibration']:
                        self.adaptive_calibration.optimize_hyperparameters(
                            training_data['adaptive_calibration']['training_data'],
                            training_data['adaptive_calibration']['validation_split']
                        )
                    else:
                        # Standardowy trening
                        self.adaptive_calibration.train(
                            training_data['adaptive_calibration']['training_data'],
                            validation_split=0.2
                        )
                    
                logger.info("Trening modeli ML zakończony")
            except Exception as e:
                logger.error(f"Błąd podczas treningu modeli ML: {str(e)}")
                raise
                
            
    def enable_feature(self, feature_name: str):
        """
        Włącza funkcję ML i inicjalizuje odpowiedni model.
        
        Args:
            feature_name: Nazwa funkcji do włączenia
        """
        try:
            logger.info(f"Włączanie funkcji: {feature_name}")
            self.feature_manager.enable_feature(feature_name)
            self.initialize_models()
            logger.info(f"Funkcja {feature_name} została włączona")
        except Exception as e:
            logger.error(f"Błąd podczas włączania funkcji {feature_name}: {str(e)}")
            raise
        
    def disable_feature(self, feature_name: str):
        """
        Wyłącza funkcję ML i zwalnia zasoby odpowiedniego modelu.
        
        Args:
            feature_name: Nazwa funkcji do wyłączenia
        """
        try:
            logger.info(f"Wyłączanie funkcji: {feature_name}")
            self.feature_manager.disable_feature(feature_name)
            
            # Zwolnij zasoby modelu
            if feature_name == "color_correction":
                self.color_correction = None
            elif feature_name == "anomaly_detection":
                self.anomaly_detection = None
            elif feature_name == "sensor_optimization":
                self.sensor_optimization = None
            elif feature_name == "adaptive_calibration":
                self.adaptive_calibration = None
                
            logger.info(f"Funkcja {feature_name} została wyłączona")
        except Exception as e:
            logger.error(f"Błąd podczas wyłączania funkcji {feature_name}: {str(e)}")
            raise
        
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Sprawdza, czy funkcja ML jest włączona.
        
        Args:
            feature_name: Nazwa funkcji do sprawdzenia
            
        Returns:
            True, jeśli funkcja jest włączona, False w przeciwnym razie
        """
        return self.feature_manager.is_feature_enabled(feature_name)
        
    def get_performance_stats(self) -> Dict:
        """
        Zwraca statystyki wydajności modeli ML.
        
        Returns:
            Słownik zawierający statystyki wydajności
        """
        return {
            'color_correction': self._calculate_model_stats('color_correction'),
            'anomaly_detection': self._calculate_model_stats('anomaly_detection'),
            'sensor_optimization': self._calculate_model_stats('sensor_optimization'),
            'adaptive_calibration': self._calculate_model_stats('adaptive_calibration')
        }
        
    def _calculate_model_stats(self, model_name: str) -> Dict:
        """
        Oblicza statystyki wydajności dla danego modelu.
        
        Args:
            model_name: Nazwa modelu
            
        Returns:
            Słownik zawierający statystyki wydajności
        """
        if not self.performance_stats[model_name]['inference_time']:
            return {
                'avg_inference_time': 0,
                'min_inference_time': 0,
                'max_inference_time': 0,
                'avg_memory_usage': 0
            }
            
        inference_times = self.performance_stats[model_name]['inference_time']
        memory_usages = self.performance_stats[model_name]['memory_usage']
        
        return {
            'avg_inference_time': sum(inference_times) / len(inference_times),
            'min_inference_time': min(inference_times),
            'max_inference_time': max(inference_times),
            'avg_memory_usage': sum(memory_usages) / len(memory_usages) if memory_usages else 0
        }
        
    def _calculate_average_performance(self) -> Dict:
        """
        Oblicza średnie statystyki wydajności dla wszystkich modeli.
        
        Returns:
            Słownik zawierający średnie statystyki wydajności
        """
        all_times = []
        all_memory = []
        
        for model_name in self.performance_stats:
            all_times.extend(self.performance_stats[model_name]['inference_time'])
            all_memory.extend(self.performance_stats[model_name]['memory_usage'])
            
        if not all_times:
            return {
                'avg_inference_time': 0,
                'total_inference_time': 0,
                'avg_memory_usage': 0
            }
            
        return {
            'avg_inference_time': sum(all_times) / len(all_times),
            'total_inference_time': sum(all_times),
            'avg_memory_usage': sum(all_memory) / len(all_memory) if all_memory else 0
        }
        
    def _get_memory_usage(self) -> float:
        """
        Zwraca aktualne zużycie pamięci procesu.
        
        Returns:
            Zużycie pamięci w MB
        """
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0
        
    def _update_data_history(self, sensor_data: np.ndarray, env_data: np.ndarray):
        """
        Aktualizuje historię danych z czujników.
        
        Args:
            sensor_data: Dane z czujników
            env_data: Dane środowiskowe
        """
        self.data_history.append({
            'sensor_data': sensor_data,
            'env_data': env_data,
            'timestamp': datetime.now()
        })
        
        # Ogranicz rozmiar historii
        if len(self.data_history) > self.max_history_size:
            self.data_history = self.data_history[-self.max_history_size:]
            
    def save_config(self):
        """
        Zapisuje konfigurację funkcji ML do pliku.
        """
        self.feature_manager.save_config()
        
    def load_config(self):
        """
        Ładuje konfigurację funkcji ML z pliku.
        """
        self.feature_manager.load_config()
        self.initialize_models()