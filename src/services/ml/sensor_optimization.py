import numpy as np
from tensorflow import keras
from collections import deque
import random
from typing import Dict, Optional, List
import os
from datetime import datetime
from .data_manager import MLDataManager

class SensorOptimizationAgent:
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicjalizacja agenta optymalizacji czujników.
        
        Args:
            model_path: Ścieżka do zapisanego modelu (opcjonalna)
        """
        self.data_manager = MLDataManager()
        self.q_network = None
        self.target_network = None
        self.version = "1.0.0"
        
        # Parametry uczenia ze wzmocnieniem
        self.memory = deque(maxlen=10000)
        self.gamma = 0.95  # Współczynnik dyskontowania
        self.epsilon = 1.0  # Współczynnik eksploracji
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.update_target_frequency = 10
        self.training_count = 0
        
        if model_path and os.path.exists(model_path):
            self.q_network = keras.models.load_model(model_path)
            self.target_network = keras.models.clone_model(self.q_network)
            self.target_network.set_weights(self.q_network.get_weights())
    
    def build_model(self) -> None:
        """Buduje model sieci Q do optymalizacji czujników."""
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(4,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.1),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(3)  # 3 możliwe akcje optymalizacji
        ])
        
        model.compile(
            optimizer='adam',
            loss='huber',  # Bardziej odporny na wartości odstające
            metrics=['mae']
        )
        
        self.q_network = model
        self.target_network = keras.models.clone_model(model)
        self.target_network.set_weights(model.get_weights())
    
    def train(self, hours: int = 24, episodes: int = 100, 
              batch_size: int = 32) -> Dict[str, float]:
        """
        Trenuje agenta na danych historycznych.
        
        Args:
            hours: Liczba godzin danych do treningu
            episodes: Liczba epizodów treningu
            batch_size: Rozmiar batcha
            
        Returns:
            Metryki treningu
        """
        if not self.q_network:
            self.build_model()
        
        # Pobierz dane treningowe
        X, y = self.data_manager.prepare_sensor_optimization_data(hours)
        
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Brak danych treningowych")
        
        total_rewards = []
        losses = []
        
        for episode in range(episodes):
            # Wybierz losowy stan początkowy
            state_idx = random.randrange(len(X))
            state = X[state_idx]
            total_reward = 0
            
            for step in range(100):  # Maksymalnie 100 kroków na epizod
                # Wybierz akcję
                if random.random() < self.epsilon:
                    action = random.randrange(3)
                else:
                    q_values = self.q_network.predict(state.reshape(1, -1), verbose=0)
                    action = np.argmax(q_values[0])
                
                # Symuluj następny stan i nagrodę
                next_state_idx = (state_idx + 1) % len(X)
                next_state = X[next_state_idx]
                reward = self._calculate_reward(state, action, y[state_idx])
                
                # Zapisz doświadczenie
                self.remember(state, action, reward, next_state)
                
                # Trening na batchu
                if len(self.memory) >= batch_size:
                    loss = self.replay(batch_size)
                    losses.append(loss)
                
                total_reward += reward
                state = next_state
                state_idx = next_state_idx
                
                # Aktualizuj sieć docelową
                if self.training_count % self.update_target_frequency == 0:
                    self.target_network.set_weights(self.q_network.get_weights())
            
            # Aktualizuj epsilon
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            total_rewards.append(total_reward)
        
        # Oblicz metryki
        metrics = {
            'mean_reward': float(np.mean(total_rewards)),
            'final_epsilon': float(self.epsilon),
            'mean_loss': float(np.mean(losses)) if losses else 0.0,
            'memory_size': len(self.memory)
        }
        
        return metrics
    
    def optimize_settings(self, sensor_data: np.ndarray) -> Dict:
        """
        Wybiera optymalne ustawienia dla czujników.
        
        Args:
            sensor_data: Dane z czujników do optymalizacji
            
        Returns:
            Słownik z wybranymi ustawieniami i pewnością
        """
        if not self.q_network:
            raise ValueError("Model nie został wytrenowany")
        
        # Normalizacja danych wejściowych
        sensor_data = self.data_manager.scaler.transform(sensor_data.reshape(1, -1))
        
        # Wybierz akcję
        q_values = self.q_network.predict(sensor_data, verbose=0)
        action = np.argmax(q_values[0])
        
        # Oblicz pewność
        sorted_q_values = np.sort(q_values[0])[::-1]
        confidence = (sorted_q_values[0] - sorted_q_values[1]) / (np.max(np.abs(sorted_q_values)) + 1e-6)
        confidence = min(1.0, max(0.0, confidence))
        
        return {
            'action': int(action),
            'confidence': float(confidence),
            'q_values': q_values[0].tolist()
        }
    
    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray):
        """Zapisuje doświadczenie w pamięci."""
        self.memory.append((state, action, reward, next_state))
    
    def replay(self, batch_size: int) -> float:
        """
        Trenuje sieć Q na podstawie losowej próbki doświadczeń.
        
        Returns:
            Wartość funkcji straty
        """
        minibatch = random.sample(self.memory, batch_size)
        states = np.array([exp[0] for exp in minibatch])
        actions = np.array([exp[1] for exp in minibatch])
        rewards = np.array([exp[2] for exp in minibatch])
        next_states = np.array([exp[3] for exp in minibatch])
        
        # Oblicz cele dla sieci Q
        targets = self.q_network.predict(states, verbose=0)
        next_q_values = self.target_network.predict(next_states, verbose=0)
        
        for i in range(batch_size):
            targets[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
        
        # Trenuj sieć Q
        history = self.q_network.fit(states, targets, epochs=1, verbose=0, batch_size=batch_size)
        self.training_count += 1
        
        return float(history.history['loss'][0])
    
    def _calculate_reward(self, state: np.ndarray, action: int, optimal_values: np.ndarray) -> float:
        """
        Oblicza nagrodę za akcję w danym stanie.
        
        Returns:
            Wartość nagrody
        """
        # Symuluj efekt akcji na parametrach czujników
        if action == 0:  # Zwiększ czułość
            new_values = state * 1.1
        elif action == 1:  # Zmniejsz czułość
            new_values = state * 0.9
        else:  # Nie zmieniaj
            new_values = state.copy()
        
        # Oblicz błąd między nowymi wartościami a optymalnymi
        error = np.mean(np.square(new_values - optimal_values))
        
        # Nagroda jest odwrotnie proporcjonalna do błędu
        reward = 1.0 / (1.0 + error)
        
        return float(reward)
    
    def save(self, save_dir: str) -> str:
        """
        Zapisuje model i jego parametry.
        
        Args:
            save_dir: Katalog do zapisu
            
        Returns:
            Ścieżka do zapisanego modelu
        """
        if not self.q_network:
            raise ValueError("Brak modelu do zapisu")
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs(save_dir, exist_ok=True)
        
        # Generuj nazwę pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"sensor_optimization_model_{timestamp}"
        model_path = os.path.join(save_dir, model_name)
        
        # Zapisz model
        self.q_network.save(model_path)
        
        # Zapisz informacje o modelu w bazie danych
        parameters = {
            'architecture': self.q_network.to_json(),
            'input_shape': self.q_network.input_shape,
            'output_shape': self.q_network.output_shape,
            'epsilon': self.epsilon,
            'gamma': self.gamma,
            'memory_size': len(self.memory)
        }
        
        metrics = self.evaluate()
        
        self.data_manager.save_model_results(
            model_name="sensor_optimization",
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
        if not self.q_network:
            raise ValueError("Model nie został wytrenowany")
        
        # Pobierz dane do ewaluacji
        X, y = self.data_manager.prepare_sensor_optimization_data(hours)
        
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Brak danych do ewaluacji")
        
        total_rewards = []
        predictions = []
        
        for i in range(len(X)):
            state = X[i]
            optimal = y[i]
            
            # Wybierz akcję
            q_values = self.q_network.predict(state.reshape(1, -1), verbose=0)
            action = np.argmax(q_values[0])
            
            # Oblicz nagrodę
            reward = self._calculate_reward(state, action, optimal)
            total_rewards.append(reward)
            predictions.append(q_values[0])
        
        predictions = np.array(predictions)
        
        return {
            'mean_reward': float(np.mean(total_rewards)),
            'mean_q_value': float(np.mean(predictions)),
            'max_q_value': float(np.max(predictions)),
            'min_q_value': float(np.min(predictions)),
            'action_distribution': [float(np.mean(np.argmax(predictions, axis=1) == i)) for i in range(3)]
        } 