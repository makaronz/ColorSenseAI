#include <Wire.h>
#include <Adafruit_AS726x.h>
#include <Adafruit_TSL2591.h>
#include <DFRobot_CCT_ALS_Meter.h>
#include <EEPROM.h>
#include <CircularBuffer.h>

// Sensor objects
Adafruit_AS726x as7262;
Adafruit_TSL2591 tsl = Adafruit_TSL2591(2591);
DFRobot_CCT_ALS_Meter sen0611;

// Configuration
const unsigned long MEASUREMENT_INTERVAL = 1000; // ms
const bool DEBUG_MODE = true;
const int TRIGGER_PIN = 7; // Pin do sprzętowego wyzwalania pomiarów
const int BUFFER_SIZE = 5; // Rozmiar bufora dla każdego czujnika

// Data structures
struct SensorData {
  // AS7262 data
  float spectralValues[AS726x_NUM_CHANNELS];
  
  // TSL2591 data
  float luminance;
  uint16_t ir;
  uint16_t full;
  
  // DFRobot SEN0611 data
  float cct;
  float als;
  
  // Timestamp
  unsigned long timestamp;
  // Validation
  bool isValid;
  float confidence;
};

// Global variables
SensorData currentData;
unsigned long lastMeasurement = 0;
CircularBuffer<SensorData, BUFFER_SIZE> dataBuffer;
volatile bool triggerReady = false;
void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  if (DEBUG_MODE) {
    Serial.println("ColorSense Initialization");
  }

  // Initialize I2C
  Wire.begin();
  
  // Initialize hardware trigger
  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(TRIGGER_PIN), triggerISR, FALLING);
  
  // Initialize sensors
  initializeSensors();
  
  // Load calibration data
  loadCalibration();
  
  if (DEBUG_MODE) {
    Serial.println("System ready");
  }
}

// Interrupt Service Routine dla sprzętowego wyzwalania
void triggerISR() {
  triggerReady = true;
}
}
void loop() {
  unsigned long currentTime = millis();
  
  // Sprawdź czy jest wyzwalanie sprzętowe lub upłynął interwał czasowy
  if (triggerReady || (currentTime - lastMeasurement >= MEASUREMENT_INTERVAL)) {
    triggerReady = false;
    
    // Synchronizowane odczytywanie wszystkich czujników
    readSensors();
    
    // Process and validate data
    processData();
    
    // Dodaj dane do bufora
    dataBuffer.push(currentData);
    
    // Send data
    sendData();
    
    lastMeasurement = currentTime;
  }
  
  // Handle any incoming commands
  handleCommands();
}
}

void initializeSensors() {
  // Initialize AS7262
  if (!as7262.begin()) {
    Serial.println("AS7262 initialization failed!");
    while (1);
  }
  as7262.setMeasurementMode(AS726X_MEASUREMENT_MODE_6CHAN_CONTINUOUS);
  as7262.setGain(AS726X_GAIN_16X);
  as7262.setIntegrationTime(50);
  
  // Initialize TSL2591
  if (!tsl.begin()) {
    Serial.println("TSL2591 initialization failed!");
    while (1);
  }
  tsl.setGain(TSL2591_GAIN_MED);
  tsl.setTiming(TSL2591_INTEGRATIONTIME_300MS);
  
  // Initialize DFRobot SEN0611
  if (!sen0611.begin()) {
    Serial.println("SEN0611 initialization failed!");
    while (1);
  }
}

void readSensors() {
  unsigned long startTime = micros();
  
  // Przygotuj wszystkie czujniki do pomiaru
  as7262.startMeasurement();
  tsl.enable(true);
  
  // Synchronizowane odczytywanie danych
  // Read AS7262
  while (!as7262.dataReady()) {
    // Krótkie opóźnienie zamiast blokującego oczekiwania
    delayMicroseconds(100);
  }
  as7262.readCalibratedValues(currentData.spectralValues);
  
  // Read TSL2591
  uint32_t lum = tsl.getFullLuminosity();
  currentData.ir = lum >> 16;
  currentData.full = lum & 0xFFFF;
  currentData.luminance = tsl.calculateLux(currentData.full, currentData.ir);
  
  // Read DFRobot SEN0611
  currentData.cct = sen0611.getCCT();
  currentData.als = sen0611.getALS();
  
  // Update timestamp z precyzją mikrosekundową
  currentData.timestamp = micros();
  
  // Domyślnie dane są ważne
  currentData.isValid = true;
  currentData.confidence = 1.0;
  
  // Sprawdź czas odczytu dla walidacji czasowej
  unsigned long readTime = micros() - startTime;
  if (readTime > 50000) { // Jeśli odczyt trwał dłużej niż 50ms
    currentData.confidence = 0.5; // Zmniejsz pewność danych
    if (DEBUG_MODE) {
      Serial.print("Warning: Sensor read time exceeded threshold: ");
      Serial.println(readTime);
    }
  }
}
void processData() {
  // Validate sensor readings
  validateData();
  
  // Calculate additional metrics
  calculateMetrics();
}

