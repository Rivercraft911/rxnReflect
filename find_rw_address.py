#!/usr/bin/env python3
"""
rw_probe.py – exhaustive address/flag sweep for RW4‑12 reaction wheels.

• Uses SERIAL_PORT & BAUD_RATE from config.py
• Sends multiple PING variants + INIT→PING
• Reports any wheel that replies (address & port bits)

Copy into your project root and run:  python rw_probe.py
"""

import time
import serial
from pathlib import Path

# -- project imports ----------------------------------------------------
import config                      # your existing config.py
from rw_wheel.driver import (FEND, FESC, TFEND, TFESC, _crc_func)

# -- helpers ------------------------------------------------------------
def slip_encode(payload: bytes, preamble=False) -> bytes:
    out = bytearray()
    if preamble:
        out += b'\xC0\xC0\xC0\xC0'      # legacy resync trick
    out.append(FEND)
    for b in payload:
        if b == FEND:
            out += bytes([FESC, TFEND])
        elif b == FESC:
            out += bytes([FESC, TFESC])
        else:
            out.append(b)
    out.append(FEND)
    return bytes(out)

def build_frame(dest: int, src: int, ctl: int, data: bytes = b'',
                preamble=False) -> bytes:
    body = bytes([dest, src, ctl]) + data
    crc  = _crc_func(body).to_bytes(2, "little")
    return slip_encode(body + crc, preamble=preamble)

def read_frame(ser: serial.Serial, timeout=0.5) -> bytes | None:
    start = time.time()
    while time.time() - start < timeout:
        chunk = ser.read_until(bytes([FEND]))
        if not chunk:
            return None
        if chunk[0] == FEND and chunk[-1] == FEND:
            return chunk
    return None

def slip_decode(frame: bytes) -> bytes | None:
    if not (frame and frame[0] == FEND and frame[-1] == FEND):
        return None
    data, out = frame[1:-1], bytearray()
    i = 0
    while i < len(data):
        if data[i] == FESC:
            i += 1
            out.append(FEND if data[i] == TFEND else FESC)
        else:
            out.append(data[i])
        i += 1
    return bytes(out)

def print_reply(pkt: bytes):
    dst, src, ctl = pkt[:3]
    crc_ok = _crc_func(pkt[:-2]).to_bytes(2, "little") == pkt[-2:]
    if crc_ok:
        port_bits = (src >> 4) & 0x03
        print(f"  ↳  SRC=0x{src:02X}  (port bits {port_bits:02b})  CTL=0x{ctl:02X}")
    else:
        print("  ↳  reply CRC mismatch")

# -- main sweep ----------------------------------------------------------
def main():
    port = config.SERIAL_PORT
    baud = config.BAUD_RATE
    src_host = 0x11                     # factory‑recommended host address

    print(f"Opening {port} @ {baud} bps …")
    with serial.Serial(port, baud, timeout=0.2) as ser:

        def tx_and_wait(frame: bytes, label: str):
            ser.reset_input_buffer()
            ser.write(frame); ser.flush()
            reply = read_frame(ser)
            if reply:
                pkt = slip_decode(reply)
                if pkt and len(pkt) >= 5:
                    print(label, "→ reply!")
                    print_reply(pkt)
                    return True
            return False

        # 1 & 2  Broadcast scans (Poll=1 then 0)
        for poll in (0x80, 0x00):
            print(f"\n[Scan] Broadcast groups, Poll={'1' if poll else '0'}")
            for dest in (0x00, 0x10, 0x20, 0x30):
                frame = build_frame(dest, src_host, poll | 0x00)
                print(f" TX 0x{dest:02X} …", end="")
                if not tx_and_wait(frame, ""):
                    print(" no reply")

        # 3  INIT then PING
        print("\n[Init→Ping] broadcast INIT 0x20050000 then PING")
        init_frame = build_frame(0x00, src_host, 0x81,
                                 data=(0x20050000).to_bytes(4, "little"))
        tx_and_wait(init_frame, " INIT")
        time.sleep(0.3)
        ping_frame = build_frame(0x00, src_host, 0x80)
        tx_and_wait(ping_frame, " PING")

        # 4  Broadcast with 4×FEND preamble
        print("\n[Scan] Broadcast w/ 4×FEND preamble")
        pre_frame = build_frame(0x00, src_host, 0x80, preamble=True)
        tx_and_wait(pre_frame, " preamble‑PING")

        # 5  Full address sweep 0‑255
        print("\n[Sweep] Poll=1 to every address 0‑255 (takes ≈2 s)")
        found = False
        for dest in range(256):
            frame = build_frame(dest, src_host, 0x80)
            if tx_and_wait(frame, f" addr 0x{dest:02X}"):
                found = True
                break   # stop at first success for clarity
        if not found:
            print("No wheel spoke up in full sweep.")

if __name__ == "__main__":
    main()
