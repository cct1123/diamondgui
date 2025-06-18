"""
VDI 400GHz System
This module contains the driver for the VDI 400GHz system, which is used
to control the VDI synthesizer and the low-frequency modulation circuit.
"""

import logging
from typing import Callable

import hardware.config as hcf
from hardware.mw.mwmodulation import Modulator
from hardware.mw.mwsynthesizer import Synthesizer

logger = logging.getLogger(__name__)


class VDISource:
    """
    A class to control a Virginia Diodes Inc. (VDI) microwave source,
    encompassing both a synthesizer for frequency control and a modulator
    for amplitude and phase control.
    """

    def __init__(
        self,
        ch_amp: str,
        ch_phase: str,
        ser: str,
        vidpid="auto",
        baudrate=9600,
    ):
        """
        Initializes the VDI Source, which combines a microwave synthesizer and a modulator.
        Connections are opened upon initialization.

        Args:
            ch_amp (str): The NI-DAQ channel for amplitude control (e.g., "Dev1/ao0").
            ch_phase (str): The NI-DAQ channel for phase control (e.g., "Dev1/ao1").
            ser (str): The serial number of the VDI synthesizer.
            vidpid (str, optional): The VID:PID of the synthesizer's FTDI chip. Defaults to "auto".
            baudrate (int, optional): The baud rate for serial communication. Defaults to 9600.
        """
        self.mwsyn = Synthesizer(ser, vidpid=vidpid, baudrate=baudrate)
        self.mwmod = Modulator(ch_amp=ch_amp, ch_phase=ch_phase)
        logger.info("VDISource initialized and connections are open.")

    def open(self):
        """
        Opens or re-opens the connections to the synthesizer and modulator
        after they have been closed.
        """
        logger.info("Opening VDI Source connections...")
        if hasattr(self, "mwsyn"):
            self.mwsyn.open()  # Re-opens the serial port if it's closed
            if self.mwsyn.serialcom.is_open:
                logger.info("Synthesizer serial port is open.")
        if hasattr(self, "mwmod"):
            self.mwmod.restart()  # Re-initializes the NI-DAQ tasks
            logger.info("Modulator tasks have been restarted.")
        logger.info("VDISource is open and ready.")

    def load_calibration(
        self, amp_cal: Callable[[float], float], phase_cal: Callable[[float], float]
    ):
        """
        Loads the calibration functions for amplitude and phase modulation.

        Args:
            amp_cal (Callable[[float], float]): A function that converts amplitude percentage (0-100) to voltage.
            phase_cal (Callable[[float], float]): A function that converts phase degrees (0-360) to voltage.
        """
        self.mwmod.load_amp_calibration(amp_cal)
        self.mwmod.load_phase_calibration(phase_cal)
        logger.info("Amplitude and Phase calibration loaded.")

    def set_freq(self, frequency: float):
        """
        Set the microwave frequency.
        If the connection is found to be closed, it will be automatically reopened.

        Args:
            frequency (float): The desired frequency in GHz.
        """
        try:
            # Check if the synthesizer port is open, and reopen if necessary.
            if not self.mwsyn.serialcom.is_open:
                logger.warning("Synthesizer connection is closed. Reopening...")
                self.mwsyn.open()  # Calls the open method from the Synthesizer class

            logger.info(f"Setting frequency to {frequency} GHz...")
            returned_freq = self.mwsyn.cw_frequency(frequency / hcf.VDISYN_multiplier)
            if returned_freq is not None:
                logger.info(
                    f"Synthesizer frequency set to {returned_freq * hcf.VDISYN_multiplier:.6f} GHz."
                )
                return returned_freq * hcf.VDISYN_multiplier
            else:
                logger.warning("Failed to confirm frequency setting from synthesizer.")
                return None
        except Exception:
            logger.exception("Error setting frequency")

    def set_amp(self, amplitude: float):
        """
        Set the microwave amplitude in percent.
        This function will automatically restart the required tasks if the connection was closed.
        Requires an amplitude calibration function to be loaded first via `load_calibration`.

        Args:
            amplitude (float): The desired amplitude as a percentage (from 0.0 to 100.0).
        """
        logger.info(f"Setting amplitude to {amplitude}%%...")
        try:
            self.mwmod.set_amp_percent(amplitude)
            logger.info("Amplitude set successfully.")
        except (ValueError, RuntimeError):
            logger.exception("Error setting amplitude")

    def set_phase(self, phase: float):
        """
        Set the microwave phase in degrees.
        This function will automatically restart the required tasks if the connection was closed.
        Requires a phase calibration function to be loaded first via `load_calibration`.

        Args:
            phase (float): The desired phase in degrees (from 0.0 to 360.0).
        """
        logger.info(f"Setting phase to {phase} deg...")
        try:
            self.mwmod.set_phase_deg(phase)
            logger.info("Phase set successfully.")
        except (ValueError, RuntimeError):
            logger.exception("Error setting phase")

    def set_amp_volt(self, voltage: float):
        """
        Set the amplitude modulation voltage directly.

        Args:
            voltage (float): The desired voltage for the amplitude modulator (typically 0-5V).
        """
        logger.info(f"Setting amplitude voltage to {voltage} V...")
        try:
            # This calls the corresponding method in the underlying Modulator object
            self.mwmod.set_amp_volt(voltage)
            logger.info("Amplitude voltage set successfully.")
        except Exception:
            logger.exception("Error setting amplitude voltage")

    def set_phase_volt(self, voltage: float):
        """
        Set the phase modulation voltage directly.

        Args:
            voltage (float): The desired voltage for the phase modulator (typically 0-5V).
        """
        logger.info(f"Setting phase voltage to {voltage} V...")
        try:
            # This calls the corresponding method in the underlying Modulator object
            self.mwmod.set_phase_volt(voltage)
            logger.info("Phase voltage set successfully.")
        except Exception:
            logger.exception("Error setting phase voltage")

    def reset(self):
        """
        Resets the instrument to a default state.
        This involves rebooting the synthesizer and setting modulator voltages to 0V.
        """
        logger.info("Resetting VDI Source...")
        try:
            logger.info("Rebooting the synthesizer...")
            # This calls the corresponding method in the underlying Synthesizer object
            self.mwsyn.reboot()
            self.mwsyn.close_gracefully()
            self.mwsyn.open()  # Reopen the synthesizer connection
            logger.info("Synthesizer rebooted.")

            logger.info("Setting modulator voltages to 0V...")
            self.set_amp_volt(0.0)
            self.set_phase_volt(0.0)
            self.mwmod.restart()  # Restart the modulator tasks
            logger.info("VDISource reset complete.")
        except Exception:
            logger.exception("An error occurred during VDI Source reset.")

    def close(self):
        """
        Closes the connections to the synthesizer and modulator, releasing all hardware resources.
        """
        logger.info("Closing VDI Source...")
        if hasattr(self, "mwsyn"):
            self.mwsyn.close_gracefully()
        if hasattr(self, "mwmod"):
            self.mwmod.close()
        logger.info("VDISource closed.")

    def __enter__(self):
        """Enables the use of the 'with' statement for resource management."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures that the close method is called upon exiting a 'with' block."""
        self.close()
