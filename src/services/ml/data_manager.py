import numpy as np
import pandas as pd
from datetime import datetime, timedelta, UTC
from typing import Tuple, List, Dict, Optional, Any
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from database.operations import get_latest_readings
from database.schema import SensorReading
from database.db import get_session
from sqlalchemy import and_

class MLDataManager:
    def __init__(self):
        self.scaler = StandardScaler()
        
    def prepare_color_correction_data(self, hours: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """
        Przygotowuje dane do treningu modelu korekcji kolorów.
        
        Args:
            hours: Liczba godzin danych do pobrania
            
        Returns:
            X: Cechy (spektrum AS7262)
            y: Etykiety (CCT z SEN0611)
        """
        session = get_session()
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=hours)
            
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return np.array([]), np.array([])
            
            # Przygotuj cechy (spektrum AS7262)
            X = np.array([[
                r.as7262_450nm, r.as7262_500nm, r.as7262_550nm,
                r.as7262_570nm, r.as7262_600nm, r.as7262_650nm
            ] for r in readings])
            
            # Przygotuj etykiety (CCT)
            y = np.array([r.sen0611_cct for r in readings])
            
            # Normalizacja danych
            X = self.scaler.fit_transform(X)
            
            return X, y
            
        finally:
            session.close()
    
    def prepare_anomaly_detection_data(self, hours: int = 24) -> np.ndarray:
        """
        Przygotowuje dane do treningu modelu wykrywania anomalii.
        
        Args:
            hours: Liczba godzin danych do pobrania
            
        Returns:
            X: Dane do treningu detektora anomalii
        """
        session = get_session()
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=hours)
            
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return np.array([])
            
            # Przygotuj dane ze wszystkich czujników
            X = np.array([[
                r.as7262_450nm, r.as7262_500nm, r.as7262_550nm,
                r.as7262_570nm, r.as7262_600nm, r.as7262_650nm,
                r.tsl2591_lux, r.tsl2591_ir, r.tsl2591_full,
                r.sen0611_cct, r.sen0611_als,
                r.as7262_temperature, r.ambient_temperature
            ] for r in readings])
            
            # Normalizacja danych
            X = self.scaler.fit_transform(X)
            
            return X
            
        finally:
            session.close()
    
    def prepare_sensor_optimization_data(self, hours: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """
        Przygotowuje dane do treningu modelu optymalizacji czujników.
        
        Args:
            hours: Liczba godzin danych do pobrania
            
        Returns:
            X: Cechy (odczyty czujników i warunki)
            y: Etykiety (optymalne parametry)
        """
        session = get_session()
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=hours)
            
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return np.array([]), np.array([])
            
            # Przygotuj cechy (warunki pomiarowe)
            X = np.array([[
                float(getattr(r, 'ambient_temperature')),
                float(getattr(r, 'tsl2591_lux')),
                float(getattr(r, 'sen0611_als')),
                float(getattr(r, 'as7262_temperature'))
            ] for r in readings], dtype=np.float64)
            
            # Przygotuj etykiety (zakładamy, że optymalne parametry to średnie wartości)
            spectrum_values = np.array([[
                float(getattr(r, 'as7262_450nm')), float(getattr(r, 'as7262_500nm')), 
                float(getattr(r, 'as7262_550nm')), float(getattr(r, 'as7262_570nm')), 
                float(getattr(r, 'as7262_600nm')), float(getattr(r, 'as7262_650nm'))
            ] for r in readings], dtype=np.float64)
            
            y = np.array([[
                np.mean(spectrum),
                float(getattr(r, 'tsl2591_full')),
                float(getattr(r, 'sen0611_cct'))
            ] for r, spectrum in zip(readings, spectrum_values)], dtype=np.float64)
            
            # Normalizacja danych
            X = self.scaler.fit_transform(X)
            y = self.scaler.fit_transform(y)
            
            return X, y
            
        finally:
            session.close()
    
    def prepare_calibration_data(self, hours: int = 24) -> Dict[str, np.ndarray]:
        """
        Przygotowuje dane do treningu modelu kalibracji adaptacyjnej.
        
        Args:
            hours: Liczba godzin danych do pobrania
            
        Returns:
            Dict zawierający dane kalibracyjne dla każdego czujnika
        """
        session = get_session()
        try:
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(hours=hours)
            
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return {}
            
            # Przygotuj dane kalibracyjne dla każdego czujnika
            calibration_data = {
                'AS7262': np.array([[
                    r.as7262_450nm, r.as7262_500nm, r.as7262_550nm,
                    r.as7262_570nm, r.as7262_600nm, r.as7262_650nm,
                    r.as7262_temperature, r.ambient_temperature
                ] for r in readings]),
                
                'TSL2591': np.array([[
                    r.tsl2591_lux, r.tsl2591_ir, r.tsl2591_full,
                    r.ambient_temperature
                ] for r in readings]),
                
                'SEN0611': np.array([[
                    r.sen0611_cct, r.sen0611_als,
                    r.ambient_temperature
                ] for r in readings])
            }
            
            # Normalizacja danych dla każdego czujnika
            for sensor in calibration_data:
                calibration_data[sensor] = self.scaler.fit_transform(calibration_data[sensor])
            
            return calibration_data
            
        finally:
            session.close()
    
    def get_training_validation_split(self, X: np.ndarray, y: np.ndarray,
                                    test_size: float = 0.2, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Dzieli dane na zbiór treningowy i walidacyjny.
        """
        return train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    def save_model_results(self, model_name: str, version: str, metrics: Dict[str, float],
                          model_path: str, parameters: Dict[str, Any]) -> None:
        """
        Zapisuje wyniki modelu do bazy danych.
        """
        from database.operations import save_ml_model
        save_ml_model(model_name, version, model_path, parameters, metrics) 