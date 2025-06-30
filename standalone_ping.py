
import sys, serial, time

# ---------- SLIP / NSP constants ----------
FEND, FESC, TFEND, TFESC = 0xC0, 0xDB, 0xDC, 0xDD
DEST, SRC, CTL_PING = 0x20, 0x11, 0x80        # Poll bit set, cmd 0x00

def crc16(data: bytes, init: int = 0xFFFF) -> int:
    crc = init
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc & 0xFFFF

def slip_encode(payload: bytes) -> bytes:
    esc = bytearray()
    for b in payload:
        if b == FEND: esc += bytes([FESC, TFEND])
        elif b == FESC: esc += bytes([FESC, TFESC])
        else: esc.append(b)
    return bytes([FEND]) + esc + bytes([FEND])

def build_ping() -> bytes:
    core = bytes([DEST, SRC, CTL_PING])
    crc  = crc16(core)
    core += bytes([crc & 0xFF, crc >> 8])      # little‑endian CRC
    return slip_encode(core)

def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/cu.usbserial-B00320NW"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
    frame = build_ping()
    print(f"TX ({len(frame)} bytes):", frame.hex(" "))
    with serial.Serial(port, baud, timeout=1.0) as ser:
        ser.reset_input_buffer()
        ser.write(frame); ser.flush()
        print("PING sent… waiting up to 1 s for reply.")
        reply = ser.read(64)
        if reply: print("RX:", reply.hex(" "))
        else:     print("No response within timeout.")
if __name__ == "__main__":
    main()

