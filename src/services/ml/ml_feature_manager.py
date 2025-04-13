import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .data_manager import MLDataManager

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/ml_feature_manager.log'
)
logger = logging.getLogger('MLFeatureManager')

class MLFeatureManager:
    """
    Klasa odpowiedzialna za zarządzanie funkcjami uczenia maszynowego.
    Umożliwia włączanie i wyłączanie funkcji oraz zapisywanie i ładowanie konfiguracji.
    """
    def __init__(self, config_path: str = "config/ml_features.json"):
        """
        Inicjalizuje menedżera funkcji ML.
        
        Args:
            config_path: Ścieżka do pliku konfiguracyjnego
        """
        self.config_path = config_path
        self.data_manager = MLDataManager()
        self.features = {
            "color_correction": {
                "enabled": False,
                "last_training": None,
                "performance_metrics": {},
                "model_path": None
            },
            "anomaly_detection": {
                "enabled": False,
                "last_training": None,
                "performance_metrics": {},
                "model_path": None
            },
            "sensor_optimization": {
                "enabled": False,
                "last_training": None,
                "performance_metrics": {},
                "model_path": None
            },
            "adaptive_calibration": {
                "enabled": False,
                "last_training": None,
                "performance_metrics": {},
                "model_path": None
            }
        }
        
        # Utwórz katalog konfiguracyjny, jeśli nie istnieje
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Załaduj konfigurację, jeśli istnieje
        self.load_config()
        
    def enable_feature(self, feature_name: str) -> bool:
        """
        Włącza funkcję ML.
        
        Args:
            feature_name: Nazwa funkcji do włączenia
            
        Returns:
            True, jeśli funkcja została włączona, False w przeciwnym razie
        """
        if feature_name in self.features:
            self.features[feature_name]["enabled"] = True
            logger.info(f"Funkcja {feature_name} została włączona")
            self.save_config()
            return True
        else:
            logger.warning(f"Próba włączenia nieistniejącej funkcji: {feature_name}")
            return False
            
    def disable_feature(self, feature_name: str) -> bool:
        """
        Wyłącza funkcję ML.
        
        Args:
            feature_name: Nazwa funkcji do wyłączenia
            
        Returns:
            True, jeśli funkcja została wyłączona, False w przeciwnym razie
        """
        if feature_name in self.features:
            self.features[feature_name]["enabled"] = False
            logger.info(f"Funkcja {feature_name} została wyłączona")
            self.save_config()
            return True
        else:
            logger.warning(f"Próba wyłączenia nieistniejącej funkcji: {feature_name}")
            return False
            
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Sprawdza, czy funkcja ML jest włączona.
        
        Args:
            feature_name: Nazwa funkcji do sprawdzenia
            
        Returns:
            True, jeśli funkcja jest włączona, False w przeciwnym razie
        """
        return self.features.get(feature_name, {}).get("enabled", False)
        
    def get_enabled_features(self) -> List[str]:
        """
        Zwraca listę włączonych funkcji ML.
        
        Returns:
            Lista włączonych funkcji
        """
        return [feature for feature, config in self.features.items() if config["enabled"]]

    def update_feature_metrics(self, feature_name: str, metrics: Dict[str, float], model_path: str) -> bool:
        """
        Aktualizuje metryki wydajności dla danej funkcji ML.
        
        Args:
            feature_name: Nazwa funkcji
            metrics: Słownik z metrykami wydajności
            model_path: Ścieżka do zapisanego modelu
            
        Returns:
            True, jeśli metryki zostały zaktualizowane, False w przeciwnym razie
        """
        if feature_name in self.features:
            self.features[feature_name]["performance_metrics"] = metrics
            self.features[feature_name]["last_training"] = datetime.now().isoformat()
            self.features[feature_name]["model_path"] = model_path
            self.save_config()
            
            # Zapisz metryki w bazie danych
            self.data_manager.save_model_results(
                model_name=feature_name,
                version=datetime.now().strftime("%Y%m%d_%H%M%S"),
                metrics=metrics,
                model_path=model_path,
                parameters={}
            )
            return True
        return False

    def get_feature_metrics(self, feature_name: str) -> Optional[Dict]:
        """
        Pobiera metryki wydajności dla danej funkcji ML.
        
        Args:
            feature_name: Nazwa funkcji
            
        Returns:
            Słownik z metrykami lub None, jeśli funkcja nie istnieje
        """
        if feature_name in self.features:
            return {
                "metrics": self.features[feature_name]["performance_metrics"],
                "last_training": self.features[feature_name]["last_training"],
                "model_path": self.features[feature_name]["model_path"]
            }
        return None

    def prepare_training_data(self, feature_name: str, hours: int = 24) -> Optional[tuple]:
        """
        Przygotowuje dane treningowe dla danej funkcji ML.
        
        Args:
            feature_name: Nazwa funkcji
            hours: Liczba godzin danych do przygotowania
            
        Returns:
            Tuple (X, y) z danymi treningowymi lub None w przypadku błędu
        """
        try:
            if feature_name == "color_correction":
                return self.data_manager.prepare_color_correction_data(hours)
            elif feature_name == "anomaly_detection":
                return self.data_manager.prepare_anomaly_detection_data(hours)
            elif feature_name == "sensor_optimization":
                return self.data_manager.prepare_sensor_optimization_data(hours)
            elif feature_name == "adaptive_calibration":
                return self.data_manager.prepare_calibration_data(hours)
            else:
                logger.warning(f"Nieznana funkcja ML: {feature_name}")
                return None
        except Exception as e:
            logger.error(f"Błąd podczas przygotowywania danych dla {feature_name}: {str(e)}")
            return None
            
    def save_config(self) -> bool:
        """
        Zapisuje konfigurację funkcji ML do pliku.
        
        Returns:
            True, jeśli konfiguracja została zapisana, False w przeciwnym razie
        """
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.features, f, indent=4)
            logger.info(f"Konfiguracja zapisana do {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania konfiguracji: {str(e)}")
            return False
            
    def load_config(self) -> bool:
        """
        Ładuje konfigurację funkcji ML z pliku.
        
        Returns:
            True, jeśli konfiguracja została załadowana, False w przeciwnym razie
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_features = json.load(f)
                    
                # Aktualizuj tylko istniejące funkcje
                for feature in self.features:
                    if feature in loaded_features:
                        self.features[feature].update(loaded_features[feature])
                        
                logger.info(f"Konfiguracja załadowana z {self.config_path}")
                return True
            else:
                logger.info(f"Plik konfiguracyjny {self.config_path} nie istnieje, używam domyślnej konfiguracji")
                self.save_config()  # Zapisz domyślną konfigurację
                return False
        except Exception as e:
            logger.error(f"Błąd podczas ładowania konfiguracji: {str(e)}")
            return False