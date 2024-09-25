'''
the parameters here will overwrite the default hardware config
'''
from hardware.config import *

PSch_Laser = 0 # trigger the laser
PSch_DAQClock = 1 # as the clock for DAQ
PSch_DAQstart = 3 # trigger pulse to start the DAQ
PSch_MW_A = 4 # control switch of MW line with 0 phase shift  
PSch_MW_B = 5 # control switch of MW line with certain phase shift  
PSch_RFconsole = 7 # to trigger the red stone RF console
PSch_PHASE_B = 8 # control the phase of the MW line B, analog channel

PS_chmap = {"laser":PSch_Laser, 
            "dclk":PSch_DAQClock, 
            "dtrig":PSch_DAQstart,
            "mwA":PSch_MW_A, 
            "mwB":PSch_MW_B,
            "phB":PSch_PHASE_B
            }

PS_choffs = {"laser":0, 
            "dclk":0, 
            "dtrig":0,
            "mwA":0, 
            "mwB":0,
            "phB":0
            }