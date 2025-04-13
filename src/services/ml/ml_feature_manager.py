import os
import json
import logging
from typing import Dict, List, Optional

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
        self.features = {
            "color_correction": False,
            "anomaly_detection": False,
            "sensor_optimization": False,
            "adaptive_calibration": False,
            "self_learning": False,
            "failure_prediction": False,
            "power_optimization": False
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
            self.features[feature_name] = True
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
            self.features[feature_name] = False
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
        return self.features.get(feature_name, False)
        
    def get_enabled_features(self) -> List[str]:
        """
        Zwraca listę włączonych funkcji ML.
        
        Returns:
            Lista włączonych funkcji
        """
        return [feature for feature, enabled in self.features.items() if enabled]
        
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
                        self.features[feature] = loaded_features[feature]
                        
                logger.info(f"Konfiguracja załadowana z {self.config_path}")
                return True
            else:
                logger.info(f"Plik konfiguracyjny {self.config_path} nie istnieje, używam domyślnej konfiguracji")
                self.save_config()  # Zapisz domyślną konfigurację
                return False
        except Exception as e:
            logger.error(f"Błąd podczas ładowania konfiguracji: {str(e)}")
            return False
            
    def reset_to_defaults(self) -> bool:
        """
        Resetuje konfigurację funkcji ML do wartości domyślnych.
        
        Returns:
            True, jeśli konfiguracja została zresetowana, False w przeciwnym razie
        """
        try:
            self.features = {
                "color_correction": False,
                "anomaly_detection": False,
                "sensor_optimization": False,
                "adaptive_calibration": False,
                "self_learning": False,
                "failure_prediction": False,
                "power_optimization": False
            }
            
            self.save_config()
            logger.info("Konfiguracja zresetowana do wartości domyślnych")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas resetowania konfiguracji: {str(e)}")
            return False
            
    def add_feature(self, feature_name: str, enabled: bool = False) -> bool:
        """
        Dodaje nową funkcję ML.
        
        Args:
            feature_name: Nazwa nowej funkcji
            enabled: Czy funkcja ma być włączona
            
        Returns:
            True, jeśli funkcja została dodana, False w przeciwnym razie
        """
        if feature_name not in self.features:
            self.features[feature_name] = enabled
            logger.info(f"Dodano nową funkcję: {feature_name}, włączona: {enabled}")
            self.save_config()
            return True
        else:
            logger.warning(f"Funkcja {feature_name} już istnieje")
            return False
            
    def remove_feature(self, feature_name: str) -> bool:
        """
        Usuwa funkcję ML.
        
        Args:
            feature_name: Nazwa funkcji do usunięcia
            
        Returns:
            True, jeśli funkcja została usunięta, False w przeciwnym razie
        """
        if feature_name in self.features:
            del self.features[feature_name]
            logger.info(f"Usunięto funkcję: {feature_name}")
            self.save_config()
            return True
        else:
            logger.warning(f"Próba usunięcia nieistniejącej funkcji: {feature_name}")
            return False