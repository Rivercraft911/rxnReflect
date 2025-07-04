# logging_config.py

import logging
import sys

LOG_FILENAME = "wheel_test_log.txt"

def setup_logging():
    """
    Configures the root logger to output to a file and the console.
    """
 
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  

    # --- Create a handler to write logs to a file ---
    file_handler = logging.FileHandler(LOG_FILENAME, mode='w')
    file_handler.setLevel(logging.DEBUG)  # Log everything to the file

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    print(f"Logging configured. Detailed logs will be written to '{LOG_FILENAME}'")