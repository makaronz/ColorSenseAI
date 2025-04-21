# Dashboard Guide

## Overview

The ColorSenseAI Browser Dashboard is a comprehensive visualization and monitoring tool designed to provide real-time insights into sensor data, spectral analysis, and exposure measurements. The dashboard offers an intuitive interface for viewing and analyzing data from the ColorSenseAI system's three main sensors:

- **AS7262**: 6-channel spectral sensor
- **TSL2591**: High dynamic range luminance sensor
- **DFRobot SEN0611**: Factory-calibrated CCT and ALS meter
- **Optional GPS Module**: Location data (latitude, longitude, altitude, satellites, HDOP)

## Dashboard Features

### Main Features

1. **Real-time Data Visualization**
   - Live display of sensor readings
   - Interactive charts and graphs
   - Status indicators and gauges

2. **Detailed Calculation Explanations**
   - Step-by-step breakdown of color temperature calculations
   - Tint (Duv) computation process
   - Spectral analysis methodology

3. **Responsive Design**
   - Adapts to different screen sizes and devices
   - Optimized for desktop and tablet viewing
   - Collapsible sidebar for space efficiency

4. **Notification System**
   - Alert notifications for sensor anomalies
   - Status updates and system messages
   - User feedback indicators

### Dashboard Panels

The dashboard is organized into four main panels, each focusing on a specific aspect of the ColorSenseAI system:

#### 1. Main Dashboard Panel

- **Raw Data Section**
  - Direct sensor readings from all connected sensors
  - Timestamp information
  - Data validity indicators
  - System status overview

- **Status Cards**
  - Quick overview of key metrics
  - System health indicators
  - Sensor connection status
  - Data quality assessment

#### 2. Spectral Analysis Panel

- **Spectral Charts**
  - 6-channel spectral visualization (450nm, 500nm, 550nm, 570nm, 600nm, 650nm)
  - Relative intensity graphs
  - Wavelength distribution
  - Spectral power distribution

- **Color Calculations**
  - CIE color space coordinates
  - CCT (Correlated Color Temperature) calculation
  - Tint (Duv) measurement
  - Color rendering metrics

- **Calculation Explanations**
  - Detailed breakdown of spectral analysis methods
  - Color science formulas and their application
  - Step-by-step calculation process
  - Reference information

#### 3. Exposure Monitoring Panel

- **Exposure Indicators**
   - Luminance measurements (lux)
   - Dynamic range visualization
   - Exposure warnings and alerts
   - Ambient light sensing (ALS)
   - Comparative luminance analysis

- **Exposure Trends**
   - Historical exposure data
   - Time-based analysis
   - Pattern recognition
   - Environmental adaptation

- **Calculation Explanations**
   - Exposure measurement methodology
   - Light metering techniques
   - Dynamic range computation
   - Exposure value (EV) calculations

#### 4. Machine Learning Panel

- **ML Feature Utilization**
   - Active ML features display
   - Feature importance visualization
   - Model confidence indicators
   - Real-time prediction display

- **Model Performance**
   - Accuracy metrics
   - Loss visualization
   - Version comparison
   - Training progress

- **Data Processing Visualization**
   - Feature extraction illustration
   - Data transformation flow
   - Decision process visualization
   - Confidence scoring

## Dashboard Technical Implementation

### 1. Technology Stack

- **Frontend Technologies**
   - HTML5 for structure
   - CSS3 for styling (responsive design)
   - JavaScript for interactivity
   - Chart.js for data visualization

- **Data Handling**
   - JSON data format
   - Local data processing
   - Simulated sensor data for demonstration
   - Real-time updates via polling

### 2. Dashboard Architecture

- **Modular Design**
   - Component-based structure
   - Separation of concerns
   - Event-driven communication
   - Responsive layout system

- **Data Flow**
   - Sensor data acquisition
   - Data transformation and processing
   - Visualization rendering
   - User interaction handling

### 3. Local Operation

The dashboard is designed to operate locally without requiring a backend connection:
   - Uses sample data that simulates Arduino sensor readings
   - Performs all calculations and transformations in the browser
   - Stores temporary data in browser memory
   - Can be run from a local file system or simple web server

## Getting Started

### 1. Launching the Dashboard

1. Navigate to the dashboard directory: `cd dashboard`
2. Start a local web server: `python -m http.server 8000` (or any other simple web server)
3. Open a browser and navigate to: `http://localhost:8000`

### 2. Dashboard Navigation

- Use the sidebar menu to switch between different panels
- Collapse the sidebar using the menu toggle button for more screen space
- Access notifications through the bell icon in the top navigation bar
- Use time filter buttons to change the time range for data visualization

### 3. Interpreting the Data

- **Raw Data Section**: Shows direct sensor readings in their original format
- **Charts and Graphs**: Visualize trends and patterns in the data
- **Status Cards**: Provide quick overview of key metrics and system status
- **Calculation Explanations**: Help understand how values are derived

## Customization Options

- **Time Ranges**: Switch between day, week, month, and year views
- **Chart Types**: Toggle between different visualization formats
- **Display Options**: Show/hide specific data series or indicators
- **Layout Adjustments**: Resize panels or change column layouts

## Troubleshooting

- **Data Not Updating**: Check if the simulation is running properly
- **Charts Not Rendering**: Verify browser compatibility and JavaScript errors
- **Layout Issues**: Test on different screen sizes and browsers
- **Performance Problems**: Reduce data points or simplify visualizations
