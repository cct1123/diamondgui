"""
Fake data acquisition system driver for demonstration purposes.

Author: Jacob Feder
Date: 12/27/2021
"""
import logging
import random
import time
import math
from rpyc.utils.classic import obtain


logger = logging.getLogger(__name__)


class FakeInstrument:
    """Simulate a data acquisition device and produce some fake data"""
    def __init__(self):
        self._output_en = False
        self._amplitude = 0.0
        self._frequency = 100e3

    def cnts(self, t: float):
        """Return the number of counts received from a fake photon counter.

        Args:
            t: acquisition time (s)

        Returns:
            integer number of counts received.
        """
        time.sleep(t)
        fwhm = 100e6
        gamma = fwhm / 2
        signal = 2000 * (2 - gamma**2/((self._frequency-3.5e9)**2 + gamma**2))
        return int(signal) + random.randint(-300, 300)

    def output_en(self):
        return self._output_en

    def set_output_en(self, tf):
        """Enable / disable the RF output.
        
        Args:
            tf: True to enable, False to disable
        """
        tf = obtain(tf)
        self._output_en = tf

    def frequency(self):
        return self._frequency

    def set_frequency(self, value):
        """Change the frequency (Hz)"""
        value = obtain(value)
        if value < 100e3 or value > 10e9:
            raise ValueError('Frequency must be in range [100kHz, 10GHz].')
        self._frequency = value
        logger.info(f'Set frequency to {self._frequency} Hz')

    def amplitude(self):
        return self._amplitude

    def set_amplitude(self, value):
        """Change the amplitude (dBm)"""
        value = obtain(value)
        if value < -30 or value > 10:
            raise ValueError('Amplitude must be in range [-30dBm, 10dBm].')
        self._amplitude = value
        logger.info(f'Set amplitude to {self._amplitude} dBm')

    def calibrate(self):
        logger.info('Sig-gen calibration succeeded.')
