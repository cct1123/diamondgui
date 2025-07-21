import logging
import time

import numpy as np

from hardware import config as hcf
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import (
    REPEAT_INFINITELY,
    OutputState,
    TriggerRearm,
    TriggerStart,
)
from measurement.task_base import Measurement

logger = logging.getLogger(__name__)
hw = HardwareManager()


def average_repeated_data(seg_store, seg_count, start, stop, bgextend_size=256):
    # average over repetitions -------------------------------------
    averaged_norm = np.mean(seg_store[:, start:stop], axis=1) / seg_count
    # get the apd bias background --------------------
    averaged_bg = (
        np.mean(seg_store[:, bgextend_size - 156 : bgextend_size - 56], axis=1)
        / seg_count
    )  # TODO: use parameters instead of fixed number to select background

    # offset the apd reading by the electronic background --------------------
    idx_tsbegin = 2
    dark = averaged_norm[0] - averaged_bg[0]
    bright = averaged_norm[1] - averaged_bg[1]
    weight = np.abs(bright - dark)
    weight = weight / np.sum(weight)  # normalize the weight
    sig_p = averaged_norm[idx_tsbegin::2] - averaged_bg[idx_tsbegin::2]
    sig_n = averaged_norm[idx_tsbegin + 1 :: 2] - averaged_bg[idx_tsbegin + 1 :: 2]
    # perform weighted integration---------------------------------------------
    sig_p_int = sig_p * weight
    sig_n_int = sig_n * weight
    dark_int = dark * weight
    bright_int = bright * weight
    return dark_int, bright_int, sig_p_int, sig_n_int


def seq_init(init_nslaser: int, init_isc: int, init_wait: int, init_repeat: int):
    return [(["laser"], init_nslaser), ([], init_isc)] * init_repeat + [([], init_wait)]


def seq_read(read_wait: int, read_laser: int):
    return [([], read_wait), (["laser", "sdtrig"], read_laser)]


