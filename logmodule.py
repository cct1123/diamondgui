import logging.config
import os
import queue
import time
from pathlib import Path


class LogQueue(queue.Queue):
    """Singleton Queue for Logging"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogQueue, cls).__new__(cls)
            super(LogQueue, cls._instance).__init__()  # Initialize the Queue
        return cls._instance


def setup_logging():
    HERE = Path(__file__).parent
    # import tempfile
    # log_dir = os.path.join(tempfile.gettempdir(), 'qtracelog')
    # print(log_dir)
    LOGGING_DIR = os.path.join(HERE, "temp/log")
    os.makedirs(LOGGING_DIR, exist_ok=True)

    LOG_TEMP_FILE = os.path.join(
        LOGGING_DIR, f"{time.strftime('%Y%m%d', time.localtime())}_temp.log"
    )

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s %(levelname)s %(module)s PID %(process)d %(threadName)s %(thread)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(asctime)s %(levelname)s %(module)s %(threadName)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console_handler": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "file_handler": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": LOG_TEMP_FILE,
                "formatter": "verbose",
            },
            "queue_handler": {
                "level": "DEBUG",
                "class": "logging.handlers.QueueHandler",
                "queue": LogQueue(),
                "formatter": "simple",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console_handler", "file_handler", "queue_handler"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }
    logging.config.dictConfig(LOGGING_CONFIG)


# ------------------------------------------------------------------------------------------------
# backup file seting -------------------------------------------------------------------------------------
HERE = Path(__file__).parent
BACKUP_DIR = os.path.join(HERE, "temp", "backup")
os.makedirs(BACKUP_DIR, exist_ok=True)
