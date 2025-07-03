# analysis/test_saturation_and_power.py

import sys
import os
import time
import math
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rw_wheel import ReactionWheel, WheelError, WheelMode, config
from logging_config import setup_logging

# --- Test Configuration ---
MAX_SAFE_RPM = 5252.0
TARGET_RPM = MAX_SAFE_RPM * 0.95  # Target 95% of max safe speed
HOLD_DURATION = 5.0              # seconds to hold at target speed
MAX_TORQUE = 0.2                 # N·m (Max spec from datasheet)
SAMPLE_INTERVAL = 0.05           # seconds (20 Hz sampling rate)

setup_logging()

print("--- Test: Saturation & Power Profile ---")
print(f"This test will spin the wheel to {TARGET_RPM:.0f} RPM using max torque, hold, then brake.")
print("It will log speed, voltage, and current to analyze performance and power draw.")
response = input("!!! WARNING: HIGH-SPEED MOTION TEST. Ensure wheel is secure. Proceed? (yes/no): ")
if response.lower() != 'yes':
    print("Test aborted.")
    sys.exit()

# --- Data Collection ---
test_data = []
time_to_target = None
try:
    with ReactionWheel(
        port=config.SERIAL_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=config.WHEEL_ADDRESS,
        host_addr=config.HOST_ADDRESS
    ) as wheel:
        # Phase 0: Setup
        wheel.set_idle()
        time.sleep(1.0)
        start_time = time.time()
        
        # --- Phase 1: Full Torque Spin-Up ---
        print("\n--- Phase 1: Applying max torque spin-up... ---")
        wheel.set_torque(MAX_TORQUE)
        
        while True:
            elapsed_time = time.time() - start_time
            try:
                speed_rad_s = wheel.read_speed()
                vbus = wheel.read_vbus()
                current = wheel.read_current()
                
                speed_rpm = speed_rad_s * (60.0 / (2.0 * math.pi))
                
                test_data.append({
                    'time_s': elapsed_time, 'phase': 'spin-up', 'speed_rpm': speed_rpm,
                    'vbus_V': vbus, 'current_A': current
                })
                print(f"Time: {elapsed_time:5.2f}s, Speed: {speed_rpm:8.1f} RPM, VBUS: {vbus:5.2f}V, Current: {current:5.2f}A")
                
                if speed_rpm >= TARGET_RPM:
                    if time_to_target is None: time_to_target = elapsed_time
                    print(f"\n--- Reached target RPM in {time_to_target:.2f} seconds! ---")
                    break
            except WheelError as e:
                print(f"Warning: A communication error occurred: {e}")
            time.sleep(SAMPLE_INTERVAL)

        # --- Phase 2: Hold Speed ---
        print("\n--- Phase 2: Holding target speed... ---")
        wheel.set_speed_rpm(TARGET_RPM)
        hold_start_time = time.time()
        while (time.time() - hold_start_time) < HOLD_DURATION:
            elapsed_time = time.time() - start_time
            try:
                speed_rad_s = wheel.read_speed()
                vbus = wheel.read_vbus()
                current = wheel.read_current()
                speed_rpm = speed_rad_s * (60.0 / (2.0 * math.pi))
                
                test_data.append({
                    'time_s': elapsed_time, 'phase': 'hold', 'speed_rpm': speed_rpm,
                    'vbus_V': vbus, 'current_A': current
                })
                print(f"Time: {elapsed_time:5.2f}s, Speed: {speed_rpm:8.1f} RPM, VBUS: {vbus:5.2f}V, Current: {current:5.2f}A")
            except WheelError as e:
                print(f"Warning: A communication error occurred: {e}")
            time.sleep(SAMPLE_INTERVAL)
            
        # --- Phase 3: Full Torque Spin-Down (Braking) ---
        print("\n--- Phase 3: Applying max torque braking... ---")
        wheel.set_torque(-MAX_TORQUE)
        while True:
            elapsed_time = time.time() - start_time
            try:
                speed_rad_s = wheel.read_speed()
                vbus = wheel.read_vbus()
                current = wheel.read_current()
                speed_rpm = speed_rad_s * (60.0 / (2.0 * math.pi))
                
                test_data.append({
                    'time_s': elapsed_time, 'phase': 'spin-down', 'speed_rpm': speed_rpm,
                    'vbus_V': vbus, 'current_A': current
                })
                print(f"Time: {elapsed_time:5.2f}s, Speed: {speed_rpm:8.1f} RPM, VBUS: {vbus:5.2f}V, Current: {current:5.2f}A")
                
                if speed_rpm <= 1.0: # Check if wheel is nearly stopped
                    print("\n--- Wheel has stopped. ---")
                    break
            except WheelError as e:
                print(f"Warning: A communication error occurred: {e}")
            time.sleep(SAMPLE_INTERVAL)
            
        print("Test profile complete. Commanding wheel to idle.")
        wheel.set_idle()
