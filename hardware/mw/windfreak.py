from windfreak import SynthHD


class WindfreakSynth(object):
    def __init__(self, port="COM4"):
        self.port = port
        self.synth = None

        self.connect()

    def connect(self):
        """Initialize connection (matches your working code)"""
        try:
            self.synth = SynthHD("COM4")
            self.synth.init()
            print(f"Connected to Windfreak on {self.port}")
        except Exception as e:
            print(f"Connection failed: {e}")
            raise

    def set_output(self, freq, power=0, channel=0):
        """Set frequency and power (like your working example)"""
        if not self.synth:
            raise RuntimeError("Device not connected")

        ch = self.synth[channel]
        # disable output
        ch.enable = False
        self.synth.enable = False

        # set frequency and power
        ch.power = power
        ch.frequency = freq

        # output MW
        ch.enable = True
        self.synth.enable = True
        # print(f"Channel {channel}: {freq / 1e6} MHz, {power} dBm (ON)")

    def disable(self, channel=0):
        """Turn off output (matches your disable logic)"""
        if self.synth:
            self.synth[channel].enable = False
            self.synth.enable = False
            print(f"Channel {channel} disabled")

    def disconnect(self):
        """Cleanup on destruction"""
        self.synth.disable()
        self.synth.close()
