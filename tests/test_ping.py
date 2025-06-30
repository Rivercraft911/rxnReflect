import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
setup_logging()

from rw_wheel import ReactionWheel
import rw_wheel.config as config

print("--- Test 1: PING Communication Check ---")
print("This script will attempt to ping the reaction wheel.")
print("If successful, it means wiring and basic communication are working.\n")

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        identity = wheel.ping()
        print("\nSUCCESS! Communication established.")
        print(f"Wheel reported identity: '{identity}'")

except Exception as e:
    print(f"\nERROR: An exception occurred: {e}")