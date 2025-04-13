# Moduł GPS w projekcie ColorSense

## Wprowadzenie

Moduł GPS NEO-6M został dodany do projektu ColorSense, aby umożliwić geotagowanie pomiarów kolorów i ekspozycji. Dzięki temu możliwe jest powiązanie danych pomiarowych z konkretną lokalizacją geograficzną, co jest szczególnie przydatne w zastosowaniach terenowych, takich jak fotografia krajobrazowa, filmowanie w plenerze czy pomiary środowiskowe.

## Specyfikacja modułu GPS NEO-6M

- **Chipset**: u-blox NEO-6M
- **Częstotliwość odświeżania**: 5Hz (maksymalnie)
- **Czułość śledzenia**: -161 dBm
- **Dokładność pozycji**: 2.5m CEP (Circular Error Probable)
- **Czas do pierwszego ustalenia pozycji (TTFF)**:
  - Cold start: 27s
  - Warm start: 27s
  - Hot start: 1s
- **Interfejs**: UART (TTL)
- **Prędkość transmisji**: 9600 baud (domyślnie)
- **Napięcie zasilania**: 3.3V - 5V
- **Antena**: Ceramiczna, aktywna
- **Format danych**: NMEA 0183

## Podłączenie modułu GPS do Arduino

Moduł GPS NEO-6M komunikuje się z Arduino za pomocą interfejsu UART. W projekcie ColorSense wykorzystujemy bibliotekę SoftwareSerial do utworzenia wirtualnego portu szeregowego na pinach cyfrowych, ponieważ sprzętowy port szeregowy jest używany do komunikacji z komputerem.

### Schemat podłączenia

| Moduł GPS NEO-6M | Arduino UNO |
|------------------|-------------|
| VCC              | 5V          |
| GND              | GND         |
| TX               | Pin 10 (RX) |
| RX               | Pin 11 (TX) |

### Uwagi dotyczące podłączenia

1. **Zasilanie**: Moduł GPS może być zasilany napięciem 3.3V lub 5V. W przypadku Arduino UNO, które pracuje na napięciu 5V, podłączamy moduł do pinu 5V.
2. **Poziomy logiczne**: Moduł GPS pracuje na poziomach logicznych 3.3V, ale większość modułów NEO-6M dostępnych na rynku posiada konwerter poziomów logicznych, dzięki czemu można je bezpośrednio podłączyć do Arduino pracującego na 5V.
3. **Antena**: Upewnij się, że antena GPS jest umieszczona w miejscu z dobrą widocznością nieba. W pomieszczeniach sygnał GPS może być słaby lub niedostępny.

## Implementacja w oprogramowaniu

### Wymagane biblioteki

Do obsługi modułu GPS w projekcie ColorSense wykorzystujemy bibliotekę TinyGPS++, która ułatwia parsowanie danych NMEA i udostępnia wygodne API do odczytu informacji o pozycji, wysokości, czasie, itp.

```cpp
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
```

### Inicjalizacja

```cpp
// Utworzenie obiektów
TinyGPSPlus gps;
SoftwareSerial gpsSerial(10, 11); // RX, TX

// W funkcji setup()
void setup() {
  // ...
  gpsSerial.begin(9600); // Inicjalizacja komunikacji z modułem GPS
  // ...
}
```

### Odczyt danych GPS

Dane GPS są odczytywane w tle, aby nie blokować głównej pętli programu. Za każdym razem, gdy dostępny jest nowy bajt danych z modułu GPS, jest on przekazywany do biblioteki TinyGPS++ do przetworzenia.

```cpp
void readGPS() {
  while (gpsSerial.available() > 0) {
    if (gps.encode(gpsSerial.read())) {
      // Nowe dane GPS są dostępne
      updateGPSData();
    }
  }
}

void updateGPSData() {
  if (gps.location.isValid()) {
    // Aktualizacja danych o pozycji
    currentData.latitude = gps.location.lat();
    currentData.longitude = gps.location.lng();
  }
  
  if (gps.altitude.isValid()) {
    // Aktualizacja danych o wysokości
    currentData.altitude = gps.altitude.meters();
  }
  
  // ...
}
```

### Integracja z danymi czujników

Dane GPS są integrowane z danymi z czujników kolorów i ekspozycji, tworząc kompletny rekord pomiarowy. Dane te są następnie wysyłane w formacie JSON przez port szeregowy.

```cpp
void sendData() {
  // ...
  
  // Dodanie danych GPS do dokumentu JSON
  JsonObject gpsData = doc.createNestedObject("gps");
  gpsData["valid"] = gps.location.isValid();
  if (gps.location.isValid()) {
    gpsData["latitude"] = currentData.latitude;
    gpsData["longitude"] = currentData.longitude;
    gpsData["altitude"] = currentData.altitude;
    gpsData["satellites"] = currentData.satellites;
    gpsData["hdop"] = currentData.hdop;
  }
  
  // ...
}
```

## Diagnostyka i rozwiązywanie problemów

