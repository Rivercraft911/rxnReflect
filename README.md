# RW4-12 Reaction Wheel Controller

A comprehensive Python-based control system for the **Rocket Lab / Sinclair Interplanetary RW4-12 reaction wheel**. This library provides a safe, robust, and easy-to-use interface for commanding and monitoring the reaction wheel, with full implementation of the Nanosatellite Protocol (NSP) as specified in the E400281 Software ICD.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Hardware](https://img.shields.io/badge/hardware-RW4--12-orange.svg)

## Features

- **Complete NSP Implementation**: Full Nanosatellite Protocol with SLIP framing and CRC-16-CCITT validation
- **Safety First**: Comprehensive error handling and safe operation modes
- **Rich Telemetry**: Read voltages, temperatures, speed, momentum, and more
- **Multiple Control Modes**: Support for IDLE, SPEED, TORQUE, and MOMENTUM control
- **Analysis Tools**: Built-in data collection and visualization for performance analysis
- **Comprehensive Testing**: Sequential test suite for safe validation
- **Easy Configuration**: Centralized config for quick setup

## Table of Contents

- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Testing Suite](#testing-suite)
- [Analysis Tools](#analysis-tools)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Safety Guidelines](#safety-guidelines)
- [Troubleshooting](#troubleshooting)

## Hardware Requirements

| Component | Specification | Notes |
|-----------|---------------|-------|
| **Reaction Wheel** | RW4-12 (Rocket Lab/Sinclair) | Firmware compatible with E400281 ICD |
| **Interface** | RS485 adapter | Waveshare RS485 HAT recommended |
| **Power Supply** | 28V DC, 2A+ | Must be stable and well-regulated |
| **Host Computer** | Raspberry Pi 4+ or equivalent | Python 3.9+ support required |
| **Cabling** | RS485 to Glenair connector | Custom harness required |

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/rw4-12-testing-control.git
cd rw4-12-testing-control
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Hardware Settings
Edit `rw_wheel/config.py` with your hardware configuration:
```python
SERIAL_PORT = "/dev/cu.usbserial-B00320NW"  # Your RS485 adapter
BAUD_RATE = 115200
WHEEL_ADDRESS = 0x20
HOST_ADDRESS = 0x11
```

## Quick Start

### Basic Usage
```python
from rw_wheel import ReactionWheel, config

# Connect to the wheel
with ReactionWheel(
    port=config.SERIAL_PORT,
    baud=config.BAUD_RATE,
    wheel_addr=config.WHEEL_ADDRESS,
    host_addr=config.HOST_ADDRESS
) as wheel:
    
    # Initialize and ping
    wheel.initialize_application()
    identity = wheel.ping()
    print(f"Connected to: {identity}")
    
    # Read telemetry
    voltage = wheel.read_vbus()
    speed = wheel.read_speed()
    print(f"Bus voltage: {voltage:.2f}V, Speed: {speed:.2f} rad/s")
    
    # Control the wheel
    wheel.set_speed_rpm(100)  # Spin at 100 RPM
    time.sleep(5)
    wheel.set_idle()          # Stop
```

## Testing Suite

**WARNING**: Always run tests in the specified order, especially on first use.

### Sequential Test Protocol

| Test | Command | Description | Safety Level |
|------|---------|-------------|--------------|
| **0** | `python tests/test_initial.py` | Initialize wheel to application mode | Safe |
| **1** | `python tests/test_ping.py` | Communication verification | Safe |
| **2** | `python tests/test_read_telemetry.py` | Read all telemetry points | Safe |
| **3** | `python tests/test_safe_spin.py` | Low-speed motion test (30 RPM) | Motion |
| **4** | `python tests/test_ramp.py` | Speed ramping test | Motion |
| **5** | `python tests/test_max_torque.py` | Maximum torque verification | High Power |

### Example Test Session
```bash
# Start with communication verification
python tests/test_initial.py
python tests/test_ping.py

# Verify telemetry readings
python tests/test_read_telemetry.py

# Motion tests (ensure wheel is secured!)
python tests/test_safe_spin.py
python tests/test_ramp.py
```

## Analysis Tools

The `analysis/` directory contains advanced testing and data collection tools:

### Torque Linearity Analysis
```bash
python analysis/test_torque_linearity.py
```
- Maps torque command vs. actual acceleration
- Generates interactive Plotly visualizations
- Exports data to CSV and HTML formats
- Identifies deadband and linearity characteristics

### Saturation & Power Profile
```bash
python analysis/test_saturation_and_power.py
```
- High-speed performance testing
- Power consumption analysis
- Real-time monitoring at 20Hz
- Safety limits enforcement

### Generated Outputs
- **CSV Data**: `torque_linearity_YYYYMMDD_HHMMSS.csv`
- **Interactive Plots**: `torque_linearity_YYYYMMDD_HHMMSS.html`
- **Log Files**: `wheel_test_log.txt`

## API Reference

### Core Classes

#### `ReactionWheel`
Main interface for wheel control and monitoring.

**Connection Management:**
```python
wheel = ReactionWheel(port, baud, wheel_addr, host_addr)
wheel.open()  # or use as context manager: with ReactionWheel(...) as wheel:
```

**Control Methods:**
```python
wheel.set_idle()                    # Stop wheel
wheel.set_speed_rpm(rpm)           # Speed control mode
wheel.set_torque(torque_nm)        # Torque control mode
wheel.initialize_application()      # Initialize firmware
```

**Telemetry Methods:**
```python
wheel.ping()                       # Communication test
wheel.read_vbus()                  # Bus voltage (V)
wheel.read_vcc()                   # 3.3V rail voltage (V)
wheel.read_speed()                 # Angular velocity (rad/s)
wheel.read_momentum()              # Angular momentum (N⋅m⋅s)
wheel.read_temperature(sensor_id)  # Temperature (°C)
wheel.read_inertia()              # Wheel inertia (kg⋅m²)
```

### Enumerations

#### `WheelMode`
- `IDLE = 0x00`: Wheel stopped
- `SPEED = 0x03`: Speed control mode
- `TORQUE = 0x12`: Torque control mode
- `MOMENTUM = 0x11`: Momentum control mode

#### `NSPCommand`
Low-level protocol commands (advanced users).

## Configuration

### Serial Configuration (`rw_wheel/config.py`)
```python
SERIAL_PORT = "/dev/cu.usbserial-B00320NW"  # Platform-specific
BAUD_RATE = 115200                          # Fixed by protocol
WHEEL_ADDRESS = 0x20                        # Wheel NSP address
HOST_ADDRESS = 0x11                         # Host NSP address
```

### Logging Configuration (`logging_config.py`)
```python
LOG_FILENAME = "wheel_test_log.txt"
# Logs: DEBUG level to file, INFO level to console
```

## Safety Guidelines

### Critical Safety Rules

1. **Secure Mounting**: Always ensure the wheel is securely mounted before any motion tests
2. **Power Supply**: Use a stable, well-regulated 28V supply
3. **Test Sequence**: Follow the sequential test protocol - never skip communication tests
4. **Emergency Stop**: Always be prepared to disconnect power immediately
5. **Speed Limits**: Respect the maximum safe speed of 5,252 RPM

### Electrical Safety

- Verify all connections before powering on
- Use proper grounding techniques
- Monitor supply voltage and current
- Check for loose connections regularly

### Operational Safety

- Start with low-speed tests (< 100 RPM)
- Monitor wheel temperature during operation
- Allow cool-down periods between high-power tests
- Keep emergency stop procedures readily available

## Troubleshooting

### Common Issues

| Problem | Symptoms | Solution |
|---------|----------|----------|
| **No Communication** | Ping fails, timeout errors | Check serial port, cable connections, power |
| **CRC Errors** | `WheelCrcError` exceptions | Verify cable integrity, check for interference |
| **Wheel Not Responding** | Commands ignored | Run initialization test, check power supply |
| **Speed Oscillation** | Unstable speed readings | Check mounting, reduce commanded speeds |

### Debug Steps

1. **Verify Hardware**:
   ```bash
   # Check if serial port exists
   ls /dev/cu.usbserial*  # macOS
   ls /dev/ttyUSB*        # Linux
   ```

2. **Test Communication**:
   ```bash
   python tests/test_ping.py
   ```

3. **Check Logs**:
   ```bash
   tail -f wheel_test_log.txt
   ```

4. **Verify Power Supply**:
   - Measure voltage at wheel connector
   - Check current draw during operation
   - Ensure supply can handle startup surges

### Error Codes

- `WheelError`: Base exception for all wheel-related errors
- `WheelCrcError`: Invalid CRC in received packet
- `WheelNackError`: Wheel rejected command (NACK response)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/rw4-12-testing-control/issues)
- **Documentation**: See inline code documentation
- **Hardware Support**: Consult E400281 RW4-12 Software ICD

---

**Disclaimer**: This software is provided as-is for educational and research purposes. Always follow proper safety procedures when working with high-speed rotating machinery. The authors are not responsible for any damage or injury resulting from the use of this software.
