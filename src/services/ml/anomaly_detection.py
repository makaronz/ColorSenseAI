import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from tensorflow import keras
from typing import Dict, Optional
import os
from datetime import datetime
from .data_manager import MLDataManager

class AnomalyDetectionSystem:
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicjalizacja systemu wykrywania anomalii.
        
        Args:
            model_path: Ścieżka do zapisanego modelu (opcjonalna)
        """
        self.data_manager = MLDataManager()
        self.autoencoder = None
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.one_class_svm = OneClassSVM(nu=0.1, kernel='rbf', gamma='scale')
        self.version = "1.0.0"
        
        if model_path and os.path.exists(model_path):
            self.autoencoder = keras.models.load_model(model_path)
    
    def build_model(self) -> None:
        """Buduje model autoenkodera do wykrywania anomalii."""
        input_dim = 13  # Liczba cech wejściowych
        encoding_dim = 6
        
        # Encoder
        input_layer = keras.layers.Input(shape=(input_dim,))
        x = keras.layers.Dense(10, activation='relu')(input_layer)
        x = keras.layers.Dropout(0.2)(x)
        encoded = keras.layers.Dense(encoding_dim, activation='relu')(x)
        
        # Decoder
        x = keras.layers.Dense(10, activation='relu')(encoded)
        x = keras.layers.Dropout(0.2)(x)
        decoded = keras.layers.Dense(input_dim, activation='sigmoid')(x)
        
        # Autoencoder
        self.autoencoder = keras.Model(input_layer, decoded)
        self.autoencoder.compile(
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
        if not self.autoencoder:
            self.build_model()
        
        # Pobierz dane treningowe
        X = self.data_manager.prepare_anomaly_detection_data(hours)
        
        if len(X) == 0:
            raise ValueError("Brak danych treningowych")
        
        # Podziel dane na treningowe i walidacyjne
        X_train, X_val = self.data_manager.get_training_validation_split(
            X, X, test_size=validation_split
        )[:2]  # Bierzemy tylko X_train i X_val
        
        # Trening autoenkodera
        history = self.autoencoder.fit(
            X_train, X_train,  # Autoenkoder uczy się rekonstruować dane wejściowe
            epochs=epochs,
            validation_data=(X_val, X_val),
            verbose=1
        )
        
        # Trening innych modeli
        self.isolation_forest.fit(X_train)
        self.one_class_svm.fit(X_train)
        
        # Oblicz metryki
        metrics = {
            'train_loss': float(history.history['loss'][-1]),
            'train_mae': float(history.history['mae'][-1]),
            'val_loss': float(history.history['val_loss'][-1]),
            'val_mae': float(history.history['val_mae'][-1])
        }
        
        return metrics
    
    def detect_anomalies(self, sensor_data: np.ndarray) -> Dict:
        """
        Wykrywa anomalie w danych z czujników.
        
        Args:
            sensor_data: Dane z czujników do analizy
            
        Returns:
            Słownik z wynikami detekcji anomalii
        """
        if not self.autoencoder:
            raise ValueError("Model nie został wytrenowany")
        
        # Normalizacja danych wejściowych
        sensor_data = self.data_manager.scaler.transform(sensor_data.reshape(1, -1))
        
        # Rekonstrukcja przez autoenkoder
        reconstructed = self.autoencoder.predict(sensor_data)
        reconstruction_error = np.mean(np.square(sensor_data - reconstructed))
        
        # Wykrywanie anomalii przez inne modele
        if_score = self.isolation_forest.score_samples(sensor_data)[0]
        svm_prediction = self.one_class_svm.predict(sensor_data)[0]
        
        # Łączenie wyników
        is_anomaly = (reconstruction_error > 0.3 or 
                     if_score < -0.3 or 
                     svm_prediction == -1)
        
        confidence = (1.0 - min(1.0, reconstruction_error * 10) +
                     1.0 - (if_score + 0.5) / 0.5) / 2.0
        
        return {
            'is_anomaly': bool(is_anomaly),
            'confidence': float(confidence),
            'reconstruction_error': float(reconstruction_error),
            'isolation_forest_score': float(if_score),
            'error_type': self._classify_error_type(reconstruction_error, if_score)
        }
    
    def _classify_error_type(self, reconstruction_error: float, if_score: float) -> str:
        """
        Klasyfikuje typ błędu na podstawie charakterystyki anomalii.
        """
        if reconstruction_error > 0.5:
            return 'sensor_failure'
        elif if_score < -0.4:
            return 'outlier'
        elif reconstruction_error > 0.2:
            return 'drift'
        else:
            return 'unknown'
    
    def save(self, save_dir: str) -> str:
        """
        Zapisuje model i jego parametry.
        
        Args:
            save_dir: Katalog do zapisu
            
        Returns:
            Ścieżka do zapisanego modelu
        """
        if not self.autoencoder:
            raise ValueError("Brak modelu do zapisu")
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs(save_dir, exist_ok=True)
        
        # Generuj nazwę pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"anomaly_detection_model_{timestamp}"
        model_path = os.path.join(save_dir, model_name)
        
        # Zapisz model
        self.autoencoder.save(model_path)
        
        # Zapisz informacje o modelu w bazie danych
        parameters = {
            'architecture': self.autoencoder.to_json(),
            'input_shape': self.autoencoder.input_shape,
            'output_shape': self.autoencoder.output_shape,
            'isolation_forest_params': self.isolation_forest.get_params(),
            'one_class_svm_params': self.one_class_svm.get_params()
        }
        
        metrics = self.evaluate()
        
        self.data_manager.save_model_results(
            model_name="anomaly_detection",
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
        if not self.autoencoder:
            raise ValueError("Model nie został wytrenowany")
        
        # Pobierz dane do ewaluacji
        X = self.data_manager.prepare_anomaly_detection_data(hours)
        
        if len(X) == 0:
            raise ValueError("Brak danych do ewaluacji")
        
        # Ewaluacja autoenkodera
        loss, mae = self.autoencoder.evaluate(X, X, verbose=0)
        
        # Ewaluacja innych modeli
        if_scores = self.isolation_forest.score_samples(X)
        svm_predictions = self.one_class_svm.predict(X)
        
        return {
            'autoencoder_loss': float(loss),
            'autoencoder_mae': float(mae),
            'isolation_forest_mean_score': float(np.mean(if_scores)),
            'one_class_svm_anomaly_ratio': float(np.mean(svm_predictions == -1))
        }