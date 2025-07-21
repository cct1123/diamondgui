import logging
import time

import numpy as np

from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import HIGH, INF, TriggerRearm, TriggerStart
from measurement.task_base import Measurement

logger = logging.getLogger(__name__)
hw = HardwareManager()

DEFAULT_PWRSPEED = 1  # descriptive constant for speed setting
DEFAULT_PWRAVG = 8  # descriptive constant for averaging


class RFPhaseTune(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            freq_mhz=600.0,
            power_dbm=0.0,
            tol_end=1e-3,
            phaseA_deg=0.0,
            initial_step_deg=10.0,
            min_step_deg=0.05,
            max_step_deg=12.0,
            rate_refresh=10.0,
        )

        __dataset = dict(
            phase_history=[],
            power_history=[],
            optimal_phase=None,
        )

        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        logger.info("Setting up Phase Calibration for the RF outputs")

        hw.pg.forceFinal()
        hw.pg.reset()

        seq_rfA = [(1e6, HIGH)]  # just to keep it on
        seq_rfB = [(1e6, HIGH)]  # just to keep it on
        hw.pg.setDigital("rfA", seq_rfA)
        hw.pg.setDigital("rfB", seq_rfB)
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)
        hw.pg.stream(n_runs=INF)
        hw.pg.startNow()

        f_mhz = self.paraset["freq_mhz"]
        p_dbm = self.paraset["power_dbm"]
        hw.windfreak.set_reference("ext", freq_hz=10e6)
        hw.windfreak.set_output(
            freq=f_mhz * 1e6, power=p_dbm, phase=0.0, channel="rfA"
        )  # synthHD uses Hz
        hw.windfreak.set_output(freq=f_mhz * 1e6, power=p_dbm, phase=0.0, channel="rfB")

        hw.pwr.set_frequency(f_mhz)  # power meter uses MHz
        hw.pwr.set_speed(DEFAULT_PWRSPEED)
        hw.pwr.set_averaging(DEFAULT_PWRAVG)

        hw.windfreak.set_phase(0, channel="rfA")
        hw.windfreak.set_phase(0, channel="rfB")

        hw.windfreak.disable_output("rfA")
        time.sleep(1 / self.paraset["rate_refresh"])
        pB_only = hw.pwr.read_power_uW()

        hw.windfreak.enable_output("rfA")
        hw.windfreak.disable_output("rfB")
        time.sleep(1 / self.paraset["rate_refresh"])
        pA_only = hw.pwr.read_power_uW()

        hw.windfreak.enable_output("rfB")

        logger.info(f"Power with only rfB: {pB_only:.3f} uW")
        logger.info(f"Power with only rfA: {pA_only:.3f} uW")

        self.reference_power = 0.5 * (pA_only + pB_only)
        self.best_power = None
        self.best_phase = None
        self.current_phase = np.random.uniform(0, 360)  # randomized initial phase
        self.prev_power = None
        self.step_size = self.paraset["initial_step_deg"]
        self.search_done = False
        self.direction = 1

    def _run_exp(self):
        if self.search_done:
            self._thread.stop_request.is_set()  # force to break the measurement loop
        hw.windfreak.set_phase(self.current_phase, channel="rfB")
        time.sleep(1.0 / self.paraset["rate_refresh"])
        power = hw.pwr.read_power_uW()

        self.dataset["phase_history"].append(self.current_phase)
        self.dataset["power_history"].append(power)

        if self.best_power is None or power < self.best_power:
            self.best_power = power
            self.best_phase = self.current_phase

        if self.prev_power is not None:
            # diff = abs(power - self.prev_power)
            if power > self.prev_power:
                self.direction *= -1
            speed = min(power / self.reference_power, 2.0)
            scaling = max(speed, 0.5)
            self.step_size = np.clip(
                self.step_size * scaling,
                self.paraset["min_step_deg"],
                self.paraset["max_step_deg"],
            )

        self.prev_power = power
        # Add 10% random noise to the step size
        noise = np.random.uniform(-0.1, 0.1)  # ±10%
        noisy_step = self.step_size * (1 + noise)
        self.current_phase = (self.current_phase + self.direction * noisy_step) % 360.0

        if self.step_size <= self.paraset["min_step_deg"]:
            termination_ratio = abs(power - self.best_power) / max(
                self.best_power, 1e-9
            )
            logger.debug(f"Termination ratio: {termination_ratio:.6e}")
            if termination_ratio < self.paraset["tol_end"]:
                self.dataset["optimal_phase"] = self.best_phase
                logger.info(
                    f"Optimal phase found: {self.best_phase:.2f} deg with power {self.best_power:.6f} uW"
                )
                self.search_done = True
        print(self.step_size)

    def _shutdown_exp(self):
        logger.info("Shutting down PhaseAdjustment task")
        hw.pg.forceFinal()
        hw.pg.constant()  # all channels to zero
        # hw.pg.reset()
        # !! DONT TURN OFF the RF OUTPUTS

    def _handle_exp_error(self):
        logger.error("Handling error in PhaseAdjustment task")
        # Separate error handling for each device
        try:
            hw.windfreak.disable_output("rfA")
            hw.windfreak.disable_output("rfB")
        except Exception as e:
            logger.error(f"Error disabling windfreak outputs: {e}")

        try:
            hw.windfreak.disconnect()
            hw.windfreak.connect()
        except Exception as e:
            logger.error(f"Error closing or opening windfreak: {e}")

        try:
            hw.pwr.close()
            hw.pwr.open()
        except Exception as e:
            logger.error(f"Error closing or opening power meter: {e}")

        try:
            hw.pg.forceFinal()
            hw.pg.constant()  # all channels to zero
            hw.pg.reset()
        except Exception as e:
            logger.error(f"Error resetting pulse generator: {e}")
