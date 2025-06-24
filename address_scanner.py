# address_scanner.py
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logging
setup_logging()

from rw_wheel import ReactionWheel, WheelError
import config

print("--- RW4-12 Address Scanner ---")
print("This script will ping every possible NSP address (0-255) to find the wheel.")
print(f"Using Port: {config.SERIAL_PORT} at {config.BAUD_RATE} baud.")
print(f"Host address is set to: 0x{config.HOST_ADDRESS:02X}")
print("Scanning... \n")

wheel = None
found_address = -1

try:
    wheel = ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=0x00, # will be updated in loop
        host_addr=config.HOST_ADDRESS
    )
    wheel.open()

    wheel.ser.timeout = 0.1

    # 4. Loop through all possible 8-bit addresses
    for address_to_test in range(256): # covers 0x00 to 0xFF
        
        if address_to_test == wheel.host_addr:
            continue

        print(f"  Pinging address 0x{address_to_test:02X}...", end='\r')

        wheel.wheel_addr = address_to_test
        
        try:
            identity = wheel.ping()
            
            # If we get here ping succeeded
            found_address = address_to_test
            print("\n" + "="*40)
            print(f"  SUCCESS! Found wheel at address: 0x{found_address:02X} ({found_address})")
            print(f"  Wheel reported identity: '{identity}'")
            print("="*40)
            print(f"\nUpdate 'WHEEL_ADDRESS' in your config.py to 0x{found_address:02X} and try the ping_test again.")
            
            break
            
        except Exception:
            pass
            
    else:
        print("\n\nScan complete. No responding device found.")

finally:
    if wheel and wheel.ser and wheel.ser.is_open:
        wheel.close()