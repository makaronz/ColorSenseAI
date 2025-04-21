import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from astral import sun, location

# --- Konfiguracja Symulacji ---
OUTPUT_FILE = 'data/simulated_dashboard_data.csv' # Poprawiono ścieżkę na względną do katalogu data wewnątrz projektu
LOCATION_CITY = "Warsaw"
LOCATION_REGION = "Poland"
LATITUDE = 52.2297  # Szerokość geograficzna Warszawy
LONGITUDE = 21.0122 # Długość geograficzna Warszawy
ELEVATION = 110     # Przybliżona wysokość n.p.m. w Warszawie
DATE_STR = "2024-11-12"
TIMEZONE = "Europe/Warsaw"
START_TIME_STR = f"{DATE_STR} 00:00:00"
END_TIME_STR = f"{DATE_STR} 23:59:59"
FREQUENCY_SECONDS = 15

# Parametry pogodowe
CLOUD_COVER_PROBABILITY = 0.4  # Prawdopodobieństwo wystąpienia chmury w danym kroku czasowym
CLOUD_DURATION_MEAN = 5 * 60   # Średni czas trwania chmury (w sekundach)
CLOUD_DURATION_STD = 2 * 60    # Odchylenie standardowe czasu trwania chmury
LUX_DROP_FACTOR_MEAN = 0.6     # Średni spadek LUX podczas zachmurzenia (np. 0.6 = 60% spadku)
LUX_DROP_FACTOR_STD = 0.1
CCT_CLOUD_MEAN = 7000          # Średnia CCT podczas zachmurzenia (K)
CCT_CLOUD_STD = 500
CCT_SUN_MEAN = 5250            # Średnia CCT przy czystym niebie w południe
CCT_SUN_STD = 250
CCT_SUNRISE_SUNSET = 3500      # CCT podczas wschodu/zachodu

# Parametry czujników
MAX_LUX_NOON = 80000           # Maksymalne natężenie światła w południe przy czystym niebie
MIN_LUX_NIGHT = 5              # Minimalne natężenie światła w nocy
ALS_LUX_RATIO_MEAN = 1.0       # Średni stosunek ALS do LUX
ALS_LUX_RATIO_STD = 0.05
SPECTRAL_NOISE_FACTOR = 0.05   # Współczynnik szumu dla danych spektralnych
IR_FULL_RATIO_MEAN = 0.3       # Średni stosunek IR do Full dla TSL2591
IR_FULL_RATIO_STD = 0.05
SATELLITES_MEAN_DAY = 10       # Średnia liczba satelitów w dzień
SATELLITES_STD = 2
HDOP_MEAN = 1.5
HDOP_STD = 0.5
CONFIDENCE_DROP_CLOUD = 0.2    # Spadek pewności podczas zachmurzenia
CONFIDENCE_DROP_LOW_LIGHT = 0.1 # Spadek pewności przy niskim świetle

# --- Funkcje Pomocnicze ---

def get_sun_info(lat, lon, date, tz):
    """Pobiera informacje o wschodzie i zachodzie słońca."""
    loc = location.LocationInfo(LOCATION_CITY, LOCATION_REGION, tz, lat, lon)
    s = sun.sun(loc.observer, date=date, tzinfo=loc.timezone)
    return s['sunrise'], s['sunset'], s['noon']

def solar_intensity_factor(current_time, sunrise, sunset, noon):
    """Oblicza współczynnik intensywności słonecznej (0-1) w zależności od pory dnia."""
    if current_time < sunrise or current_time > sunset:
        return 0.0
    # Model sinusoidalny dla intensywności
    total_daylight_seconds = (sunset - sunrise).total_seconds()
    time_since_sunrise = (current_time - sunrise).total_seconds()
    factor = np.sin(np.pi * time_since_sunrise / total_daylight_seconds)
    return max(0.0, factor) # Upewnij się, że nie jest ujemny

def color_temperature_model(current_time, sunrise, sunset, noon, is_cloudy):
    """Modeluje temperaturę barwową w zależności od pory dnia i zachmurzenia."""
    if is_cloudy:
        return np.random.normal(CCT_CLOUD_MEAN, CCT_CLOUD_STD)

    if current_time < sunrise or current_time > sunset:
        # W nocy można zwrócić stałą niską wartość lub np. NaN
        return np.nan # lub np. 2000

    # Płynne przejście CCT
    time_to_noon = abs((current_time - noon).total_seconds())
    daylight_half_duration = (noon - sunrise).total_seconds()
    # Współczynnik (0 przy wschodzie/zachodzie, 1 w południe)
    noon_factor = 1.0 - min(1.0, time_to_noon / daylight_half_duration)

    # Interpolacja między CCT wschodu/zachodu a CCT południa
    cct = CCT_SUNRISE_SUNSET + (CCT_SUN_MEAN - CCT_SUNRISE_SUNSET) * noon_factor**2 # Używamy kwadratu dla szybszego wzrostu
    cct += np.random.normal(0, CCT_SUN_STD) # Dodajemy szum
    return max(1000, min(10000, cct)) # Ograniczamy zakres

