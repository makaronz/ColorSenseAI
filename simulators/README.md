# Arduino Simulator for ColorSense Project

This simulator allows testing ColorSense software without the need for physical hardware. It simulates an Arduino microcontroller with connected sensors and a GPS module.

## Simulated Sensors

The simulator includes the following sensors:

1. **AS7262** - 6-channel spectral sensor
   - Simulates readings for 6 wavelengths: 450nm, 500nm, 550nm, 570nm, 600nm, 650nm
   - Takes into account the influence of time of day and weather conditions on readings
   - Simulates sensor temperature

2. **TSL2591** - High Dynamic Range Luminance Sensor
   - Simulates luminance readings (lux)
   - Simulates IR and full spectrum values
   - Takes into account time of day and weather conditions

3. **DFRobot SEN0611** - CCT and ALS Meter
   - Simulates Color Temperature readings (CCT)
   - Simulates Ambient Light Sensor readings (ALS)
   - Takes into account time of day and weather conditions

4. **NEO-6M** - GPS Module
   - Simulates geographic position readings
   - Simulates altitude, number of satellites, HDOP data
   - Generates data in NMEA-compatible format

## Simulator Features

- Simulation of sensor readings at specified time and location
- Simulation of various weather conditions (sunny, cloudy, rainy, foggy, night)
- TCP server for transmitting data to client applications
- Realistic simulation of sensor noise and drift
- Simulation of daily changes (time-of-day dependency)

## Requirements

- Python 3.6 or newer
- Standard Python libraries (no additional packages required)

## Installation

No special installation is required. Simply clone the repository and run the script.

## Usage

### Basic Launch

```bash
python arduino_simulator.py
```

By default, the simulator will generate data for a cloudy day in Warsaw city center (March 1, 2023, 17:30).

### Configuration Options

```bash
python arduino_simulator.py --help
```

Available options:

- `--date DATE` - Simulation date (format: YYYY-MM-DD)
- `--time TIME` - Simulation time (format: HH:MM:SS)
- `--lat LAT` - Latitude
- `--lon LON` - Longitude
- `--weather WEATHER` - Weather conditions (sunny, cloudy, rainy, foggy, night)
- `--interval INTERVAL` - Data reading interval in seconds
- `--host HOST` - TCP server host address
- `--port PORT` - TCP server port
- `--no-server` - Don't start TCP server

### Examples

Simulating a sunny day in Krakow:

```bash
python arduino_simulator.py --weather sunny --lat 50.0647 --lon 19.9450
```

Simulating a rainy evening with readings every 2 seconds:

```bash
python arduino_simulator.py --weather rainy --time 20:00:00 --interval 2.0
```

## Connecting to the Simulator

The simulator runs a TCP server on port 8765 (by default). You can connect to it using any TCP client, e.g., telnet:

```bash
telnet localhost 8765
```

Data is transmitted in JSON format, with each reading on a separate line.

## Data Format

Example JSON data format:

```json
{
  "timestamp": "2023-03-01T17:30:00",
  "as7262": {
    "450nm": 0.42,
    "500nm": 0.51,
    "550nm": 0.62,
    "570nm": 0.57,
    "600nm": 0.48,
    "650nm": 0.43,
    "temperature": 27.5
  },
  "tsl2591": {
    "lux": 4850.2,
    "ir": 1455,
    "full": 6305
  },
  "sen0611": {
    "cct": 6580.5,
    "als": 4320.8
  },
  "gps": {
    "latitude": 52.2297,
    "longitude": 21.0122,
    "altitude": 110.5,
    "speed": 0.0,
    "satellites": 9,
    "hdop": 1.2,
    "time": "173000.00",
    "date": "010323",
    "fix": 1
  },
  "ambient_temperature": 4.2
}
```

## Integration with ColorSense Project

The simulator can be easily integrated with the main ColorSense project, replacing real Arduino readings with simulator data. To do this:

1. Launch the simulator with appropriate parameters
2. Configure the ColorSense application to connect to the simulator's TCP server
3. Process JSON data received from the simulator in the same way as data from a real Arduino

## Extending the Simulator

The simulator can be easily extended with additional features:

- Adding new sensors
- Implementing more advanced simulation models
- Adding error and failure simulation
- Implementing user interface

## Known Limitations

- The simulator doesn't exactly reproduce real sensor characteristics
- Simulated data is simplified and may not reflect all nuances of real measurements
- The simulator doesn't account for all environmental factors affecting sensor readings

## License

This simulator is part of the ColorSense project and is subject to the same license.