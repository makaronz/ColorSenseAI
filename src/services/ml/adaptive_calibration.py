import numpy as np
from tensorflow import keras
from typing import Dict, Optional
import os
from datetime import datetime
from .data_manager import MLDataManager

class AdaptiveCalibrationSystem:
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicjalizacja systemu kalibracji adaptacyjnej.
        
        Args:
            model_path: Ścieżka do zapisanego modelu (opcjonalna)
        """
        self.data_manager = MLDataManager()
        self.calibration_model = None
        self.version = "1.0.0"
        self.calibration_history = []
        
        if model_path and os.path.exists(model_path):
            self.calibration_model = keras.models.load_model(model_path)
    
    def build_model(self) -> None:
        """Buduje model sieci neuronowej do kalibracji adaptacyjnej."""
        # Model przyjmuje dane z czujników i temperaturę
        input_layer = keras.layers.Input(shape=(14,))  # 13 pomiarów + temperatura
        
        # Główna ścieżka dla danych z czujników
        x = keras.layers.Dense(64, activation='relu')(input_layer)
        x = keras.layers.Dropout(0.2)(x)
        
        # Ścieżka dla historycznych danych (dryf)
        x = keras.layers.Dense(32, activation='relu')(x)
        x = keras.layers.Dropout(0.1)(x)
        
        # Wspólne warstwy
        x = keras.layers.Dense(16, activation='relu')(x)
        outputs = keras.layers.Dense(13)(x)  # Korekcja dla każdego pomiaru
        
        self.calibration_model = keras.Model(input_layer, outputs)
        self.calibration_model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
    
    def train(self, hours: int = 24, epochs: int = 100, 
              validation_split: float = 0.2) -> Dict[str, float]:
        """
        Trenuje model na danych historycznych.
        
        Args:
            hours: Liczba godzin danych do treningu
            epochs: Liczba epok treningu
            validation_split: Proporcja danych walidacyjnych
            
        Returns:
            Metryki treningu
        """
        if not self.calibration_model:
            self.build_model()
        
        # Pobierz dane kalibracyjne dla wszystkich czujników
        calibration_data = self.data_manager.prepare_calibration_data(hours)
        
        if not calibration_data:
            raise ValueError("Brak danych treningowych")
        
        # Przygotuj dane treningowe
        X = np.concatenate([
            calibration_data['AS7262'],
            calibration_data['TSL2591'],
            calibration_data['SEN0611']
        ], axis=1)
        
        # Podziel dane na treningowe i walidacyjne
        X_train, X_val = self.data_manager.get_training_validation_split(
            X, X, test_size=validation_split
        )[:2]  # Bierzemy tylko X_train i X_val
        
        # Trening modelu
        history = self.calibration_model.fit(
            X_train, X_train,  # Model uczy się korygować odczyty
            epochs=epochs,
            validation_data=(X_val, X_val),
            verbose=1
        )
        
        # Oblicz metryki
        metrics = {
            'train_loss': float(history.history['loss'][-1]),
            'train_mae': float(history.history['mae'][-1]),
            'val_loss': float(history.history['val_loss'][-1]),
            'val_mae': float(history.history['val_mae'][-1])
        }
        
        return metrics
    
    def calibrate(self, sensor_data: np.ndarray) -> Dict:
        """
        Kalibruje dane z czujników.
        
        Args:
            sensor_data: Dane z czujników do kalibracji
            
        Returns:
            Słownik z skalibrowanymi danymi i pewnością
        """
        if not self.calibration_model:
            raise ValueError("Model nie został wytrenowany")
        
        # Normalizacja danych wejściowych
        sensor_data = self.data_manager.scaler.transform(sensor_data.reshape(1, -1))
        
        # Kalibracja
        calibrated_data = self.calibration_model.predict(sensor_data, verbose=0)
        
        # Oblicz pewność kalibracji
        correction = np.abs(calibrated_data - sensor_data)
        confidence = 1.0 / (1.0 + np.mean(correction))
        
        # Zapisz kalibrację w historii
        self.calibration_history.append({
            'timestamp': datetime.now(),
            'original_data': sensor_data[0].tolist(),
            'calibrated_data': calibrated_data[0].tolist(),
            'confidence': float(confidence)
        })
        
        # Ogranicz historię do ostatnich 1000 kalibracji
        if len(self.calibration_history) > 1000:
            self.calibration_history = self.calibration_history[-1000:]
        
        return {
            'calibrated_data': calibrated_data[0].tolist(),
            'confidence': float(confidence),
            'correction': correction[0].tolist()
        }
    
    def save(self, save_dir: str) -> str:
        """
        Zapisuje model i jego parametry.
        
        Args:
            save_dir: Katalog do zapisu
            
        Returns:
            Ścieżka do zapisanego modelu
        """
        if not self.calibration_model:
            raise ValueError("Brak modelu do zapisu")
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs(save_dir, exist_ok=True)
        
        # Generuj nazwę pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"adaptive_calibration_model_{timestamp}"
        model_path = os.path.join(save_dir, model_name)
        
        # Zapisz model
        self.calibration_model.save(model_path)
        
        # Zapisz informacje o modelu w bazie danych
        parameters = {
            'architecture': self.calibration_model.to_json(),
            'input_shape': self.calibration_model.input_shape,
            'output_shape': self.calibration_model.output_shape,
            'history_size': len(self.calibration_history)
        }
        
        metrics = self.evaluate()
        
        self.data_manager.save_model_results(
            model_name="adaptive_calibration",
            version=self.version,
            metrics=metrics,
            model_path=model_path,
            parameters=parameters
        )
        
        return model_path
    
    def evaluate(self, hours: int = 24) -> Dict[str, float]:
        """
        Ewaluacja modelu na najnowszych danych.
        
        Args:
            hours: Liczba godzin danych do ewaluacji
            
        Returns:
            Metryki ewaluacji
        """
        if not self.calibration_model:
            raise ValueError("Model nie został wytrenowany")
        
        # Pobierz dane do ewaluacji
        calibration_data = self.data_manager.prepare_calibration_data(hours)
        
        if not calibration_data:
            raise ValueError("Brak danych do ewaluacji")
        
        # Przygotuj dane do ewaluacji
        X = np.concatenate([
            calibration_data['AS7262'],
            calibration_data['TSL2591'],
            calibration_data['SEN0611']
        ], axis=1)
        
        # Ewaluacja modelu
        loss, mae = self.calibration_model.evaluate(X, X, verbose=0)
        
        # Oblicz dodatkowe metryki
        predictions = self.calibration_model.predict(X, verbose=0)
        corrections = np.abs(predictions - X)
        
        return {
            'loss': float(loss),
            'mae': float(mae),
            'mean_correction': float(np.mean(corrections)),
            'max_correction': float(np.max(corrections)),
            'min_correction': float(np.min(corrections)),
            'std_correction': float(np.std(corrections))
        } 