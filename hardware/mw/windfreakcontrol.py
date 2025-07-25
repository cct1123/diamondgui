import logging
import time as time

from windfreak import SynthHD

# Setup logging
logger = logging.getLogger(__name__)

API_PARAMS = [
    "channel",
    "frequency",
    "power",
    "calibrated",
    "temp_comp_mode",
    "vga_dac",
    "phase_step",
    "rf_enable",
    "pa_power_on",
    "pll_power_on",
    "model_type",
    "serial_number",
    "fw_version",
    "hw_version",
    "sub_version",
    "save",
    "reference_mode",
    "trig_function",
    "pll_lock",
    "temperature",
    "ref_frequency",
    "channelspacing",
    "sweep_freq_low",
    "sweep_freq_high",
    "sweep_freq_step",
    "sweep_time_step",
    "sweep_power_low",
    "sweep_power_high",
    "sweep_direction",
    "sweep_diff_freq",
    "sweep_diff_meth",
    "sweep_type",
    "sweep_single",
    "sweep_cont",
    "am_time_step",
    "am_num_samples",
    "am_cont",
    "am_lookup_table",
    "pulse_on_time",
    "pulse_off_time",
    "pulse_num_rep",
    "pulse_invert",
    "pulse_single",
    "pulse_cont",
    "dual_pulse_mod",
    "fm_frequency",
    "fm_deviation",
    "fm_num_samples",
    "fm_mod_type",
    "fm_cont",
]


