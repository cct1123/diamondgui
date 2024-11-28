GUI_PORT = 9982
DEBUG = True
RELOAD = True and DEBUG
SILENCE_LOGGING = not DEBUG
SILENCE_LOGGING = True
ADD_HARDWARE = False
# ===============================================================================

import logging
from pathlib import Path

import psutil

import hardware.config_custom as hcf

HERE = Path(__file__).parent

python_process = []
python_process_pid = []
for p in psutil.process_iter():
    if "python" in p.name():
        python_process_pid.append(p.pid)
        python_process.append(p)

is_main_process = (
    len(python_process) == 3
)  # WARNING!! change the number by yourself when debugging!
flag_add_hardwares = (
    ((not is_main_process) and RELOAD)
    or ((not RELOAD) and is_main_process)
    or (not DEBUG)
)
flag_add_hardwares = flag_add_hardwares and ADD_HARDWARE
# ===============================================================================
# logging
# ===============================================================================
import logging.config

from config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)

if flag_add_hardwares:
    # load the hardware manager
    # # add some devices to the server (if they aren't already added) ##################################################

    from hardware.hardwaremanager import HardwareManager

    inserv = HardwareManager()

    # pulse generator
    try:
        inserv.add(
            "pg",
            HERE / "hardware" / "pulser" / "pulser.py",
            "PulseGenerator",
            [],
            dict(ip=hcf.PS_IP, chmap=hcf.PS_chmap, choffs=hcf.PS_choffs),
        )
    except Exception as ee:
        print(ee)

    # mw signal generator
    try:
        inserv.add(
            "mwsyn",
            HERE / "hardware" / "mw" / "mwsynthesizer.py",
            "Synthesizer",
            [hcf.VDISYN_SN],
            dict(
                vidpid=hcf.VDISYN_VIDPID,
                baudrate=hcf.VDISYN_BAUD,
                timeout=5,
                write_timeout=5,
            ),
        )
    except Exception as ee:
        print(ee)

    # # positioners
    # try:
    #     inserv.add(
    #             'positioner',
    #             HERE / 'hardware' / 'positioner' / 'positioner.py',
    #             'XYZPositioner',
    #             [hcf.AMC_IP]
    #         )
    # except Exception as ee:
    #     print(ee)

    # laser
    try:
        inserv.add(
            "laser",
            HERE / "hardware" / "laser" / "laser.py",
            "LaserControl",
            [hcf.LASER_SN],
        )
    except Exception as ee:
        print(ee)

# ===============================================================================
# start the Dash GUI ###############################################################################
import webbrowser

from app.main import *

if not DEBUG:
    webbrowser.open(f"http://127.0.0.1:{GUI_PORT}")
app.run(
    host="0.0.0.0",
    port=GUI_PORT,
    threaded=False,  # single-threaded only with the built-in WSGI server!!
    debug=DEBUG,
    use_reloader=RELOAD,
    # dev_tools_hot_reload=True,
    dev_tools_silence_routes_logging=SILENCE_LOGGING,
)
# --------------------------------------------------------------------------------------------------
