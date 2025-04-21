# ColorSenseAI

AI-powered color analysis and manipulation tool with IoT integration capabilities.

## Overview

ColorSenseAI is an innovative solution that combines artificial intelligence with IoT technology for advanced color analysis and real-time data processing. The system utilizes Arduino-based hardware with Wi-Fi HaLow and GSM connectivity for reliable data transmission.

### Key Features

- Advanced color analysis using AI
- Real-time data processing
- Dual connectivity options:
  - Wi-Fi HaLow for long-range, low-power wireless communication
  - GSM module for backup cellular connectivity
- Robust hardware implementation using Arduino

## Hardware Requirements

- Arduino (compatible board)
- Wi-Fi HaLow module
- GSM module (backup connectivity)
- Color sensors
- Power supply unit

## Software Requirements

- Python 3.13+
- Poetry for dependency management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ColorSenseAI.git
cd ColorSenseAI
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Activate the virtual environment:
```bash
poetry shell
```

## Hardware Setup

Detailed hardware setup instructions can be found in `docs/hardware_setup.md`.

## Development Roadmap

1. Current Phase:
   - Software implementation and testing
   - AI model development and optimization

2. Next Phase:
   - Arduino hardware integration
   - Wi-Fi HaLow module implementation
   - GSM module backup system setup
   - End-to-end testing and optimization

## Usage

[Add usage instructions here]

## Development

1. Install development dependencies:
```bash
poetry install --with dev
```

2. Run tests:
```bash
poetry run pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 