# rw_wheel/driver.py
"""
Core driver for the RW4-12 Reaction Wheel.

This module implements the low-level Nanosatellite Protocol (NSP)
as specified in the E400281 RW4-12 Software ICD document. It handles
SLIP framing, packet construction, CRC validation, and provides a
high-level API for controlling the wheel.

Author: River Dowdy
Date: June 2025
"""
import math
import struct
import serial
import crcmod
import time
import logging
from enum import IntEnum

# --- Protocol Constants (from E400281 Software ICD) ---

# SLIP Framing Characters (ICD §4.1, Table 2)
FEND = 0xC0  # Frame End
FESC = 0xDB  # Frame Escape
TFEND = 0xDC # Transposed Frame End
TFESC = 0xDD # Transposed Frame Escape

# CRC-16/CCITT-FALSE (ICD 5.7)
# The C-code example in the datasheet implies a reflected (LSB-first)
# algorithm. 'rev=True' in crcmod handles this.
_crc_func = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, rev=True, xorOut=0x0000)

# NSP Commands (ICD 6.3, Table 5)
class NSPCommand(IntEnum):
    PING = 0x00
    INIT = 0x01
    PEEK = 0x02
    POKE = 0x03
    DIAGNOSTIC = 0x04
    CRC = 0x06
    READ_FILE = 0x07
    WRITE_FILE = 0x08
    #add more later if needed


# Wheel Command Modes (ICD 7.5, Page 36)
class WheelMode(IntEnum):
    IDLE = 0x00
    SPEED = 0x03
    TORQUE = 0x12
    MOMENTUM = 0x11
    #add more later if needed

# EDAC Memory File Addresses (ICD 7.4, Table 9)
class EDACFile(IntEnum):
    COMMAND_VALUE = 0x00
    VBUS = 0x03
    SPEED = 0x15
    MOMENTUM = 0x16
    TORQUE = 0x12
    # Add other telemetry files if needed

# --- Custom Exceptions for Error Handling ---
class WheelError(Exception):
    """Base exception for all wheel-related errors."""
    pass

class WheelCrcError(WheelError):
    """Raised when a received packet has an invalid CRC."""
    pass

class WheelNackError(WheelError):
    """Raised when the wheel responds with a NACK (Negative Acknowledgement)."""
    pass

# SLIP Encoding/Decoding Helper Functions
def _slip_encode(data: bytes) -> bytes:

    #Note to self: Remove After Testing
    # out = bytearray([FEND, FEND, FEND, FEND])
    out = bytearray([FEND])
    
    for byte in data:
        if byte == FEND:
            out.extend([FESC, TFEND])
        elif byte == FESC:
            out.extend([FESC, TFESC])
        else:
            out.append(byte)
    out.append(FEND)
    return bytes(out)

def _slip_decode(frame: bytes) -> bytes | None:
    if not frame.startswith(FEND.to_bytes(1, 'little')) or not frame.endswith(FEND.to_bytes(1, 'little')):
        return None
    
    # Strip FEND bytes
    data = frame[1:-1]
    decoded = bytearray()
    i = 0
    while i < len(data):
        if data[i] == FESC:
            i += 1
            if data[i] == TFEND:
                decoded.append(FEND)
            elif data[i] == TFESC:
                decoded.append(FESC)
        else:
            decoded.append(data[i])
        i += 1
    return bytes(decoded)

log = logging.getLogger(__name__)

