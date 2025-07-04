import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
setup_logging()

from rw_wheel import ReactionWheel
import rw_wheel.config as config

print("--- Test 2: Read Telemetry ---")
print("This script will attempt to read all available telemetry points from the wheel,")
print("including voltages, speed, momentum, and temperatures.\n")

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        print("\nAttempting to read all available telemetry points...")
        time.sleep(0.1)

        # --- Read Core Telemetry ---
        voltage = wheel.read_vbus()
        vcc = wheel.read_vcc()
        speed = wheel.read_speed()
        momentum = wheel.read_momentum()
        
        # --- Read Temperature Sensors ---
        temperatures = []
        for i in range(4):
            temp = wheel.read_temperature(i)
            temperatures.append(temp)
            time.sleep(0.1) 
        
        print("\n--- Telemetry Readout SUCCESS ---")
        
        print("\n[ Electrical ]")
        print(f"  Bus Voltage (VBUS):    {voltage:.2f} V")
        print(f"  3.3V Rail (VCC):       {vcc:.2f} V")
        
        print("\n[ Mechanical ]")
        print(f"  Wheel Speed:           {speed:.2f} Rad/s")
        print(f"  Wheel Momentum:        {momentum:.3f} N·m·s")
        
        print("\n[ Thermal ]")
        for i, temp in enumerate(temperatures):
            print(f"  Sensor {i} (TEMP{i}):    {temp:.2f} °C")
            
        print("\n" + ("-"*35))


except Exception as e:
    print(f"\nERROR: An exception occurred: {e}")