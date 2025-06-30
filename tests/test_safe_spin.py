import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
setup_logging()

from rw_wheel import ReactionWheel
import rw_wheel.config as config

print("--- Test 3: Safe Low-Speed Spin ---")
print("!!! WARNING: This test will command the motor to move. !!!")
print("The wheel will spin at a very low speed (30 RPM) for 5 seconds, then stop.\n")

response = input("Are you sure you want to proceed? (yes/no): ")
if response.lower() != 'yes':
    print("Test aborted by user.")
    sys.exit()

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        # Command a low speed
        wheel.set_speed_rpm(30.0)
        
        # Let it spin for 5 seconds
        print("Wheel spinning. Waiting for 5 seconds...")
        time.sleep(5)
        
        print("Commanding wheel to stop (IDLE).")
        wheel.set_idle()
        time.sleep(2) # Give it time to receive the command before closing

    print("\nSUCCESS! The safe spin test completed.")

except Exception as e:
    print(f"\nERROR: An exception occurred during the spin test: {e}")