class TimeSweep(Measurement):
    _para_seq = dict()  # can be overridden in subclasses

    def __init__(self, name="default"):
        __paraset = dict(
            rate_refresh=10.0,
            # --------------------
            laser_current=30.0,  # percentage
            mw_freq=392.83924,  # GHz
            mw_powervolt=5.0,  # voltage 0.0 to 5.0
            mw_phasevolt=7.72,  # voltage 0.0 to 5.0
            amp_input=1000,  # input amplitude for digitizer
            bgextend_size=256,  # TODO: why 256? is it a fixed number?
            # -------------------
            init_nslaser=50,  # [ns]
            init_isc=150,
            init_repeat=40,
            init_wait=1000.0,
            t_pi_mwa=90,
            t_pi_mwb=90,
            read_wait=300.0,
            read_laser=900.0,
            tau_begin=0.0,
            tau_end=100,
            tau_step=10.0,  # [ns]
            n_pi=2,
            # tau_dd=435,
            # -------------------
            # other squence parameters------------
            # ......
            # --------------------------------------
        )
        __paraset.update(self._para_seq)

        __dataset = dict(
            num_repeat=0,
            tau=np.zeros(10),
            sig_p=np.zeros(10),
            sig_n=np.zeros(10),
            bright=0.0,
            dark=0.0,
        )

        super().__init__(name, __paraset, __dataset)

    def _sequence_ts(self, tau):
        tau_ext = 0.0
        return [([], tau)], tau_ext

    def _sequence(self):
        # dark ref + dark ref + tau sweep sequence
        sq_init = seq_init(
            self.paraset["init_nslaser"],
            self.paraset["init_isc"],
            self.paraset["init_wait"],
            self.paraset["init_repeat"],
        )

        sq_read = seq_read(self.paraset["read_wait"], self.paraset["read_laser"])

        sq_exp = []
        # start with a bright and dark reference
        sq_dark = sq_init + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
        sq_bright = sq_init + [([], self.paraset["t_pi_mwa"])] + sq_read
        sq_exp += sq_dark + sq_bright

        # add tau sweep sequence
        tau_begin = self.paraset["tau_begin"]
        tau_end = self.paraset["tau_end"]
        tau_step = self.paraset["tau_step"]
        tauarray = np.arange(tau_begin, tau_end + tau_step, tau_step)
        tauaprime = np.arange(tau_begin, tau_end + tau_step, tau_step)

        for ii, tau in enumerate(tauarray):
            sq_ts, tau_ext = self._sequence_ts(tau)
            tauaprime[ii] = tau + tau_ext
            sq_exp += sq_init + sq_ts + [([], self.paraset["t_pi_mwa"])] + sq_read
            sq_exp += sq_init + sq_ts + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
        return sq_exp, tauaprime

    def _setup_exp(self):
        # set the mw frequency, power and phase --------------------------------------------------
        mw_freq = self.paraset["mw_freq"]
        mwpower_vlevel = self.paraset["mw_powervolt"]  # 5V equals to max power
        mwphase_vlevel = self.paraset["mw_phasevolt"]  # voltage to phase shifter
        _freq_actual = hw.vdi.set_freq(mw_freq)
        hw.vdi.set_amp_volt(mwpower_vlevel)
        hw.vdi.set_phase_volt(mwphase_vlevel)
        # -----------------------------------------------------------------------

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # # -----------------------------------------------------------------------

        # set the pulse sequence-------------------------------------------
        start = time.time()
        seq_exp, tau_arr = self._sequence()
        end = time.time()
        logger.info(f"Time taken for generating sequence: {end - start:.4f} seconds")

        tt_seq = hw.pg.setSequence(seq_exp, reset=True)
        hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        hw.pg.setClock10MHzExt()
        hw.pg.stream(n_runs=REPEAT_INFINITELY)
        # -----------------------------------------------------------------------

        # set up the digitizer-------------------------------------------
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        self.tau_arr_num = len(tau_arr)
        self.databufferlen = 2 * self.tau_arr_num + 2

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming
        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            max(
                int(self.databufferlen / (tt_seq * rate_refresh / 1e9)),
                self.databufferlen,
            )
            // 32
            * 32
        )  # number of "reads" every data refresh, just for buffering

        # configures the readout to match the pulse sequence
        pretrig_size = (
            int((read_wait / 2) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
        )  # pretrigger based on the t_wait time
        posttrig_size = (
            int((read_laser) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
        )  # posttrigger based on the t_laser time and init_isc
        segment_size = pretrig_size + posttrig_size
        segment_size = 2 ** int(np.log2(segment_size) + 1)  # make it power of 2
        posttrig_size = (
            segment_size - pretrig_size
        )  # recalculate posttrigger size to ensure it is power of 2
        self.bgextend_size = self.paraset["bgextend_size"]
        # To set the configuration, make a dictionary with the key and value
        hw.dig.reset_param()
        hw.dig.assign_param(
            dict(
                readout_ch=readout_ch,
                amp_input=amp_input,
                num_segment=num_segment,
                pretrig_size=pretrig_size + self.bgextend_size,  # TODO: why 256?
                posttrig_size=posttrig_size - self.bgextend_size,
                segment_size=segment_size,
            )
        )
        logger.debug(
            f"readout_ch = {readout_ch}, amp_input = {amp_input}, num_segment = {num_segment}, pretrig_size = {pretrig_size}, posttrig_size = {posttrig_size}, segment_size = {segment_size}"
        )
        hw.dig.set_ext_clock()
        hw.dig.set_config()
        # -----------------------------------------------------------------------

        # put some necessary variables in self-------------------------------------
        self.tau_arr = tau_arr
        if not self.tokeep:
            self.idx_pointer = 0
            self.dataset["tau"] = self.tau_arr
            # self.dataset["bright"] = 0.0
            # self.dataset["dark"] = 0.0
            self.dataset["sig_p"] = np.zeros(self.tau_arr_num)
            self.dataset["sig_n"] = np.zeros(self.tau_arr_num)
            self.seg_count = np.zeros(
                self.databufferlen,
                dtype=np.float64,
                order="C",
            )
            self.seg_store = np.zeros(
                (self.databufferlen, segment_size),
                dtype=np.float64,
                order="C",
            )
        # -----------------------------------------------------------------------
        # start the laser and digitizer then wait for trigger from the  pulse streamer--------------
        hw.laser.laser_on()  # turn on laser
        hw.dig.start_buffer()
        # logger.debug("Start the trigger from the pulse streamer")
        hw.pg.startNow()

    def _run_exp(self):
        self.rawraw = hw.dig.stream()
        if self.rawraw is not None:
            num_segs = self.rawraw.shape[0]
            idx_ptr_overflow = self.idx_pointer + num_segs
            count_fill, idx_pointer_new = divmod(idx_ptr_overflow, self.databufferlen)
            if count_fill < 1:
                # underfill================================
                # if the segment number is small to the remaining slot numbers in the buffer
                idx_i = self.idx_pointer
                idx_f = self.idx_pointer + num_segs
                self.seg_store[idx_i:idx_f, :] += np.reshape(
                    self.rawraw[:num_segs], (num_segs, -1)
                )
                self.seg_count[idx_i:idx_f] += 1
            else:
                # exactly fill or overfill===============================

                # fill the tail of the data_store buffer ----------------
                num_tailslot = self.databufferlen - self.idx_pointer
                idx_i = self.idx_pointer
                idx_f = self.databufferlen
                self.seg_store[idx_i:idx_f, :] += np.reshape(
                    self.rawraw[:num_tailslot], (num_tailslot, -1)
                )

                self.seg_count[idx_i:idx_f] += 1

                # fill the entire data_store buffer multiple times ----------------
                if count_fill > 1:
                    to_add_unstructured = np.reshape(
                        self.rawraw[
                            num_tailslot : num_tailslot
                            + (count_fill - 1) * self.databufferlen
                        ],
                        (count_fill - 1, self.databufferlen, -1),
                    )
                    self.seg_store += np.sum(to_add_unstructured, axis=0)
                    self.seg_count += count_fill - 1

                # fill the head of the data_store buffer for the remaining segments --------------
                self.seg_store[:idx_pointer_new, :] += (
                    np.reshape(self.rawraw[-idx_pointer_new:], (idx_pointer_new, -1))
                    if idx_pointer_new
                    else self.seg_store[:idx_pointer_new, :]
                )  # the if condition is needed to handle the case that the idx_pointer_new is 0
                self.seg_count[:idx_pointer_new] += 1
            self.idx_pointer = idx_pointer_new

        self.idx_run = self.seg_count[-1]
        # -----------------------------------------------------------------------
        return None

    # TODO: Generalize the start stop, maybe add the SNR opt
    def _organize_data(self):
        dark, bright, sig_p, sig_n = average_repeated_data(
            self.seg_store,
            self.seg_count,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            bgextend_size=self.paraset["bgextend_size"],
        )  # TODO: use parameters instead of fixed number to select integration window

        self.dataset["tau"] = self.tau_arr
        self.dataset["dark"] = dark
        self.dataset["bright"] = bright
        self.dataset["sig_p"] = sig_p
        self.dataset["sig_n"] = sig_n
        self.dataset["num_repeat"] = self.idx_run
        return super()._organize_data()

    def _shutdown_exp(self):
        # turn off laser and set diode current to zero
        hw.laser.laser_off()
        hw.laser.set_diode_current(0.00, save_memory=False)
        # set pulse generator to zero
        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())

        # set mw amp and phase to zero
        hw.vdi.set_amp_volt(0)
        # hw.vdi.set_phase_volt(0)
        hw.vdi.set_phase_volt(0)

        # dump remaining data & stop digitizer
        # _ = hw.dig.stream()
        hw.dig.stop_card()
        # hw.dig.reset()

    def _handle_exp_error(self):
        try:
            hw.laser.laser_off()  # turn off laser
            hw.laser.set_diode_current(0.00, save_memory=False)
        except Exception as ee:
            print("I tried to turn off laser and set diode current to zero but failed")
            print(ee)

        try:
            hw.laser.reset_alarm()
        except Exception as ee:
            print("I tried to reset alarm but failed")
            print(ee)

        try:
            hw.laser.close()
        except Exception as ee:
            print("I tried to close laser but failed")
            print(ee)

        try:
            hw.laser.open()
        except Exception as ee:
            print("I tried to open laser but failed")
            print(ee)

        try:
            hw.vdi.reset()
        except Exception as ee:
            print("I tried to reset vdi mw sourcebut failed")
            print(ee)

        try:
            hw.vdi.close()
        except Exception as ee:
            print("I tried to close vdi mw source but failed")
            print(ee)

        try:
            hw.vdi.open()
        except Exception as ee:
            print("I tried to open vdi mw source but failed")
            print(ee)

        try:
            hw.pg.forceFinal()
        except Exception as ee:
            print("I tried to force final pulse generator but failed")
            print(ee)

        try:
            hw.pg.constant(OutputState.ZERO())
        except Exception as ee:
            print("I tried to set pulse generator to zero but failed")
            print(ee)

        try:
            hw.pg.reset()
        except Exception as ee:
            print("I tried to reset pulse generator but failed")
            print(ee)

        try:
            hw.pg.reboot()
        except Exception as ee:
            print("I tried to reboot pulse generator but failed")
            print(ee)

        try:
            hw.mwmod.set_phase_volt(0)
        except Exception as ee:
            print("I tried to set mw phase to zero but failed")
            print(ee)

        try:
            _ = hw.dig.stream()
        except Exception as ee:
            print("I tried to get digitizer stream but failed")
            print(ee)

        try:
            hw.dig.stop_card()
        except Exception as ee:
            print("I tried to stop digitizer but failed")
            print(ee)

        try:
            hw.dig.reset()
        except Exception as ee:
            print("I tried to reset digitizer but failed")
            print(ee)


class DummyTimeSweep(TimeSweep):
    _para_seq = dict()

    def sequence():
        # return a time-based sequence and
        tau_x = 0.0
        sq = []
        return sq, tau_x


class Relaxation(TimeSweep):
    # TODO: use log scale tau
    def _sequence_ts(self, tau):
        return [([], tau)], 0.0


# TODO: allow slope or variance detectoin, pi/2x +pi/2y or pi/2x + pi/2x
class Ramsey(TimeSweep):
    _para_seq = dict(
        # t_pio2_mwa=50.0,  # duration of the pi pulse in ns
        slope_det=False,
    )

    def _sequence_ts(self, tau):
        t_pio2_mwa = int(self.paraset["t_pi_mwa"] / 2)
        t_pio2_mwb = int(self.paraset["t_pi_mwb"] / 2)
        mwAB_pio2 = "mwB" if self.paraset["slope_det"] else "mwA"
        t_pio2_mwab = (
            int(t_pio2_mwa / 2) if self.paraset["slope_det"] else int(t_pio2_mwb / 2)
        )
        seq = [
            (["mwA"], t_pio2_mwa),
            ([], tau),
            ([mwAB_pio2], t_pio2_mwab),
        ]
        tau_ext = (t_pio2_mwa + t_pio2_mwab) / 2
        return seq, tau_ext


class HahnEcho(TimeSweep):
    _para_seq = dict(
        # t_pio2_mwa=50.0,  # duration of the pi pulse in ns
        # t_pi_mwa=100.0,  # duration of the pi pulse in ns
        slope_det=False,
    )

    def _sequence_ts(self, tau):
        t_pio2_mwa = int(self.paraset["t_pi_mwa"] / 2)
        t_pio2_mwb = int(self.paraset["t_pi_mwb"] / 2)
        mwAB_pio2 = "mwB" if self.paraset["slope_det"] else "mwA"
        t_pio2_mwab = (
            int(t_pio2_mwa / 2) if self.paraset["slope_det"] else int(t_pio2_mwb / 2)
        )
        seq = [
            (["mwA"], t_pio2_mwa),
            ([], tau),
            (["mwA"], self.paraset["t_pi_mwa"]),
            ([], tau),
            ([mwAB_pio2], t_pio2_mwab),
        ]
        tau_ext = (self.paraset["t_pi_mwa"] + 0.5 * t_pio2_mwa + 0.5 * t_pio2_mwab) / 2
        return seq, tau_ext


class CPMG(TimeSweep):
    _para_seq = dict(
        # t_pio2_mwa=50.0,  # duration of the pi/2 pulse in ns
        # t_pi_mwa=100.0,  # duration of the pi pulse in ns
        n_pi=10,  # number of pi pulses in the CPMG sequence, n should be >= 2
        slope_det=False,
    )

    def _sequence_ts(self, tau):
        t_pi_mwa = self.paraset["t_pi_mwa"]
        t_pio2_mwa = int(t_pi_mwa / 2)
        t_pio2_mwb = int(self.paraset["t_pi_mwb"] / 2)
        mwAB_pio2 = "mwB" if self.paraset["slope_det"] else "mwA"
        t_pio2_mwab = (
            int(t_pio2_mwa / 2) if self.paraset["slope_det"] else int(t_pio2_mwb / 2)
        )
        tauhalf = int(tau / 2.0)
        seq_ts = []
        seq_ts += [(["mwA"], t_pio2_mwa), ([], tauhalf)]
        seq_ts += [(["mwA"], t_pi_mwa), ([], tau)] * (self.paraset["n_pi"] - 1)
        seq_ts += [(["mwA"], t_pi_mwa), ([], tauhalf)]
        seq_ts += [([mwAB_pio2], t_pio2_mwab)]
        tau_ext = (
            self.paraset["n_pi"] * t_pi_mwa + +0.5 * t_pio2_mwa + 0.5 * t_pio2_mwab
        ) / self.paraset["n_pi"]
        return seq_ts, tau_ext


class XY4(TimeSweep):
    # TODO: implement XY4 sequence
    _para_seq = dict(
        # t_pi_mwa=100.0,  # duration of the pi pulse in ns
        # t_pi_mwb=100.0,  # duration of the pi pulse in ns
        n_XY4=1,  # number of repetitions of the XY4 sequence
        slope_det=False,
    )

    def _sequence_ts(self, tau):
        t_pi_mwa = self.paraset["t_pi_mwa"]
        t_pi_mwb = self.paraset["t_pi_mwb"]
        t_pio2_mwa = int(t_pi_mwa / 2)
        t_pio2_mwb = int(self.paraset["t_pi_mwb"] / 2)
        mwAB_pio2 = "mwB" if self.paraset["slope_det"] else "mwA"
        t_pio2_mwab = (
            int(t_pio2_mwa / 2) if self.paraset["slope_det"] else int(t_pio2_mwb / 2)
        )
        tauhalf = int(tau / 2.0)
        seq_ts = []

        seq_ts += [(["mwA"], t_pio2_mwa)]

        XY4_seq = []
        XY4_seq += [([], tauhalf), (["mwA"], t_pi_mwa), ([], tau)]  # X
        XY4_seq += [(["mwB"], t_pi_mwb), ([], tau)]  # Y
        XY4_seq += [(["mwA"], t_pi_mwa), ([], tau)]  # X
        XY4_seq += [(["mwA"], t_pi_mwb), ([], tauhalf)]  # X

        XY4_seq_n = XY4_seq * self.paraset["n_XY4"]
        seq_ts += XY4_seq_n

        seq_ts += [([mwAB_pio2], t_pio2_mwab)]

        tau_ext = (
            self.paraset["n_XY4"] * 4 * t_pi_mwa + +0.5 * t_pio2_mwa + 0.5 * t_pio2_mwab
        ) / (self.paraset["n_XY4"] * 4)  # TODO check

        return seq_ts, tau_ext


class XY8(TimeSweep):
    # TODO: implement XY4 sequence
    _para_seq = dict(
        # t_pi_mwa=100.0,  # duration of the pi pulse in ns
        # t_pi_mwb=100.0,  # duration of the pi pulse in ns
        n_XY8=1,  # number of repetitions of the XY8 sequence
        slope_det=False,
    )

    def _sequence_ts(self, tau):
        t_pi_mwa = self.paraset["t_pi_mwa"]
        t_pi_mwb = self.paraset["t_pi_mwb"]
        t_pio2_mwa = int(t_pi_mwa / 2)
        t_pio2_mwb = int(self.paraset["t_pi_mwb"] / 2)
        mwAB_pio2 = "mwB" if self.paraset["slope_det"] else "mwA"
        t_pio2_mwab = (
            int(t_pio2_mwa / 2) if self.paraset["slope_det"] else int(t_pio2_mwb / 2)
        )
        tauhalf = int(tau / 2.0)
        seq_ts = []

        seq_ts += [(["mwA"], t_pio2_mwa)]

        XY8_seq = []
        XY8_seq += [([], tauhalf), (["mwA"], t_pi_mwa), ([], tau)]  # X
        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau)]  # Y
        XY8_seq += [(["mwA"], t_pi_mwa), ([], tau)]  # X
        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau)]  # Y

        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau)]  # Y
        XY8_seq += [(["mwA"], t_pi_mwa), ([], tau)]  # X
        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau)]  # Y
        XY8_seq += [(["mwA"], t_pi_mwa), ([], tauhalf)]  # X

        XY8_seq_n = XY8_seq * self.paraset["n_XY8"]
        seq_ts += XY8_seq_n

        seq_ts += [([mwAB_pio2], t_pio2_mwab)]

        tau_ext = (
            self.paraset["n_XY8"] * 8 * t_pi_mwa + +0.5 * t_pio2_mwa + 0.5 * t_pio2_mwab
        ) / (self.paraset["n_XY8"] * 8)  # yTODO make this correct

        return seq_ts, tau_ext


