import numpy as np
from tensorflow import keras
from typing import Dict, Tuple, Optional
import os
import json
from datetime import datetime
from .data_manager import MLDataManager

class ColorCorrectionModel:
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicjalizacja modelu korekcji kolorów.
        
        Args:
            model_path: Ścieżka do zapisanego modelu (opcjonalna)
        """
        self.data_manager = MLDataManager()
        self.model = None
        self.version = "1.0.0"
        
        if model_path and os.path.exists(model_path):
            self.model = keras.models.load_model(model_path)
    
    def build_model(self) -> None:
        """Buduje model sieci neuronowej do korekcji kolorów."""
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(6,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.1),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1)  # Przewidywanie CCT
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
    
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
        if not self.model:
            self.build_model()
        
        # Pobierz dane treningowe
        X, y = self.data_manager.prepare_color_correction_data(hours)
        
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Brak danych treningowych")
        
        # Podziel dane na treningowe i walidacyjne
        X_train, X_val, y_train, y_val = self.data_manager.get_training_validation_split(
            X, y, test_size=validation_split
        )
        
        # Trening modelu
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            validation_data=(X_val, y_val),
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
    
    def predict(self, spectrum_data: np.ndarray) -> float:
        """
        Przewiduje temperaturę barwową na podstawie spektrum.
        
        Args:
            spectrum_data: Dane spektralne (6 kanałów)
            
        Returns:
            Przewidywana temperatura barwowa (CCT)
        """
        if not self.model:
            raise ValueError("Model nie został wytrenowany")
        
        # Normalizacja danych wejściowych
        spectrum_data = self.data_manager.scaler.transform(spectrum_data.reshape(1, -1))
        
        # Przewidywanie
        prediction = self.model.predict(spectrum_data)
        
        return float(prediction[0])
    
    def save(self, save_dir: str) -> str:
        """
        Zapisuje model i jego parametry.
        
        Args:
            save_dir: Katalog do zapisu
            
        Returns:
            Ścieżka do zapisanego modelu
        """
        if not self.model:
            raise ValueError("Brak modelu do zapisu")
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs(save_dir, exist_ok=True)
        
        # Generuj nazwę pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"color_correction_model_{timestamp}"
        model_path = os.path.join(save_dir, model_name)
        
        # Zapisz model
        self.model.save(model_path)
        
        # Zapisz informacje o modelu w bazie danych
        parameters = {
            'architecture': self.model.to_json(),
            'input_shape': self.model.input_shape,
            'output_shape': self.model.output_shape
        }
        
        metrics = self.evaluate()
        
        self.data_manager.save_model_results(
            model_name="color_correction",
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
        if not self.model:
            raise ValueError("Model nie został wytrenowany")
        
        # Pobierz dane do ewaluacji
        X, y = self.data_manager.prepare_color_correction_data(hours)
        
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Brak danych do ewaluacji")
        
        # Ewaluacja
        loss, mae = self.model.evaluate(X, y, verbose=0)
        
        return {
            'loss': float(loss),
            'mae': float(mae)
        }