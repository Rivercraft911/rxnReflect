import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
import config
from rw_wheel import ReactionWheel, WheelError

setup_logging()
log = logging.getLogger(__name__)

print("--- Test: Initialize Wheel to Application Mode ---")
print("This script will send the INIT command to start the main flight software.")

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        # Step 1: Initialize the application
        wheel.initialize_application()
        
        # Step 2: Now try to ping it
        identity = wheel.ping()
        
        print("\n" + "="*50)
        print("    SUCCESS! Wheel initialized and pinged successfully.")
        print(f"    Wheel Identity: '{identity}'")
        print("="*50)

except WheelError as e:
    print("\n" + "!"*50)
    print(f"    FAILURE! The test failed with an error: {e}")
    print("!"*50)
    log.critical(f"Test failed: {e}", exc_info=True)