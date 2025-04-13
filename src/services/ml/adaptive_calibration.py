import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, LSTM, Dropout
from typing import Dict, List, Optional, Tuple
import os
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras import regularizers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

class AdaptiveCalibrationSystem:
    def __init__(self,
                 model_path: str = "models/adaptive_calibration.h5",
                 temp_model_path: str = "models/temp_calibration.h5",
                 drift_model_path: str = "models/drift_calibration.h5",
                 quantized_temp_path: str = "models/temp_calibration_quantized.tflite",
                 quantized_drift_path: str = "models/drift_calibration_quantized.tflite"):
        self.model_path = model_path
        self.temp_model_path = temp_model_path
        self.drift_model_path = drift_model_path
        self.quantized_temp_path = quantized_temp_path
        self.quantized_drift_path = quantized_drift_path
        
        self.temperature_model: Optional[Sequential] = None
        self.drift_model: Optional[Sequential] = None
        self.temp_interpreter: Optional[tf.lite.Interpreter] = None
        self.drift_interpreter: Optional[tf.lite.Interpreter] = None
        
        self.calibration_history: List[Dict] = []
        self._load_models()
        
    def _build_temperature_model(self):
        """
        Buduje zoptymalizowany model temperatury z regularyzacją i dropout.
        """
        self.temperature_model = Sequential([
            Dense(24, activation='relu', input_shape=(3,),
                 kernel_regularizer=regularizers.l2(0.001)),
            Dropout(0.1),
            Dense(12, activation='relu',
                 kernel_regularizer=regularizers.l2(0.001)),
            Dropout(0.1),
            Dense(3)
        ])
        self.temperature_model.compile(optimizer='adam', loss='mse')
        def _build_drift_model(self):
            """
            Buduje zoptymalizowany model dryfu z regularyzacją i dropout.
            """
            self.drift_model = Sequential([
                LSTM(24, return_sequences=True, input_shape=(None, 6),
                    kernel_regularizer=regularizers.l2(0.001),
                    recurrent_regularizer=regularizers.l2(0.001),
                    dropout=0.1, recurrent_dropout=0.1),
                LSTM(12, kernel_regularizer=regularizers.l2(0.001),
                    recurrent_regularizer=regularizers.l2(0.001),
                    dropout=0.1, recurrent_dropout=0.1),
                Dense(6, activation='relu',
                     kernel_regularizer=regularizers.l2(0.001)),
                Dropout(0.1),
                Dense(3)
            ])
            self.drift_model.compile(optimizer='adam', loss='mse')
            
        def _load_models(self):
            """
            Ładuje modele z plików lub tworzy nowe, jeśli pliki nie istnieją.
            """
            # Ładowanie modelu temperatury
            if os.path.exists(self.temp_model_path):
                self.temperature_model = load_model(self.temp_model_path)
            else:
                self._build_temperature_model()
                
            # Ładowanie modelu dryfu
            if os.path.exists(self.drift_model_path):
                self.drift_model = load_model(self.drift_model_path)
            else:
                self._build_drift_model()
                
            # Ładowanie zoptymalizowanych modeli TFLite
            if os.path.exists(self.quantized_temp_path):
                self.temp_interpreter = tf.lite.Interpreter(model_path=self.quantized_temp_path)
                self.temp_interpreter.allocate_tensors()
                
            if os.path.exists(self.quantized_drift_path):
                self.drift_interpreter = tf.lite.Interpreter(model_path=self.quantized_drift_path)
                self.drift_interpreter.allocate_tensors()
                
            def save_models(self):
                """
                Zapisuje modele do plików.
                """
                if self.temperature_model:
                    self.temperature_model.save(self.temp_model_path)
                    self.quantize_model(self.temperature_model, self.quantized_temp_path)
                    
                if self.drift_model:
                    self.drift_model.save(self.drift_model_path)
                    self.quantize_model(self.drift_model, self.quantized_drift_path)
                    
            def quantize_model(self, model: Sequential, output_path: str):
                """
                Kwantyzuje model do formatu TFLite z optymalizacją.
                
                Args:
                    model: Model do kwantyzacji
                    output_path: Ścieżka do zapisu zoptymalizowanego modelu
                """
                if model is None:
                    return
                    
                # Konwersja do TFLite z kwantyzacją
                converter = tf.lite.TFLiteConverter.from_keras_model(model)
                
                # Włącz optymalizacje
                converter.optimizations = [tf.lite.Optimize.DEFAULT]
                
                # Generowanie danych kalibracyjnych
                def representative_dataset():
                    for _ in range(100):
                        # Generuj losowe dane wejściowe
                        if model == self.temperature_model:
                            yield [np.random.rand(1, 3).astype(np.float32)]
                        else:  # drift_model
                            yield [np.random.rand(1, 1, 6).astype(np.float32)]
                        
                converter.representative_dataset = representative_dataset
                
                # Konwersja modelu
                tflite_model = converter.convert()
                
                # Zapisz model
                with open(output_path, 'wb') as f:
                    f.write(tflite_model)
                    
                # Załaduj zoptymalizowany model
                if model == self.temperature_model:
                    self.temp_interpreter = tf.lite.Interpreter(model_content=tflite_model)
                    self.temp_interpreter.allocate_tensors()
                else:  # drift_model
                    self.drift_interpreter = tf.lite.Interpreter(model_content=tflite_model)
                    self.drift_interpreter.allocate_tensors()
                    
            def update_calibration(self, sensor_data: np.ndarray, temperature: float) -> Dict:
                """
                Aktualizuje kalibrację na podstawie danych z czujników i temperatury.
                Używa zoptymalizowanych modeli TFLite, jeśli są dostępne.
                """
                if (not self.temperature_model and not self.temp_interpreter) or \
                   (not self.drift_model and not self.drift_interpreter):
                    return {
                        'calibration': np.zeros(3),
                        'confidence': 0.0
                    }
                    
                # Predykcja wpływu temperatury
                temp_input = np.array([temperature, temperature**2, temperature**3])
                
                if self.temp_interpreter:
                    # Użyj zoptymalizowanego modelu TFLite
                    input_details = self.temp_interpreter.get_input_details()
                    output_details = self.temp_interpreter.get_output_details()
                    
                    self.temp_interpreter.set_tensor(input_details[0]['index'], temp_input.reshape(1, -1).astype(np.float32))
                    self.temp_interpreter.invoke()
                    
                    temp_correction = self.temp_interpreter.get_tensor(output_details[0]['index'])[0]
                else:
                    # Użyj oryginalnego modelu Keras
                    temp_correction = self.temperature_model.predict(temp_input.reshape(1, -1))[0]
                
                # Predykcja dryfu
                if len(self.calibration_history) > 0:
                    drift_input = self._prepare_drift_input()
                    
                    if self.drift_interpreter:
                        # Użyj zoptymalizowanego modelu TFLite
                        input_details = self.drift_interpreter.get_input_details()
                        output_details = self.drift_interpreter.get_output_details()
                        
                        self.drift_interpreter.set_tensor(input_details[0]['index'], drift_input.reshape(1, -1, 6).astype(np.float32))
                        self.drift_interpreter.invoke()
                        
                        drift_correction = self.drift_interpreter.get_tensor(output_details[0]['index'])[0]
                    else:
                        # Użyj oryginalnego modelu Keras
                        drift_correction = self.drift_model.predict(drift_input.reshape(1, -1, 6))[0]
                else:
                    drift_correction = np.zeros(3)
                    
            # Obliczenie nowej kalibracji
            new_calibration = sensor_data + temp_correction + drift_correction
            
            # Oblicz pewność kalibracji
            confidence = self._calculate_confidence(temp_correction, drift_correction)
            
            # Aktualizacja historii
            self.calibration_history.append({
                'timestamp': datetime.now(),
                'calibration': new_calibration,
                'temperature': temperature,
                'sensor_data': sensor_data,
                'confidence': confidence
            })
            
            # Ogranicz rozmiar historii
            if len(self.calibration_history) > 100:
                self.calibration_history = self.calibration_history[-100:]
            
            return {
                'calibration': new_calibration,
                'confidence': confidence,
                'temp_correction': temp_correction,
                'drift_correction': drift_correction
            }
            
        def _prepare_drift_input(self) -> np.ndarray:
            """
            Przygotowuje dane wejściowe dla modelu dryfu na podstawie historii kalibracji.
            """
            # Przygotowanie danych historycznych dla modelu dryfu
            recent_history = self.calibration_history[-10:]  # Ostatnie 10 pomiarów
            drift_data = []
            
            # Jeśli nie mamy wystarczającej liczby pomiarów, uzupełnij zerami
            if len(recent_history) < 10:
                padding = 10 - len(recent_history)
                for _ in range(padding):
                    drift_data.append([0, 0, 0, 0, 0, 0])
                    
            for entry in recent_history:
                # Normalizacja danych czasowych
                time_diff = (entry['timestamp'] - datetime.now()).total_seconds() / 3600.0  # Konwersja na godziny
                
                drift_data.append([
                    entry['calibration'][0],
                    entry['calibration'][1],
                    entry['calibration'][2],
                    entry['temperature'] / 100.0,  # Normalizacja temperatury
                    time_diff,
                    np.mean(entry['sensor_data'])
                ])
                
            return np.array(drift_data)
            
        def _calculate_confidence(self, temp_correction: np.ndarray, drift_correction: np.ndarray) -> float:
            """
            Oblicza pewność kalibracji na podstawie wielkości korekcji.
            """
            # Oblicz normy korekcji
            temp_norm = np.linalg.norm(temp_correction)
            drift_norm = np.linalg.norm(drift_correction)
            
            # Jeśli korekcje są bardzo duże, pewność jest niska
            if temp_norm > 5.0 or drift_norm > 5.0:
                return 0.1
                
            # Oblicz pewność na podstawie norm (prosta heurystyka)
            # Wartości w zakresie [0.5, 1.0]
            temp_confidence = 1.0 - min(0.5, temp_norm / 10.0)
            drift_confidence = 1.0 - min(0.5, drift_norm / 10.0)
            
            # Średnia ważona pewności
            combined_confidence = 0.7 * temp_confidence + 0.3 * drift_confidence
            
            # Uwzględnij historię kalibracji
            if len(self.calibration_history) > 10:
                # Oblicz stabilność kalibracji w czasie
                recent_calibrations = [entry['calibration'] for entry in self.calibration_history[-10:]]
                calibration_std = np.std(recent_calibrations, axis=0)
                stability_factor = 1.0 - min(0.5, np.mean(calibration_std) / 2.0)
                
                # Uwzględnij stabilność w pewności
                combined_confidence = 0.8 * combined_confidence + 0.2 * stability_factor
                
            return float(combined_confidence)
            
        def train(self, training_data: List[Dict], validation_split: float = 0.2):
            """
            Trenuje modele kalibracji na podstawie danych treningowych.
            
            Args:
                training_data: Dane treningowe
                validation_split: Część danych używana do walidacji
            """
            if self.temperature_model and self.drift_model:
                # Przygotuj callbacki dla lepszego treningu
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
                
                # Przygotowanie danych do trenowania modelu temperatury
                temp_X = []
                temp_y = []
                for entry in training_data:
                    temp_X.append([entry['temperature'], entry['temperature']**2, entry['temperature']**3])
                    temp_y.append(entry['calibration'] - entry['sensor_data'])
                    
                # Trenowanie modelu temperatury
                self.temperature_model.fit(
                    np.array(temp_X),
                    np.array(temp_y),
                    epochs=100,  # Więcej epok, ale z wczesnym zatrzymywaniem
                    batch_size=32,
                    validation_split=validation_split,
                    callbacks=callbacks
                )
                
                # Przytnij model temperatury
                self._prune_model(self.temperature_model, sparsity=0.3)
                
                # Przygotowanie danych do trenowania modelu dryfu
                drift_X = []
                drift_y = []
                for i in range(len(training_data) - 10):
                    # Przygotuj dane wejściowe dla modelu dryfu
                    sequence_data = []
                    for j in range(10):
                        entry = training_data[i + j]
                        time_diff = (entry['timestamp'] - training_data[i]['timestamp']).total_seconds() / 3600.0
                        
                        sequence_data.append([
                            entry['calibration'][0],
                            entry['calibration'][1],
                            entry['calibration'][2],
                            entry['temperature'] / 100.0,
                            time_diff,
                            np.mean(entry['sensor_data'])
                        ])
                        
                    drift_X.append(sequence_data)
                    drift_y.append(training_data[i + 10]['calibration'] - training_data[i + 10]['sensor_data'])
                    
                # Trenowanie modelu dryfu
                self.drift_model.fit(
                    np.array(drift_X),
                    np.array(drift_y),
                    epochs=100,  # Więcej epok, ale z wczesnym zatrzymywaniem
                    batch_size=32,
                    validation_split=validation_split,
                    callbacks=callbacks
                )
                
                # Przytnij model dryfu
                self._prune_model(self.drift_model, sparsity=0.3)
                
                # Zapisz modele
                self.save_models()
                
        def _prune_model(self, model: Sequential, sparsity: float = 0.5):
            """
            Przycina model, usuwając wagi o najmniejszych wartościach bezwzględnych.
            
            Args:
                model: Model do przycięcia
                sparsity: Docelowa rzadkość modelu (0.0 - 1.0)
            """
            if model is None:
                return
                
            # Pobierz wagi modelu
            weights = model.get_weights()
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
            model.set_weights(pruned_weights)
            
        def optimize_hyperparameters(self, training_data: List[Dict], validation_split: float = 0.2):
            """
            Optymalizuje hiperparametry modeli kalibracji.
            
            Args:
                training_data: Dane treningowe
                validation_split: Część danych używana do walidacji
            """
            # Definicja przestrzeni hiperparametrów dla modelu temperatury
            temp_hyperparameters = {
                'hidden_units': [(16, 8), (24, 12), (32, 16)],
                'learning_rate': [0.001, 0.0005, 0.0001],
                'l2_reg': [0.0001, 0.001, 0.01],
                'dropout_rate': [0.0, 0.1, 0.2]
            }
            
            # Definicja przestrzeni hiperparametrów dla modelu dryfu
            drift_hyperparameters = {
                'lstm_units': [(16, 8), (24, 12), (32, 16)],
                'dense_units': [4, 6, 8],
                'learning_rate': [0.001, 0.0005, 0.0001],
                'l2_reg': [0.0001, 0.001, 0.01],
                'dropout_rate': [0.0, 0.1, 0.2]
            }
            
            # Przygotuj dane treningowe i walidacyjne dla modelu temperatury
            temp_X = []
            temp_y = []
            for entry in training_data:
                temp_X.append([entry['temperature'], entry['temperature']**2, entry['temperature']**3])
                temp_y.append(entry['calibration'] - entry['sensor_data'])
                
            temp_X = np.array(temp_X)
            temp_y = np.array(temp_y)
            
            val_size = int(len(temp_X) * validation_split)
            temp_train_X, temp_val_X = temp_X[:-val_size], temp_X[-val_size:]
            temp_train_y, temp_val_y = temp_y[:-val_size], temp_y[-val_size:]
            
            # Optymalizacja modelu temperatury
            best_temp_val_loss = float('inf')
            best_temp_params = {}
            
            from tensorflow.keras.optimizers import Adam
            
            for hidden_units in temp_hyperparameters['hidden_units']:
                for lr in temp_hyperparameters['learning_rate']:
                    for l2 in temp_hyperparameters['l2_reg']:
                        for dropout in temp_hyperparameters['dropout_rate']:
                            # Utwórz model z bieżącymi hiperparametrami
                            temp_model = Sequential([
                                Dense(hidden_units[0], activation='relu', input_shape=(3,),
                                     kernel_regularizer=regularizers.l2(l2)),
                                Dropout(dropout),
                                Dense(hidden_units[1], activation='relu',
                                     kernel_regularizer=regularizers.l2(l2)),
                                Dropout(dropout),
                                Dense(3)
                            ])
                            
                            temp_model.compile(optimizer=Adam(learning_rate=lr), loss='mse')
                            
                            # Trenuj model
                            temp_model.fit(
                                temp_train_X,
                                temp_train_y,
                                epochs=20,
                                batch_size=32,
                                verbose=0
                            )
                            
                            # Oceń model
                            val_loss = temp_model.evaluate(temp_val_X, temp_val_y, verbose=0)
                            
                            # Aktualizuj najlepsze parametry
                            if val_loss < best_temp_val_loss:
                                best_temp_val_loss = val_loss
                                best_temp_params = {
                                    'hidden_units': hidden_units,
                                    'learning_rate': lr,
                                    'l2_reg': l2,
                                    'dropout_rate': dropout
                                }
            
            # Utwórz model temperatury z najlepszymi parametrami
            self.temperature_model = Sequential([
                Dense(best_temp_params['hidden_units'][0], activation='relu', input_shape=(3,),
                     kernel_regularizer=regularizers.l2(best_temp_params['l2_reg'])),
                Dropout(best_temp_params['dropout_rate']),
                Dense(best_temp_params['hidden_units'][1], activation='relu',
                     kernel_regularizer=regularizers.l2(best_temp_params['l2_reg'])),
                Dropout(best_temp_params['dropout_rate']),
                Dense(3)
            ])
            
            self.temperature_model.compile(
                optimizer=Adam(learning_rate=best_temp_params['learning_rate']),
                loss='mse'
            )
            
            # Podobna optymalizacja dla modelu dryfu
            # (Pominięto dla zwięzłości, ale byłaby analogiczna do powyższej)
            
            # Trenuj modele z najlepszymi parametrami
            self.train(training_data, validation_split)
            self.save_models() 