import logging
from services.ml.ml_feature_manager import MLFeatureManager
from services.analysis import SensorAnalysis
from database.operations import get_latest_readings
from database.db import init_db
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ColorSense")

def main():
    """Główna funkcja aplikacji."""
    try:
        # Inicjalizacja bazy danych
        init_db()
        logger.info("Baza danych zainicjalizowana")
        
        # Inicjalizacja menedżera funkcji ML
        ml_manager = MLFeatureManager()
        logger.info("Menedżer ML zainicjalizowany")
        
        # Inicjalizacja analizy danych
        analyzer = SensorAnalysis()
        logger.info("System analizy zainicjalizowany")
        
        # Przykład: pobierz ostatnie odczyty
        readings = get_latest_readings(10)
        if readings:
            logger.info(f"Pobrano {len(readings)} ostatnich odczytów")
            
            # Przykład: oblicz statystyki dzienne
            stats = analyzer.get_daily_statistics(datetime.now())
            logger.info(f"Statystyki dzienne: {stats}")
        else:
            logger.warning("Brak dostępnych odczytów")
            
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania aplikacji: {str(e)}")
        raise

if __name__ == "__main__":
    main() 