def simulate_clouds(timestamps):
    """Symuluje okresy zachmurzenia."""
    cloud_status = pd.Series(False, index=timestamps)
    is_currently_cloudy = False
    cloud_end_time = timestamps[0] # Inicjalizacja

    for ts in timestamps:
        if ts >= cloud_end_time:
            is_currently_cloudy = False # Koniec poprzedniej chmury

        if not is_currently_cloudy:
            # Sprawdź, czy zaczyna się nowa chmura
            if np.random.rand() < CLOUD_COVER_PROBABILITY * (FREQUENCY_SECONDS / 60.0):
                duration = int(np.random.normal(CLOUD_DURATION_MEAN, CLOUD_DURATION_STD))
                duration = max(FREQUENCY_SECONDS, duration) # Minimalny czas trwania
                cloud_end_time = ts + timedelta(seconds=duration)
                is_currently_cloudy = True

        if is_currently_cloudy:
            cloud_status[ts] = True

    return cloud_status

# --- Główna Logika Symulacji ---

# Ustawienie strefy czasowej
tz = pytz.timezone(TIMEZONE)
start_time = tz.localize(datetime.strptime(START_TIME_STR, "%Y-%m-%d %H:%M:%S"))
end_time = tz.localize(datetime.strptime(END_TIME_STR, "%Y-%m-%d %H:%M:%S"))
date_obj = start_time.date()

# Pobranie informacji o słońcu
sunrise, sunset, noon = get_sun_info(LATITUDE, LONGITUDE, date_obj, tz)
print(f"Symulacja dla {DATE_STR} w {LOCATION_CITY}")
print(f"Wschód słońca: {sunrise.strftime('%H:%M:%S %Z')}")
print(f"Południe słoneczne: {noon.strftime('%H:%M:%S %Z')}")
print(f"Zachód słońca: {sunset.strftime('%H:%M:%S %Z')}")

# Generowanie timestampów
timestamps = pd.date_range(start=start_time, end=end_time, freq=f'{FREQUENCY_SECONDS}s', tz=TIMEZONE)
data = pd.DataFrame(index=timestamps)
data['Timestamp'] = data.index.strftime('%Y-%m-%d %H:%M:%S') # Format CSV

# Symulacja zachmurzenia
data['IsCloudy'] = simulate_clouds(data.index)

# Symulacja LUX i CCT
data['SolarFactor'] = data.index.map(lambda t: solar_intensity_factor(t, sunrise, sunset, noon))
data['BaseLUX'] = data['SolarFactor'] * MAX_LUX_NOON + np.random.normal(0, MIN_LUX_NIGHT, size=len(data))
data['BaseLUX'] = data['BaseLUX'].clip(lower=0) # LUX nie może być ujemny

data['CloudDropFactor'] = 1.0
data.loc[data['IsCloudy'], 'CloudDropFactor'] = np.random.normal(1.0 - LUX_DROP_FACTOR_MEAN, LUX_DROP_FACTOR_STD, size=data['IsCloudy'].sum()).clip(0.1, 1.0)

data['LUX'] = data['BaseLUX'] * data['CloudDropFactor'] + np.random.normal(0, 2, size=len(data)) # Dodajemy mały szum odczytu
data['LUX'] = data['LUX'].clip(lower=0).round(2)

data['ColorTemperature_K'] = data.apply(lambda row: color_temperature_model(row.name, sunrise, sunset, noon, row['IsCloudy']), axis=1)
data['ColorTemperature_K'] = data['ColorTemperature_K'].round(0)

# Symulacja pozostałych czujników
# ALS (SEN0611) - skorelowany z LUX
data['ALS'] = data['LUX'] * np.random.normal(ALS_LUX_RATIO_MEAN, ALS_LUX_RATIO_STD, size=len(data))
data['ALS'] = data['ALS'].clip(lower=0).round(2)

# TSL2591 - IR i Full (symulujemy na podstawie LUX)
# Zakładamy, że 'full' jest proporcjonalne do LUX, a 'ir' to część 'full'
# Te wartości są uint16, więc max 65535
# Skalujemy LUX do zakresu TSL2591 (bardzo uproszczone)
lux_to_full_scale = 60000 / MAX_LUX_NOON # Przybliżony współczynnik skalowania
data['Full'] = (data['LUX'] * lux_to_full_scale * np.random.normal(1, 0.1, size=len(data))).clip(0, 65535).astype(int)
data['IR'] = (data['Full'] * np.random.normal(IR_FULL_RATIO_MEAN, IR_FULL_RATIO_STD, size=len(data))).clip(0, 65535).astype(int)
# Upewniamy się, że IR <= Full
data['IR'] = data[['IR', 'Full']].min(axis=1)
# Symulujemy obliczoną luminancję (powinna być bliska 'LUX')
data['Luminance'] = data['LUX'] * np.random.normal(1, 0.02, size=len(data)) # Mały błąd obliczeniowy
data['Luminance'] = data['Luminance'].clip(lower=0).round(2)


