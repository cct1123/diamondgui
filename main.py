GUI_PORT = 9982
DEBUG = True
RELOAD = True and DEBUG
# SILENCE_LOGGING = not DEBUG
SILENCE_LOGGING = True
#===============================================================================

import time
import logging
from pathlib import Path
import os
import psutil
HERE = Path(__file__).parent

python_process = []
python_process_pid = []
for p in psutil.process_iter():
    if 'python' in p.name():
        python_process_pid.append(p.pid)
        python_process.append(p)

is_main_process = (len(python_process) == 4) # WARNING!! change the number by yourself when debugging!
flag_add_hardwares = ((not is_main_process) and RELOAD) or ((not RELOAD) and is_main_process) or (not DEBUG)
flag_add_hardwares = False
#===============================================================================
# logging
#===============================================================================
import logging.config
import tempfile

# create a temp file in the directory specified by the user
log_dir = os.path.join(tempfile.gettempdir(), 'qtracelog')
log_dir = HERE
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'temp.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': log_file,
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
logging.config.dictConfig(LOGGING)

if flag_add_hardwares:
    # load the hardware manager
    # # add some devices to the server (if they aren't already added) ##################################################
    import hardware.config_custom as hcf
    from hardware.hardwaremanager import HardwareManager
    
    inserv = HardwareManager()

    # pulse generator
    try:
        inserv.add(
            'pg', 
            HERE / 'hardware' / 'pulser' / 'pulser.py', 
            'PulseGenerator', 
            [],
            dict(ip=hcf.PS_IP, chmap=hcf.PS_chmap, choffs=hcf.PS_choffs), 
        )
    except Exception as ee:
        print(ee)

    # # mw signal generator
    # try:
    #     inserv.add(
    #         'mwsyn', 
    #         HERE / 'hardware' / 'mw' / 'mwsynthesizer.py', 
    #         'Synthesizer', 
    #         [hcf.VDISYN_SN], 
    #         dict(vidpid=hcf.VDISYN_VIDPID,
    #             baudrate=hcf.VDISYN_BAUD, 
    #             timeout=5, 
    #             write_timeout=5)
    #     )
    # except Exception as ee:
    #     print(ee)

    # positioners
    try:
        inserv.add(
                'positioner', 
                HERE / 'hardware' / 'positioner' / 'positioner.py', 
                'XYZPositioner', 
                [hcf.AMC_IP]
            )
    except Exception as ee:
        print(ee)

    # laser
    try:
        inserv.add(
                'laser', 
                HERE / 'hardware' / 'laser' / 'laser.py', 
                'LaserControl', 
                [hcf.LASER_SN]
            )
    except Exception as ee:
        print(ee)

#===============================================================================
# start the Dash GUI ###############################################################################
import webbrowser
import dash
from app.main import *

if not DEBUG:
    webbrowser.open(f'http://127.0.0.1:{GUI_PORT}') 
app.run(
        host="0.0.0.0", 
        port=GUI_PORT,
        threaded=False, # single-threaded only with the built-in WSGI server!!
        debug=DEBUG,
        use_reloader=RELOAD,
        # dev_tools_hot_reload=True,
        dev_tools_silence_routes_logging=SILENCE_LOGGING
)
#--------------------------------------------------------------------------------------------------
