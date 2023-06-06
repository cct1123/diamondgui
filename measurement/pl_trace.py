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

from measurement.task_base import StoppableThread
from hardware.config_custom import DAQch_APD

# 
# from task_base import StoppableThread
# DAQch_APD = "/Dev1/ai16"

class PLTrace():
    def __init__(self):
        self.thread = StoppableThread() # the thread the manager loop is running in
        self.lock = threading.Condition() # lock to control access to 'queue' and 'running'

        self.num_iter = 0

        # self.task = nidaqmx.Task(new_task_name="PL Trace")
        self.task = nidaqmx.Task()

        min_volt = -5.0 # [V]
        max_volt = 5.0 # [V]
        n_samples = 5000 # [V]
        refresh_rate = 30.0 # [Hz]
        sampling_rate = n_samples*refresh_rate
        history_window = 1.0 # [s]
        num_trace = int(history_window*refresh_rate)
        self.buffer = np.zeros(n_samples, dtype=np.float64, order='C')

        self.params = dict(
            min_volt = min_volt,
            max_volt = max_volt,
            n_samples = n_samples,
            refresh_rate = refresh_rate, # [Hz]
            sampling_rate = sampling_rate, 
            history_window = history_window,
            num_trace = num_trace
        ) # parameters maybe dependent on each other

        self.dataset = dict(timestamp=np.arange(num_trace), data= np.zeros(num_trace, dtype=np.float64, order='C'))

    def set_params(self, **para_dict):
            # set parametes
        # for kk, vv in para_dict:
        for kk, vv in para_dict.items():
            self.params[kk] = vv

    def _setup_exp(self):
        ch_clock = ""
        clock_edge = Edge.RISING
        min_volt = self.params["min_volt"]
        max_volt = self.params["max_volt"]
        n_samples = self.params["n_samples"]
        sampling_rate = self.params["sampling_rate"]

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
        # read_task.timing.ai_conv_src = self.ch_clock
        # read_task.timing.ai_conv_active_edge = self.clock_edge

        # Configure reader stream
        self.reader = stream_readers.AnalogSingleChannelReader(self.task.in_stream)
        # reader = stream_readers.AnalogMultiChannelReader(task.in_stream)
        self.reader.read_all_avail_samp  = True

        self.buffer = np.zeros(n_samples, dtype=np.float64, order='C')

        num_trace = self.params["num_trace"]
        # self.dataset["timestamp"] = np.arange(num_trace)
        # self.dataset["data"] = np.zeros(num_trace, dtype=np.float64, order='C')
        self.dataset["timestamp"] = np.full(num_trace, np.nan,  order='C')
        self.dataset["data"] = np.full(num_trace, np.nan,  order='C')

        self.num_iter = 2**32

    def _run_exp(self):
        # task.start()
        # timeout = 10
        num_read = self.reader.read_many_sample(
                self.buffer,
                READ_ALL_AVAILABLE,
                # timeout, 
                10.0
            )

    def _shutdown_exp(self):
        self.task.stop()
        self.task.close()
        self.num_iter = 0

    def _run(self):
        """Method that runs in a thread."""
        try:
            self.state='run'
            start_time = time.time()
            self._setup_exp()
            self.idx_iter = 0
            for iii in range(self.num_iter):
                curr_time = time.time()
                # self.thread.stop_request.wait(0.5) # little trick to have a long (0.5 s) refresh interval but still react immediately to a stop request
                if self.thread.stop_request.isSet():
                    # logger.debug('Received stop signal. Returning from thread.')
                    break
                self._run_exp()
                self.dataset["data"][:-1] = self.dataset["data"][1:]
                self.dataset["timestamp"][:-1] = self.dataset["timestamp"][1:]
                self.dataset["timestamp"][-1] = curr_time
                self.dataset["data"][-1] = np.mean(self.buffer)
                self.idx_iter += 1
                self.run_time = curr_time - start_time
                time.sleep(max(1/self.params["refresh_rate"]-(time.time()-curr_time), 0))
                # self._upload_dataserv()
            else:
                if self.num_iter == 0:
                    self.state = "idle"
                else:
                    self.state='done'
        except Exception as ee:
            # logger.exception('Error in job.')
            self.state='error'
            print(ee)
        finally:
            # logger.debug('Turning off all instruments.')  
            self._shutdown_exp()

    def start(self):
        self.thread = StoppableThread(target = self._run, name=self.__class__.__name__ + str(time.time()))
        self.thread.start()

    def stop(self, timeout=None):
        """Stop the process loop."""
        self.thread.stop_request.set()
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()        
        self.thread.stop(timeout=timeout)

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
    pltrace.set_params(min_volt=min_volt, 
                       max_volt=max_volt, 
                       n_samples=n_samples, 
                       refresh_rate=refresh_rate, 
                       sampling_rate=sampling_rate, 
                       history_window = history_window,
                       num_trace = num_trace
                      )
    pltrace.start() 