# AS7262 - Spectral Values (bardzo uproszczona symulacja)
# Zakładamy, że suma wartości spektralnych jest proporcjonalna do LUX
# Rozkład spektralny zależy od CCT (bardzo zgrubnie)
spectral_sum_scale = 500 / MAX_LUX_NOON # Arbitralny współczynnik skalowania sumy spektralnej
data['SpectralSumTarget'] = data['LUX'] * spectral_sum_scale

# Definiujemy przybliżone profile spektralne dla różnych CCT
def get_spectral_profile(cct):
    if pd.isna(cct): return np.zeros(6)
    if cct < 4000: # Ciepłe światło
        profile = np.array([0.5, 0.8, 1.0, 1.0, 0.9, 0.7])
    elif cct < 6000: # Neutralne
        profile = np.array([0.7, 0.9, 1.0, 0.9, 0.8, 0.7])
    else: # Zimne
        profile = np.array([0.9, 1.0, 0.9, 0.8, 0.7, 0.6])
    return profile / profile.sum() # Normalizujemy

# Przekształcamy serię profili w tablicę numpy (N, 6)
spectral_profiles_array = np.stack(data['ColorTemperature_K'].apply(get_spectral_profile).values)
# Mnożymy przez docelową sumę spektralną
spectral_values = spectral_profiles_array * data['SpectralSumTarget'].values[:, np.newaxis]
# Dodajemy szum
# Obliczamy średnią dla każdego wiersza (timestampu) przed dodaniem szumu
mean_spectral_per_ts = spectral_values.mean(axis=1, keepdims=True)
# Dodajemy szum proporcjonalny do średniej dla danego timestampu
spectral_values += np.random.normal(0, mean_spectral_per_ts * SPECTRAL_NOISE_FACTOR, size=spectral_values.shape)
spectral_values = spectral_values.clip(min=0)

for i in range(6):
    data[f'Spectral_{i+1}'] = spectral_values[:, i].round(4)

# Arduino Timestamp (micros)
start_micros = np.uint64(start_time.timestamp() * 1_000_000)
data['ArduinoTimestamp'] = start_micros + np.arange(len(data)) * FREQUENCY_SECONDS * 1_000_000

# GPS Data
data['GPS_Valid'] = True # Zakładamy, że GPS ma fixa przez większość czasu
data['Latitude'] = LATITUDE + np.random.normal(0, 0.00001, size=len(data)) # Małe fluktuacje
data['Longitude'] = LONGITUDE + np.random.normal(0, 0.00001, size=len(data))
data['Altitude'] = ELEVATION + np.random.normal(0, 1, size=len(data))
data['Satellites'] = np.random.normal(SATELLITES_MEAN_DAY, SATELLITES_STD, size=len(data)).clip(4, 15).astype(int) # Min 4 satelity dla fixa
data['HDOP'] = np.random.normal(HDOP_MEAN, HDOP_STD, size=len(data)).clip(0.5, 5.0).round(2)
# Losowo ustawiamy GPS_Valid na False w nocy
night_mask = (data.index.hour < sunrise.hour) | (data.index.hour >= sunset.hour)
data.loc[night_mask & (np.random.rand(len(data)) < 0.1), 'GPS_Valid'] = False
data.loc[~data['GPS_Valid'], ['Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP']] = np.nan


# Validation (IsValid, Confidence) - uproszczone
data['IsValid'] = True
data['Confidence'] = 1.0
# Obniżamy pewność podczas zachmurzenia
data.loc[data['IsCloudy'], 'Confidence'] -= CONFIDENCE_DROP_CLOUD
# Obniżamy pewność przy bardzo niskim świetle (np. w nocy)
data.loc[data['LUX'] < MIN_LUX_NIGHT * 2, 'Confidence'] -= CONFIDENCE_DROP_LOW_LIGHT
# Losowo ustawiamy niektóre dane jako nieprawidłowe (np. 1% szansy)
invalid_mask = np.random.rand(len(data)) < 0.01
data.loc[invalid_mask, 'IsValid'] = False
data.loc[invalid_mask, 'Confidence'] = 0.0
data['Confidence'] = data['Confidence'].clip(0.0, 1.0).round(2)


# Wybór i kolejność kolumn do CSV
output_columns = [
    'Timestamp',
    'LUX', # Zmieniono nazwę z ALS na LUX zgodnie z głównym celem
    'ColorTemperature_K',
    'Spectral_1', 'Spectral_2', 'Spectral_3', 'Spectral_4', 'Spectral_5', 'Spectral_6',
    'Luminance', 'IR', 'Full', 'ALS', # Dodano ALS dla spójności z SEN0611
    'ArduinoTimestamp', 'IsValid', 'Confidence',
    'GPS_Valid', 'Latitude', 'Longitude', 'Altitude', 'Satellites', 'HDOP'
]
final_data = data[output_columns]

# Zapis do CSV
final_data.to_csv(OUTPUT_FILE, index=False)

print(f"\nSymulowane dane zostały zapisane do pliku: {OUTPUT_FILE}")
print(f"Liczba wygenerowanych rekordów: {len(final_data)}")
print("\nPrzykładowe dane:")
print(final_data.head())
print("...")
print(final_data.tail())