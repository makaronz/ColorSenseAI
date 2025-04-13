import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .schema import Base

# Ścieżka do katalogu data w głównym katalogu projektu
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Ścieżka do pliku bazy danych
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'colorsense.db')}"

# Utworzenie silnika bazy danych
engine = create_engine(DATABASE_URL)

# Utworzenie sesji
Session = sessionmaker(bind=engine)

def init_db():
    """Inicjalizacja bazy danych i utworzenie wszystkich tabel."""
    Base.metadata.create_all(engine)

def get_session():
    """Zwraca nową sesję bazy danych."""
    return Session()

def close_session(session):
    """Zamyka sesję bazy danych."""
    session.close() 