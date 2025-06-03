import logging
import time

import numpy as np

from hardware import config as hcf
from hardware.daq.sidig import TERMIN_INPUT_1MOHM
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import (
    HIGH,
    INF,
    LOW,
    OutputState,
    TriggerRearm,
    TriggerStart,
)
from measurement.task_base import Measurement

logger = logging.getLogger(__name__)
hw = HardwareManager()


class PL_trace(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            laser_current=80.0,
            num_segment=64,
            pre_trig_size=16,
            segment_size=256 * 16 * 2,
            sampling_rate=10e6,
            amp_input=1000,
            readout_ch=hcf.SIDIG_chmap["apd"],
            terminate_input=TERMIN_INPUT_1MOHM,
            DCCOUPLE=0,
            wait_time=1e7,
            window_size=20.0,
            scale_window=5.0,
            run_time=3600.0,  # Total run time in seconds
        )
        # TODO move these calculations to the _setup_exp
        __paraset["post_trig_size"] = (
            __paraset["segment_size"] - __paraset["pre_trig_size"]
        )
        __paraset["memsize"] = __paraset["num_segment"] * __paraset["segment_size"]
        __paraset["notify_size"] = int(__paraset["memsize"] // 4)

        __dataset = dict(
            x_data=[],
            y_data=[],
            run_time=0,
            num_repeat=0,
        )

        super().__init__(name, __paraset, __dataset)
        # self.start_time = None

    def _setup_exp(self):
        logger.debug("Setting up PL_trace experiment")
        # Clean up instruments
        hw.laser.laser_off()
        hw.dig.stop_card()
        hw.pg.forceFinal()
        hw.pg.reset()

        # Set up the laser
        hw.laser.open()
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(self.paraset["laser_current"], save_memory=False)

        # Set up the pulse generator
        time_on = self.paraset["segment_size"] * (
            1 / self.paraset["sampling_rate"] * 1e9
        )
        wait = self.paraset["wait_time"]
        seq_laser = [
            (time_on / 3, HIGH),
            (time_on / 3, LOW),
            (time_on / 3, HIGH),
            (wait, LOW),
        ]
        seq_dig = [(time_on, HIGH), (wait, LOW)]

        hw.pg.setDigital("sdtrig", seq_dig)
        hw.pg.setDigital("laser", seq_laser)
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

        # Set up the digitizer
        hw.dig.reset_param()
        hw.dig.assign_param(
            dict(
                readout_ch=self.paraset["readout_ch"],
                amp_input=self.paraset["amp_input"],
                num_segment=self.paraset["num_segment"],
                pretrig_size=self.paraset["pre_trig_size"],
                posttrig_size=self.paraset["post_trig_size"],
                segment_size=self.paraset["segment_size"],
                terminate_input=self.paraset["terminate_input"],
                DCCOUPLE=self.paraset["DCCOUPLE"],
                sampling_rate=self.paraset["sampling_rate"],
                notify_size=self.paraset["notify_size"],
                mem_size=self.paraset["memsize"],
            )
        )
        hw.dig.set_config()

        # Start hardware
        hw.pg.stream(n_runs=INF)
        hw.dig.start_buffer()
        hw.pg.startNow()
        hw.laser.laser_on()

        # Reset the pl start time
        if not self.tokeep:
            self.pl_start_time = time.time()
            # self.start_time = None  # Set to None to trigger reset in _run_exp
            logger.debug(
                "Dataset reset: x_data, y_data, num_repeat cleared;"
                # "Dataset reset: x_data, y_data, num_repeat cleared; start_time set to None"
            )

        _new_y = hw.dig.stream()  # to acquire and throw out the first data

    def _run_exp(self):
        self.new_y = hw.dig.stream()
        if self.new_y is None or len(self.new_y) == 0:
            logger.debug("No data from digitizer")
            return
        self.timestamp = time.time() - self.pl_start_time

    def _organize_data(self):
        self.dataset["x_data"].append(self.timestamp)
        self.dataset["y_data"].append(np.mean(self.new_y) * 1e3)  # in mV
        # Keep only the last window_size seconds of data
        while (
            len(self.dataset["x_data"]) > 0
            and (self.timestamp - self.dataset["x_data"][0])
            > self.paraset["window_size"]
        ):
            self.dataset["x_data"].pop(0)
            self.dataset["y_data"].pop(0)
        self.dataset["num_repeat"] += 1
        super()._organize_data()  # update the default set

    def _shutdown_exp(self):
        logger.debug("Shutting down PL_trace experiment")
        try:
            hw.laser.laser_off()
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.dig.stop_card()
            # hw.dig.reset()
            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            logger.info("PL_trace shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.state = "error"

    def _handle_exp_error(self):
        logger.debug("Handling PL_trace experiment error")
        try:
            hw.laser.laser_off()
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            hw.dig.stop_card()
            hw.dig.reset()
            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            hw.pg.reboot()
            logger.info("PL_trace error handling complete")
        except Exception as e:
            logger.error(f"Error during error handling: {e}")
            print(f"Error handling failed: {e}")