### Sprawdzanie statusu GPS

Dodano nową komendę "GPS" do interfejsu poleceń, która zwraca szczegółowe informacje o statusie modułu GPS:

```cpp
void sendGPSStatus() {
  StaticJsonDocument<256> doc;
  doc["valid"] = gps.location.isValid();
  doc["satellites"] = gps.satellites.value();
  doc["hdop"] = gps.hdop.hdop();
  doc["location_valid"] = gps.location.isValid();
  doc["altitude_valid"] = gps.altitude.isValid();
  doc["course_valid"] = gps.course.isValid();
  doc["speed_valid"] = gps.speed.isValid();
  doc["chars_processed"] = gps.charsProcessed();
  doc["sentences_with_fix"] = gps.sentencesWithFix();
  doc["failed_checksums"] = gps.failedChecksum();
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}
```

### Typowe problemy i rozwiązania

1. **Brak danych GPS**
   - Sprawdź podłączenie modułu GPS do Arduino
   - Upewnij się, że antena GPS ma dobrą widoczność nieba
   - Sprawdź, czy dioda LED na module GPS miga (wskazuje na odbiór sygnału)
   - Zweryfikuj, czy prędkość transmisji (baud rate) jest ustawiona poprawnie

2. **Nieprawidłowe dane pozycji**
   - Poczekaj na ustalenie pozycji (może to zająć kilka minut po pierwszym uruchomieniu)
   - Sprawdź wartość HDOP (Horizontal Dilution of Precision) - niższe wartości oznaczają lepszą dokładność
   - Upewnij się, że antena GPS nie jest zasłonięta metalowymi przedmiotami

3. **Problemy z zasilaniem**
   - Moduł GPS może wymagać znacznego prądu, szczególnie podczas wyszukiwania satelitów
   - Jeśli używasz zasilania z USB, upewnij się, że port USB może dostarczyć wystarczający prąd
   - Rozważ użycie zewnętrznego zasilacza dla Arduino i modułu GPS

## Zastosowania danych GPS w projekcie ColorSense

### Geotagowanie pomiarów

Dane GPS umożliwiają geotagowanie pomiarów kolorów i ekspozycji, co pozwala na:
- Mapowanie warunków oświetleniowych w różnych lokalizacjach
- Śledzenie zmian kolorów i ekspozycji w zależności od lokalizacji
- Tworzenie map cieplnych dla różnych parametrów (CCT, luminancja, itp.)

### Korelacja z danymi środowiskowymi

Dane GPS mogą być wykorzystane do korelacji pomiarów z danymi środowiskowymi, takimi jak:
- Warunki pogodowe w danej lokalizacji
- Wysokość nad poziomem morza
- Pora dnia i roku (na podstawie lokalizacji)

### Automatyczna konfiguracja

Dane GPS mogą być wykorzystane do automatycznej konfiguracji urządzenia na podstawie lokalizacji:
- Dostosowanie kalibracji do lokalnych warunków oświetleniowych
- Automatyczne przełączanie między trybami pracy (np. dzień/noc)
- Optymalizacja parametrów pomiarowych na podstawie lokalizacji

## Rozszerzenia i przyszłe ulepszenia

### Zapisywanie tras

Implementacja zapisywania tras (track logging) umożliwiłaby śledzenie ścieżki pomiarowej i tworzenie map z danymi pomiarowymi.

### Integracja z mapami

Integracja z mapami (np. Google Maps, OpenStreetMap) umożliwiłaby wizualizację danych pomiarowych na mapie w czasie rzeczywistym.

### Geofencing

Implementacja geofencingu umożliwiłaby automatyczne uruchamianie pomiarów po wejściu w określony obszar geograficzny.

### Synchronizacja czasu

Wykorzystanie danych czasowych z GPS do synchronizacji zegara urządzenia, co zapewniłoby dokładne znaczniki czasowe dla pomiarów.

## Wymagania sprzętowe i programowe

### Sprzęt

- Moduł GPS NEO-6M
- Antena GPS (dołączona do modułu)
- Przewody połączeniowe
- Arduino UNO lub kompatybilny

### Oprogramowanie

- Biblioteka TinyGPS++ (https://github.com/mikalhart/TinyGPSPlus)
- Biblioteka SoftwareSerial (wbudowana w Arduino IDE)
- Biblioteka ArduinoJson (https://arduinojson.org/)

## Podsumowanie

Dodanie modułu GPS do projektu ColorSense znacząco rozszerza możliwości urządzenia, umożliwiając geotagowanie pomiarów i korelację danych z lokalizacją geograficzną. Moduł GPS NEO-6M jest łatwy w integracji z Arduino i oferuje dobrą dokładność pozycjonowania przy niskim koszcie.

Implementacja w oprogramowaniu jest zoptymalizowana pod kątem niskiego zużycia zasobów i nie blokuje głównej pętli programu, co zapewnia płynne działanie urządzenia nawet podczas odczytu danych GPS.