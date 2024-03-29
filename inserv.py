import logging
from pathlib import Path

from nspyre import InstrumentGateway, InstrumentGatewayError, InstrumentServer, InstrumentServerDeviceExistsError,  serve_instrument_server_cli
from nspyre import nspyre_init_logger

import hardware.config_custom as hcf

HERE = Path(__file__).parent

nspyre_init_logger(
    logging.INFO,
    log_path= HERE / 'hardware' / 'logs_hardware',
    log_path_level=logging.DEBUG,
    prefix='inserv',
    file_size=10_000_000,
)



# first try connecting to an existing instrument server, if one is already running
try:
    # inserv = InstrumentGateway(port=INSERV_PORT)
    inserv = InstrumentGateway()
    inserv.connect()
except InstrumentGatewayError:
    # if no server was running, start one
    # inserv = InstrumentServer(port=INSERV_PORT)
    inserv = InstrumentServer()
    inserv.start()

# add some devices to the server (if they aren't already added) ##################################################

# mw signal generator
try:
    inserv.add(
        'mwgen', 
        HERE / 'hardware' / 'mw' / 'mwsythesizer.py', 
        'Synthesizer', 
        # *arg, 
        # **karg
    )
except InstrumentServerDeviceExistsError:
    pass

# positioners
try:
    inserv.add(
            'positioner', 
            HERE / 'hardware' / 'positioner' / 'positiioner.py', 
            'Positioner', 
            [hcf.AMC_IP],
        )
except InstrumentServerDeviceExistsError:
    pass

# laser
try:
    inserv.add(
            'laser', 
            HERE / 'hardware' / 'laser' / 'laser.py', 
            'LaserControl', 
            [hcf.LASER_SN],
        )
except InstrumentServerDeviceExistsError:
    pass

# daq
try:
    inserv.add(
            'daq', 
            HERE / 'hardware' / 'daq' / 'nidaq.py', 
            'DAQControl', 
            [hcf.DAQch_APD,
            hcf.DAQch_Clock,
            hcf.DAQch_Trig]
        )
except InstrumentServerDeviceExistsError:
    pass


# -------------------------------------------------------------------------------------------------------------------

# run a CLI (command-line interface) that allows the user to enter
# commands to control the server
serve_instrument_server_cli(inserv)

