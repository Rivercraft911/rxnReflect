import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rw_wheel import ReactionWheel
import config

print("--- Test 1: PING Communication Check ---")
print("This script will attempt to ping the reaction wheel.")
print("If successful, it means wiring and basic communication are working.\n")

try:
    # The 'with' statement automatically opens and closes the connection,
    # and ensures the wheel is left in a safe state.
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