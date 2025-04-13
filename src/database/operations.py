import json
from datetime import datetime
from .db import get_session
from .schema import SensorReading, CalibrationData, MLModel

def save_sensor_reading(reading_data: dict) -> None:
    """Zapisuje odczyt z czujników do bazy danych."""
    session = get_session()
    try:
        reading = SensorReading(
            timestamp=datetime.fromisoformat(reading_data['timestamp']),
            # AS7262
            as7262_450nm=reading_data['as7262']['450nm'],
            as7262_500nm=reading_data['as7262']['500nm'],
            as7262_550nm=reading_data['as7262']['550nm'],
            as7262_570nm=reading_data['as7262']['570nm'],
            as7262_600nm=reading_data['as7262']['600nm'],
            as7262_650nm=reading_data['as7262']['650nm'],
            as7262_temperature=reading_data['as7262']['temperature'],
            # TSL2591
            tsl2591_lux=reading_data['tsl2591']['lux'],
            tsl2591_ir=reading_data['tsl2591']['ir'],
            tsl2591_full=reading_data['tsl2591']['full'],
            # SEN0611
            sen0611_cct=reading_data['sen0611']['cct'],
            sen0611_als=reading_data['sen0611']['als'],
            # GPS
            latitude=reading_data['gps']['latitude'],
            longitude=reading_data['gps']['longitude'],
            altitude=reading_data['gps']['altitude'],
            satellites=reading_data['gps']['satellites'],
            # Environmental
            ambient_temperature=reading_data['ambient_temperature']
        )
        session.add(reading)
        session.commit()
    finally:
        session.close()

def save_calibration_data(sensor_type: str, parameters: dict) -> None:
    """Zapisuje dane kalibracyjne dla czujnika."""
    session = get_session()
    try:
        # Dezaktywuj poprzednią kalibrację
        previous = session.query(CalibrationData)\
            .filter_by(sensor_type=sensor_type, is_active=1)\
            .first()
        if previous:
            previous.is_active = 0
        
        # Dodaj nową kalibrację
        calibration = CalibrationData(
            sensor_type=sensor_type,
            parameters=json.dumps(parameters),
            is_active=1
        )
        session.add(calibration)
        session.commit()
    finally:
        session.close()

def save_ml_model(name: str, version: str, path: str, parameters: dict, metrics: dict) -> None:
    """Zapisuje informacje o modelu ML."""
    session = get_session()
    try:
        # Dezaktywuj poprzedni model
        previous = session.query(MLModel)\
            .filter_by(name=name, is_active=1)\
            .first()
        if previous:
            previous.is_active = 0
        
        # Dodaj nowy model
        model = MLModel(
            name=name,
            version=version,
            path=path,
            parameters=json.dumps(parameters),
            metrics=json.dumps(metrics),
            is_active=1
        )
        session.add(model)
        session.commit()
    finally:
        session.close()

def get_latest_readings(limit: int = 100) -> list:
    """Pobiera ostatnie odczyty z czujników."""
    session = get_session()
    try:
        readings = session.query(SensorReading)\
            .order_by(SensorReading.timestamp.desc())\
            .limit(limit)\
            .all()
        return readings
    finally:
        session.close()

def get_active_calibration(sensor_type: str) -> dict:
    """Pobiera aktywne dane kalibracyjne dla czujnika."""
    session = get_session()
    try:
        calibration = session.query(CalibrationData)\
            .filter_by(sensor_type=sensor_type, is_active=1)\
            .first()
        if calibration:
            return json.loads(calibration.parameters)
        return None
    finally:
        session.close()

def get_active_ml_model(name: str) -> MLModel:
    """Pobiera aktywny model ML."""
    session = get_session()
    try:
        model = session.query(MLModel)\
            .filter_by(name=name, is_active=1)\
            .first()
        return model
    finally:
        session.close() 