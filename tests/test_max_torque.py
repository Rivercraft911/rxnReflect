import sys
import os
import time

# Add the parent directory to the system path to find other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging_config import setup_logging
setup_logging()

from rw_wheel import ReactionWheel
import rw_wheel.config as config

# --- Test Parameters ---

MAX_TORQUE = .05  # Maximum testing torque in N·m
TEST_DURATION_S = 1 

print("--- Test 5: Max Torque Check ---")
print("This script will attempt to command the wheel to its maximum torque.")
print("It will apply the torque for a few seconds while monitoring wheel speed.")
print("\nWARNING: This will cause the wheel to spin up. Ensure it is securely mounted.")
print(f"Torque to be applied: {MAX_TORQUE:.3f} N·m for {TEST_DURATION_S} seconds.")

response = input("Are you sure you want to proceed? (yes/no): ")
if response.lower() != 'yes':
    sys.exit()

try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        
        print("\nConnecting to wheel...")
        print("Putting wheel in IDLE mode before test...")
        wheel.set_idle()
        time.sleep(0.5) # Give it time to process the command

        initial_speed = wheel.read_speed()
        print(f"Initial speed: {initial_speed:.2f} Rad/s")
        time.sleep(1)

        print(f"\n--> COMMANDING MAX TORQUE: {MAX_TORQUE:.3f} N·m")
        wheel.set_torque(MAX_TORQUE)
        
        print(f"Holding torque for {TEST_DURATION_S} seconds and monitoring speed...")
        for i in range(TEST_DURATION_S):
            time.sleep(1)
            current_speed = wheel.read_speed()
            print(f"  [t={i+1}s] Current Speed: {current_speed:.2f} Rad/s")
        
        print("\n--> COMMANDING IDLE MODE")
        wheel.set_idle()

        time.sleep(1) 
        final_speed = wheel.read_speed()
        print(f"Final speed after commanding IDLE: {final_speed:.2f} Rad/s")
        
        if final_speed > initial_speed:
            print("\nSUCCESS: Wheel speed increased, indicating torque was applied.")
        else:
            print("\nWARNING: Wheel speed did not increase as expected.")
            
        print("\n--- Max Torque Test COMPLETE ---")


except Exception as e:
    print(f"\nERROR: An exception occurred during the test: {e}")