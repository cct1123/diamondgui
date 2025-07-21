from typing import Callable, Optional

import nidaqmx

PHASE_VOLT_MAX = 10.0
UCA_VOLT_MAX = 5.0


class Modulator:
    def __init__(self, ch_amp: str, ch_phase: str):
        self.ch_amp = ch_amp
        self.ch_phase = ch_phase
        self.amp_calibration: Optional[Callable[[float], float]] = None
        self.phase_calibration: Optional[Callable[[float], float]] = None
        self.task_amp = None
        self.task_phase = None
        self._init_tasks()

    def _init_tasks(self):
        if self.task_amp is None:
            self.task_amp = nidaqmx.Task("MW UCA")
            self.task_amp.ao_channels.add_ao_voltage_chan(
                self.ch_amp, min_val=0.0, max_val=UCA_VOLT_MAX
            )
            self.task_amp.start()
        if self.task_phase is None:
            self.task_phase = nidaqmx.Task("MW Phase")
            self.task_phase.ao_channels.add_ao_voltage_chan(
                self.ch_phase, min_val=0.0, max_val=PHASE_VOLT_MAX
            )
            self.task_phase.start()

    def load_amp_calibration(self, percent_to_volt: Callable[[float], float]):
        self.amp_calibration = percent_to_volt

    def load_phase_calibration(self, deg_to_volt: Callable[[float], float]):
        self.phase_calibration = deg_to_volt

    def set_amp_percent(self, percent: float):
        if not (0.0 <= percent <= 100.0):
            raise ValueError("Amplitude percent must be in range 0–100%.")
        if self.amp_calibration is None:
            raise RuntimeError("Amplitude calibration not loaded.")
        self.set_amp_volt(self.amp_calibration(percent))

    def set_phase_deg(self, degrees: float):
        if not (0.0 <= degrees <= 360.0):
            raise ValueError("Phase degrees must be in range 0–360°.")
        if self.phase_calibration is None:
            raise RuntimeError("Phase calibration not loaded.")
        self.set_phase_volt(self.phase_calibration(degrees))

    def set_amp_volt(self, voltage: float):
        if not (0.0 <= voltage <= UCA_VOLT_MAX):
            raise ValueError(
                f"Amplitude voltage must be in range 0–{int(UCA_VOLT_MAX)} V."
            )
        self._init_tasks()
        self.task_amp.write([voltage], auto_start=False)

    def set_phase_volt(self, voltage: float):
        if not (0.0 <= voltage <= PHASE_VOLT_MAX):
            raise ValueError(
                f"Phase voltage must be in range 0–{int(PHASE_VOLT_MAX)} V."
            )
        self._init_tasks()
        self.task_phase.write([voltage], auto_start=False)

    def set_amp(self, s: str):
        s = s.strip().lower()
        if s.endswith("v"):
            voltage = float(s[:-1])
            self.set_amp_volt(voltage)
        elif s.endswith("%"):
            percent = float(s[:-1])
            self.set_amp_percent(percent)
        else:
            raise ValueError(
                "Amplitude string must end with 'V' or '%' (e.g. '1.2V', '80%')."
            )

    def set_phase(self, s: str):
        s = s.strip().lower()
        if s.endswith("v"):
            voltage = float(s[:-1])
            self.set_phase_volt(voltage)
        elif s.endswith("deg"):
            degrees = float(s[:-3])
            self.set_phase_deg(degrees)
        else:
            raise ValueError(
                "Phase string must end with 'V' or 'deg' (e.g. '1.5V', '180deg')."
            )

    def close(self):
        if self.task_amp:
            self.task_amp.stop()
            self.task_amp.close()
            self.task_amp = None
        if self.task_phase:
            self.task_phase.stop()
            self.task_phase.close()
            self.task_phase = None

    def restart(self):
        """Reinitialize after close() if needed."""
        self._init_tasks()

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ---------------------- Dummy calibration functions ---------------------- #


def dummy_amp_percent_to_voltage(percent: float) -> float:
    """
    Dummy calibration: 0–100% → 0–5V linearly.
    Replace this with experimental fit.
    """
    if not (0 <= percent <= 100):
        raise ValueError("Amplitude percent must be between 0 and 100.")
    return 5.0 * percent / 100.0


def dummy_phase_deg_to_voltage(degrees: float) -> float:
    """
    Dummy calibration: 0–360° → 0–5V linearly.
    Replace this with experimental fit.
    """
    if not (0 <= degrees <= 360):
        raise ValueError("Phase degrees must be between 0 and 360.")
    return 5.0 * degrees / 360.0


# ---------------------- Example usage ---------------------- #

if __name__ == "__main__":
    # Replace with your NI DAQ device channels
    ch_amp = "Dev1/ao0"
    ch_phase = "Dev1/ao1"

    mwmod = Modulator(ch_amp, ch_phase)
    mwmod.load_amp_calibration(dummy_amp_percent_to_voltage)
    mwmod.load_phase_calibration(dummy_phase_deg_to_voltage)

    # Smart string-based input
    mwmod.set_amp("80%")
    mwmod.set_phase("180deg")

    mwmod.set_amp("2.5V")
    mwmod.set_phase("1.2V")

    # Restart after manual close
    mwmod.close()
    mwmod.set_amp("1.0V")  # still works due to auto-restart
