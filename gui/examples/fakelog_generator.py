import threading
import time
from logging import getLogger

logger = getLogger(__name__)


def generate_logs():
    for i in range(100000):
        logger.debug(f"Debug message {i}")
        if i % 5 == 0:
            logger.info(f"Info message {i}")
        if i % 10 == 0:
            logger.warning(f"Warning message {i}")
        if i % 15 == 0:
            logger.error(f"Error message {i}")
        if i % 20 == 0:
            logger.critical(f"Critical message {i}")
        time.sleep(0.5)


def fakelogging_start():
    # Start log processing and generation threads
    threading.Thread(target=generate_logs, daemon=True).start()