# class CorrSpec(TimeSweep):
#     _para_seq = dict(
#         tau_dd=47,
#         t_pi_mwa=70,
#         t_pi_mwb=70,
#     )

#     def _sequence_ts(self, tau):
#         tau_dd = int(self.paraset["tau_dd"])
#         t_pi_mwa = int(self.paraset["t_pi_mwa"])
#         t_pi_mwb = int(self.paraset["t_pi_mwb"])
#         t_pio2_mwa = int(t_pi_mwa / 2)
#         t_pio2_mwb = int(t_pi_mwb / 2)
#         sq_dd = [
#             (["mwA"], t_pio2_mwa),
#             ([], tau_dd),
#             (["mwA"], t_pi_mwa),
#             ([], tau_dd),
#             (["mwB"], t_pio2_mwb),
#         ]
#         seq_fe = [([], tau)]
#         seq_ts = sq_dd + seq_fe + sq_dd
#         tau_ext = 0
#         return seq_ts, tau_ext


# class CorrSpec(TimeSweep):
#     _para_seq = dict(
#         tau_dd=47,
#         t_pi_mwa=70,
#         t_pi_mwb=70,
#         ac_freq=2,  # MHz
#     )

#     def _sequence_ts(self, tau):
#         def get_sequence_duration(seq):
#             total_duration = 0
#             for step in seq:
#                 if not isinstance(step, tuple) or len(step) != 2:
#                     raise ValueError(f"Invalid sequence step: {step}")
#                 _, duration = step
#                 if not isinstance(duration, (int, float)):
#                     raise ValueError(
#                         f"Duration must be int or float, got {type(duration)}"
#                     )
#                 total_duration += int(duration)
#             return total_duration

