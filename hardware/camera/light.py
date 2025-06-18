# hardware/whitelight.py

from typing import Callable, Optional

import nidaqmx


class WhiteLight:
    """
    Control a white-light LED over one AO channel.
    You can set intensity by percent or by voltage, and turn on/off.
    """

    def __init__(
        self,
        channel: str,
        percent_to_volt: Optional[Callable[[float], float]] = None,
        name: str = "WhiteLight",
        v_min: float = 0.0,
        v_max: float = 5.0,
    ):
        self.channel = channel
        self.v_min = v_min
        self.v_max = v_max
        self._calibration = percent_to_volt or (
            lambda pct: pct / 100.0 * (v_max - v_min) + v_min
        )
        self._task: Optional[nidaqmx.Task] = None
        self._last_voltage: float = v_min
        self._init_task(name)

    def _init_task(self, task_name: str):
        if self._task is None:
            self._task = nidaqmx.Task(task_name)
            ao = self._task.ao_channels.add_ao_voltage_chan(
                self.channel, min_val=self.v_min, max_val=self.v_max
            )
            # you can set defaults on the channel here if needed
            self._task.start()

    def set_voltage(self, voltage: float):
        """Set raw voltage (clamped to [v_min, v_max])."""
        if voltage < self.v_min or voltage > self.v_max:
            raise ValueError(
                f"Voltage must be between {self.v_min} V and {self.v_max} V."
            )
        self._init_task(self._task.name if self._task else "WhiteLight")
        self._task.write([voltage], auto_start=False)
        self._last_voltage = voltage

    def set_percent(self, percent: float):
        """Set intensity by percent (0–100%)."""
        if not (0.0 <= percent <= 100.0):
            raise ValueError("Percent must be between 0 and 100.")
        v = self._calibration(percent)
        self.set_voltage(v)

    def turn_on(self):
        """Restore to last set voltage (or zero if never set)."""
        self.set_voltage(self._last_voltage)

    def turn_off(self):
        """Set output voltage to zero."""
        self.set_voltage(self.v_min)

    def close(self):
        """Stop and close the NI-DAQ task."""
        if self._task:
            try:
                self._task.stop()
                self._task.close()
            except Exception:
                pass
            finally:
                self._task = None

    def restart(self):
        """Reinitialize if you’ve closed the task."""
        self._init_task(self._task.name if self._task else "WhiteLight")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        self.close()
