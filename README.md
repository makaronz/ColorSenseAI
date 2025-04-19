# ColorSense

Professional color temperature and exposure measurement system with advanced machine learning capabilities.

## Overview

ColorSense is a sophisticated measurement system that combines three different sensors to provide comprehensive color and light analysis:

- **AS7262**: 6-channel spectral sensor for detailed color analysis
- **TSL2591**: High dynamic range luminance sensor
- **DFRobot SEN0611**: Factory-calibrated CCT and ALS meter

## Features

### Core Features
- **Color Temperature Analysis**
  - Direct CCT measurement (2700-6500K)
  - Spectral analysis for extended range
  - Tint (Duv) calculation
  - Color coordinates (CIE XYZ, xy, u'v')

- **Exposure Monitoring**
  - High dynamic range luminance measurement
  - Multiple sensor validation
  - Configurable integration times
  - Automatic gain adjustment

- **Data Processing**
  - Real-time sensor fusion
  - Advanced color calculations
  - Data validation and error handling
  - Configurable output formats

- **Browser Dashboard**
  - Real-time data visualization
  - Spectral analysis charts
  - Exposure monitoring indicators
  - Detailed calculation explanations
  - Responsive design for various devices

### Machine Learning Features
- **Color Correction**
  - Neural network-based color temperature prediction
  - Pattern recognition for lighting conditions
  - Adaptive calibration algorithms
  - Real-time optimization

- **Anomaly Detection**
  - Automated error detection
  - Pattern-based fault prediction
  - Self-diagnostic capabilities
  - Predictive maintenance

- **Sensor Optimization**
  - Dynamic integration time adjustment
  - Automatic gain control
  - Power consumption optimization
  - Performance tuning

- **Adaptive Calibration**
  - Temperature compensation
  - Aging compensation
  - Environmental adaptation
  - Continuous learning

## Project Structure

```
ColorSense/
├── src/                # Source code
│   ├── arduino/        # Arduino firmware
│   ├── api/            # API endpoints
│   ├── database/       # Database management
│   ├── models/         # Data models
│   ├── services/       # Business logic
│   │   └── ml/         # Machine learning services
│   └── utils/          # Utility functions
├── dashboard/          # Browser dashboard
│   ├── css/            # Dashboard styles
│   ├── js/             # Dashboard scripts
│   └── assets/         # Dashboard assets
├── docs/               # Documentation
├── config/             # Configuration files
│   └── ml_features.json # ML feature configuration
├── models/             # Trained ML models
├── simulators/         # Sensor simulators
└── tests/              # Test files
```

## Machine Learning Configuration

The system includes several machine learning features that can be enabled or disabled independently:

```json
{
    "color_correction": false,
    "anomaly_detection": false,
    "sensor_optimization": false,
    "adaptive_calibration": false,
    "self_learning": false,
    "failure_prediction": false,
    "power_optimization": false
}
```

To enable or disable features, use the MLManager:

```python
from services.ml.ml_manager import MLManager

ml_manager = MLManager()
ml_manager.enable_feature("color_correction")
ml_manager.disable_feature("anomaly_detection")
```

## Hardware Requirements

- Arduino UNO or compatible
- AS7262 Spectral Sensor
- TSL2591 Luminance Sensor
- DFRobot SEN0611 CCT & ALS Meter
- I2C level shifter (if needed)
- Power supply (5V)

## Software Requirements

- Python 3.8+
- TensorFlow 2.x
- scikit-learn
- NumPy
- Pandas
- Arduino IDE

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure the system in `config/`
4. Configure ML features in `config/ml_features.json`
5. Upload Arduino firmware: `src/arduino/main.ino`
6. Run the API server: `python src/main.py`
7. Open the dashboard: `dashboard/index.html`

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Hardware Setup](docs/hardware_setup.md)
- [Software Architecture](docs/software_architecture.md)
- [Technical Overview](docs/technical_overview.md)
- [Feature Extensions](docs/feature_extensions.md)
- [API Documentation](docs/api.md)
- [Calibration Guide](docs/calibration.md)
- [Machine Learning Guide](docs/ml_guide.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Dashboard Guide](docs/dashboard_guide.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details 