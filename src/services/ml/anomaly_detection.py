import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from tensorflow.keras.models import Model, Sequential, load_model
from tensorflow.keras.layers import Dense, Input, Dropout
from typing import Dict, List, Optional, Tuple
import os
import tensorflow as tf
from tensorflow.keras import regularizers
from sklearn.model_selection import GridSearchCV
from joblib import dump, load

class AnomalyDetectionSystem:
    def __init__(self,
                 model_path: str = "models/anomaly_detection.h5",
                 quantized_model_path: str = "models/anomaly_detection_quantized.tflite",
                 isolation_forest_path: str = "models/isolation_forest.joblib",
                 one_class_svm_path: str = "models/one_class_svm.joblib"):
        self.model_path = model_path
        self.quantized_model_path = quantized_model_path
        self.isolation_forest_path = isolation_forest_path
        self.one_class_svm_path = one_class_svm_path
        
        self.autoencoder: Optional[Model] = None
        self.quantized_interpreter: Optional[tf.lite.Interpreter] = None
        self.isolation_forest = IsolationForest(contamination=0.1, n_estimators=100, random_state=42)
        self.one_class_svm = OneClassSVM(nu=0.1, kernel='rbf', gamma='scale')
        
        self._load_models()
        
    def _build_autoencoder(self):
        """
        Buduje zoptymalizowany autoenkoder z regularyzacją i dropout.
        """
        input_dim = 9  # Liczba cech wejściowych
        encoding_dim = 3
        
        # Encoder
        input_layer = Input(shape=(input_dim,))
        x = Dropout(0.1)(input_layer)
        x = Dense(6, activation='relu',
                 kernel_regularizer=regularizers.l2(0.001))(x)
        encoder = Dense(encoding_dim, activation='relu',
                       kernel_regularizer=regularizers.l2(0.001))(x)
        
        # Decoder
        x = Dense(6, activation='relu',
                 kernel_regularizer=regularizers.l2(0.001))(encoder)
        x = Dropout(0.1)(x)
        decoder = Dense(input_dim, activation='sigmoid',
                       kernel_regularizer=regularizers.l2(0.001))(x)
        
        # Autoencoder
        self.autoencoder = Model(input_layer, decoder)
        self.autoencoder.compile(optimizer='adam', loss='mse')
        
    def _load_models(self):
        """
        Ładuje modele z plików lub tworzy nowe, jeśli pliki nie istnieją.
        """
        # Ładowanie autoenkodera
        if os.path.exists(self.model_path):
            self.autoencoder = load_model(self.model_path)
        else:
            self._build_autoencoder()
            
        # Ładowanie zoptymalizowanego modelu TFLite
        if os.path.exists(self.quantized_model_path):
            self.quantized_interpreter = tf.lite.Interpreter(model_path=self.quantized_model_path)
            self.quantized_interpreter.allocate_tensors()
            
        # Ładowanie modeli sklearn
        if os.path.exists(self.isolation_forest_path):
            self.isolation_forest = load(self.isolation_forest_path)
            
        if os.path.exists(self.one_class_svm_path):
            self.one_class_svm = load(self.one_class_svm_path)
            
    def save_models(self):
        """
        Zapisuje wszystkie modele do plików.
        """
        if self.autoencoder:
            self.autoencoder.save(self.model_path)
            self.quantize_model()
            
        # Zapisz modele sklearn
        dump(self.isolation_forest, self.isolation_forest_path)
        dump(self.one_class_svm, self.one_class_svm_path)
            
    def quantize_model(self):
        """
        Kwantyzuje autoenkoder do formatu TFLite z optymalizacją.
        """
        if self.autoencoder is None:
            return
            
        # Konwersja do TFLite z kwantyzacją
        converter = tf.lite.TFLiteConverter.from_keras_model(self.autoencoder)
        
        # Włącz optymalizacje
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # Generowanie danych kalibracyjnych
        def representative_dataset():
            for _ in range(100):
                # Generuj losowe dane wejściowe w zakresie wartości czujników
                yield [np.random.rand(1, 9).astype(np.float32)]
                
        converter.representative_dataset = representative_dataset
        
        # Konwersja modelu
        tflite_model = converter.convert()
        
        # Zapisz model
        with open(self.quantized_model_path, 'wb') as f:
            f.write(tflite_model)
            
        # Załaduj zoptymalizowany model
        self.quantized_interpreter = tf.lite.Interpreter(model_content=tflite_model)
        self.quantized_interpreter.allocate_tensors()
            
    def detect_anomalies(self, sensor_readings: np.ndarray) -> Dict:
        """
        Wykrywa anomalie w odczytach czujników.
        Używa zoptymalizowanego modelu TFLite, jeśli jest dostępny.
        """
        if not self.autoencoder and not self.quantized_interpreter:
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'error_type': 'unknown'
            }
            
        # Przygotuj dane wejściowe
        input_data = sensor_readings.reshape(1, -1) if len(sensor_readings.shape) == 1 else sensor_readings
        
        # Rekonstrukcja danych
        if self.quantized_interpreter:
            # Użyj zoptymalizowanego modelu TFLite
            input_details = self.quantized_interpreter.get_input_details()
            output_details = self.quantized_interpreter.get_output_details()
            
            self.quantized_interpreter.set_tensor(input_details[0]['index'], input_data.astype(np.float32))
            self.quantized_interpreter.invoke()
            
            reconstructed = self.quantized_interpreter.get_tensor(output_details[0]['index'])
        else:
            # Użyj oryginalnego modelu Keras
            reconstructed = self.autoencoder.predict(input_data)
            
        reconstruction_error = np.mean(np.square(input_data - reconstructed))
        
        # Wykrywanie anomalii
        anomaly_score = self.isolation_forest.score_samples(input_data)
        is_anomaly = self.one_class_svm.predict(input_data) == -1
        
        # Oblicz pewność na podstawie wszystkich modeli
        autoencoder_confidence = 1.0 - min(1.0, reconstruction_error * 10)
        isolation_forest_confidence = 1.0 - (anomaly_score + 0.5) / 0.5  # Normalizacja do [0, 1]
        
        # Połącz wyniki z różnych modeli
        combined_is_anomaly = bool(is_anomaly[0]) or reconstruction_error > 0.3 or anomaly_score < -0.3
        combined_confidence = (autoencoder_confidence + isolation_forest_confidence) / 2.0
        
        return {
            'is_anomaly': combined_is_anomaly,
            'confidence': float(combined_confidence),
            'reconstruction_error': float(reconstruction_error),
            'anomaly_score': float(anomaly_score[0]),
            'error_type': self._classify_error_type(input_data, reconstruction_error, anomaly_score)
        }
        
    def _classify_error_type(self, data: np.ndarray, error: float, anomaly_score: np.ndarray) -> str:
        """
        Klasyfikuje typ błędu na podstawie charakterystyki anomalii.
        """
        if error > 0.5:
            return 'sensor_failure'  # Duży błąd rekonstrukcji wskazuje na awarię czujnika
        elif anomaly_score[0] < -0.4:
            return 'outlier'  # Niski wynik Isolation Forest wskazuje na wartość odstającą
        elif error > 0.2:
            return 'drift'  # Umiarkowany błąd rekonstrukcji może wskazywać na dryf czujnika
        else:
            return 'unknown'
        
    def optimize_hyperparameters(self, normal_data: np.ndarray, validation_data: np.ndarray):
        """
        Optymalizuje hiperparametry modeli wykrywania anomalii.
        
        Args:
            normal_data: Dane normalne do treningu
            validation_data: Dane walidacyjne (zawierające anomalie)
        """
        # Optymalizacja Isolation Forest
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_samples': ['auto', 0.5, 0.8],
            'contamination': [0.05, 0.1, 0.2],
            'max_features': [0.5, 0.8, 1.0]
        }
        
        grid_search = GridSearchCV(
            IsolationForest(random_state=42),
            param_grid,
            cv=3,
            scoring='neg_mean_squared_error'
        )
        
        grid_search.fit(normal_data)
        self.isolation_forest = grid_search.best_estimator_
        
        # Optymalizacja One-Class SVM
        param_grid = {
            'nu': [0.05, 0.1, 0.2],
            'kernel': ['rbf', 'sigmoid'],
            'gamma': ['scale', 'auto', 0.1, 0.01]
        }
        
        grid_search = GridSearchCV(
            OneClassSVM(),
            param_grid,
            cv=3,
            scoring='neg_mean_squared_error'
        )
        
        grid_search.fit(normal_data)
        self.one_class_svm = grid_search.best_estimator_
        
        # Zapisz zoptymalizowane modele
        self.save_models()
        
    def train(self, normal_data: np.ndarray, epochs: int = 50, batch_size: int = 32, validation_split: float = 0.2):
        """
        Trenuje wszystkie modele wykrywania anomalii.
        
        Args:
            normal_data: Dane normalne do treningu
            epochs: Liczba epok treningu autoenkodera
            batch_size: Rozmiar batcha
            validation_split: Część danych używana do walidacji
        """
        if self.autoencoder:
            # Trenowanie autoenkodera z wczesnym zatrzymywaniem
            from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
            
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.0001
                )
            ]
            
            # Trenowanie autoenkodera
            self.autoencoder.fit(
                normal_data,
                normal_data,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=callbacks
            )
            
            # Przycinanie modelu
            self._prune_model(sparsity=0.3)
            
            # Trenowanie modeli wykrywania anomalii
            self.isolation_forest.fit(normal_data)
            self.one_class_svm.fit(normal_data)
            
            # Zapisz wszystkie modele
            self.save_models()
            
    def _prune_model(self, sparsity: float = 0.5):
        """
        Przycina model autoenkodera, usuwając wagi o najmniejszych wartościach bezwzględnych.
        
        Args:
            sparsity: Docelowa rzadkość modelu (0.0 - 1.0)
        """
        if self.autoencoder is None:
            return
            
        # Pobierz wagi modelu
        weights = self.autoencoder.get_weights()
        pruned_weights = []
        
        for w in weights:
            # Spłaszcz wagi
            flat_weights = w.flatten()
            # Oblicz próg dla sparsity
            threshold = np.percentile(np.abs(flat_weights), sparsity * 100)
            # Utwórz maskę dla wag poniżej progu
            mask = np.abs(w) > threshold
            # Zastosuj maskę
            pruned_w = w * mask
            pruned_weights.append(pruned_w)
            
        # Ustaw przycięte wagi
        self.autoencoder.set_weights(pruned_weights)