except Exception as e:
    print(f"\nFATAL ERROR: Test failed with an unhandled exception: {e}")
else:
    print("\nSUCCESS! Data collection finished.")
    if time_to_target:
        print(f"\n>>>> Performance Result: Time to reach {TARGET_RPM:.0f} RPM was {time_to_target:.2f} seconds. <<<<\n")

# --- Data Processing and Saving ---
if not test_data:
    print("No data was collected. Exiting.")
    sys.exit()

df = pd.DataFrame(test_data)
# Calculate power using the measured VBUS and current.
df['power_W'] = df['vbus_V'] * df['current_A']

timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"saturation_power_{timestamp_str}.csv"
html_plot_filename = f"saturation_power_{timestamp_str}.html"

df.to_csv(csv_filename, index=False)
print(f"Data saved to '{csv_filename}'")

# --- Plotting with Plotly ---
print("Generating Plotly chart...")
fig = make_subplots(
    rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08,
    subplot_titles=("Speed Profile", "Electricals (Voltage & Current)", "Power Draw")
)

# Plot 1: Speed
fig.add_trace(go.Scatter(
    x=df['time_s'], y=df['speed_rpm'], mode='lines', name='Speed (RPM)'
), row=1, col=1)

# Plot 2: VBUS and Current
fig.add_trace(go.Scatter(
    x=df['time_s'], y=df['vbus_V'], mode='lines', name='VBUS (V)', line=dict(color='blue')
), row=2, col=1)
fig.add_trace(go.Scatter(
    x=df['time_s'], y=df['current_A'], mode='lines', name='Current (A)', line=dict(color='red')
), row=2, col=1)

# Plot 3: Power
fig.add_trace(go.Scatter(
    x=df['time_s'], y=df['power_W'], mode='lines', name='Power (W)', line=dict(color='purple'), fill='tozeroy'
), row=3, col=1)

# --- Update Layout ---
fig.update_layout(
    title_text=f'Saturation & Power Profile (Torque: ±{MAX_TORQUE} N·m)',
    height=900, template='plotly_white', showlegend=True
)
fig.update_yaxes(title_text="Speed (RPM)", row=1, col=1)
fig.update_yaxes(title_text="Electrical (V/A)", row=2, col=1)
fig.update_yaxes(title_text="Power (W)", row=3, col=1)
fig.update_xaxes(title_text="Time (s)", row=3, col=1)

# Add vertical lines to show the test phases
if time_to_target:
    fig.add_vline(x=time_to_target, line_width=1, line_dash="dash", line_color="green", annotation_text="Hold Start")
    fig.add_vline(x=time_to_target + HOLD_DURATION, line_width=1, line_dash="dash", line_color="red", annotation_text="Brake Start")

fig.write_html(html_plot_filename)
print(f"Interactive plot saved to '{html_plot_filename}'")
fig.show()