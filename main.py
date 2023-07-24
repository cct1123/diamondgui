import os
import signal
import webbrowser
import dash

# run the instrument server and data server ########################################################
# !! run the bash scripts manually when debuging!!

import subprocess
import time
comand = "start /wait bash run_dataserv.sh"
process_dataserv = subprocess.Popen(comand, shell=True)
# time.sleep(1) 
comand = "start /wait bash run_inserv.sh"
process_inserv = subprocess.Popen(comand, shell=True)
# time.sleep(1)

pid_dataserv = process_dataserv.pid
pid_inserv = process_inserv.pid
pid_appserv = os.getpid()

from gui.app import *
@app.callback(dash.Output("shutdown-dummy", "data"), dash.Input('button-shutdown', 'on'), prevent_initial_call=True)
def _shutdown_app(_):
        # os.kill(pid_dataserv, signal.SIGTERM)
        process_inserv.terminate()
        print(f"Killed Data server with PID :{pid_dataserv}")
        # os.kill(pid_inserv, signal.SIGTERM)
        process_dataserv.terminate()
        print(f"Killed Instrument server with PID :{pid_inserv}")
        print(f"Killed Dash App server with PID :{pid_appserv}")
        os.kill(pid_appserv, signal.SIGTERM)
        return []

#---------------------------------------------------------------------------------------------------------------------
# start the Dash GUI ###############################################################################

GUI_PORT = 9982
DEBUG = False
# webbrowser.open(f'http://127.0.0.1:{GUI_PORT}') 
app.run_server(
        host="0.0.0.0", 
        debug=DEBUG,
        port=GUI_PORT,
        threaded=False # single-threaded only with the built-in WSGI server!!
)
#--------------------------------------------------------------------------------------------------
