
# ------------------------------------------------------------------------------------------------
# logging seting -------------------------------------------------------------------------------------
import os
from pathlib import Path
import time
HERE = Path(__file__).parent
# import tempfile
# log_dir = os.path.join(tempfile.gettempdir(), 'qtracelog')
# print(log_dir)
LOGGING_DIR = os.path.join(HERE, "temp/log")
os.makedirs(LOGGING_DIR, exist_ok=True)

LOG_TEMP_FILE = os.path.join(LOGGING_DIR, f"{time.strftime('%Y%m%d', time.localtime())}_temp.log")

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s PID %(process)d %(threadName)s %(thread)d %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(module)s %(threadName)s\n  %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_TEMP_FILE,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'temp': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# ------------------------------------------------------------------------------------------------
# backup file seting -------------------------------------------------------------------------------------
BACKUP_DIR = os.path.join(HERE, "temp", "backup")
os.makedirs(BACKUP_DIR, exist_ok=True)