#         def get_analog_duration(pattern):
#             total_duration = 0
#             for step in pattern:
#                 if not isinstance(step, tuple) or len(step) != 2:
#                     raise ValueError(f"Invalid analog step: {step}")
#                 duration, value = step
#                 if not isinstance(duration, (int, float)):
#                     raise ValueError(
#                         f"Duration must be int or float, got {type(duration)}"
#                     )
#                 total_duration += int(duration)
#             return total_duration

#         # handling for sin wave
#         ac_freq = self.paraset["ac_freq"]

#         tau_dd = int(self.paraset["tau_dd"])
#         t_pi_mwa = int(self.paraset["t_pi_mwa"])
#         t_pi_mwb = int(self.paraset["t_pi_mwb"])

#         t_pio2_mwa = int(t_pi_mwa / 2)
#         t_pio2_mwb = int(t_pi_mwb / 2)

#         if tau % 500 == 0:
#             ac_duration = int(
#                 t_pio2_mwa / 2 + 2 * (tau_dd) + t_pi_mwa + t_pio2_mwb / 2
#             )  # ns
#             ac_samplerate = 1e9  # 1GS/s
#             samples_per_cycle = int(ac_samplerate / (ac_freq * 1e6))
#             total_samples = int(ac_duration)

#             # Generate time steps and sine values
#             t = np.arange(total_samples)
#             cos_wave = np.cos(2 * np.pi * ac_freq * t / ac_samplerate)

