from typing import Dict, Optional
import json
import os

class MLFeatureManager:
    def __init__(self, config_path: str = "config/ml_features.json"):
        self.config_path = config_path
        self.features: Dict[str, bool] = {
            "color_correction": False,
            "anomaly_detection": False,
            "sensor_optimization": False,
            "adaptive_calibration": False,
            "self_learning": False,
            "failure_prediction": False,
            "power_optimization": False
        }
        self._load_config()
        
    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.features.update(json.load(f))
                
    def _save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.features, f, indent=4)
            
    def enable_feature(self, feature_name: str):
        if feature_name in self.features:
            self.features[feature_name] = True
            self._save_config()
            
    def disable_feature(self, feature_name: str):
        if feature_name in self.features:
            self.features[feature_name] = False
            self._save_config()
            
    def is_feature_enabled(self, feature_name: str) -> bool:
        return self.features.get(feature_name, False) 