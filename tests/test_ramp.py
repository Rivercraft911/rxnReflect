import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logging
setup_logging()
from rw_wheel import ReactionWheel
import rw_wheel.config as config


# --- Test 4: Ramp ---
# This test will command the motor to move, starting from an inert state,
# then ramping up to a specified percentage of its maximum speed, and finally ramping back down to a stop.

# Constants

#MAX_SAFE_RPM = 5252
MAX_SAFE_RPM = 1000
#add incremntal speed adjusts later

print("--- Test 4: Ramp ---")
print("!!! WARNING: This test will command the motor to move. !!!")
print("The motor will start inert, then ramp up to a % of its max speed, and ramp back down to a stop.\n")

# Give the user a chance to back out
response = input("Are you sure you want to proceed? (yes/no): ")
if response.lower() != 'yes':
    print("Test aborted by user.")
    sys.exit()

speed_percent =  int(input("Enter the percentage of max speed for the motor to ramp to: ")) 
if speed_percent < 0 or speed_percent > 100:
    print("Invalid percentage. Please enter a value between 0 and 100.")
    sys.exit ()

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        for i in range(0, speed_percent + 1, 5):
            rpm = (i / 100.0) * MAX_SAFE_RPM
            print(f"Ramping up to {rpm:.2f} RPM...")
            wheel.set_speed_rpm(rpm)
            time.sleep(2)
        print("Reached target speed. Now ramping down to IDLE...")
        for i in range(speed_percent, 0, -5):
            rpm = (i / 100.0) * MAX_SAFE_RPM
            print(f"Ramping down to {rpm:.2f} RPM...")
            wheel.set_speed_rpm(rpm)
            time.sleep(2)
        print("Motor has stopped. Setting to IDLE state...")


        wheel.set_idle()
        time.sleep(2) # Give it time to receive the command before closing

    print("\nSUCCESS! The safe spin test completed.")

except Exception as e:
    print(f"\nERROR: An exception occurred during the spin test: {e}")