#             # Convert to pulse pattern [(duration, value)]
#             pulse_pattern = [(1, float(val)) for val in cos_wave]
#             analog_pio2o2_wait = [((int(t_pio2_mwa / 2)), 0.0)]
#             analog_pause = [(tau, 0.0)]

#         else:
#             ac_duration = int(
#                 t_pio2_mwa / 2 + 2 * (tau_dd) + t_pi_mwa + t_pio2_mwb / 2
#             )  # ns
#             ac_samplerate = 1e9  # 1GS/s
#             samples_per_cycle = int(ac_samplerate / (ac_freq * 1e6))
#             total_samples = int(ac_duration)

#             # Convert to pulse pattern [(duration, value)]
#             pulse_pattern = [(ac_duration, 0.0)]
#             analog_pio2o2_wait = [((int(t_pio2_mwa / 2)), 0.0)]
#             analog_pause = [(tau, 0.0)]

#         sq_dd = [
#             (["mwA"], t_pio2_mwa),
#             ([], tau_dd),
#             (["mwA"], t_pi_mwa),
#             ([], tau_dd),
#             (["mwB"], t_pio2_mwb),
#         ]

#         seq_fe = [([], tau)]
#         seq_ts = sq_dd + seq_fe + sq_dd
#         seq_analog = (
#             analog_pio2o2_wait
#             + pulse_pattern
#             + analog_pause
#             + 2 * analog_pio2o2_wait
#             + pulse_pattern
#         )
#         tau_ext = 0
#         len_dig = get_sequence_duration(seq_ts)
#         len_analogue = get_analog_duration(seq_analog)
#         seq_analog += [(len_dig - len_analogue, 0.0)]

#         return seq_ts, tau_ext, seq_analog

#     def _sequence(self):
#         def get_sequence_duration(seq):
#             total_duration = 0
#             for step in seq:
#                 if not isinstance(step, tuple) or len(step) != 2:
#                     raise ValueError(f"Invalid sequence step: {step}")
#                 _, duration = step
#                 if not isinstance(duration, (int, float)):
#                     raise ValueError(
#                         f"Duration must be int or float, got {type(duration)}"
#                     )
#                 total_duration += int(duration)
#             return total_duration

#         def get_analog_duration(pattern):
#             total_duration = 0
#             for step in pattern:
#                 if not isinstance(step, tuple) or len(step) != 2:
#                     raise ValueError(f"Invalid analog step: {step}")
#                 duration, value = step
#                 if not isinstance(duration, (int, float)):
#                     raise ValueError(
#                         f"Duration must be int or float, got {type(duration)}"
#                     )
#                 total_duration += int(duration)
#             return total_duration

#         # dark ref + dark ref + tau sweep sequence
#         sq_init = seq_init(
#             self.paraset["init_nslaser"],
#             self.paraset["init_isc"],
#             self.paraset["init_wait"],
#             self.paraset["init_repeat"],
#         )
#         sq_init_analog = [(get_sequence_duration(sq_init), 0.0)]
#         sq_read = seq_read(self.paraset["read_wait"], self.paraset["read_laser"])
#         sq_read_analog = [(get_sequence_duration(sq_read), 0.0)]
#         sq_exp = []
#         seq_analog_exp = []
#         # start with a bright and dark reference
#         sq_dark = sq_init + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
#         sq_bright = sq_init + [([], self.paraset["t_pi_mwa"])] + sq_read
#         sq_exp += sq_dark + sq_bright
#         seq_analog_exp += [(get_sequence_duration(sq_dark), 0.0)] + [
#             (get_sequence_duration(sq_bright), 0.0)
#         ]

#         # add tau sweep sequence
#         tau_begin = self.paraset["tau_begin"]
#         tau_end = self.paraset["tau_end"]
#         tau_step = self.paraset["tau_step"]
#         tauarray = np.arange(tau_begin, tau_end + tau_step, tau_step)
#         tauaprime = np.arange(tau_begin, tau_end + tau_step, tau_step)

#         for ii, tau in enumerate(tauarray):
#             sq_ts, tau_ext, seq_analog = self._sequence_ts(tau)
#             tauaprime[ii] = tau + tau_ext

#             sq_exp += sq_init + sq_ts + [([], self.paraset["t_pi_mwa"])] + sq_read
#             seq_analog_exp += (
#                 sq_init_analog
#                 + seq_analog
#                 + [(self.paraset["t_pi_mwa"], 0.0)]
#                 + sq_read_analog
#             )

#             sq_exp += sq_init + sq_ts + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
#             seq_analog_exp += (
#                 sq_init_analog
#                 + seq_analog
#                 + [(self.paraset["t_pi_mwa"], 0.0)]
#                 + sq_read_analog
#             )
#         return sq_exp, tauaprime, seq_analog_exp

#     def _setup_exp(self):
#         # set the mw frequency, power and phase --------------------------------------------------
#         mw_freq = self.paraset["mw_freq"]
#         mwpower_vlevel = self.paraset["mw_powervolt"]  # 5V equals to max power
#         mwphase_vlevel = self.paraset["mw_phasevolt"]  # voltage to phase shifter
#         _freq_actual = hw.vdi.set_freq(mw_freq)
#         hw.vdi.set_amp_volt(mwpower_vlevel)
#         hw.vdi.set_phase_volt(mwphase_vlevel)
#         # -----------------------------------------------------------------------

#         # set the laser power -------------------------------------------------
#         current_percent = self.paraset["laser_current"]
#         hw.laser.laser_off()
#         hw.laser.set_analog_control_mode("current")
#         hw.laser.set_modulation_state("Pulsed")
#         hw.laser.set_diode_current(current_percent, save_memory=False)
#         # # -----------------------------------------------------------------------

