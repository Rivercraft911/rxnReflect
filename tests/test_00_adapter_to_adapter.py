import sys
import os
import time
import logging
import threading
import struct
import serial

# --- Setup Paths and Logging ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logging
import config


from rw_wheel import (
    ReactionWheel,
    WheelError,
    NSPCommand,
    _slip_encode,
    _slip_decode,
    _crc_func,
    FEND
)

# --- Configuration for Test ---
HOST_PORT = "/dev/cu.usbserial-BG00Q8TP"
DEVICE_PORT = "/dev/cu.usbserial-B00320NW"
HOST_ADDR = config.HOST_ADDRESS
DEVICE_ADDR = config.WHEEL_ADDRESS

# --- The Test Threads ---
setup_logging()
log = logging.getLogger(__name__)
test_complete_event = threading.Event()

def device_simulator():
    """
    This function runs in a separate thread and acts like the reaction wheel.
    It listens for a PING command and sends a valid reply.
    """
    log.info("[Device Sim] Starting device simulator thread.")
    try:
        with serial.Serial(DEVICE_PORT, config.BAUD_RATE, timeout=0.2) as dev_ser:
            log.info(f"[Device Sim] Opened port {DEVICE_PORT} to act as wheel.")
            while not test_complete_event.is_set():
                frame_received = dev_ser.read_until(FEND.to_bytes(1, 'little'))
                if not frame_received: continue

                log.debug(f"[Device Sim] RX < Received frame: {frame_received.hex(' ')}")
                packet = _slip_decode(frame_received)
                
                if not packet or len(packet) < 5:
                    log.warning(f"[Device Sim] Decoded invalid packet: {packet}")
                    continue

                body, received_crc_bytes = packet[:-2], packet[-2:]
                calculated_crc_val = _crc_func(body)
                received_crc_val = int.from_bytes(received_crc_bytes, 'little')

                if calculated_crc_val != received_crc_val:
                    log.error(f"[Device Sim] BAD CRC. Got {received_crc_val:04x}, expected {calculated_crc_val:04x}")
                    continue

                dest, src, ctrl = body[0], body[1], body[2]
                command = ctrl & 0x1F

                if dest == DEVICE_ADDR and command == NSPCommand.PING:
                    log.info("[Device Sim] Valid PING received. Sending reply...")
                    
                    reply_data = b"Simulated Wheel OK"
                    reply_ctrl = 0b10100000 | NSPCommand.PING.value
                    
                    reply_body = struct.pack('<BB', src, dest) + reply_ctrl.to_bytes(1, 'little') + reply_data
                    reply_crc_bytes = _crc_func(reply_body).to_bytes(2, 'little')
                    
                    frame_to_send = _slip_encode(reply_body + reply_crc_bytes)
                    
                    dev_ser.write(frame_to_send)
                    log.debug(f"[Device Sim] TX > Sent frame: {frame_to_send.hex(' ')}")

    except Exception as e:
        log.critical(f"[Device Sim] Thread crashed: {e}", exc_info=True)
    finally:
        log.info("[Device Sim] Thread finished.")

def host_test():
    """
    This function runs in the main thread and uses the actual ReactionWheel class
    to send a command and verify the reply from the simulator.
    """
    log.info("[Host] Starting host test.")
    host_wheel = ReactionWheel(
        port=HOST_PORT,
        baud=config.BAUD_RATE,
        wheel_addr=DEVICE_ADDR,
        host_addr=HOST_ADDR
    )
    try:
        with host_wheel:
            response_str = host_wheel.ping()
            log.info(f"[Host] Received reply: '{response_str}'")
            if "Simulated Wheel OK" in response_str:
                print("\n" + "="*50)
                print("    SUCCESS! ADAPTER-TO-ADAPTER TEST PASSED!")
                print("="*50)
            else:
                print("\n" + "!"*50 + "\n    FAILURE! Received an unexpected reply.\n" + "!"*50)
    except WheelError as e:
        print("\n" + "!"*50 + f"\n    FAILURE! Host test failed: {e}\n" + "!"*50)
        log.critical(f"[Host] Test failed: {e}", exc_info=True)
    finally:
        test_complete_event.set()

if __name__ == "__main__":
    print("--- Test 0: Adapter-to-Adapter Communication Check ---")
    device_thread = threading.Thread(target=device_simulator, daemon=True)
    device_thread.start()
    time.sleep(2) # Give simulator thread time to open port
    host_test()
    device_thread.join(timeout=2)