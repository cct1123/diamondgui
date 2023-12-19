'''
create: 2023-04-18
unfinished!!
    not using instrument server
    not using data server
it will be modified later
'''


########### hardware parts, should  instrument server, implement later

import nidaqmx
from nidaqmx.constants import TerminalConfiguration, VoltageUnits, Edge, AcquisitionType, READ_ALL_AVAILABLE
from nidaqmx.constants import LogicFamily 
# TWO_POINT_FIVE_V, THREE_POINT_THREE_V, FIVE_V

from nidaqmx import stream_readers 

##########

import numpy as np
import time
import threading

from measurement.task_base import Measurement
from hardware.config_custom import DAQch_APD

# 
# from task_base import StoppableThread
# DAQch_APD = "/Dev1/ai16"

class PLTrace(Measurement):

    def __init__(self):
        super().__init__()

        self.reset_paraset()
        self.reset_dataset()

    def reset_paraset(self):
        min_volt = -5.0 # [V]
        max_volt = 5.0 # [V]
        n_samples = 5000 # [V]
        refresh_rate = 30.0 # [Hz]
        sampling_rate = n_samples*refresh_rate
        history_window = 1.0 # [s]
        num_trace = int(history_window*refresh_rate)

        self.paraset = dict(
            min_volt = min_volt,
            max_volt = max_volt,
            n_samples = n_samples,
            refresh_rate = refresh_rate, # [Hz]
            sampling_rate = sampling_rate, 
            history_window = history_window,
            num_trace = num_trace
        ) # parameters maybe dependent on each other

    def reset_dataset(self):
        num_trace = self.paraset["num_trace"]
        self.dataset = dict(
            timestamp=np.arange(num_trace), 
            data= np.zeros(num_trace, dtype=np.float64, order='C')
        )

    def _setup_exp(self):
        super()._setup_exp

        # self.task = nidaqmx.Task(new_task_name="PL Trace")
        self.task = nidaqmx.Task(self._name)
        ch_clock = ""
        clock_edge = Edge.RISING
        min_volt = self.paraset["min_volt"]
        max_volt = self.paraset["max_volt"]
        n_samples = self.paraset["n_samples"]
        sampling_rate = self.paraset["sampling_rate"]

        self.task = nidaqmx.Task()
        self.channel = self.task.ai_channels.add_ai_voltage_chan(
            DAQch_APD,"",
            # TerminalConfiguration.RSE,
            TerminalConfiguration.DIFF,
            min_volt, max_volt,
            VoltageUnits.VOLTS
        )
        # Configure sample clock
        self.task.timing.cfg_samp_clk_timing(
            sampling_rate,
            ch_clock,
            clock_edge,
            AcquisitionType.FINITE, 
            n_samples)
        self.task.timing.ai_conv_src = self.ch_clock
        self.task.timing.ai_conv_active_edge = self.clock_edge

        # Configure reader stream
        self.reader = stream_readers.AnalogSingleChannelReader(self.task.in_stream)
        # reader = stream_readers.AnalogMultiChannelReader(task.in_stream)
        self.reader.read_all_avail_samp  = True

        self.buffer = np.zeros(n_samples, dtype=np.float64, order='C')

        num_trace = self.paraset["num_trace"]
        # self.dataset["timestamp"] = np.arange(num_trace)
        # self.dataset["data"] = np.zeros(num_trace, dtype=np.float64, order='C')
        self.dataset["timestamp"] = np.full(num_trace, np.nan,  order='C')
        self.dataset["data"] = np.full(num_trace, np.nan,  order='C')

        self.task.start()

        self.num_run = 2**32 # run indefinitely
        
    def _run_exp(self):
        # task.start()
        # timeout = 10
        num_read = self.reader.read_many_sample(
                self.buffer,
                READ_ALL_AVAILABLE,
                # timeout, 
                10.0
            )
        self.dataset["data"][:-1] = self.dataset["data"][1:]
        self.dataset["timestamp"][:-1] = self.dataset["timestamp"][1:]
        self.dataset["timestamp"][-1] = self.time_run
        self.dataset["data"][-1] = np.mean(self.buffer)
        time.sleep(max(1/self.paraset["refresh_rate"]-(time.time()-curr_time), 0))
        # self._upload_dataserv()

    def _shutdown_exp(self):
        self.task.stop()
        self.task.close()
        self.num_iter = 0

if __name__ == "__main__":
    # for testing only
    min_volt = -5.0
    max_volt = 5.0
    n_samples = 5000
    refresh_rate = 30.0 # [Hz]
    sampling_rate = n_samples*refresh_rate
    history_window = 1.0 # [s]
    num_trace = int(history_window*refresh_rate)

    pltrace = PLTrace()
    pltrace.set_paraset(min_volt=min_volt, 
                       max_volt=max_volt, 
                       n_samples=n_samples, 
                       refresh_rate=refresh_rate, 
                       sampling_rate=sampling_rate, 
                       history_window = history_window,
                       num_trace = num_trace
                      )
    pltrace.start() 
