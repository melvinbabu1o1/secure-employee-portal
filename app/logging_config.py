import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    os.makedirs('logs', exist_ok=True)
    logger = logging.getLogger('security')
    if not logger.handlers:  # prevents duplicate log lines if this runs twice
        handler = RotatingFileHandler('logs/security.log', maxBytes=1_000_000, backupCount=5)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

security_logger = setup_logger()