#         # set the pulse sequence-------------------------------------------
#         start = time.time()
#         seq_exp, tau_arr, seq_analog_all = self._sequence()
#         end = time.time()
#         logger.info(f"Time taken for generating sequence: {end - start:.4f} seconds")

#         tt_seq = hw.pg.setSequence(seq_exp, reset=True)
#         hw.pg.setAnalog("Bz", seq_analog_all)

#         hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
#         hw.pg.setClock10MHzExt()
#         hw.pg.stream(n_runs=REPEAT_INFINITELY)
#         # -----------------------------------------------------------------------

#         # set up the digitizer-------------------------------------------
#         read_wait = self.paraset["read_wait"]
#         read_laser = self.paraset["read_laser"]
#         self.tau_arr_num = len(tau_arr)
#         self.databufferlen = 2 * self.tau_arr_num + 2

#         rate_refresh = self.paraset[
#             "rate_refresh"
#         ]  # Hz rate of refreshing the data streaming
#         amp_input = self.paraset["amp_input"]
#         readout_ch = hcf.SIDIG_chmap["apd"]
#         num_segment = (
#             max(
#                 int(self.databufferlen / (tt_seq * rate_refresh / 1e9)),
#                 self.databufferlen,
#             )
#             // 32
#             * 32
#         )  # number of "reads" every data refresh, just for buffering

#         # configures the readout to match the pulse sequence
#         pretrig_size = (
#             int((read_wait / 2) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
#         )  # pretrigger based on the t_wait time
#         posttrig_size = (
#             int((read_laser) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
#         )  # posttrigger based on the t_laser time and init_isc
#         segment_size = pretrig_size + posttrig_size
#         segment_size = 2 ** int(np.log2(segment_size) + 1)  # make it power of 2
#         posttrig_size = (
#             segment_size - pretrig_size
#         )  # recalculate posttrigger size to ensure it is power of 2
#         self.bgextend_size = self.paraset["bgextend_size"]
#         # To set the configuration, make a dictionary with the key and value
#         hw.dig.reset_param()
#         hw.dig.assign_param(
#             dict(
#                 readout_ch=readout_ch,
#                 amp_input=amp_input,
#                 num_segment=num_segment,
#                 pretrig_size=pretrig_size + self.bgextend_size,  # TODO: why 256?
#                 posttrig_size=posttrig_size - self.bgextend_size,
#                 segment_size=segment_size,
#             )
#         )
#         logger.debug(
#             f"readout_ch = {readout_ch}, amp_input = {amp_input}, num_segment = {num_segment}, pretrig_size = {pretrig_size}, posttrig_size = {posttrig_size}, segment_size = {segment_size}"
#         )
#         hw.dig.set_ext_clock()
#         hw.dig.set_config()
#         # -----------------------------------------------------------------------

#         # put some necessary variables in self-------------------------------------
#         self.tau_arr = tau_arr
#         if not self.tokeep:
#             self.idx_pointer = 0
#             self.dataset["tau"] = self.tau_arr
#             # self.dataset["bright"] = 0.0
#             # self.dataset["dark"] = 0.0
#             self.dataset["sig_p"] = np.zeros(self.tau_arr_num)
#             self.dataset["sig_n"] = np.zeros(self.tau_arr_num)
#             self.seg_count = np.zeros(
#                 self.databufferlen,
#                 dtype=np.float64,
#                 order="C",
#             )
#             self.seg_store = np.zeros(
#                 (self.databufferlen, segment_size),
#                 dtype=np.float64,
#                 order="C",
#             )
#         # -----------------------------------------------------------------------
#         # start the laser and digitizer then wait for trigger from the  pulse streamer--------------
#         hw.laser.laser_on()  # turn on laser
#         hw.dig.start_buffer()
#         # logger.debug("Start the trigger from the pulse streamer")
#         hw.pg.startNow()

#     def _run_exp(self):
#         self.rawraw = hw.dig.stream()
#         if self.rawraw is not None:
#             num_segs = self.rawraw.shape[0]
#             idx_ptr_overflow = self.idx_pointer + num_segs
#             count_fill, idx_pointer_new = divmod(idx_ptr_overflow, self.databufferlen)
#             if count_fill < 1:
#                 # underfill================================
#                 # if the segment number is small to the remaining slot numbers in the buffer
#                 idx_i = self.idx_pointer
#                 idx_f = self.idx_pointer + num_segs
#                 self.seg_store[idx_i:idx_f, :] += np.reshape(
#                     self.rawraw[:num_segs], (num_segs, -1)
#                 )
#                 self.seg_count[idx_i:idx_f] += 1
#             else:
#                 # exactly fill or overfill===============================

#                 # fill the tail of the data_store buffer ----------------
#                 num_tailslot = self.databufferlen - self.idx_pointer
#                 idx_i = self.idx_pointer
#                 idx_f = self.databufferlen
#                 self.seg_store[idx_i:idx_f, :] += np.reshape(
#                     self.rawraw[:num_tailslot], (num_tailslot, -1)
#                 )

#                 self.seg_count[idx_i:idx_f] += 1

#                 # fill the entire data_store buffer multiple times ----------------
#                 if count_fill > 1:
#                     to_add_unstructured = np.reshape(
#                         self.rawraw[
#                             num_tailslot : num_tailslot
#                             + (count_fill - 1) * self.databufferlen
#                         ],
#                         (count_fill - 1, self.databufferlen, -1),
#                     )
#                     self.seg_store += np.sum(to_add_unstructured, axis=0)
#                     self.seg_count += count_fill - 1

#                 # fill the head of the data_store buffer for the remaining segments --------------
#                 self.seg_store[:idx_pointer_new, :] += (
#                     np.reshape(self.rawraw[-idx_pointer_new:], (idx_pointer_new, -1))
#                     if idx_pointer_new
#                     else self.seg_store[:idx_pointer_new, :]
#                 )  # the if condition is needed to handle the case that the idx_pointer_new is 0
#                 self.seg_count[:idx_pointer_new] += 1
#             self.idx_pointer = idx_pointer_new


