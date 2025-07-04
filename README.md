# Rocket Lab RW4-12 Reaction Wheel Controller

This repository contains a Python-based controller for the Rocket Lab / Sinclair Interplanetary RW4-12 reaction wheel. It provides a safe and modular framework for sending commands and running tests from a Raspberry Pi with an RS485 HAT.

The implementation is based on the **E400281 RW4-12 Software ICD** document.

## Features

*   Full implementation of the Nanosatellite Protocol (NSP) layer, including SLIP framing and CRC-16-CCITT validation.
*   A high-level, easy-to-use Python class (`ReactionWheel`) to abstract away complex protocol details.
*   A set of safe, sequential test scripts for verifying communication and functionality.
*   Centralized configuration for easy setup.

## Hardware Requirements

*   Waveshare RS485 adapter (or equivalent)
*   A stable power supply (28V DC recommended)
*   Cabling to connect RS485 interface to the wheel's Glenair connector.


## How to Use

**IMPORTANT:** Always follow the test sequence in order, especially the first time, to ensure safety and prevent damage to the wheel.

1.  **Configure:**
    Open the `config.py` file and verify that `SERIAL_PORT`, `WHEEL_ADDRESS`, and `HOST_ADDRESS` are correct for your setup.

2.  **Run the Tests:**
    Execute the test scripts from the `tests/` directory.

    *   **Test 1: Ping (Communication Check)**
        This is the most important first step. It does not move the motor.
        ```bash
        python tests/test_ping.py
        ```
    *   **Test 2: Initialize Wheel**
        This test initializes the Wheel to Application Mode.
        ```bash
        python test_initial.py
        ```
        
    *   **Test 3: Read Telemetry**
        This test reads the bus voltage from the wheel.
        ```bash
        python tests/test_read_telemetry.py
        ```

    *   **Test 4: Safe Spin**
        **WARNING:** This test will move the motor. It spins the wheel at a very low speed and then commands it to stop.
        ```bash
        python tests/test_safe_spin.py
        ```
