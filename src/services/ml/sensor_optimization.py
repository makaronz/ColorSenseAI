import numpy as np
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout
from collections import deque
import random
from typing import Dict, List, Optional, Tuple
import os
import tensorflow as tf
from tensorflow.keras import regularizers
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

class SensorOptimizationAgent:
    def __init__(self,
                 model_path: str = "models/sensor_optimization.h5",
                 quantized_model_path: str = "models/sensor_optimization_quantized.tflite",
                 target_model_path: str = "models/sensor_optimization_target.h5"):
        self.model_path = model_path
        self.quantized_model_path = quantized_model_path
        self.target_model_path = target_model_path
        
        self.q_network: Optional[Sequential] = None
        self.target_network: Optional[Sequential] = None
        self.quantized_interpreter: Optional[tf.lite.Interpreter] = None
        
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.update_target_frequency = 10  # Częstotliwość aktualizacji sieci docelowej
        self.training_count = 0
        
        self._load_model()
        def _build_q_network(self):
            """
            Buduje zoptymalizowaną sieć Q z regularyzacją i dropout.
            """
            model = Sequential([
                Dense(48, activation='relu', input_shape=(9,),
                     kernel_regularizer=regularizers.l2(0.001)),
                Dropout(0.1),
                Dense(24, activation='relu',
                     kernel_regularizer=regularizers.l2(0.001)),
                Dropout(0.1),
                Dense(4)  # 4 możliwe akcje
            ])
            model.compile(optimizer='adam', loss='huber_loss')  # Huber loss jest bardziej odporny na wartości odstające
            return model
            
        def _load_model(self):
            """
            Ładuje modele z plików lub tworzy nowe, jeśli pliki nie istnieją.
            """
            # Ładowanie głównej sieci Q
            if os.path.exists(self.model_path):
                self.q_network = load_model(self.model_path)
            else:
                self.q_network = self._build_q_network()
                
            # Ładowanie sieci docelowej
            if os.path.exists(self.target_model_path):
                self.target_network = load_model(self.target_model_path)
            else:
                self.target_network = self._build_q_network()
                self.target_network.set_weights(self.q_network.get_weights())
                
            # Ładowanie zoptymalizowanego modelu TFLite
            if os.path.exists(self.quantized_model_path):
                self.quantized_interpreter = tf.lite.Interpreter(model_path=self.quantized_model_path)
                self.quantized_interpreter.allocate_tensors()
                
        def save_model(self):
            """
            Zapisuje modele do plików.
            """
            if self.q_network:
                self.q_network.save(self.model_path)
                
            if self.target_network:
                self.target_network.save(self.target_model_path)
                
            self.quantize_model()
                
        def quantize_model(self):
            """
            Kwantyzuje model do formatu TFLite z optymalizacją.
            """
            if self.q_network is None:
                return
                
            # Konwersja do TFLite z kwantyzacją
            converter = tf.lite.TFLiteConverter.from_keras_model(self.q_network)
            
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
                
            def optimize_settings(self, current_state: np.ndarray) -> Dict:
                """
                Wybiera optymalną akcję na podstawie bieżącego stanu.
                Używa zoptymalizowanego modelu TFLite, jeśli jest dostępny.
                """
                if not self.q_network and not self.quantized_interpreter:
                    return {
                        'action': 0,
                        'confidence': 0.0
                    }
                    
                # Eksploracja vs eksploatacja
                if np.random.rand() <= self.epsilon:
                    action = random.randrange(4)
                    confidence = 0.0
                else:
                    # Przygotuj dane wejściowe
                    input_data = current_state.reshape(1, -1)
                    
                    # Użyj zoptymalizowanego modelu TFLite, jeśli jest dostępny
                    if self.quantized_interpreter:
                        input_details = self.quantized_interpreter.get_input_details()
                        output_details = self.quantized_interpreter.get_output_details()
                        
                        self.quantized_interpreter.set_tensor(input_details[0]['index'], input_data.astype(np.float32))
                        self.quantized_interpreter.invoke()
                        
                        q_values = self.quantized_interpreter.get_tensor(output_details[0]['index'])
                    else:
                        # Użyj oryginalnego modelu Keras
                        q_values = self.q_network.predict(input_data)
                        
                    action = np.argmax(q_values[0])
                    
                    # Oblicz pewność na podstawie różnicy między najlepszą a drugą najlepszą akcją
                    sorted_q_values = np.sort(q_values[0])[::-1]  # Sortuj malejąco
                    if len(sorted_q_values) > 1:
                        confidence = (sorted_q_values[0] - sorted_q_values[1]) / (np.max(np.abs(sorted_q_values)) + 1e-6)
                        confidence = min(1.0, max(0.0, confidence))  # Ogranicz do [0, 1]
                    else:
                        confidence = 1.0
                    
                return {
                    'action': int(action),
                    'confidence': float(confidence)
                }
                
        def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
            """
            Zapisuje doświadczenie w pamięci.
            """
            self.memory.append((state, action, reward, next_state, done))
            
        def replay(self, batch_size: int):
            """
            Trenuje sieć Q na podstawie losowej próbki doświadczeń z pamięci.
            Używa sieci docelowej do stabilizacji treningu.
            """
            if len(self.memory) < batch_size:
                return
                
            # Pobierz losową próbkę z pamięci
            minibatch = random.sample(self.memory, batch_size)
            
            # Przygotuj dane treningowe
            states = np.array([experience[0] for experience in minibatch])
            actions = np.array([experience[1] for experience in minibatch])
            rewards = np.array([experience[2] for experience in minibatch])
            next_states = np.array([experience[3] for experience in minibatch])
            dones = np.array([experience[4] for experience in minibatch])
            
            # Oblicz cele dla sieci Q
            targets = self.q_network.predict(states)
            next_q_values = self.target_network.predict(next_states)
            
            for i in range(batch_size):
                if dones[i]:
                    targets[i, actions[i]] = rewards[i]
                else:
                    targets[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
            
            # Trenuj sieć Q
            self.q_network.fit(states, targets, epochs=1, verbose=0, batch_size=batch_size)
            
            # Aktualizuj epsilon
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
                
            # Aktualizuj sieć docelową
            self.training_count += 1
            if self.training_count % self.update_target_frequency == 0:
                self.target_network.set_weights(self.q_network.get_weights())
                
        def _prune_model(self, sparsity: float = 0.5):
            """
            Przycina model, usuwając wagi o najmniejszych wartościach bezwzględnych.
            
            Args:
                sparsity: Docelowa rzadkość modelu (0.0 - 1.0)
            """
            if self.q_network is None:
                return
                
            # Pobierz wagi modelu
            weights = self.q_network.get_weights()
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
            self.q_network.set_weights(pruned_weights)
            self.target_network.set_weights(pruned_weights)
            def train(self, episodes: int, batch_size: int, validation_data: Optional[List[Tuple[np.ndarray, int, float, np.ndarray, bool]]] = None):
                """
                Trenuje agenta przez określoną liczbę epizodów.
                
                Args:
                    episodes: Liczba epizodów treningu
                    batch_size: Rozmiar batcha
                    validation_data: Opcjonalne dane walidacyjne
                """
                # Przygotuj callbacki dla lepszego treningu
                callbacks = []
                if validation_data:
                    # Przygotuj dane walidacyjne
                    val_states = np.array([exp[0] for exp in validation_data])
                    val_actions = np.array([exp[1] for exp in validation_data])
                    val_rewards = np.array([exp[2] for exp in validation_data])
                    val_next_states = np.array([exp[3] for exp in validation_data])
                    val_dones = np.array([exp[4] for exp in validation_data])
                    
                    # Dodaj callbacki
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
                
                for episode in range(episodes):
                    state = np.random.rand(9)  # Przykładowy stan
                    done = False
                    episode_reward = 0
                    
                    while not done:
                        # Wybierz akcję
                        action = self.optimize_settings(state)['action']
                        
                        # Wykonaj akcję (symulacja)
                        next_state = np.random.rand(9)  # Przykładowy następny stan
                        reward = random.random()  # Przykładowa nagroda
                        done = random.random() < 0.1  # Przykładowe zakończenie
                        
                        # Zapisz doświadczenie
                        self.remember(state, action, reward, next_state, done)
                        episode_reward += reward
                        
                        # Przejdź do następnego stanu
                        state = next_state
                        
                        # Trenuj na batchu doświadczeń
                        if len(self.memory) > batch_size:
                            self.replay(batch_size)
                    
                    # Po każdym epizodzie
                    if episode % 10 == 0:
                        print(f"Epizod {episode}/{episodes}, Nagroda: {episode_reward}, Epsilon: {self.epsilon}")
                        
                    # Co 100 epizodów, przytnij model
                    if episode % 100 == 0 and episode > 0:
                        self._prune_model(sparsity=0.3)
                        
                    # Zapisz model co 50 epizodów
                    if episode % 50 == 0:
                        self.save_model()
                        
                # Przytnij model na końcu treningu
                self._prune_model(sparsity=0.3)
                
                # Zapisz ostateczny model
                self.save_model()
                
            def optimize_hyperparameters(self, validation_data: List[Tuple[np.ndarray, int, float, np.ndarray, bool]]):
                """
                Optymalizuje hiperparametry agenta.
                
                Args:
                    validation_data: Dane walidacyjne
                """
                # Definicja przestrzeni hiperparametrów
                hyperparameters = {
                    'gamma': [0.9, 0.95, 0.99],
                    'epsilon_decay': [0.99, 0.995, 0.999],
                    'learning_rate': [0.001, 0.0005, 0.0001],
                    'hidden_units': [(48, 24), (64, 32), (32, 16)]
                }
                
                best_val_loss = float('inf')
                best_params = {}
                
                # Przygotuj dane walidacyjne
                val_states = np.array([exp[0] for exp in validation_data])
                val_actions = np.array([exp[1] for exp in validation_data])
                val_rewards = np.array([exp[2] for exp in validation_data])
                val_next_states = np.array([exp[3] for exp in validation_data])
                val_dones = np.array([exp[4] for exp in validation_data])
                
                # Oblicz cele dla danych walidacyjnych
                val_targets = np.zeros((len(validation_data), 4))
                
                # Proste przeszukiwanie siatki
                for gamma in hyperparameters['gamma']:
                    for epsilon_decay in hyperparameters['epsilon_decay']:
                        for lr in hyperparameters['learning_rate']:
                            for hidden_units in hyperparameters['hidden_units']:
                                # Utwórz model z bieżącymi hiperparametrami
                                from tensorflow.keras.optimizers import Adam
                                
                                model = Sequential([
                                    Dense(hidden_units[0], activation='relu', input_shape=(9,),
                                         kernel_regularizer=regularizers.l2(0.001)),
                                    Dropout(0.1),
                                    Dense(hidden_units[1], activation='relu',
                                         kernel_regularizer=regularizers.l2(0.001)),
                                    Dropout(0.1),
                                    Dense(4)
                                ])
                                
                                model.compile(optimizer=Adam(learning_rate=lr), loss='huber_loss')
                                
                                # Oblicz cele dla danych walidacyjnych
                                for i, (_, action, reward, next_state, done) in enumerate(validation_data):
                                    if done:
                                        val_targets[i, action] = reward
                                    else:
                                        next_q_values = model.predict(next_state.reshape(1, -1))[0]
                                        val_targets[i, action] = reward + gamma * np.max(next_q_values)
                                
                                # Trenuj model
                                model.fit(val_states, val_targets, epochs=10, batch_size=32, verbose=0)
                                
                                # Oceń model
                                val_loss = model.evaluate(val_states, val_targets, verbose=0)
                                
                                # Aktualizuj najlepsze parametry
                                if val_loss < best_val_loss:
                                    best_val_loss = val_loss
                                    best_params = {
                                        'gamma': gamma,
                                        'epsilon_decay': epsilon_decay,
                                        'learning_rate': lr,
                                        'hidden_units': hidden_units
                                    }
                
                # Ustaw najlepsze parametry
                self.gamma = best_params['gamma']
                self.epsilon_decay = best_params['epsilon_decay']
                
                # Utwórz model z najlepszymi parametrami
                from tensorflow.keras.optimizers import Adam
                
                self.q_network = Sequential([
                    Dense(best_params['hidden_units'][0], activation='relu', input_shape=(9,),
                         kernel_regularizer=regularizers.l2(0.001)),
                    Dropout(0.1),
                    Dense(best_params['hidden_units'][1], activation='relu',
                         kernel_regularizer=regularizers.l2(0.001)),
                    Dropout(0.1),
                    Dense(4)
                ])
                
                self.q_network.compile(optimizer=Adam(learning_rate=best_params['learning_rate']), loss='huber_loss')
                
                # Utwórz sieć docelową
                self.target_network = Sequential([
                    Dense(best_params['hidden_units'][0], activation='relu', input_shape=(9,),
                         kernel_regularizer=regularizers.l2(0.001)),
                    Dropout(0.1),
                    Dense(best_params['hidden_units'][1], activation='relu',
                         kernel_regularizer=regularizers.l2(0.001)),
                    Dropout(0.1),
                    Dense(4)
                ])
                
                self.target_network.compile(optimizer=Adam(learning_rate=best_params['learning_rate']), loss='huber_loss')
                self.target_network.set_weights(self.q_network.get_weights())
                
                # Zapisz zoptymalizowane modele
                self.save_model()
            self.save_model() 