# The Main Driver Class
class ReactionWheel:
    def __init__(self, port, baud, wheel_addr, host_addr):
        self.port = port
        self.baud = baud
        self.wheel_addr = wheel_addr
        self.host_addr = host_addr
        self.ser = None
        
    def open(self):
        """Opens the serial port to communicate with the wheel."""
        if self.ser is None or not self.ser.is_open:
            self.ser = serial.Serial(self.port, self.baud, timeout=1.0)
        print(f"Serial port {self.port} opened successfully.")

    def close(self):
        """Closes the serial port."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Serial port {self.port} closed.")

    # Context manager methods for 'with' statement
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Always try to command the wheel to a safe IDLE state on exit
        try:
            print("Ensuring wheel is in safe IDLE state...")
            self.set_idle()
        except Exception as e:
            print(f"Warning: Could not command wheel to IDLE on exit: {e}")
        self.close()

    def _send_and_receive(self, command: NSPCommand, payload: bytes = b''):
        """
        Handles the full send-and-receive logic for a command.
        1. Builds the NSP packet.
        2. SLIP-encodes it.
        3. Sends it.
        4. Waits for the reply.
        5. SLIP-decodes the reply.
        6. Validates the reply's CRC and ACK bit.
        7. Returns the reply's data payload.
        """

        # 1. Build the NSP Packet
        # Control byte: Bit 7=Poll, Bit 5=ACK. In this case we always set Poll to get a reply.
        control_byte = 0b10000000 | command.value
        
        # Packet body for CRC calculation (ICD 5.7)
        packet_body = struct.pack(
            '<BB', self.wheel_addr, self.host_addr
        ) + control_byte.to_bytes(1, 'little') + payload
        
        crc = _crc_func(packet_body).to_bytes(2, 'little')
        full_packet = packet_body + crc
        
        # 2. SLIP-encode and send
        frame_to_send = _slip_encode(full_packet)
        self.ser.write(frame_to_send)

        # Debug logging
        log.debug(f"TX > Raw packet: {full_packet.hex(' ')}")
        log.debug(f"TX > SLIP-encoded frame: {frame_to_send.hex(' ')}")
        
        # 3. Wait for and decode the reply
        frame_received = self.ser.read_until(FEND.to_bytes(1, 'little'))
        if not frame_received:
            raise WheelError("Timeout: No reply received from the wheel.")
            
        # Log the received frame
        log.debug(f"RX < Received frame: {frame_received.hex(' ')}")
        
        packet_received = _slip_decode(frame_received)
        # Check and log the received packet
        if packet_received:
            log.debug(f"RX < Raw packet: {packet_received.hex(' ')}")
        else:
            log.warning("Received an invalid SLIP frame.") # Use log.warning
            raise WheelError("Received an invalid SLIP frame.")

        # --- 4. Validate the reply ---
        # Separate the received packet into its body and CRC 
        if len(packet_received) < 5:
            raise WheelError(f"Reply packet is too short: {len(packet_received)} bytes.")
        
        received_body = packet_received[:-2]
        received_crc = packet_received[-2:]
        
        # Check CRC
        calculated_crc = _crc_func(received_body).to_bytes(2, 'little')
        if received_crc != calculated_crc:
            raise WheelCrcError(f"CRC mismatch! Got {received_crc.hex()}, expected {calculated_crc.hex()}")
        
        # Check for NACK
        # The ACK bit (Bit 5) in the control byte (3rd byte) must be 1.
        reply_control_byte = received_body[2]
        if not (reply_control_byte & 0b00100000):
            raise WheelNackError("Wheel responded with NACK (command failed).")
            
        # 5. Return the data payload
        return received_body[3:] # Everything after [DST][SRC][CTRL]


    # High-Level API

    def initialize_application(self):
        """
        Sends the INIT command to transition the wheel from bootloader
        to application mode..
        """
        log.info("Sending INIT command to start application firmware...")
        
        start_address = 0x20050000
        payload = struct.pack('<I', start_address) # '<I' is 4-byte unsigned int, little-endian
        
        original_timeout = self.ser.timeout
        self.ser.timeout = 3.0 # Give it 3 seconds to reply
        
        try:
            self._send_and_receive(NSPCommand.INIT, payload)
            log.info("INIT command successful. Wheel should now be in Application Mode.")
        finally:
            #restore the original timeout
            self.ser.timeout = original_timeout

    def ping(self) -> str:
        """
        Sends a PING command to the wheel.
        """
        print("Pinging the wheel...")
        reply_payload = self._send_and_receive(NSPCommand.PING)
        return reply_payload.decode('ascii', errors='ignore')

    def read_vbus(self) -> float:
        """Reads the bus voltage from the wheel's telemetry."""
        print("Reading bus voltage (VBUS)...")
        payload = EDACFile.VBUS.value.to_bytes(1, 'little')
        
        reply = self._send_and_receive(NSPCommand.READ_FILE, payload)
        
        file_addr, value = struct.unpack('<Bf', reply)
        if file_addr != EDACFile.VBUS:
            raise WheelError(f"Wheel replied with wrong file! Expected {EDACFile.VBUS}, got {file_addr}")
        return value

    def set_idle(self):
        """Commands the wheel to the safe IDLE mode."""
        print("Commanding wheel to IDLE mode...")
        payload = struct.pack(
            '<BBf', EDACFile.COMMAND_VALUE, WheelMode.IDLE, 0.0
        )
        self._send_and_receive(NSPCommand.WRITE_FILE, payload)
        print("Wheel is now in IDLE mode.")
        
    def set_speed_rpm(self, rpm: float):
        """Commands the wheel to a specific speed in revolutions per minute."""
        print(f"Commanding wheel to SPEED mode at {rpm:.1f} RPM...")
        # Convert RPM to rad/s for the wheel's firmware
        rad_s = rpm * (2.0 * math.pi / 60.0)
        
        payload = struct.pack(
            '<BBf', EDACFile.COMMAND_VALUE, WheelMode.SPEED, rad_s
        )
        self._send_and_receive(NSPCommand.WRITE_FILE, payload)
        print("SPEED command sent successfully.")

    