import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
setup_logging()

from rw_wheel import ReactionWheel
import config

print("--- Test 2: Read Telemetry ---")
print("This script will attempt to read the bus voltage from the wheel.\n")

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        voltage = wheel.read_vbus()
        print(f"\nSUCCESS! Read telemetry from wheel.")
        print(f"Bus Voltage: {voltage:.2f} V")

except Exception as e:
    print(f"\nERROR: An exception occurred: {e}")