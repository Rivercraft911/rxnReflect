# analysis/test_torque_linearity.py

import sys
import os
import time
import math
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rw_wheel import ReactionWheel, WheelError, config
from logging_config import setup_logging

# --- Test Configuration ---
# We will test a range of torque commands
TORQUE_COMMANDS = np.linspace(-0.2, 0.2, 21) # From -0.2 to +0.2 Nm in 21 steps
#TEST_DURATION_PER_STEP = 3.0 # How long to apply each torque command
TEST_DURATION_PER_STEP = 3
SAMPLE_INTERVAL = 0.05

setup_logging()

print("--- Test: Torque Linearity & Deadband ---")
print(f"This test will sweep through {len(TORQUE_COMMANDS)} torque commands to map the wheel's response.")
response = input("This is an automated test. Ensure wheel is secure. Proceed? (yes/no): ")
if response.lower() != 'yes':
    print("Test aborted.")
    sys.exit()

# --- Data Collection ---
linearity_results = []
wheel_inertia = None
try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        # Read the inertia once at the start
        wheel_inertia = wheel.read_inertia()
        print(f"Successfully read wheel inertia: {wheel_inertia:.5f} kg·m²")

        # Loop through each torque command
        for i, torque_cmd in enumerate(TORQUE_COMMANDS):
            print(f"\n--- Testing Step {i+1}/{len(TORQUE_COMMANDS)}: Torque = {torque_cmd:.3f} N·m ---")
            
            # Always start from a standstill for a clean measurement
            wheel.set_idle()
            time.sleep(2.0) # Let any residual motion die down

            step_data = []
            wheel.set_torque(torque_cmd)
            start_time = time.time()
            while (elapsed_time := time.time() - start_time) < TEST_DURATION_PER_STEP:
                try:
                    speed_rad_s = wheel.read_speed()
                    step_data.append({'time_s': elapsed_time, 'speed_rad_s': speed_rad_s})
                except WheelError as e:
                    print(f"Warning: Comm error during step: {e}")
                time.sleep(SAMPLE_INTERVAL)
            
            # --- Analyze the data for this single step ---
            if not step_data:
                print("No data collected for this step, skipping.")
                continue

            step_df = pd.DataFrame(step_data)
            step_df['acceleration_rad_s2'] = step_df['speed_rad_s'].diff() / step_df['time_s'].diff()
            
            # Calculate the average acceleration, ignoring the noisy first few points
            # We'll average the middle 50% of the data to avoid startup transients
            start_idx = int(len(step_df) * 0.25)
            end_idx = int(len(step_df) * 0.75)
            avg_accel = step_df['acceleration_rad_s2'].iloc[start_idx:end_idx].mean()

            print(f"Result: Commanded Torque={torque_cmd:.3f} -> Avg Acceleration={avg_accel:.4f} rad/s²")
            linearity_results.append({
                'commanded_torque_Nm': torque_cmd,
                'measured_accel_rad_s2': avg_accel
            })
        
        print("\n--- Test sweep complete. Setting wheel to IDLE. ---")
        wheel.set_idle()

except Exception as e:
    print(f"\nFATAL ERROR: Test failed with an unhandled exception: {e}")
else:
    print("\nSUCCESS! Data collection finished.")

# --- Data Processing and Saving ---
if not linearity_results:
    print("No data was collected. Exiting.")
    sys.exit()

df = pd.DataFrame(linearity_results)
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"torque_linearity_{timestamp_str}.csv"
html_plot_filename = f"torque_linearity_{timestamp_str}.html"

df.to_csv(csv_filename, index=False)
print(f"\nData saved to '{csv_filename}'")

# --- Plotting ---
print("Generating linearity plot...")
fig = go.Figure()

# Add the measured data points
fig.add_trace(go.Scatter(
    x=df['commanded_torque_Nm'],
    y=df['measured_accel_rad_s2'],
    mode='markers+lines',
    name='Measured Response',
    marker=dict(size=8, color='blue')
))

# Add the theoretical line based on the measured inertia
if wheel_inertia is not None:
    # y = (1/I) * x
    theoretical_x = np.array([-0.2, 0.2])
    theoretical_y = (1 / wheel_inertia) * theoretical_x
    fig.add_trace(go.Scatter(
        x=theoretical_x,
        y=theoretical_y,
        mode='lines',
        name='Theoretical Response (1/I)',
        line=dict(color='red', dash='dash')
    ))

fig.update_layout(
    title_text='Torque Linearity & Deadband Analysis',
    xaxis_title='Commanded Torque (N·m)',
    yaxis_title='Measured Acceleration (rad/s²)',
    height=700,
    template='plotly_white',
    legend=dict(x=0.01, y=0.98)
)

fig.write_html(html_plot_filename)
print(f"Interactive plot saved to '{html_plot_filename}'")
fig.show()