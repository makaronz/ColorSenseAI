from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class SensorReading(Base):
    __tablename__ = 'sensor_readings'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # AS7262 readings
    as7262_450nm = Column(Float)
    as7262_500nm = Column(Float)
    as7262_550nm = Column(Float)
    as7262_570nm = Column(Float)
    as7262_600nm = Column(Float)
    as7262_650nm = Column(Float)
    as7262_temperature = Column(Float)
    
    # TSL2591 readings
    tsl2591_lux = Column(Float)
    tsl2591_ir = Column(Float)
    tsl2591_full = Column(Float)
    
    # SEN0611 readings
    sen0611_cct = Column(Float)
    sen0611_als = Column(Float)
    
    # GPS data
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    satellites = Column(Integer)
    
    # Environmental data
    ambient_temperature = Column(Float)

class CalibrationData(Base):
    __tablename__ = 'calibration_data'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    sensor_type = Column(String)  # AS7262, TSL2591, or SEN0611
    parameters = Column(String)  # JSON string of calibration parameters
    is_active = Column(Integer, default=1)  # 1 for active, 0 for historical

class MLModel(Base):
    __tablename__ = 'ml_models'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    path = Column(String)  # Path to the saved model file
    parameters = Column(String)  # JSON string of model parameters
    is_active = Column(Integer, default=1)  # 1 for active, 0 for historical
    metrics = Column(String)  # JSON string of model performance metrics 