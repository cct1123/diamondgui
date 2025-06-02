import logging

import nidaqmx
import numpy as np
from nidaqmx.constants import (
    AcquisitionType,
    Edge,
    TaskMode,
    TerminalConfiguration,
    VoltageUnits,
)
from nidaqmx.stream_readers import AnalogSingleChannelReader, DigitalSingleChannelReader

import nidaqmx
from nidaqmx.constants import TerminalConfiguration, VoltageUnits, Edge, AcquisitionType, READ_ALL_AVAILABLE
from nidaqmx.stream_readers import AnalogSingleChannelReader
from hardware import config as hcf
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import (
    OutputState,
    TriggerStart,
    TriggerRearm,
    HIGH,
    LOW,
    INF,
    REPEAT_INFINITELY
)
from measurement.task_base import Measurement
import math
from functools import reduce

def lcm(a, b):
    """Calculate the least common multiple of two numbers."""
    return abs(a * b) // math.gcd(a, b)


def lcm_of_list(numbers):
    """Find the LCM of a list of numbers."""
    return reduce(lcm, numbers)

def seqtime(seq_tb):
    return np.sum([pulse[-1] for pulse in seq_tb])


# some constants
Hz = 1e-9 # GHz
kHz = 1e-6 # GHz
MHz = 1e-3 # GHz
pi = np.pi

hm = HardwareManager()

timebase = lcm_of_list(
    [hcf.VDISYN_timebase, hcf.SIDIG_timebase, hcf.PS_timebase, hcf.RSRF_timebase]
)

class EmulationAERIS(Measurement):


    def __init__(self, name="default"):
        # ==some dictionaries stored with some default values--------------------------
        __paraset = dict(
            # Settings for MW
            mw_freq=398.5467,  # GHz
            mw_hopspan=2 * 2.87E-3,  # GHz
            # mw_hoptime=mw_hoptime,  # (Uncomment if defined)
            mw_powervolt=5.0,  # Voltage 0.0 to 5.0
            mw_phasevolt=0.0,  # Voltage 0.0 to 5.0
            # Setting for data acquisition
            min_volt=-10.0E-3,  # V
            max_volt=150.0E-3,  # V
            # Setting for laser
            laser_current=95.0,  # Percentage
            # Settings for the RF
            rf_freq=600,  # MHz

            # Nuclear spin preparation
            ninit_pihalf=1000,  # ns
            # Locking block
            t_lock_idle=20,  # ns
            t_lock_rf=3980,  # ns
            n_lock = 2,
            t_lbloc_mwwait = 20,  # ns
            t_lbloc_mw = 7908,  # ns
            # Laser read and init block
            t_ribloc_wait=400.0,  # ns
            
            t_ribloc_laser=6800,  # ns
            t_ribloc_isc=800.0,  # ns
            # Reference blocks
            t_brbloc_wait=400.0,  # ns
            t_brbloc_laser=6800,  # ns
            t_brbloc_isc=800.0,  # ns

            t_brbloc_mw_idle=7908,  # ns
            t_brbloc_mw=7908,  # ns
            t_drbloc_wait=400.0,  # ns
            t_brbloc_laser=6800,  # ns
            t_brbloc_isc=800.0,  # ns

            # Clearing block
            t_cbloc_laser=10,  # ns
            t_cbloc_isc=400,  # ns
            n_cbloc_laser=20,
            # Free evolution
            t_fevol=80e3,  # ns
            # Tracking
            n_track=5000,  # Repetitions
            # Stopping criteria
            rate_refresh=10  # Hz
        )


        # !!< has to be specific by users>
        __dataset = dict(
            num_repeat=0,
            freq=np.zeros(10),
            sig_mw_rise=np.zeros(10),
            sig_mw_fall=np.zeros(10),
            sig_nomw_rise=np.zeros(10),
            sig_nomw_fall=np.zeros(10),
        )
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def check_param(self):
        paraset = self.paraset

        t_lock = paraset['t_lock_idle'] + paraset['t_lock_rf'] + paraset['t_lock']  # ns
        t_lbloc = t_lock * paraset['n_lock']
        t_ribloc = paraset['t_ribloc_wait'] + paraset['t_ribloc_laser']+paraset['t_ribloc_isc'] 
        t_brbloc = paraset['t_brbloc_wait'] + paraset['t_brbloc_laser']+paraset['t_brbloc_isc'] 
        t_drbloc = paraset['t_brbloc_mwwait']+paraset['t_brbloc_mw']+paraset['t_drbloc_wait'] + paraset['t_drbloc_isc'] + paraset['t_drbloc_laser']
        t_cbloc = paraset['t_cbloc_laser'] * paraset['n_cbloc_laser'] + paraset['t_cbloc_isc']


        t_lbloc_mwwait=20.0,  # ns
        

        n_fevol_div=80e3 // ((t_lock_idle + t_lock_rf) * 2),
        t_fevol=(80e3 // ((t_lock_idle + t_lock_rf) * 2)) * ((t_lock_idle + t_lock_rf) * 2),
        t_brbloc=((t_lock_idle + t_lock_rf) * 2),  # ns
        t_drbloc=((t_lock_idle + t_lock_rf) * 2) + ((t_lock_idle + t_lock_rf) * 2),  # ns
        t_cbloc=(80e3 // ((t_lock_idle + t_lock_rf) * 2)) * ((t_lock_idle + t_lock_rf) * 2) - ((t_lock_idle + t_lock_rf) * 2) - (((t_lock_idle + t_lock_rf) * 2) + ((t_lock_idle + t_lock_rf) * 2)) - ((t_lock_idle + t_lock_rf) * 2),  # ns
        t_cbloc_pad= #ns
        t_atrack=((t_lock_idle + t_lock_rf) * 2) + ((80e3 // ((t_lock_idle + t_lock_rf) * 2)) * ((t_lock_idle + t_lock_rf) * 2)),  # ns
        T_alltrack=5000 * (((t_lock_idle + t_lock_rf) * 2) + ((80e3 // ((t_lock_idle + t_lock_rf) * 2)) * ((t_lock_idle + t_lock_rf) * 2))),  # Total time in ns


    def _setup_exp(self):
        pass

    def _run_exp(self):
        pass
    def _organize_data(self):
        pass

    def _handle_exp_error(self):
        pass

    def _shutdown_exp(self):
        pass