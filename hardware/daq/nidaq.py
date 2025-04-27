"""
DAQ control class to configure, read, stream a single task

ref:
    [1] qdSpectro

Author: ChunTung Cheung
Email: ctcheung1123@gmail.com
Created:  2023-01-10
Modified: 2023-02-01

"""

import logging

import nidaqmx
import numpy as np
from nidaqmx import stream_readers
from nidaqmx.constants import (
    READ_ALL_AVAILABLE,
    AcquisitionType,
    Edge,
    TerminalConfiguration,
    VoltageUnits,
)

# import hardware.config_custom as hcf


logger = logging.getLogger(__name__)


class DataAcquisition(object):
    # Currently, this class only handles configuration and reading of a single AI channel

    def __init__(
        self,
        ch_ai,
        ch_clock,
        ch_trig,
        # clock_rate, sampling_rate,
        sampling_rate,
        ch_refclk,
    ):
        self.ch_ai = ch_ai
        self.ch_clock = ch_clock
        self.ch_trig = ch_trig
        # self.clock_rate = clock_rate
        self.sampling_rate = sampling_rate
        self.clock_edge = Edge.RISING
        self.trig_edge = Edge.RISING
        self.ch_refclk = ch_refclk

        # allocate the read tasks and readers
        self.read_tasks = []
        self.readers = []
        self.buffers = []

    def config_readtask(self, n_samples, min_volt=-10.0, max_volt=10.0):
        try:
            # Create and configure an analog input voltage task
            task = nidaqmx.Task()
            channel = task.ai_channels.add_ai_voltage_chan(
                self.ch_ai,
                "",
                # TerminalConfiguration.RSE,
                TerminalConfiguration.DIFF,
                min_volt,
                max_volt,
                VoltageUnits.VOLTS,
            )
            # Configure reference clock
            task.timing.ref_clk_src = (
                self.ch_refclk
            )  # CHANGED: External reference clock (e.g., "Dev1/PFI0")
            task.timing.ref_clk_rate = (
                10e6  # CHANGED: Set reference clock frequency (e.g., 10 MHz)
            )

            # Configure sample clock
            task.timing.cfg_samp_clk_timing(
                self.sampling_rate,
                self.ch_clock,
                self.clock_edge,
                AcquisitionType.FINITE,
                n_samples,
            )
            # read_task.timing.ai_conv_src = self.ch_clock
            # read_task.timing.ai_conv_active_edge = self.clock_edge
            # Configure start trigger
            read_trig = task.triggers.start_trigger
            read_trig.cfg_dig_edge_start_trig(self.ch_trig, self.trig_edge)
            logger.info("Reference clock source: " + task.timing.ref_clk_src)
            print("Reference clock source: " + task.timing.ref_clk_src)

            # Configure reader stream
            reader = stream_readers.AnalogSingleChannelReader(task.in_stream)
            # reader = stream_readers.AnalogMultiChannelReader(task.in_stream)
            reader.read_all_avail_samp = True
            self.read_tasks.append(task)
            self.readers.append(reader)
            buffer = np.zeros(n_samples, dtype=np.float64, order="C")
            self.buffers.append(buffer)
        except Exception as excpt:
            print(excpt)
            # logger.info(f'Error configuring DAQ. Please check your DAQ is connected and powered. Exception details: {type(excpt).__name__} {excpt}')
            self.clear_preallo_all()
        return task

    def read(self, idx=0, timeout=10):
        num_read = self.readers[idx].read_many_sample(
            self.buffers[idx], READ_ALL_AVAILABLE, timeout
        )
        return self.buffers[idx]

    def clear_preallo(self, idx=0):
        del self.read_tasks[idx]
        del self.read_tasks[idx]
        del self.read_tasks[idx]

    def clear_preallo_all(self):
        self.read_tasks = []
        self.readers = []
        self.buffers = []

    def close_readtask(self, idx=0):
        self.read_tasks[idx].close()
        self.clear_preallo(idx)

    def close_readtask_all(self):
        for tk in self.read_tasks:
            tk.close()
        self.clear_preallo_all()


class Scanner(object):
    def __init__(
        self,
        ch_ai,
        ch_clock,
        ch_trig,
        sampling_rate,
    ):
        self.ch_ai = ch_ai
        self.ch_clock = ch_clock
        self.ch_trig = ch_trig
        self.sampling_rate = sampling_rate
        self.clock_edge = Edge.RISING
        self.trig_edge = Edge.RISING

        # allocate the read tasks and readers
        self.read_tasks = []
        self.readers = []
        self.buffers = []
