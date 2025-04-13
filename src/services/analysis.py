import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy import func, and_
from database.db import get_session
from database.schema import SensorReading

class SensorAnalysis:
    @staticmethod
    def get_daily_statistics(date: datetime) -> Dict[str, Dict[str, float]]:
        """Oblicza statystyki dzienne dla wszystkich czujników."""
        session = get_session()
        try:
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            # Pobierz dane z danego dnia
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_date,
                    SensorReading.timestamp < end_date
                )
            ).all()
            
            if not readings:
                return {}
            
            # Konwersja do DataFrame
            df = pd.DataFrame([{
                'timestamp': r.timestamp,
                'cct': r.sen0611_cct,
                'lux': r.tsl2591_lux,
                'als': r.sen0611_als,
                'temp': r.as7262_temperature
            } for r in readings])
            
            # Oblicz statystyki
            stats = {
                'cct': {
                    'min': df['cct'].min(),
                    'max': df['cct'].max(),
                    'mean': df['cct'].mean(),
                    'std': df['cct'].std()
                },
                'lux': {
                    'min': df['lux'].min(),
                    'max': df['lux'].max(),
                    'mean': df['lux'].mean(),
                    'std': df['lux'].std()
                },
                'als': {
                    'min': df['als'].min(),
                    'max': df['als'].max(),
                    'mean': df['als'].mean(),
                    'std': df['als'].std()
                },
                'temperature': {
                    'min': df['temp'].min(),
                    'max': df['temp'].max(),
                    'mean': df['temp'].mean(),
                    'std': df['temp'].std()
                }
            }
            
            return stats
        finally:
            session.close()
    
    @staticmethod
    def analyze_color_spectrum(start_time: datetime, end_time: datetime) -> Dict[str, List[float]]:
        """Analizuje widmo kolorów w zadanym okresie."""
        session = get_session()
        try:
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return {}
            
            # Przygotuj dane spektralne
            wavelengths = ['450nm', '500nm', '550nm', '570nm', '600nm', '650nm']
            spectrum_data = {
                'wavelengths': wavelengths,
                'mean_values': [],
                'max_values': [],
                'min_values': []
            }
            
            # Zbierz dane dla każdej długości fali
            for wavelength in wavelengths:
                values = [getattr(r, f'as7262_{wavelength}') for r in readings]
                spectrum_data['mean_values'].append(np.mean(values))
                spectrum_data['max_values'].append(np.max(values))
                spectrum_data['min_values'].append(np.min(values))
            
            return spectrum_data
        finally:
            session.close()
    
    @staticmethod
    def detect_anomalies(hours: int = 24) -> List[Dict[str, any]]:
        """Wykrywa anomalie w danych z ostatnich n godzin."""
        session = get_session()
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return []
            
            # Konwersja do DataFrame
            df = pd.DataFrame([{
                'timestamp': r.timestamp,
                'cct': r.sen0611_cct,
                'lux': r.tsl2591_lux,
                'als': r.sen0611_als,
                'temp': r.as7262_temperature
            } for r in readings])
            
            anomalies = []
            
            # Wykrywanie anomalii używając metody Z-score
            for column in ['cct', 'lux', 'als', 'temp']:
                mean = df[column].mean()
                std = df[column].std()
                z_scores = np.abs((df[column] - mean) / std)
                
                # Znajdź punkty odstające (Z-score > 3)
                outliers = df[z_scores > 3]
                
                for _, row in outliers.iterrows():
                    anomalies.append({
                        'timestamp': row['timestamp'],
                        'sensor': column,
                        'value': row[column],
                        'z_score': z_scores[row.name]
                    })
            
            return anomalies
        finally:
            session.close()
    
    @staticmethod
    def export_to_csv(start_time: datetime, end_time: datetime, filepath: str) -> bool:
        """Eksportuje dane do pliku CSV."""
        session = get_session()
        try:
            readings = session.query(SensorReading).filter(
                and_(
                    SensorReading.timestamp >= start_time,
                    SensorReading.timestamp <= end_time
                )
            ).all()
            
            if not readings:
                return False
            
            # Konwersja do DataFrame
            df = pd.DataFrame([{
                'timestamp': r.timestamp,
                'as7262_450nm': r.as7262_450nm,
                'as7262_500nm': r.as7262_500nm,
                'as7262_550nm': r.as7262_550nm,
                'as7262_570nm': r.as7262_570nm,
                'as7262_600nm': r.as7262_600nm,
                'as7262_650nm': r.as7262_650nm,
                'as7262_temperature': r.as7262_temperature,
                'tsl2591_lux': r.tsl2591_lux,
                'tsl2591_ir': r.tsl2591_ir,
                'tsl2591_full': r.tsl2591_full,
                'sen0611_cct': r.sen0611_cct,
                'sen0611_als': r.sen0611_als,
                'latitude': r.latitude,
                'longitude': r.longitude,
                'altitude': r.altitude,
                'satellites': r.satellites,
                'ambient_temperature': r.ambient_temperature
            } for r in readings])
            
            # Zapisz do CSV
            df.to_csv(filepath, index=False)
            return True
            
        finally:
            session.close() 