import logging

from windfreak import SynthHD

# Setup logging
logger = logging.getLogger(__name__)


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
        self.connect()

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
            self.disable_output()
            self.synth[0].enable = False
            self.synth[1].enable = False
            self.synth.enable = False
            self.synth.close()
            logger.info("SynthHD disconnected")

    def set_freq(self, freq_hz, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.frequency = freq_hz
        logger.info(f"Channel {channel}: Set frequency to {freq_hz / 1e6:.3f} MHz")

    def set_power(self, power_dbm, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.power = power_dbm
        logger.info(f"Channel {channel}: Set power to {power_dbm:.2f} dBm")

    def set_phase(self, phase_deg, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.phase = phase_deg
        logger.info(f"Channel {channel}: Set phase to {phase_deg:.1f}°")

    def enable_output(self, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.enable = True
        self.synth.enable = True
        logger.info(f"Channel {channel}: RF output enabled")

    def disable(self, channel=0):
        self.disable_output(channel)
        self.synth.enable = False
        logger.info("Global RF output disabled")

    def disable_output(self, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        ch.enable = False
        logger.info(f"Channel {channel}: RF output disabled")

    def set_output(self, freq=0.6e6, power=0, channel=0, phase=None):
        self.set_freq(freq, channel)
        self.set_power(power, channel)
        if phase is not None:
            self.set_phase(phase, channel)
        self.enable_output(channel)

    def get_channel_status(self, channel=0):
        ch = self.synth[self._resolve_channel(channel)]
        return {
            "frequency": ch.frequency,
            "power": ch.power,
            "phase": ch.phase,
            "enabled": ch.enable,
        }

    def get_all_status(self):
        return {
            "ch0": self.get_channel_status(0),
            "ch1": self.get_channel_status(1),
        }


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
