GUI_PORT = 9982
DEBUG = False
RELOAD = True and DEBUG
SILENCE_LOGGING = not DEBUG
SILENCE_LOGGING = True
ADD_HARDWARE = True
# ===============================================================================

from pathlib import Path

import psutil

HERE = Path(__file__).parent

python_process = []
python_process_pid = []
for p in psutil.process_iter():
    if "python" in p.name():
        python_process_pid.append(p.pid)
        python_process.append(p)

is_main_process = (
    len(python_process) == 5
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
from logmodule import setup_logging

setup_logging()

if flag_add_hardwares:
    # load the hardware manager
    # # add some devices to the server (if they aren't already added) ##################################################

    from hardware.hardwaremanager import HardwareManager

    hm = HardwareManager()
    hm.add_default_hardware()

# ===============================================================================
# start the Dash GUI ###############################################################################
import webbrowser

from gui.main import app

if not DEBUG:
    webbrowser.open(f"http://127.0.0.1:{GUI_PORT}")
app.run(
    host="0.0.0.0",
    port=GUI_PORT,
    threaded=True,  # single-threaded only with the built-in WSGI server!!
    debug=DEBUG,
    use_reloader=RELOAD,
    # dev_tools_hot_reload=True,
    dev_tools_silence_routes_logging=SILENCE_LOGGING,
)
# --------------------------------------------------------------------------------------------------
