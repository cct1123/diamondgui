#!/usr/bin/env python
"""
Start up an instrument server and load drivers for ODMR experiments.

Author: Jacob Feder
Date: 12/27/2021
"""
import logging
from pathlib import Path
import time
from nspyre import InstrumentGateway, InstrumentGatewayError, InstrumentServer, InstrumentServerDeviceExistsError,  inserv_cli
from nspyre import nspyre_init_logger



HERE = Path(__file__).parent

# log to the console as well as a file inside the logs folder
nspyre_init_logger(
    logging.INFO,
    log_path=HERE / 'logs_dummy_laptop',
    log_path_level=logging.DEBUG,
    prefix='odmr_inserv',
    file_size=10_000_000,
)

# first try connecting to an existing instrument server, if one is already running
try:
    inserv = InstrumentGateway()
    inserv.connect()
except InstrumentGatewayError:
    # if no server was running, start one
    inserv = InstrumentServer()
    inserv.start()


inserv.add('drv', HERE / 'hardware' / 'driver_dummy.py', 'FakeInstrument')


# test real instruments-----------------------------------------------
import hardware.config_custom as hcf
# # laser
# try:
#     # inserv.add('laser', HERE / 'hardware' / 'driver_dummy.py', 'FakeInstrument')
#     inserv.add(
#             'laser', 
#             HERE / 'hardware' / 'laser' / 'laser.py', 
#             'LaserControl', 
#             hcf.LASER_SN,
#         )
# except InstrumentServerDeviceExistsError:
#     pass
# -------------------------------------------------------------------
inserv.add(
            'laser', 
            HERE / 'hardware' / 'laser' / 'laser.py', 
            'LaserControl', 
            hcf.LASER_SN,
        )


inserv_cli(inserv)

# while True:
#     time.sleep(1)

# # inserv.stop()