#         self.idx_run = self.seg_count[-1]
#         # -----------------------------------------------------------------------
#         return None
def get_sequence_duration(seq):
    total_duration = 0
    for step in seq:
        if not isinstance(step, tuple) or len(step) != 2:
            raise ValueError(f"Invalid sequence step: {step}")
        _, duration = step
        # if not isinstance(duration, (int, float)):
        #     raise ValueError(f"Duration must be int or float, got {type(duration)}")
        total_duration += int(duration)
    return total_duration


def get_analog_duration(pattern):
    total_duration = 0
    for step in pattern:
        if not isinstance(step, tuple) or len(step) != 2:
            raise ValueError(f"Invalid analog step: {step}")
        duration, value = step
        # if not isinstance(duration, (int, float)):
        #     raise ValueError(f"Duration must be int or float, got {type(duration)}")
        total_duration += int(duration)
    return total_duration


class CorrSpec(TimeSweep):
    _para_seq = dict(
        tau_dd=47,
        t_pi_mwa=70,
        t_pi_mwb=70,
        ac_freq=5,  # MHz
    )

    def _sequence_ts(self, tau):
        # handling for sin wave
        ac_freq = self.paraset["ac_freq"]

        tau_dd = int(self.paraset["tau_dd"])
        tau_dd_half = int(tau_dd / 2)
        t_pi_mwa = int(self.paraset["t_pi_mwa"])
        t_pi_mwb = int(self.paraset["t_pi_mwb"])

        t_pio2_mwa = int(t_pi_mwa / 2)
        t_pio2_mwb = int(t_pi_mwb / 2)
        # dur_dd = t_pio2_mwa / 2 + 2 * (tau_dd) + t_pi_mwa + t_pio2_mwb / 2 # for hahn echo
        n_XY8 = 1
        dur_dd = (
            t_pio2_mwa / 2
            + (tau_dd * 6 + tau_dd_half * 2 + t_pi_mwb * 4 + t_pi_mwa * 4) * n_XY8
            + t_pio2_mwb / 2
        )  # for XY8
        ac_duration = int(dur_dd + t_pio2_mwb + tau + t_pio2_mwa + dur_dd)  # ns

        ac_samplerate = self.paraset["ac_freq"] / 1e3 * 20.0  # 20 pt per period

        # Generate time steps and sine values
        dt = int(1 / ac_samplerate)
        ttt = np.arange(0.0, ac_duration, int(1 / ac_samplerate))  # ns
        # cos_wave = np.sin(2 * np.pi * ac_freq * ttt / 1e3)  # for hahn echo
        cos_wave = np.cos(2 * np.pi * ac_freq * ttt / 1e3)  # for XY8

        # Convert to pulse pattern [(duration, value)]
        pulse_pattern = [(dt, float(val)) for val in cos_wave]
        analog_pio2o2_wait = [((int(t_pio2_mwa)), 0.0)]
        sq_dd = []
        sq_dd += [(["mwA"], t_pio2_mwa)]

        XY8_seq = []
        XY8_seq += [([], tau_dd_half), (["mwA"], t_pi_mwa), ([], tau_dd)]  # X
        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau_dd)]  # Y
        XY8_seq += [(["mwA"], t_pi_mwa), ([], tau_dd)]  # X
        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau_dd)]  # Y

        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau_dd)]  # Y
        XY8_seq += [(["mwA"], t_pi_mwa), ([], tau_dd)]  # X
        XY8_seq += [(["mwB"], t_pi_mwb), ([], tau_dd)]  # Y
        XY8_seq += [(["mwA"], t_pi_mwa), ([], tau_dd_half)]  # X

        XY8_seq_n = XY8_seq * n_XY8
        sq_dd += XY8_seq_n

        sq_dd += [(["mwB"], t_pio2_mwb)]

        # sq_dd = [
        #     (["mwA"], t_pio2_mwa),
        #     ([], tau_dd),
        #     (["mwA"], t_pi_mwa),
        #     ([], tau_dd),
        #     (["mwB"], t_pio2_mwb),
        # ]

        seq_fe = [([], tau)]
        seq_ts = sq_dd + seq_fe + sq_dd
        seq_analog = analog_pio2o2_wait + pulse_pattern + analog_pio2o2_wait
        tau_ext = 0
        len_dig = get_sequence_duration(seq_ts)
        len_analogue = get_analog_duration(seq_analog)
        seq_analog += [(len_dig - len_analogue, 0.0)]

        return seq_ts, tau_ext, seq_analog

    def _sequence(self):
        # dark ref + dark ref + tau sweep sequence
        sq_init = seq_init(
            self.paraset["init_nslaser"],
            self.paraset["init_isc"],
            self.paraset["init_wait"],
            self.paraset["init_repeat"],
        )
        sq_init_analog = [(get_sequence_duration(sq_init), 0.0)]
        sq_read = seq_read(self.paraset["read_wait"], self.paraset["read_laser"])
        sq_read_analog = [(get_sequence_duration(sq_read), 0.0)]
        sq_exp = []
        seq_analog_exp = []
        # start with a bright and dark reference
        sq_dark = sq_init + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
        sq_bright = sq_init + [([], self.paraset["t_pi_mwa"])] + sq_read
        sq_exp += sq_dark + sq_bright
        seq_analog_exp += [(get_sequence_duration(sq_dark), 0.0)] + [
            (get_sequence_duration(sq_bright), 0.0)
        ]

        # add tau sweep sequence
        tau_begin = self.paraset["tau_begin"]
        tau_end = self.paraset["tau_end"]
        tau_step = self.paraset["tau_step"]
        tauarray = np.arange(tau_begin, tau_end + tau_step, tau_step)
        tauaprime = np.arange(tau_begin, tau_end + tau_step, tau_step)

        for ii, tau in enumerate(tauarray):
            sq_ts, tau_ext, seq_analog = self._sequence_ts(tau)
            tauaprime[ii] = tau + tau_ext

            sq_exp += sq_init + sq_ts + [([], self.paraset["t_pi_mwa"])] + sq_read
            seq_analog_exp += (
                sq_init_analog
                + seq_analog
                + [(self.paraset["t_pi_mwa"], 0.0)]
                + sq_read_analog
            )

            sq_exp += sq_init + sq_ts + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
            seq_analog_exp += (
                sq_init_analog
                + seq_analog
                + [(self.paraset["t_pi_mwa"], 0.0)]
                + sq_read_analog
            )
        return sq_exp, tauaprime, seq_analog_exp

    def _setup_exp(self):
        # set the mw frequency, power and phase --------------------------------------------------
        mw_freq = self.paraset["mw_freq"]
        mwpower_vlevel = self.paraset["mw_powervolt"]  # 5V equals to max power
        mwphase_vlevel = self.paraset["mw_phasevolt"]  # voltage to phase shifter
        _freq_actual = hw.vdi.set_freq(mw_freq)
        hw.vdi.set_amp_volt(mwpower_vlevel)
        hw.vdi.set_phase_volt(mwphase_vlevel)
        # -----------------------------------------------------------------------

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # # -----------------------------------------------------------------------

        # set the pulse sequence-------------------------------------------
        start = time.time()
        seq_exp, tau_arr, seq_analog_all = self._sequence()
        end = time.time()
        logger.info(f"Time taken for generating sequence: {end - start:.4f} seconds")

        tt_seq = hw.pg.setSequence(seq_exp, reset=True)
        hw.pg.setAnalog("Bz", seq_analog_all)

        hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        hw.pg.setClock10MHzExt()
        hw.pg.stream(n_runs=REPEAT_INFINITELY)
        # -----------------------------------------------------------------------

        # set up the digitizer-------------------------------------------
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        self.tau_arr_num = len(tau_arr)
        self.databufferlen = 2 * self.tau_arr_num + 2

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming
        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            max(
                int(self.databufferlen / (tt_seq * rate_refresh / 1e9)),
                self.databufferlen,
            )
            // 32
            * 32
        )  # number of "reads" every data refresh, just for buffering

        # configures the readout to match the pulse sequence
        pretrig_size = (
            int((read_wait / 2) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
        )  # pretrigger based on the t_wait time
        posttrig_size = (
            int((read_laser) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
        )  # posttrigger based on the t_laser time and init_isc
        segment_size = pretrig_size + posttrig_size
        segment_size = 2 ** int(np.log2(segment_size) + 1)  # make it power of 2
        posttrig_size = (
            segment_size - pretrig_size
        )  # recalculate posttrigger size to ensure it is power of 2
        self.bgextend_size = self.paraset["bgextend_size"]
        # To set the configuration, make a dictionary with the key and value
        hw.dig.reset_param()
        hw.dig.assign_param(
            dict(
                readout_ch=readout_ch,
                amp_input=amp_input,
                num_segment=num_segment,
                pretrig_size=pretrig_size + self.bgextend_size,  # TODO: why 256?
                posttrig_size=posttrig_size - self.bgextend_size,
                segment_size=segment_size,
            )
        )
        logger.debug(
            f"readout_ch = {readout_ch}, amp_input = {amp_input}, num_segment = {num_segment}, pretrig_size = {pretrig_size}, posttrig_size = {posttrig_size}, segment_size = {segment_size}"
        )
        hw.dig.set_ext_clock()
        hw.dig.set_config()
        # -----------------------------------------------------------------------

        # put some necessary variables in self-------------------------------------
        self.tau_arr = tau_arr
        if not self.tokeep:
            self.idx_pointer = 0
            self.dataset["tau"] = self.tau_arr
            # self.dataset["bright"] = 0.0
            # self.dataset["dark"] = 0.0
            self.dataset["sig_p"] = np.zeros(self.tau_arr_num)
            self.dataset["sig_n"] = np.zeros(self.tau_arr_num)
            self.seg_count = np.zeros(
                self.databufferlen,
                dtype=np.float64,
                order="C",
            )
            self.seg_store = np.zeros(
                (self.databufferlen, segment_size),
                dtype=np.float64,
                order="C",
            )
        # -----------------------------------------------------------------------
        # start the laser and digitizer then wait for trigger from the  pulse streamer--------------
        hw.laser.laser_on()  # turn on laser
        hw.dig.start_buffer()
        # logger.debug("Start the trigger from the pulse streamer")
        hw.pg.startNow()

    def _run_exp(self):
        self.rawraw = hw.dig.stream()
        if self.rawraw is not None:
            num_segs = self.rawraw.shape[0]
            idx_ptr_overflow = self.idx_pointer + num_segs
            count_fill, idx_pointer_new = divmod(idx_ptr_overflow, self.databufferlen)
            if count_fill < 1:
                # underfill================================
                # if the segment number is small to the remaining slot numbers in the buffer
                idx_i = self.idx_pointer
                idx_f = self.idx_pointer + num_segs
                self.seg_store[idx_i:idx_f, :] += np.reshape(
                    self.rawraw[:num_segs], (num_segs, -1)
                )
                self.seg_count[idx_i:idx_f] += 1
            else:
                # exactly fill or overfill===============================

                # fill the tail of the data_store buffer ----------------
                num_tailslot = self.databufferlen - self.idx_pointer
                idx_i = self.idx_pointer
                idx_f = self.databufferlen
                self.seg_store[idx_i:idx_f, :] += np.reshape(
                    self.rawraw[:num_tailslot], (num_tailslot, -1)
                )

                self.seg_count[idx_i:idx_f] += 1

                # fill the entire data_store buffer multiple times ----------------
                if count_fill > 1:
                    to_add_unstructured = np.reshape(
                        self.rawraw[
                            num_tailslot : num_tailslot
                            + (count_fill - 1) * self.databufferlen
                        ],
                        (count_fill - 1, self.databufferlen, -1),
                    )
                    self.seg_store += np.sum(to_add_unstructured, axis=0)
                    self.seg_count += count_fill - 1

                # fill the head of the data_store buffer for the remaining segments --------------
                self.seg_store[:idx_pointer_new, :] += (
                    np.reshape(self.rawraw[-idx_pointer_new:], (idx_pointer_new, -1))
                    if idx_pointer_new
                    else self.seg_store[:idx_pointer_new, :]
                )  # the if condition is needed to handle the case that the idx_pointer_new is 0
                self.seg_count[:idx_pointer_new] += 1
            self.idx_pointer = idx_pointer_new

        self.idx_run = self.seg_count[-1]
        # -----------------------------------------------------------------------
        return None
