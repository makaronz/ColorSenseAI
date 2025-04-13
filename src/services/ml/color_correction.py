import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
from typing import Dict, Optional, List, Tuple
import os
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras import regularizers

class ColorCorrectionModel:
    def __init__(self, model_path: str = "models/color_correction.h5", quantized_model_path: str = "models/color_correction_quantized.tflite"):
        self.model_path = model_path
        self.quantized_model_path = quantized_model_path
        self.model: Optional[Sequential] = None
        self.quantized_interpreter: Optional[tf.lite.Interpreter] = None
        self._load_model()
        
    def _build_model(self):
        """
        Buduje zoptymalizowany model z regularyzacją L2 i mniejszą liczbą parametrów.
        """
        self.model = Sequential([
            LSTM(48, return_sequences=True, input_shape=(None, 9),
                 kernel_regularizer=regularizers.l2(0.001),
                 recurrent_regularizer=regularizers.l2(0.001),
                 dropout=0.1, recurrent_dropout=0.1),
            LSTM(24, kernel_regularizer=regularizers.l2(0.001),
                 recurrent_regularizer=regularizers.l2(0.001),
                 dropout=0.1, recurrent_dropout=0.1),
            Dense(12, activation='relu', kernel_regularizer=regularizers.l2(0.001)),
            Dense(3)
        ])
        self.model.compile(optimizer='adam', loss='mse')
        def _load_model(self):
            """
            Ładuje model z pliku lub tworzy nowy, jeśli plik nie istnieje.
            Próbuje również załadować zoptymalizowany model TFLite.
            """
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
            else:
                self._build_model()
                
            # Próba załadowania zoptymalizowanego modelu TFLite
            if os.path.exists(self.quantized_model_path):
                self.quantized_interpreter = tf.lite.Interpreter(model_path=self.quantized_model_path)
                self.quantized_interpreter.allocate_tensors()
                
        def quantize_model(self):
            """
            Kwantyzuje model do formatu TFLite z optymalizacją.
            """
            if self.model is None:
                return
                
            # Konwersja do TFLite z kwantyzacją
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            
            # Włącz optymalizacje
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            
            # Kwantyzacja do INT8
            converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tf.int8
            converter.inference_output_type = tf.int8
            
            # Generowanie danych kalibracyjnych
            def representative_dataset():
                for _ in range(100):
                    # Generuj losowe dane wejściowe w zakresie wartości czujników
                    yield [np.random.rand(1, 1, 9).astype(np.float32) * 2 - 1]
                    
            converter.representative_dataset = representative_dataset
            
            # Konwersja modelu
            tflite_model = converter.convert()
            
            # Zapisz model
            with open(self.quantized_model_path, 'wb') as f:
                f.write(tflite_model)
                
            # Załaduj zoptymalizowany model
            self.quantized_interpreter = tf.lite.Interpreter(model_content=tflite_model)
            self.quantized_interpreter.allocate_tensors()
            
        def prune_model(self, sparsity: float = 0.5):
            """
            Przycina model, usuwając wagi o najmniejszych wartościach bezwzględnych.
            
            Args:
                sparsity: Docelowa rzadkość modelu (0.0 - 1.0)
            """
            if self.model is None:
                return
                
            # Pobierz wagi modelu
            weights = self.model.get_weights()
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
            self.model.set_weights(pruned_weights)
            
            # Zapisz przycięty model
            self.save_model()
            def save_model(self):
                """
                Zapisuje model do pliku.
                """
                if self.model:
                    self.model.save(self.model_path)
                    # Zaktualizuj również zoptymalizowany model
                    self.quantize_model()
                    
            
    def predict_correction(self, sensor_data: np.ndarray, env_data: np.ndarray) -> Dict:
        """
        Przewiduje korekcję kolorów na podstawie danych z czujników i danych środowiskowych.
        Używa zoptymalizowanego modelu TFLite, jeśli jest dostępny.
        """
        if not self.model and not self.quantized_interpreter:
            return {
                'correction': np.zeros(3),
                'confidence': 0.0
            }
            
        combined_data = np.concatenate([sensor_data, env_data])
        
        # Użyj zoptymalizowanego modelu TFLite, jeśli jest dostępny
        if self.quantized_interpreter:
            # Pobierz informacje o tensorach wejściowych i wyjściowych
            input_details = self.quantized_interpreter.get_input_details()
            output_details = self.quantized_interpreter.get_output_details()
            
            # Przygotuj dane wejściowe
            input_data = combined_data.reshape(1, -1, 9).astype(np.float32)
            
            # Ustaw dane wejściowe
            self.quantized_interpreter.set_tensor(input_details[0]['index'], input_data)
            
            # Wykonaj wnioskowanie
            self.quantized_interpreter.invoke()
            
            # Pobierz wynik
            prediction = self.quantized_interpreter.get_tensor(output_details[0]['index'])
        else:
            # Użyj oryginalnego modelu Keras
            prediction = self.model.predict(combined_data.reshape(1, -1, 9))
        
        return {
            'correction': prediction[0],
            'confidence': self._calculate_confidence(prediction)
        }
        
    def _calculate_confidence(self, prediction: np.ndarray) -> float:
        """
        Oblicza pewność predykcji na podstawie wariancji wyjścia modelu.
        """
        # Implementacja obliczania pewności predykcji
        # Oblicz normę predykcji
        norm = np.linalg.norm(prediction)
        
        # Jeśli norma jest bardzo mała, pewność jest niska
        if norm < 0.01:
            return 0.1
            
        # Oblicz pewność na podstawie normy (prosta heurystyka)
        # Wartości w zakresie [0.5, 1.0]
        confidence = 0.5 + min(0.5, norm / 10.0)
        
        return float(confidence)
        
    def train(self, training_data: np.ndarray, labels: np.ndarray, validation_split: float = 0.2):
        """
        Trenuje model na podstawie danych treningowych i etykiet.
        Używa wczesnego zatrzymywania i redukcji współczynnika uczenia.
        
        Args:
            training_data: Dane treningowe
            labels: Etykiety
            validation_split: Część danych używana do walidacji
        """
        if self.model:
            # Przygotuj callbacki dla lepszego treningu
            callbacks = [
                # Wczesne zatrzymywanie, jeśli model przestaje się poprawiać
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                # Redukcja współczynnika uczenia, gdy plateau
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.0001
                )
            ]
            
            # Trenuj model
            self.model.fit(
                training_data,
                labels,
                epochs=50,  # Więcej epok, ale z wczesnym zatrzymywaniem
                batch_size=32,
                validation_split=validation_split,
                callbacks=callbacks
            )
            
            # Przytnij model
            self.prune_model(sparsity=0.3)
            
            # Zapisz i zoptymalizuj model
            self.save_model()
            
    def optimize_hyperparameters(self, training_data: np.ndarray, labels: np.ndarray, validation_split: float = 0.2):
        """
        Optymalizuje hiperparametry modelu.
        
        Args:
            training_data: Dane treningowe
            labels: Etykiety
            validation_split: Część danych używana do walidacji
        """
        # Definicja przestrzeni hiperparametrów
        hyperparameters = {
            'lstm1_units': [32, 48, 64],
            'lstm2_units': [16, 24, 32],
            'dense_units': [8, 12, 16],
            'dropout_rate': [0.0, 0.1, 0.2],
            'l2_reg': [0.0001, 0.001, 0.01]
        }
        
        best_val_loss = float('inf')
        best_params = {}
        
        # Podziel dane na zbiór treningowy i walidacyjny
        val_size = int(len(training_data) * validation_split)
        train_x, val_x = training_data[:-val_size], training_data[-val_size:]
        train_y, val_y = labels[:-val_size], labels[-val_size:]
        
        # Proste przeszukiwanie siatki
        for lstm1 in hyperparameters['lstm1_units']:
            for lstm2 in hyperparameters['lstm2_units']:
                for dense in hyperparameters['dense_units']:
                    for dropout in hyperparameters['dropout_rate']:
                        for l2 in hyperparameters['l2_reg']:
                            # Utwórz model z bieżącymi hiperparametrami
                            model = Sequential([
                                LSTM(lstm1, return_sequences=True, input_shape=(None, 9),
                                     kernel_regularizer=regularizers.l2(l2),
                                     recurrent_regularizer=regularizers.l2(l2),
                                     dropout=dropout, recurrent_dropout=dropout),
                                LSTM(lstm2, kernel_regularizer=regularizers.l2(l2),
                                     recurrent_regularizer=regularizers.l2(l2),
                                     dropout=dropout, recurrent_dropout=dropout),
                                Dense(dense, activation='relu', kernel_regularizer=regularizers.l2(l2)),
                                Dense(3)
                            ])
                            
                            model.compile(optimizer='adam', loss='mse')
                            
                            # Trenuj model
                            model.fit(
                                train_x,
                                train_y,
                                epochs=20,
                                batch_size=32,
                                verbose=0
                            )
                            
                            # Oceń model
                            val_loss = model.evaluate(val_x, val_y, verbose=0)
                            
                            # Aktualizuj najlepsze parametry
                            if val_loss < best_val_loss:
                                best_val_loss = val_loss
                                best_params = {
                                    'lstm1_units': lstm1,
                                    'lstm2_units': lstm2,
                                    'dense_units': dense,
                                    'dropout_rate': dropout,
                                    'l2_reg': l2
                                }
        
        # Utwórz model z najlepszymi parametrami
        self.model = Sequential([
            LSTM(best_params['lstm1_units'], return_sequences=True, input_shape=(None, 9),
                 kernel_regularizer=regularizers.l2(best_params['l2_reg']),
                 recurrent_regularizer=regularizers.l2(best_params['l2_reg']),
                 dropout=best_params['dropout_rate'],
                 recurrent_dropout=best_params['dropout_rate']),
            LSTM(best_params['lstm2_units'],
                 kernel_regularizer=regularizers.l2(best_params['l2_reg']),
                 recurrent_regularizer=regularizers.l2(best_params['l2_reg']),
                 dropout=best_params['dropout_rate'],
                 recurrent_dropout=best_params['dropout_rate']),
            Dense(best_params['dense_units'], activation='relu',
                 kernel_regularizer=regularizers.l2(best_params['l2_reg'])),
            Dense(3)
        ])
        
        self.model.compile(optimizer='adam', loss='mse')
        
        # Trenuj model z najlepszymi parametrami
        self.train(training_data, labels, validation_split)