void validateData() {
  // Sprawdź wartości poza zakresem
  if (currentData.luminance < 0 || currentData.luminance > 100000) {
    currentData.isValid = false;
    if (DEBUG_MODE) {
      Serial.println("Error: Luminance out of range");
    }
  }
  
  // Sprawdź wartości CCT
  if (currentData.cct < 1000 || currentData.cct > 10000) {
    currentData.confidence *= 0.8;
    if (DEBUG_MODE) {
      Serial.println("Warning: CCT value suspicious");
    }
  }
  
  // Porównaj odczyty między czujnikami
  float alsRatio = currentData.als / currentData.luminance;
  if (alsRatio < 0.5 || alsRatio > 2.0) {
    currentData.confidence *= 0.9;
    if (DEBUG_MODE) {
      Serial.println("Warning: ALS and luminance values differ significantly");
    }
  }
  
  // Sprawdź spójność spektralną
  float spectralSum = 0;
  for (int i = 0; i < AS726x_NUM_CHANNELS; i++) {
    spectralSum += currentData.spectralValues[i];
  }
  if (spectralSum < 0.1 && currentData.luminance > 10) {
    currentData.confidence *= 0.7;
    if (DEBUG_MODE) {
      Serial.println("Warning: Spectral values inconsistent with luminance");
    }
  }
}

void calculateMetrics() {
  // Calculate color coordinates
  // Calculate tint (Duv)
  // Implement sensor fusion algorithms
}
}
void sendData() {
  // Create JSON document
  StaticJsonDocument<768> doc;
  
  // Add spectral data
  JsonArray spectral = doc.createNestedArray("spectral");
  for (int i = 0; i < AS726x_NUM_CHANNELS; i++) {
    spectral.add(currentData.spectralValues[i]);
  }
  
  // Add luminance data
  doc["luminance"] = currentData.luminance;
  doc["ir"] = currentData.ir;
  doc["full"] = currentData.full;
  
  // Add CCT and ALS data
  doc["cct"] = currentData.cct;
  doc["als"] = currentData.als;
  
  // Add timestamp
  doc["timestamp"] = currentData.timestamp;
  
  // Add validation data
  doc["valid"] = currentData.isValid;
  doc["confidence"] = currentData.confidence;
  
  // Add buffer statistics
  if (!dataBuffer.isEmpty()) {
    JsonObject stats = doc.createNestedObject("stats");
    
    // Oblicz średnią i odchylenie standardowe dla CCT
    float cctSum = 0, cctSqSum = 0;
    int validCount = 0;
    
    for (int i = 0; i < dataBuffer.size(); i++) {
      if (dataBuffer[i].isValid) {
        cctSum += dataBuffer[i].cct;
        cctSqSum += dataBuffer[i].cct * dataBuffer[i].cct;
        validCount++;
      }
    }
    
    if (validCount > 0) {
      float cctMean = cctSum / validCount;
      float cctVar = (cctSqSum / validCount) - (cctMean * cctMean);
      float cctStdDev = sqrt(cctVar > 0 ? cctVar : 0);
      
      stats["cct_mean"] = cctMean;
      stats["cct_stddev"] = cctStdDev;
      stats["valid_samples"] = validCount;
    }
  }
  
  // Serialize and send
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}
}

void handleCommands() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "CALIBRATE") {
      calibrateSensors();
    } else if (command == "STATUS") {
      sendStatus();
    }
  }
}

void calibrateSensors() {
  // Implement calibration routine
  // Store calibration data in EEPROM
}

void sendStatus() {
  // Send system status information
}

void loadCalibration() {
  // Load calibration data from EEPROM
} 