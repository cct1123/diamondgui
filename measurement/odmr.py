
import numpy as np
import nidaqmx
from nidaqmx.stream_readers import AnalogSingleChannelReader, DigitalSingleChannelReader
from nidaqmx.constants import TerminalConfiguration, VoltageUnits, Edge, AcquisitionType, READ_ALL_AVAILABLE, TaskMode

from measurement.task_base import Measurement
from hardware import config_custom as hcf
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import TriggerStart, OutputState, TriggerRearm, HIGH, LOW, INF, REPEAT_INFINITELY

import logging
logger = logging.getLogger(__name__)
hw = HardwareManager()

# f_NVguess = 392.8444
f_NVguess = 398.55

def seqtime(seq_tb):
    return np.sum([pulse[-1] for pulse in seq_tb])

def shift(arr, idx):
    arrlen = len(arr)
    if idx == arrlen or  idx == 0:
        return arr
    else:
        result = np.empty_like(arr)
        result[-idx:] = arr[:idx]
        result[:(arrlen-idx)] = arr[(idx-arrlen):]
        return result
    
class cwODMR(Measurement):
    pass

class pODMR(Measurement):
    # development notebook "dev_odmr_mwsweep.ipynb"

    def __init__(self, name="default"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict(
                        freq_start = (f_NVguess-0.025), # GHz
                        freq_stop = (f_NVguess+0.025),# GHz
                        freq_step = 0.2E-3,# GHz
                        init_laser = 1500.0,
                        init_wait = 401.0,
                        init_nslaser = 4,
                        init_isc = 200,
                        init_repeat = 20,
                        mw_time = 5000.0,
                        read_wait = 500.0,
                        read_laser = 1201.0,
                        mw_powervolt = 5.0,
                        laser_current = 81.2, #0 to 100%
                        min_volt = -0.002, # [V]
                        max_volt = 0.010,
                        repeat_daq = 10
                                                )
        
        # !!< has to be specific by users>
        __dataset = dict(freq=np.zeros(10), 
                         sig_mw_rise=np.zeros(10),
                         sig_mw_fall=np.zeros(10),
                         sig_nomw_rise=np.zeros(10),
                         sig_nomw_fall=np.zeros(10)
                         )
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        
        # design the pulse sequence-------------------------------------------
        init_nslaser = self.paraset["init_nslaser"]
        init_isc = self.paraset["init_isc"]
        init_repeat = self.paraset["init_repeat"]
        init_wait = self.paraset["init_wait"]
        mw_time = self.paraset["mw_time"]
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        timebase = np.lcm(hcf.NI_timebase, hcf.VDISYN_timebase)

        sub_init = [(["laser"], init_nslaser), ([], init_isc)]*init_repeat + [([], init_wait)]
        # sub_init = [(["laser"], init_laser), ([], init_wait)]
        sub_mw = [(["mwB"],mw_time)]
        sub_nomw = [([],mw_time)]
        sub_read = [([], read_wait), (["laser", "dclk"], read_laser)]
        seqlet_mw = sub_init+sub_mw+sub_read
        seqlet_nomw = sub_init+sub_nomw+sub_read
        seqlet_time = seqtime(seqlet_mw)

        halfsteptime = int((seqlet_time+10*timebase)/timebase)*timebase

        sub_trig = [(["dtrig"], halfsteptime-seqlet_time)]
        sub_pad = [([], halfsteptime-seqlet_time)]
        # -----------------------------------------------------------------------
        # set up laser----------------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # -----------------------------------------------------------------------
        # set MW power -----------------------------------------------------------
        mwpower_vlevel = self.paraset["mw_powervolt"] # 5V equals to max power
        task_uca = nidaqmx.Task("UCA") # user controlled attenuation
        task_uca.ao_channels.add_ao_voltage_chan(hcf.NI_ch_UCA, min_val=0, max_val=10)
        # task_uca.timing.cfg_samp_clk_timing(hcf.NI_sampling_max/100.0, sample_mode=AcquisitionType.CONTINUOUS)
        task_uca.start()
        task_uca.write([mwpower_vlevel], auto_start=False)
        # -----------------------------------------------------------------------

        # set up the MW frequency---------------------------------------------
        freq_start = self.paraset["freq_start"]/24.0
        freq_stop = self.paraset["freq_stop"]/24.0
        freq_step = self.paraset["freq_step"]/24.0

        step_min = hw.mwsyn.get_min_step_size([freq_start], [freq_stop])[0] # in Hz
        freq_step = int(freq_step/step_min*1E9)*step_min/1E9
        step_rise = freq_step
        step_fall = freq_step

        # steptime = 16.0E3 # [ns]
        # steptime = int(steptime/timebase)*timebase
        steptime = 2*halfsteptime
        steptime_rise = 0.5*steptime 
        steptime_fall = 0.5*steptime

        dwellatlow = False
        dwellathigh = False
        # num_risesweep = int((freq_stop-freq_start)/step_rise)+1
        # num_fallsweep = int((freq_stop-freq_start)/step_fall)+1
        logger.info(f"Approximated Time to Sweep along rise direction: \n{(freq_stop-freq_start)/step_rise*steptime_rise/1E6}ms")

        actualpara = hw.mwsyn.sweep(freq_start, freq_stop, 
                                step_rise, step_fall, 
                                steptime_rise, steptime_fall, 
                                dwellatlow, dwellathigh)

        (freq_start_actual, freq_stop_actual, step_rise_actual, step_fall_actual) = actualpara
        self.paraset["freq_start"] = freq_start_actual*24.0
        self.paraset["freq_stop"] = freq_stop_actual*24.0
        self.paraset["freq_step"] = step_rise_actual*24.0
        freq_actual_rise = 24.0*np.arange(freq_start_actual, freq_stop_actual+step_rise_actual, step_rise_actual)
        freq_actual_fall = 24.0*np.flip(np.arange(freq_start_actual+step_rise_actual, freq_stop_actual, step_fall_actual))
        freq_sawsweep = np.append(freq_actual_rise, freq_actual_fall)
        num_freqsaw = len(freq_sawsweep)
        # -----------------------------------------------------------------------

        # set up the pulse streamer-------------------------------------------
        seq_exp = []
        # seq_exp += (sub_trig+seqlet_mw+sub_pad+seqlet_nomw)+(sub_pad+seqlet_mw+sub_pad+seqlet_nomw)*(num_freqsaw-1)

        seq_exp += (sub_trig+seqlet_nomw)+(sub_pad+seqlet_nomw)*(num_freqsaw-1)
        seq_exp += (sub_pad+seqlet_mw)*num_freqsaw
        hw.pg.seqTranslator(seq_exp)
        # hw.pg.plotSeq(plot_all=False)
        # -----------------------------------------------------------------------

        # set up the DAQ board------------------------------------------------
        # signal reading parameters
        min_volt = self.paraset["min_volt"]
        max_volt = self.paraset["max_volt"]
        samplerate_read = 4.0/steptime*1E9 # 500kHz .max ext sampling rate of NI6343

        # num_readsample = 2*num_freqsaw*self.paraset["repeat_daq"]
        num_readsample = 2*num_freqsaw
        # time_fullsweep = steptime*num_freqsaw
        # timeout_read = max(time_fullsweep*2.0/1E9, 10)
        buffer_readpoint = np.zeros(num_readsample, dtype=np.float64, order='C')

        # Create tasks for the analog and digital inputs
        analog_task = nidaqmx.Task("Read FL")
        digital_task = nidaqmx.Task("Read VDI Synth Trigger Out")

        # Add a single analog input channel (e.g., "Dev1/ai0")
        analog_task.ai_channels.add_ai_voltage_chan(
            hcf.NI_ch_APD,"",
            # TerminalConfiguration.RSE,
            TerminalConfiguration.DIFF,
            min_volt,max_volt,
            VoltageUnits.VOLTS
        )

        # Add a single digital input channel (e.g., "Dev1/port0/line0")
        digital_task.di_channels.add_di_chan(hcf.NI_ch_VDISynTrigOut)

        # Configure both tasks to be triggered by a common TTL source (e.g., "Dev1/PFI0")
        analog_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            hcf.NI_ch_Trig, Edge.RISING
        )
        digital_task.triggers.start_trigger.cfg_dig_edge_start_trig(
            hcf.NI_ch_Trig, Edge.RISING
        )

        # Configure continuous acquisition for both tasks
        analog_task.timing.cfg_samp_clk_timing(
            rate=samplerate_read,
            source=hcf.NI_ch_Clock,
            active_edge=Edge.RISING, 
            sample_mode=AcquisitionType.CONTINUOUS,
            # sample_mode=AcquisitionType.FINITE,
            # samps_per_chan=num_readsample
        )
        digital_task.timing.cfg_samp_clk_timing(
            rate=samplerate_read,
            source=hcf.NI_ch_Clock,
            active_edge=Edge.RISING, 
            sample_mode=AcquisitionType.CONTINUOUS,
            # sample_mode=AcquisitionType.FINITE,
            # samps_per_chan=num_readsample
        )

        # Pre-commit the tasks for faster start
        analog_task.control(TaskMode.TASK_COMMIT)
        digital_task.control(TaskMode.TASK_COMMIT)

        # Initialize readers for continuous streaming
        analog_reader = AnalogSingleChannelReader(analog_task.in_stream)
        digital_reader = DigitalSingleChannelReader(digital_task.in_stream)
        # analog_reader.read_all_avail_samp  = True
        # digital_reader.read_all_avail_samp  = True

        # Read smaller samples for real-time feedback
        analog_data_buffer = np.zeros(num_readsample, dtype=np.float64, order='C')  # Buffer for analog data
        digital_data_buffer = np.zeros(num_readsample, dtype=np.uint32, order='C')  # Buffer for digital data
        # # NIDAQ can handle the buffer allocation automatically
        # buf_size = int(samples_per_read*1000)
        # analog_task.in_stream.input_buf_size = buf_size
        # digital_task.in_stream.input_buf_size = buf_size
        #-----------------------------------------------------------------------
        # put some neccessary variables in the class --------------------------
        self.task_uca = task_uca
        self.num_freqsaw = num_freqsaw
        self.freq_sawsweep = freq_sawsweep
        self.num_readsample = num_readsample
        self.buffer_readpoint = buffer_readpoint
        self.analog_data_buffer = analog_data_buffer
        self.digital_data_buffer = digital_data_buffer
        self.analog_reader = analog_reader
        self.digital_reader = digital_reader
        self.analog_task = analog_task
        self.digital_task = digital_task
        self.analog_data_sum1 = np.zeros(num_freqsaw, dtype=np.float64, order='C')  # Buffer for analog data
        self.analog_data_sum2 = np.zeros(num_freqsaw, dtype=np.float64, order='C')  # Buffer for analog data
        # self.digital_data_sum1 = np.zeros(num_freqsaw, dtype=np.uint32, order='C')  # Buffer for digital data
        # self.digital_data_sum2 = np.zeros(num_freqsaw, dtype=np.uint32, order='C')  # Buffer for digital data

        # ----------------------------------------------------------------------
        # start the measurement and wait for trigger ------------------------------
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        hw.pg.stream(n_runs=REPEAT_INFINITELY)
        # pg.stream(n_runs=1)
        hw.laser.laser_on() # turn on laser
        # start frequency sweep
        hw.mwsyn.reset_trigger()
        hw.mwsyn.sweep_continue()
        # Start the tasks
        analog_task.start()
        digital_task.start()
        hw.pg.startNow()

    def _run_exp(self):
        # Read analog and digital data
        numhaveread_ai = self.analog_reader.read_many_sample(
            self.analog_data_buffer, 
            number_of_samples_per_channel=self.num_readsample
        )
        numhaveread_di = self.digital_reader.read_many_sample_port_uint32(
            self.digital_data_buffer, 
            number_of_samples_per_channel=self.num_readsample
        )
        return numhaveread_ai, numhaveread_di

    def _upload_dataserv(self):
        # some basic data analysis ------------------------------------------------
        # analog_data_buffer = np.self.analog_data_buffer
        # self.digital_data_buffer
        ad_1 = self.analog_data_buffer[:self.num_freqsaw]
        ad_2 = self.analog_data_buffer[self.num_freqsaw:]
        idx_step_1 = np.argmax(np.diff(self.digital_data_buffer[:self.num_freqsaw]))+3
        idx_step_2 = np.argmax(np.diff(self.digital_data_buffer[self.num_freqsaw:]))+3
        self.analog_data_sum1 += np.copy(shift(ad_1, idx_step_1)) 
        self.analog_data_sum2 += np.copy(shift(ad_2, idx_step_2)) 
        # self.digital_data_sum1 += np.copy(shift(self.digital_data_buffer[:self.num_freqsaw], idx_step_1)) 
        # self.digital_data_sum2 += np.copy(shift(self.digital_data_buffer[self.num_freqsaw:], idx_step_2)) 

        analog_data_av1 = self.analog_data_sum1/self.idx_run
        # digital_data_av1 = self.digital_data_sum1/self.idx_run
        analog_data_av2 = self.analog_data_sum2/self.idx_run
        # digital_data_av2 = self.digital_data_sum2/self.idx_run

        analog_data_av = np.concatenate((analog_data_av1, analog_data_av2), axis=None)
        # digital_data_av = np.concatenate((digital_data_av1, digital_data_av2), axis=None)

        risefallcut = int(self.num_freqsaw/2)

        freq = self.freq_sawsweep[:int(self.num_freqsaw/2)]
        signal = analog_data_av[self.num_freqsaw:]
        sig_rise = signal[risefallcut:]
        sig_fall = np.flip(signal[:risefallcut])
        # sig_av = (sig_rise + sig_fall)/2.0
        backgroud = analog_data_av[:self.num_freqsaw]
        bg_rise = backgroud[risefallcut:]
        bg_fall = np.flip(backgroud[:risefallcut])
        # bg_av = (bg_rise + bg_fall)/2.0
        #------------------------------------------------------------

        self.dataset = dict(
            freq = freq,
            sig_mw_rise = sig_rise,
            sig_mw_fall = sig_fall,
            sig_nomw_rise = bg_rise,
            sig_nomw_fall = bg_fall
        )

        super()._upload_dataserv()

    def _shutdown_exp(self):
        # turn off laser and set diode current to zero
        hw.laser.laser_off() # turn off laser
        hw.laser.set_diode_current(0.01, save_memory=False)

        # turn full attenuation
        self.task_uca.write([0])
        self.task_uca.stop()
        self.task_uca.close()

        # Stop the tasks
        self.analog_task.stop()
        self.digital_task.stop()
        self.analog_task.close()
        self.digital_task.close()

        # pasue the mw pause then reboot
        hw.mwsyn.sweep_pause()
        # mwsyn.reboot()

        # clear the pulse sequence
        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())
        super()._shutdown_exp()

    def _handle_exp_error(self):
        try:
            hw.laser.laser_off() # turn off laser
            hw.laser.set_diode_current(0.01, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            
            hw.mwsyn.sweep_pause()
            hw.mwsyn.reboot()
            hw.mwsyn.close()

            hw.pg.reset()
            
            # turn full attenuation
            self.task_uca.write([0])
            self.task_uca.stop()
            self.task_uca.close()

            # Stop the tasks
            self.analog_task.stop()
            self.digital_task.stop()
            self.analog_task.close()
            self.digital_task.close()

        except:
            print("I tried T^T")
