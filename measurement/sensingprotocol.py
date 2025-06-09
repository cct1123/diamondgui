import logging
import time

import numpy as np

from hardware.hardwaremanager import HardwareManager
from measurement.task_base import Measurement

logger = logging.getLogger(__name__)
hw = HardwareManager()


class EmulatorAERIS(Measurement):
    def __init__(self, name="dumdefault"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict(epicpara1=0, epicpara2="", volt_amp=1, freq=20.0, length=100)
        # !!< has to be specific by users>
        __dataset = dict(signal=np.zeros(1), timestamp=np.zeros(1))
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        super()._setup_exp()
        logger.debug(f"Parameters are: {self.paraset}")
        logger.debug(f"this class name: {self.__class__.__name__}")
        logger.debug("Hello it's set up!")
        logger.debug(f"total number of runs: {self.num_run}")
        self.buffer_rawdata = np.zeros(self.paraset["length"])
        self.buffer_timetime = np.zeros(self.paraset["length"])

    def _run_exp(self):
        logger.debug(f"hey fake experiment-'{self._name}' no.{self.idx_run}")
        logger.debug("I'm cooking some fake data")
        time.sleep(0.1)
        self.buffer_timetime = (np.arange(self.paraset["length"]) + self.time_run) / 1e3
        self.buffer_rawdata = (
            (1 + 0.3 * np.random.rand(self.paraset["length"]))
            * self.paraset["volt_amp"]
            * np.sin(2 * np.pi * self.paraset["freq"] * self.buffer_timetime)
        )

    def _organize_data(self):
        logger.debug("Moving data to a data server if you have one")
        self.dataset["signal"] = np.copy(self.buffer_rawdata)
        self.dataset["timestamp"] = np.copy(self.buffer_timetime) + self.buffer_timetime
        super()._organize_data()

    def _handle_exp_error(self):
        super()._handle_exp_error()
        logger.debug("dumdum measurement has troubles!")

    def _shutdown_exp(self):
        super()._shutdown_exp()
        logger.debug("goodbye dumdum measurement")
