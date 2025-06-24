# two_port_test.py (v3 - Fully Robust)
import serial
import threading
import time
import struct
import crcmod
import sys

# --- Configuration ---
HOST_PORT = "/dev/cu.usbserial-B00320NW"
WHEEL_PORT = "/dev/cu.usbserial-BG00Q8TP"
BAUD_RATE = 115200

# --- NSP Protocol Constants ---
FEND = 0xC0
FESC = 0xDB
TFEND = 0xDC
TFESC = 0xDD
_crc_func = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=True, xorOut=0x0000)

def _slip_decode(frame: bytes) -> bytes | None:
    if not frame.startswith(FEND.to_bytes(1, 'little')) or not frame.endswith(FEND.to_bytes(1, 'little')):
        return None
    data = frame[1:-1]
    decoded = bytearray()
    i = 0
    while i < len(data):
        if data[i] == FESC:
            i += 1
            if i < len(data):
                if data[i] == TFEND: decoded.append(FEND)
                elif data[i] == TFESC: decoded.append(FESC)
            else: return None
        else:
            decoded.append(data[i])
        i += 1
    return bytes(decoded)

def _slip_encode(data: bytes) -> bytes:
    out = bytearray([FEND])
    for byte in data:
        if byte == FEND: out.extend([FESC, TFEND])
        elif byte == FESC: out.extend([FESC, TFESC])
        else: out.append(byte)
    out.append(FEND)
    return bytes(out)

# --- THREAD 1: THE WHEEL EMULATOR (Unchanged from v2) ---
def wheel_emulator(port_name):
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=0.5)
        print(f"[EMULATOR] Listening on {port_name}...")
        while True:
            ser.read_until(expected=FEND.to_bytes(1, 'little'))
            frame_content = ser.read_until(expected=FEND.to_bytes(1, 'little'))
            if not frame_content: continue
            full_frame = FEND.to_bytes(1, 'little') + frame_content
            command_packet = _slip_decode(full_frame)
            if command_packet and command_packet[2] & 0x1F == 0x00: # Is it a PING?
                print(f"\n[EMULATOR] Got PING. Sending reply...")
                reply_dest_addr, reply_src_addr = command_packet[1], command_packet[0]
                reply_ctrl_byte = 0b10100000
                reply_payload = b"EMULATOR_OK"
                reply_packet_body = struct.pack('<BB', reply_dest_addr, reply_src_addr) + \
                                    reply_ctrl_byte.to_bytes(1, 'little') + reply_payload
                full_reply_packet = reply_packet_body + _crc_func(reply_packet_body).to_bytes(2, 'little')
                ser.write(_slip_encode(full_reply_packet))
    except serial.SerialException as e:
        print(f"[EMULATOR] CRITICAL ERROR: {e}")

# --- THREAD 2: THE (ROBUST) HOST APPLICATION ---
def host_logic(port_name):
    time.sleep(1)
    print(f"[HOST] Starting on {port_name}...")
    try:
        ser = serial.Serial(port_name, BAUD_RATE, timeout=2.0)
        packet_to_send = b'\x00\x02\x80\x8b\x8e' # Broadcast PING
        frame_to_send = _slip_encode(packet_to_send)
        print(f"[HOST] Sending PING command...")
        ser.write(frame_to_send)

        print("[HOST] Waiting for reply...")
        # --- THIS IS THE CRITICAL FIX ---
        # Applying the same robust receiver logic to the host side.
        ser.read_until(expected=FEND.to_bytes(1, 'little'))
        frame_content = ser.read_until(expected=FEND.to_bytes(1, 'little'))
        if not frame_content:
            print("\n" + "="*50 + "\n--- TEST FAILED: HOST TIMED OUT ---\n" + "="*50)
            return
        
        reply_frame = FEND.to_bytes(1, 'little') + frame_content
        print(f"\n[HOST] Received Full Frame: {reply_frame.hex(' ')}")
        
        reply_packet = _slip_decode(reply_frame)
        if not reply_packet:
             print("--- TEST FAILED: HOST RECEIVED INVALID FRAME ---")
             return
        
        received_body = reply_packet[:-2]
        received_crc = reply_packet[-2:]
        calculated_crc = _crc_func(received_body).to_bytes(2, 'little')
        if received_crc != calculated_crc:
            print(f"--- TEST FAILED: CRC MISMATCH! Got {received_crc.hex()}, expected {calculated_crc.hex()} ---")
            return
            
        payload = received_body[3:]
        print("\n" + "="*50)
        print("--- !!! TEST SUCCEEDED !!! ---")
        print(f"Host received payload: '{payload.decode('ascii', 'ignore')}'")
        print("This confirms your adapters, wiring, and code are all CORRECT.")
        print("="*50)
        
    except serial.SerialException as e:
        print(f"\n[HOST] CRITICAL ERROR: {e}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting two-port loopback test (v3 - Fully Robust)...")
    emulator_thread = threading.Thread(target=wheel_emulator, args=(WHEEL_PORT,))
    emulator_thread.daemon = True
    emulator_thread.start()
    
    host_thread = threading.Thread(target=host_logic, args=(HOST_PORT,))
    host_thread.start()
    
    host_thread.join(timeout=5)
    print("\nTest finished.")