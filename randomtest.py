# init_monitor.py
import serial
import time
import crcmod

# --- Configuration ---
SERIAL_PORT = "/dev/cu.usbserial-B00320NW" 
BAUD_RATE = 115200
LISTEN_DURATION_S = 5.0

# --- Protocol Functions ---
FEND = 0xC0
_crc_func = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=True, xorOut=0x0000)
def _slip_encode(data: bytes) -> bytes:
    out = bytearray([FEND])
    for byte in data:
        if byte == 0xC0: out.extend([0xDB, 0xDC])
        elif byte == 0xDB: out.extend([0xDB, 0xDD])
        else: out.append(byte)
    out.append(FEND)
    return bytes(out)

print("--- Raw Serial Monitor (Forced INIT Test) ---")
print("This script will send one INIT command to the broadcast address and listen for any raw response.")
print(f"Opening port {SERIAL_PORT} at {BAUD_RATE} bps...")

ser = None
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    
    # --- Construct the INIT Command Frame ---
    # According to ICD E400281 Sec 6.1.1, the command is "INIT 0x20050000"
    # Destination: 0x00 (Broadcast)
    # Source:      0x02 (Our Host)
    # Control:     Poll=1, B=0, ACK=0, Command=INIT(0x01) -> 0b10000001 -> 0x81
    # Data:        0x20050000 (Little-Endian) -> 00 00 05 20
    
    packet_body = b'\x00\x02\x81\x00\x00\x05\x20'
    crc_bytes = _crc_func(packet_body).to_bytes(2, 'little')
    full_packet = packet_body + crc_bytes
    INIT_FRAME = _slip_encode(full_packet)
    
    # 1. Send the INIT command
    print(f"Sending INIT frame: {INIT_FRAME.hex(' ')}")
    ser.write(INIT_FRAME)
    
    # 2. Immediately start listening
    print(f"\n--- Now Listening for ANY response for {LISTEN_DURATION_S} seconds ---")
    
    all_data_received = bytearray()
    start_time = time.time()
    
    while time.time() - start_time < LISTEN_DURATION_S:
        chunk = ser.read(16)
        if chunk:
            print(f"--> Received {len(chunk)} byte(s): {chunk.hex(' ')}")
            all_data_received.extend(chunk)
            start_time = time.time()

    print("\n--- Listening Period Finished ---")
    
    # 3. Analyze the result
    if all_data_received:
        print(f"\nSUCCESS: THE WHEEL IS ALIVE! It sent back a total of {len(all_data_received)} bytes.")
        print("This strongly suggests the wiring is now correct and the wheel was waiting for this INIT command.")
        print("-" * 40)
        print("Full Hex Dump:")
        print(all_data_received.hex(' '))
        print("-" * 40)
    else:
        print("\nRESULT: Complete silence. The wheel did not respond to the broadcast INIT command.")
        print("This indicates a fundamental physical layer issue.")
        print("ACTION: Power down and SWAP the A and B wires. Then run this script again.")

except serial.SerialException as e:
    print(f"\nCRITICAL ERROR: Could not open port '{SERIAL_PORT}'. Is it plugged in? Error: {e}")
finally:
    if ser and ser.is_open:
        ser.close()
        print("\nSerial port closed.")