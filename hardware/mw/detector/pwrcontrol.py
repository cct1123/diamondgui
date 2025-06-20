# pwrcontrol.py

import os

import clr


def convert_power(power_dbm, unit="dBm"):
    """
    Convert power reading from dBm to mW or µW.

    Args:
        power_dbm (float): Power in dBm.
        unit (str): Target unit. Options: "dBm", "mW", "uW".

    Returns:
        float: Converted power value.

    Example:
        convert_power(-20, "uW") → 10.0
    """
    if unit == "dBm":
        return power_dbm
    elif unit == "mW":
        return 10 ** (power_dbm / 10)
    elif unit == "uW":
        return 1e3 * 10 ** (power_dbm / 10)
    else:
        raise ValueError("Unsupported unit. Use 'dBm', 'mW', or 'uW'.")


class MWPowerMeter:
    """
    Driver for Mini-Circuits PWR-series USB power meters (e.g. PWR-18RMS-RC)
    using the mcl_pm_NET45.dll via pythonnet.
    """

    def __init__(self, dll_path="mcl_pm_NET45.dll", serial_number=None):
        """
        Initialize and connect to a power meter.

        Args:
            dll_path (str): Path to the DLL file.
            serial_number (str, optional): Device serial number to select specific unit.
        """
        self.serial_number = serial_number
        self.dll_path = dll_path
        self._load_dll()
        self._connect()

    def _load_dll(self):
        dll_dir = os.path.abspath(os.path.dirname(self.dll_path))
        if dll_dir not in os.sys.path:
            os.sys.path.append(dll_dir)
        dll_name = os.path.splitext(os.path.basename(self.dll_path))[0]
        clr.AddReference(dll_name)
        from mcl_pm_NET45 import usb_pm

        self.usb_pm_class = usb_pm

    def _connect(self):
        self.device = self.usb_pm_class()
        if self.serial_number:
            status = self.device.Open_Sensor(self.serial_number)
        else:
            status = self.device.Open_Sensor()
        if status[0] <= 0:
            raise ConnectionError("Failed to connect to Mini-Circuits power meter.")
        self.model = self.device.GetSensorModelName()
        self.serial = self.device.GetSensorSN()

    def open(self):
        """
        (Re)connect to the power meter device.
        """
        self._connect()

    def close(self):
        """Disconnect from the power meter."""
        self.device.Close_Sensor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_id(self):
        """
        Return the model name and serial number of the connected power sensor.

        Returns:
            tuple[str, str]: (model_name, serial_number)
        """
        return self.model, self.serial

    def set_frequency(self, freq_mhz):
        """
        Set the frequency in MHz used for internal calibration.

        Args:
            freq_mhz (float): Input signal frequency in MHz.
        """
        self.device.Freq = freq_mhz

    def set_averaging(self, count=16):
        """
        Enable averaging mode and set the number of measurements to average.

        Args:
            count (int): Averaging count (1–65535). Default is 16.
        """
        self.device.AvgCount = count
        self.device.AVG = 1

    def set_speed(self, mode=1):
        """
        Set the internal measurement speed mode.

        Args:
            mode (int): Speed mode, one of:
                0 = Normal      – ~100 ms (low noise)
                1 = Fast        – ~30 ms
                2 = Very Fast   – ~10–20 ms
                3 = Ultra-Fast  – Burst mode (device-dependent)

        Raises:
            ValueError: If an unsupported mode is given.
        """
        if mode not in (0, 1, 2, 3):
            raise ValueError(
                "Speed mode must be 0 (Normal), 1 (Fast), 2 (Very Fast), or 3 (Ultra-Fast)"
            )
        self.device.Speed = mode

    def read_power(self):
        """
        Read and return the current RF power measurement in dBm.

        Returns:
            float: Power level in dBm.
        """
        return self.device.ReadPower()

    def read_power_uW(self):
        """
        Read and return the current RF power in microwatts (µW).

        Returns:
            float: Power level in µW.

        Notes:
            Conversion is done using: µW = 10^(dBm / 10) × 1000
        """
        power_dbm = self.device.ReadPower()
        power_uW = 10 ** (power_dbm / 10) * 1000
        return power_uW


if __name__ == "__main__":
    try:
        with MWPowerMeter(serial_number="12409250026") as meter:
            model, sn = meter.get_id()
            print(f"Connected to: {model} (SN: {sn})")

            meter.set_frequency(600)  # MHz
            meter.set_averaging(8)
            # meter.set_speed(1)  # Fast mode
            meter.set_speed(2)  # Very Fast mode
            for _ in range(20):
                # Read power in a loop
                power = meter.read_power()
                print(f"Measured Power: {power:.2f} dBm")

    except Exception as e:
        print("Error:", e)