class WindfreakSynth:
    """
    Windfreak SynthHD driver wrapper.
    """

    DEFAULT_CHANNEL_MAP = {
        0: 0,
        1: 1,
        "A": 0,
        "a": 0,
        "ch0": 0,
        "rfA": 0,
        "rfa": 0,
        "B": 1,
        "b": 1,
        "ch1": 1,
        "rfB": 1,
        "rfb": 1,
    }

    def __init__(self, port="COM4", channel_map=None):
        self.port = port
        self.channel_map = channel_map or self.DEFAULT_CHANNEL_MAP.copy()
        self.synth = None
        self.ch0_phase = 0
        self.ch1_phase = 0
        self.locking = "OFF"
        self.connect()
        # self.set_reference("ext", freq_hz=10e6)

    def _resolve_channel(self, channel):
        try:
            return self.channel_map[channel]
        except KeyError:
            raise ValueError(f"Invalid channel: {channel}")

    def connect(self):
        try:
            self.synth = SynthHD(self.port)
            self.synth.init()
            logger.info(f"Connected to Windfreak SynthHD on {self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            raise

    def disconnect(self):
        """Disable all outputs and close serial connection."""
        if self.synth:
            self.synth[0].enable = False
            self.synth[1].enable = False
            self.synth.close()
            logger.info("SynthHD disconnected")

    def close(self):
        # alias of disconnect
        self.disconnect()

    def set_freq(self, freq_hz, channel=0, log_it=False):
        ch = self.synth[self._resolve_channel(channel)]
        ch.frequency = freq_hz
        if log_it:
            logger.info(f"Channel {channel}: Set frequency to {freq_hz / 1e6:.3f} MHz")

    def set_power(self, power_dbm, channel=0, log_it=False):
        ch = self.synth[self._resolve_channel(channel)]
        ch.power = power_dbm
        if log_it:
            logger.info(f"Channel {channel}: Set power to {power_dbm:.2f} dBm")

    def set_phase(self, phase_deg, channel=0, locking_status="OFF", log_it=False):
        self.ch_phase_diff = self.ch0_phase - self.ch1_phase
        # ch = self.synth[self._resolve_channel(channel)]

        if locking_status == "OFF":
            self.locking = "OFF"
            if self._resolve_channel(channel) == 0:
                self.ch0_phase = phase_deg
            if self._resolve_channel(channel) == 1:
                self.ch1_phase = phase_deg
        elif locking_status == "ON":
            self.locking = "ON"
            if self._resolve_channel(channel) == 0:
                self.ch0_phase = phase_deg
                self.ch1_phase = -(self.ch_phase_diff - self.ch0_phase)
            if self._resolve_channel(channel) == 1:
                self.ch1_phase = phase_deg
                self.ch0_phase = self.ch_phase_diff + self.ch1_phase
        self.synth[0].phase = self.ch0_phase
        self.synth[1].phase = self.ch1_phase
        if log_it:
            logger.info(
                f"Channel 0 phase: {self.ch0_phase:.1f}°, Channel 1 phase: {self.ch1_phase:.1f}°, Locking: {self.locking}"
            )

    # def set_phase(self, phase_deg, channel=0):
    #     ch = self.synth[self._resolve_channel(channel)]
    #     ch.phase = phase_deg
    #     logger.info(f"Channel {channel}: Set phase to {phase_deg:.1f}°")

    def set_reference(self, mode: str, freq_hz: float):
        """
        Set the reference mode and frequency.

        - If mode is internal: freq_hz must be 10e6 or 27e6
        - If mode is external: freq_hz must be within allowed range

        Args:
            mode (str): "int", "internal", "ext", or "external"
            freq_hz (float): Frequency in Hz

        Raises:
            ValueError: if input is invalid or inconsistent
        """
        mode = mode.strip().lower()

        # Define mode aliases
        int_aliases = {"int", "internal"}
        ext_aliases = {"ext", "external"}

        # Handle internal reference
        if mode in int_aliases:
            if freq_hz == 27e6:
                selected_mode = "internal 27mhz"
            elif freq_hz == 10e6:
                selected_mode = "internal 10mhz"
            else:
                raise ValueError("Internal mode supports only 10 MHz or 27 MHz.")
            self.synth.reference_mode = selected_mode
            logger.info(f"Reference mode set to {selected_mode}")

        # Handle external reference
        elif mode in ext_aliases:
            f_range = self.synth.reference_frequency_range
            if not (f_range["start"] <= freq_hz <= f_range["stop"]):
                raise ValueError(
                    f"External frequency must be in [{f_range['start']}, {f_range['stop']}] Hz."
                )
            self.synth.reference_mode = "external"
            self.synth.reference_frequency = freq_hz
            logger.info(
                f"Reference mode set to external, frequency = {freq_hz / 1e6:.6f} MHz"
            )

        else:
            raise ValueError("Invalid mode. Use 'int' or 'ext' (or similar variants).")

    def enable_output(self, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.enable = True
        logger.info(f"Channel {channel}: RF output enabled")

    def disable_output(self, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.enable = False
        logger.info(f"Channel {channel}: RF output disabled")

    def disable(self, channel=0):
        # alias of disable_output
        self.disable_output(channel)

    def set_output(self, freq=0.6e6, power=0, channel=0, phase=None):
        self.set_freq(freq, channel)
        self.set_power(power, channel)
        if phase is not None:
            self.set_phase(phase, channel)
        self.enable_output(channel)
        logger.info(
            f"Channel {channel}: Output enabled and set to {freq / 1e6:.3f} MHz, {power:.2f} dBm"
            + (f", {phase:.1f}°" if phase is not None else "")
        )

    def get_freq(self, channel=0):
        """Get the frequency (in Hz) of the specified channel."""
        ch = self.synth[self._resolve_channel(channel)]
        freq_hz = ch.frequency
        logger.info(f"Channel {channel}: Current frequency is {freq_hz / 1e6:.3f} MHz")
        return freq_hz

    def get_power(self, channel=0):
        """Get the output power (in dBm) of the specified channel."""
        ch = self.synth[self._resolve_channel(channel)]
        power_dbm = ch.power
        logger.info(f"Channel {channel}: Current power is {power_dbm:.2f} dBm")
        return power_dbm

    def get_phase(self, channel=0):
        """Get the phase (in degrees) of the specified channel."""
        if self.locking == "OFF":
            phase = (
                self.ch0_phase
                if self._resolve_channel(channel) == 0
                else self.ch1_phase
            )
        else:  # Locking is ON, return both with relative info
            phase = (self.ch0_phase, self.ch1_phase)
        logger.info(f"Channel {channel}: Current phase is {phase}")
        return phase

    def get_output_status(self, channel=0):
        """
        Return the RF output status (True = enabled, False = disabled) of a given channel.
        """
        ch = self.synth[self._resolve_channel(channel)]
        status = ch.rf_enable
        logger.info(
            f"Channel {channel}: RF output is {'enabled' if status else 'disabled'}"
        )
        return status

    def get_reference(self):
        """
        Return current reference mode and frequency.

        Returns:
            dict:
                - "mode": "int" or "ext"
                - "frequency": float (in Hz)
        """
        raw_mode = self.synth.reference_mode.lower()
        freq = self.synth.reference_frequency

        if "internal" in raw_mode:
            mode = "int"
        elif "external" in raw_mode:
            mode = "ext"
        else:
            raise ValueError(f"Unrecognized reference mode string: {raw_mode}")

        logger.info(f"Reference mode: {mode}, Frequency: {freq / 1e6:.6f} MHz")
        return {"mode": mode, "frequency": freq}

    def get_pll_lock(self):
        """
        Returns:
            bool: True if PLL is locked, False otherwise.
        """
        status = self.synth.lock_status
        logger.info(f"PLL Lock Status: {'LOCKED' if status else 'UNLOCKED'}")
        return status

    def read_channel(self, attribute, channel=0):
        if attribute == "phase":
            return (self.ch0_phase, self.ch1_phase, self.locking)
        else:
            pass

        if attribute == "locking":
            return self.locking
        else:
            pass

        try:
            ch = self.synth[self._resolve_channel(channel)]
            return ch.read(attribute)
        except KeyError:
            raise ValueError(f"Invalid param: {attribute}")


if __name__ == "__main__":
    wf = WindfreakSynth(port="COM4")

    logger.info("Set rfA to 600 MHz, 2 dBm, 90°")
    wf.set_output(freq=600e6, power=2.0, phase=90.0, channel="rfA")

    logger.info("Set rfB to 610 MHz, 0 dBm")
    wf.set_output(freq=610e6, power=0.0, channel="rfB")

    logger.info("Channel status:")
    logger.info(wf.get_all_status())

    logger.info("Disable rfA")
    wf.disable_output("rfA")

    logger.info("Final status:")
    logger.info(wf.get_all_status())

    logger.info("Disconnecting")
    wf.disconnect()
