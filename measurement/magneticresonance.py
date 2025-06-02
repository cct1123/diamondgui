import logging

import nidaqmx
import numpy as np

from hardware import config as hcf
from hardware.daq.sidig import TERMIN_INPUT_1MOHM
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import (
    HIGH,
    INF,
    LOW,
    REPEAT_INFINITELY,
    OutputState,
    TriggerRearm,
    TriggerStart,
)
from measurement.task_base import Measurement

logger = logging.getLogger(__name__)
hw = HardwareManager()
# import time as time

# f_NVguess = 392.8444
f_NVguess = 398.55
import time


def seqtime(seq_tb):
    return np.sum([pulse[-1] for pulse in seq_tb])


def shift(arr, idx):
    arrlen = len(arr)
    if idx == arrlen or idx == 0:
        return arr
    else:
        result = np.empty_like(arr)
        result[-idx:] = arr[:idx]
        result[: (arrlen - idx)] = arr[(idx - arrlen) :]
        return result


class cwODMR(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            freq_start=398.4,  # GHz
            freq_stop=398.7,  # GHz
            freq_step=1e-3,  # GHz
            # ---
            mw_powervolt=5.0,
            laser_current=81.2,  # 0 to 100%
            min_volt=-0.002,  # [V]
            max_volt=0.080,
            repeat_daq=10,
        )
        __dataset = dict(
            num_repeat=0,
            freq=np.zeros(1),
            signal_no=np.zeros(1),
            signal_mw=np.zeros(1),
        )

    def _setup_exp(self):
        return super()._setup_exp()

    def _run_exp(self):
        pass

    def _organize_data(self):
        return super()._organize_data()

    def _shutdown_exp(self):
        return super()._shutdown_exp()

    def _handle_exp_error(self):
        return super()._handle_exp_error()


def sequence_pODMR(
    init_nslaser: int,
    init_isc: int,
    init_wait: int,
    init_repeat: int,
    read_wait: int,
    read_laser: int,
    mw_dur: int,
):
    seq_exp = []

    sub_init = [(["laser"], init_nslaser), ([], init_isc)] * init_repeat + [
        ([], init_wait)
    ]

    sub_evo_MW = [(["mwA"], mw_dur)]

    sub_read = [([], read_wait), (["laser", "sdtrig"], read_laser)]

    seq_exp += sub_init + sub_evo_MW + sub_read

    sub_evo_noMW = [([], mw_dur)]

    seq_exp += sub_init + sub_evo_noMW + sub_read

    _aux = None

    return seq_exp, _aux


def sequence_pODMR_WDF(
    init_nslaser: int,
    init_isc: int,
    init_wait: int,
    init_repeat: int,
    read_wait: int,
    read_laser: int,
    mw_dur: int,
):
    seq_exp = []

    sub_init = [(["laser"], init_nslaser), ([], init_isc)] * init_repeat + [
        ([], init_wait)
    ]

    sub_evo_MW = [(["mwswitch"], mw_dur)]

    sub_read = [([], read_wait), (["laser", "sdtrig"], read_laser)]

    seq_exp += sub_init + sub_evo_MW + sub_read

    sub_evo_noMW = [([], mw_dur)]

    seq_exp += sub_init + sub_evo_noMW + sub_read

    _aux = None

    return seq_exp, _aux


class pODMR(Measurement):
    # development notebook "dev_odmr_mwsweep.ipynb"

    def __init__(self, name="default"):
        # ==some dictionaries stored with some default values--------------------------
        # !!< has to be specific by users>
        __paraset = dict(
            freq_start=(f_NVguess - 0.025),  # GHz
            freq_stop=(f_NVguess + 0.025),  # GHz
            freq_step=0.2e-3,  # GHz
            # -------------------
            init_laser=1500.0,
            init_wait=401.0,
            init_nslaser=4,
            init_isc=200,
            init_repeat=20,
            mw_time=5000.0,
            read_wait=500.0,
            read_laser=1201.0,
            # -------------------
            mw_powervolt=5.0,
            laser_current=81.2,  # 0 to 100%
            amp_input=1000,  # input amplitude for digitizer
            repeat_daq=10,
            bz_bias_vol=1,  # -1V to 1V
            # -------------------
            rate_refresh=30.0,  # Hz rate of refreshing the entire spectrum, approx
        )

        # !!< has to be specific by users>
        __dataset = dict(
            num_repeat=0,
            freq=np.zeros(
                len(
                    np.arange(
                        __paraset["freq_start"],
                        __paraset["freq_stop"],
                        __paraset["freq_step"],
                    )
                )
            ),
            signal=np.zeros(
                len(
                    np.arange(
                        __paraset["freq_start"],
                        __paraset["freq_stop"],
                        __paraset["freq_step"],
                    )
                )
            ),
            background=np.zeros(
                len(
                    np.arange(
                        __paraset["freq_start"],
                        __paraset["freq_stop"],
                        __paraset["freq_step"],
                    )
                )
            ),
        )
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        # set the frequency array----------------------------------------------
        freq_start = self.paraset["freq_start"]
        freq_stop = self.paraset["freq_stop"]
        freq_step = self.paraset["freq_step"]
        freq_array = np.arange(freq_start, freq_stop, freq_step)
        num_freq = len(freq_array)
        # just to see if we can set the freq in the mwsyn
        freq = freq_start / hcf.VDISYN_multiplier
        hw.mwsyn.open()
        _errorbyte, _freq_actual = hw.mwsyn.cw_frequency(freq)
        hw.mwsyn.purge()

        # set the measurement sequence-------------------------------------------
        seq_exp, _ = sequence_pODMR(
            self.paraset["init_nslaser"],
            self.paraset["init_isc"],
            self.paraset["init_wait"],
            self.paraset["init_repeat"],
            self.paraset["read_wait"],
            self.paraset["read_laser"],
            self.paraset["mw_time"],
        )
        tt_seq = seqtime(seq_exp)
        # self.dig_trig_len = 20
        # self.divpart_pt = 2

        # self.mw_dur = self.paraset["mw_time"]

        # seq_laser = [(self.mw_dur, HIGH)]
        # seq_mwA = [
        #     (self.mw_dur, HIGH),
        #     (self.mw_dur, LOW),
        # ] * self.divpart_pt

        # seq_dig = [
        #     (self.dig_trig_len, HIGH),
        #     (self.mw_dur - self.dig_trig_len, LOW),
        #     (self.dig_trig_len, LOW),
        #     (self.dig_trig_len, HIGH),
        #     (self.mw_dur - self.dig_trig_len, LOW),
        # ] * self.divpart_pt
        # hw.pg.setDigital("laser", seq_laser)
        # hw.pg.setDigital("mwA", seq_mwA)
        # hw.pg.setDigital("sdtrig", seq_dig)
        hw.pg.setSequence(seq_exp)
        hw.pg.setAnalog("Bz", [(tt_seq, self.paraset["bz_bias_vol"])])
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

        # def seqtime_tb(seq_tb):
        #     return np.sum([pulse[-1] for pulse in seq_tb])

        # def seqtime_cb(seq_cb):
        #     return np.sum([pulse[-0] for pulse in seq_cb])

        # set up the digitizer-------------------------------------------
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        databufferlen = 2  # mw on and mw off

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming

        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            int(databufferlen / (tt_seq * rate_refresh / 1e9)) // 32 * 32
        )  # number of "reads" every data refresh

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
        self.bgextend_size = 256
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

        # set the pulse streamer stream-------------------------------------------
        hw.pg.setClock10MHzExt()
        hw.pg.stream(n_runs=num_segment // databufferlen)

        # amp_input = self.paraset["amp_input"]
        # self.readout_ch = hcf.SIDIG_chmap["apd"]

        # self.pretrig_size = 128
        # self.posttrig_size = 1024 * 1000 - self.pretrig_size

        # hw.dig.reset_param()
        # hw.dig.assign_param(
        #     dict(
        #         readout_ch=self.readout_ch,
        #         amp_input=amp_input,
        #         num_segment=8,
        #         pretrig_size=self.pretrig_size,
        #         posttrig_size=self.posttrig_size,
        #         segment_size=self.pretrig_size + self.posttrig_size,
        #         terminate_input=TERMIN_INPUT_1MOHM,
        #         DCCOUPLE=0,
        #         sampling_rate=hcf.SIDIG_maxsr,
        #     )
        # )

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        hw.laser.laser_on()  # turn on laser

        # Allocate arrays and arguments for the experiment------------------------------------------------
        if not self.tokeep:
            self.num_seg_singelfreq = num_segment
            self.num_freq = num_freq
            self.freq_actual = np.copy(freq_array)
            self.segment_list = np.zeros_like(self.freq_actual)
            self.sig_mwon_raw = np.zeros((len(self.freq_actual), segment_size))
            self.sig_mwoff_raw = np.zeros((len(self.freq_actual), segment_size))
            self.sig_mwon = np.zeros_like(self.freq_actual)
            self.sig_mwoff = np.zeros_like(self.freq_actual)
            self.num_repeat = 0
            self.freq_idx = 0

        # start the digitizer buffering------------------------------------
        hw.dig.set_config()
        hw.dig.start_buffer()

    def _run_exp(self):
        hw.pg.rearm()
        # for jj, ff in enumerate(self.freq_array):
        jj = self.freq_idx % self.num_freq
        ff = self.freq_actual[jj]
        freq = ff / hcf.VDISYN_multiplier
        errorbyte, freq_actual = hw.mwsyn.cw_frequency(freq)
        # hw.mwsyn.purge()
        # # hw.mwsyn.purge(self)
        bytescommand = hw.mwsyn._cw_frequency_command(freq)
        # # print_bytestring(bytescommand)
        hw.mwsyn.serialcom.write(bytescommand)
        _received = hw.mwsyn.serialcom.read(size=6)
        freq_actual = freq  # fake actual freq

        # print("Actual frequency: ", freq_actual)
        self.freq_actual[jj] = freq_actual * hcf.VDISYN_multiplier
        hw.pg.startNow()
        time.sleep(1.0 / self.paraset["rate_refresh"])
        num_seg_collected = 0
        rawraw = hw.dig.stream()
        if rawraw is not None:
            num_seg_collected = rawraw.shape[0]
            rawraw_all = np.reshape(rawraw, (num_seg_collected, -1))
            rawraw_on = rawraw_all[0::2, :]
            rawraw_off = rawraw_all[1::2, :]
            self.sig_mwon_raw[jj, :] += np.sum(rawraw_on, axis=0)
            self.sig_mwoff_raw[jj, :] += np.sum(rawraw_off, axis=0)
            self.segment_list[jj] += num_seg_collected
        self.freq_idx += 1
        # hw.pg.forceFinal()

    def average_repeated_data(self, arr, start, stop, segments):
        averaged_norm = np.mean(arr[:, start:stop], axis=1)
        averaged_bg = np.mean(
            arr[:, self.bgextend_size - 156 : self.bgextend_size - 56], axis=1
        )  # TODO: use parameters instead of fixed number to select background

        averagednormalized = averaged_norm - averaged_bg
        result = np.divide(
            averagednormalized,
            segments,
            out=np.zeros_like(averagednormalized, dtype=float),
            where=segments != 0,
        )
        return result

    def _organize_data(self):
        self.sig_mwon = self.average_repeated_data(
            self.sig_mwon_raw,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            self.segment_list,
        )
        self.sig_mwoff = self.average_repeated_data(
            self.sig_mwoff_raw,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            self.segment_list,
        )

        self.dataset["signal"] = self.sig_mwon
        self.dataset["background"] = self.sig_mwoff
        self.dataset["freq"] = self.freq_actual
        self.dataset["num_repeat"] = np.mean(self.segment_list)

        super()._organize_data()

    def _shutdown_exp(self):
        # reconnect the mw syn connection
        hw.mwsyn.close_gracefully()
        hw.mwsyn.open()

        # turn off laser and set diode current to zero
        hw.laser.laser_off()  # turn off laser
        hw.laser.set_diode_current(0.0, save_memory=False)

        hw.dig.stop_card()
        # hw.dig.reset()

        # pasue the mw pause then reboot
        # hw.mwsyn.sweep_pause()

        # mwsyn.reboot()

        # clear the pulse sequence
        hw.pg.forceFinal()
        hw.pg.rearm()
        hw.pg.constant(OutputState.ZERO())
        # hw.pg.reset()

    def _handle_exp_error(self):
        try:
            hw.laser.laser_off()  # turn off laser
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()

            hw.dig.stop_card()
            hw.dig.reset()

            hw.mwsyn.reboot()
            hw.mwsyn.close_gracefully()
            # hw.mwsyn.close()
            hw.mwsyn.open()

            hw.pg.reset()
            hw.pg.reboot()

        except Exception as ee:
            print("I tried T^T")
            print(ee)


class pODMR_WDF(Measurement):
    # development notebook "dev_odmr_mwsweep.ipynb"

    def __init__(self, name="default"):
        # ==some dictionaries stored with some default values--------------------------
        # !!< has to be specific by users>
        __paraset = dict(
            freq_start=(f_NVguess - 0.025),  # GHz
            freq_stop=(f_NVguess + 0.025),  # GHz
            freq_step=0.2e-3,  # GHz
            # -------------------
            init_laser=1500.0,
            init_wait=401.0,
            init_nslaser=4,
            init_isc=200,
            init_repeat=20,
            mw_time=5000.0,
            read_wait=500.0,
            read_laser=1201.0,
            # -------------------
            mw_powervolt=5.0,
            laser_current=81.2,  # 0 to 100%
            amp_input=1000,  # input amplitude for digitizer
            repeat_daq=10,
            bz_bias_vol=1,  # -1V to 1V
            # -------------------
            rate_refresh=30.0,  # Hz rate of refreshing the entire spectrum, approx
        )

        # !!< has to be specific by users>
        __dataset = dict(
            num_repeat=0,
            freq=np.zeros(
                len(
                    np.arange(
                        __paraset["freq_start"],
                        __paraset["freq_stop"],
                        __paraset["freq_step"],
                    )
                )
            ),
            signal=np.zeros(
                len(
                    np.arange(
                        __paraset["freq_start"],
                        __paraset["freq_stop"],
                        __paraset["freq_step"],
                    )
                )
            ),
            background=np.zeros(
                len(
                    np.arange(
                        __paraset["freq_start"],
                        __paraset["freq_stop"],
                        __paraset["freq_step"],
                    )
                )
            ),
        )
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        # set the frequency array----------------------------------------------
        freq_start = self.paraset["freq_start"]
        freq_stop = self.paraset["freq_stop"]
        freq_step = self.paraset["freq_step"]
        freq_array = np.arange(freq_start, freq_stop, freq_step)
        num_freq = len(freq_array)
        # just to see if we can set the freq in the mwsyn
        # freq = freq_start / hcf.VDISYN_multiplier

        # set the measurement sequence-------------------------------------------
        seq_exp, _ = sequence_pODMR_WDF(
            self.paraset["init_nslaser"],
            self.paraset["init_isc"],
            self.paraset["init_wait"],
            self.paraset["init_repeat"],
            self.paraset["read_wait"],
            self.paraset["read_laser"],
            self.paraset["mw_time"],
        )
        tt_seq = seqtime(seq_exp)
        # self.dig_trig_len = 20
        # self.divpart_pt = 2

        # self.mw_dur = self.paraset["mw_time"]

        # seq_laser = [(self.mw_dur, HIGH)]
        # seq_mwA = [
        #     (self.mw_dur, HIGH),
        #     (self.mw_dur, LOW),
        # ] * self.divpart_pt

        # seq_dig = [
        #     (self.dig_trig_len, HIGH),
        #     (self.mw_dur - self.dig_trig_len, LOW),
        #     (self.dig_trig_len, LOW),
        #     (self.dig_trig_len, HIGH),
        #     (self.mw_dur - self.dig_trig_len, LOW),
        # ] * self.divpart_pt
        # hw.pg.setDigital("laser", seq_laser)
        # hw.pg.setDigital("mwA", seq_mwA)
        # hw.pg.setDigital("sdtrig", seq_dig)
        hw.pg.setSequence(seq_exp)
        hw.pg.setAnalog("Bz", [(tt_seq, self.paraset["bz_bias_vol"])])
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

        # def seqtime_tb(seq_tb):
        #     return np.sum([pulse[-1] for pulse in seq_tb])

        # def seqtime_cb(seq_cb):
        #     return np.sum([pulse[-0] for pulse in seq_cb])

        # set up the digitizer-------------------------------------------
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        databufferlen = 2  # mw on and mw off

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming

        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            int(databufferlen / (tt_seq * rate_refresh / 1e9)) // 32 * 32
        )  # number of "reads" every data refresh

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
        self.bgextend_size = 256
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

        # set the pulse streamer stream-------------------------------------------
        hw.pg.setClock10MHzExt()
        hw.pg.stream(n_runs=num_segment // databufferlen)

        # amp_input = self.paraset["amp_input"]
        # self.readout_ch = hcf.SIDIG_chmap["apd"]

        # self.pretrig_size = 128
        # self.posttrig_size = 1024 * 1000 - self.pretrig_size

        # hw.dig.reset_param()
        # hw.dig.assign_param(
        #     dict(
        #         readout_ch=self.readout_ch,
        #         amp_input=amp_input,
        #         num_segment=8,
        #         pretrig_size=self.pretrig_size,
        #         posttrig_size=self.posttrig_size,
        #         segment_size=self.pretrig_size + self.posttrig_size,
        #         terminate_input=TERMIN_INPUT_1MOHM,
        #         DCCOUPLE=0,
        #         sampling_rate=hcf.SIDIG_maxsr,
        #     )
        # )

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        hw.laser.laser_on()  # turn on laser

        # Allocate arrays and arguments for the experiment------------------------------------------------
        if not self.tokeep:
            self.num_seg_singelfreq = num_segment
            self.num_freq = num_freq
            self.freq_actual = np.copy(freq_array)
            self.segment_list = np.zeros_like(self.freq_actual)
            self.sig_mwon_raw = np.zeros((len(self.freq_actual), segment_size))
            self.sig_mwoff_raw = np.zeros((len(self.freq_actual), segment_size))
            self.sig_mwon = np.zeros_like(self.freq_actual)
            self.sig_mwoff = np.zeros_like(self.freq_actual)
            self.num_repeat = 0
            self.freq_idx = 0

        # start the digitizer buffering------------------------------------
        hw.dig.set_config()
        hw.dig.start_buffer()

    def _run_exp(self):
        hw.pg.rearm()
        # for jj, ff in enumerate(self.freq_array):
        jj = self.freq_idx % self.num_freq
        ff = self.freq_actual[jj]

        freq = ff / hcf.VDISYN_multiplier
        hw.windfreak.set_output(freq=freq * 1e9, power=self.paraset["mw_powervolt"])
        time.sleep(0.1)
        # errorbyte, freq_actual = hw.mwsyn.cw_frequency(freq)

        # hw.mwsyn.purge()
        # # hw.mwsyn.purge(self)
        # bytescommand = hw.mwsyn._cw_frequency_command(freq)
        # # print_bytestring(bytescommand)
        # hw.mwsyn.serialcom.write(bytescommand)
        # _received = hw.mwsyn.serialcom.read(size=6)
        # freq_actual = freq  # fake actual freq

        # print("Actual frequency: ", freq_actual)
        self.freq_actual[jj] = ff  # freq_actual * hcf.VDISYN_multiplier
        hw.pg.startNow()
        time.sleep(1.0 / self.paraset["rate_refresh"])
        num_seg_collected = 0
        rawraw = hw.dig.stream()
        if rawraw is not None:
            num_seg_collected = rawraw.shape[0]
            rawraw_all = np.reshape(rawraw, (num_seg_collected, -1))
            rawraw_on = rawraw_all[0::2, :]
            rawraw_off = rawraw_all[1::2, :]
            self.sig_mwon_raw[jj, :] += np.sum(rawraw_on, axis=0)
            self.sig_mwoff_raw[jj, :] += np.sum(rawraw_off, axis=0)
            self.segment_list[jj] += num_seg_collected
        self.freq_idx += 1
        # hw.pg.forceFinal()

    def average_repeated_data(self, arr, start, stop, segments):
        averaged_norm = np.mean(arr[:, start:stop], axis=1)
        averaged_bg = np.mean(
            arr[:, self.bgextend_size - 156 : self.bgextend_size - 56], axis=1
        )  # TODO: use parameters instead of fixed number to select background

        averagednormalized = averaged_norm - averaged_bg
        result = np.divide(
            averagednormalized,
            segments,
            out=np.zeros_like(averagednormalized, dtype=float),
            where=segments != 0,
        )
        return result

    def _organize_data(self):
        self.sig_mwon = self.average_repeated_data(
            self.sig_mwon_raw,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            self.segment_list,
        )
        self.sig_mwoff = self.average_repeated_data(
            self.sig_mwoff_raw,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            self.segment_list,
        )

        self.dataset["signal"] = self.sig_mwon
        self.dataset["background"] = self.sig_mwoff
        self.dataset["freq"] = self.freq_actual
        self.dataset["num_repeat"] = np.mean(self.segment_list)

        super()._organize_data()

    def _shutdown_exp(self):
        # reconnect the mw syn connection
        hw.windfreak.disable()
        # hw.mwsyn.close_gracefully()
        # hw.mwsyn.open()

        # turn off laser and set diode current to zero
        hw.laser.laser_off()  # turn off laser
        hw.laser.set_diode_current(0.0, save_memory=False)

        hw.dig.stop_card()
        # hw.dig.reset()

        # pasue the mw pause then reboot
        # hw.mwsyn.sweep_pause()

        # mwsyn.reboot()

        # clear the pulse sequence
        hw.pg.forceFinal()
        hw.pg.rearm()
        hw.pg.constant(OutputState.ZERO())
        # hw.pg.reset()

    def _handle_exp_error(self):
        try:
            hw.laser.laser_off()  # turn off laser
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()

            hw.dig.stop_card()
            hw.dig.reset()
            hw.windfreak.disable()
            hw.windfreak.disconnect()
            hw.windfreak.connect()

            hw.pg.reset()
            hw.pg.reboot()

        except Exception as ee:
            print("I tried T^T")
            print(ee)


def sequence_Rabi(
    init_nslaser: int,
    init_isc: int,
    init_wait: int,
    init_repeat: int,
    read_wait: int,
    read_laser: int,
    mw_dur_begin: int,
    mw_dur_end: int,
    mw_dur_step: int,
):
    mw_dur = np.arange(mw_dur_begin, mw_dur_end, mw_dur_step)[::-1]  # reverse the mw
    seq_exp = []

    sub_init = [(["laser"], init_nslaser), ([], init_isc)] * init_repeat + [
        ([], init_wait)
    ]

    sub_evo_MW = [(["mwB"], mw_dur[0])]

    sub_read = [([], read_wait), (["laser", "sdtrig"], read_laser)]

    seq_exp += sub_init + sub_evo_MW + sub_read

    seqlet_time_max = seqtime(seq_exp)

    sub_evo_noMW = [([], mw_dur[0])]

    seq_exp += sub_init + sub_evo_noMW + sub_read

    for mwd in mw_dur[1:]:
        sub_evo_MW = [(["mwB"], mwd)]

        seqlet_MW = sub_init + sub_evo_MW + sub_read

        seqlet_time = seqtime(seqlet_MW)
        padtime = seqlet_time_max - seqlet_time
        sub_pad = [([], padtime)]

        sub_evo_noMW = [([], mwd)]

        seqlet_noMW = sub_init + sub_evo_noMW + sub_read

        seq_exp += sub_pad + seqlet_MW + sub_pad + seqlet_noMW

    sub_read = [([], read_wait), (["sdtrig"], read_laser)]
    padtime = seqlet_time_max - seqtime(sub_read)
    seqlet_bias = [([], padtime)]

    seq_rabiexp = seqlet_bias + seq_exp
    return seq_rabiexp, mw_dur


"""
TODO: fix some bugs and improve
1. the NIDAQ tasks for UCA and MWB phase
2. signal integration
"""


def sequence_Rabi_WDF(
    init_nslaser: int,
    init_isc: int,
    init_wait: int,
    init_repeat: int,
    read_wait: int,
    read_laser: int,
    mw_dur_begin: int,
    mw_dur_end: int,
    mw_dur_step: int,
):
    mw_dur = np.arange(mw_dur_begin, mw_dur_end, mw_dur_step)[::-1]  # reverse the mw
    seq_exp = []

    sub_init = [(["laser"], init_nslaser), ([], init_isc)] * init_repeat + [
        ([], init_wait)
    ]

    sub_evo_MW = [(["mwswitch"], mw_dur[0])]

    sub_read = [([], read_wait), (["laser", "sdtrig"], read_laser)]

    seq_exp += sub_init + sub_evo_MW + sub_read

    seqlet_time_max = seqtime(seq_exp)

    sub_evo_noMW = [([], mw_dur[0])]

    seq_exp += sub_init + sub_evo_noMW + sub_read

    for mwd in mw_dur[1:]:
        sub_evo_MW = [(["mwswitch"], mwd)]

        seqlet_MW = sub_init + sub_evo_MW + sub_read

        seqlet_time = seqtime(seqlet_MW)
        padtime = seqlet_time_max - seqlet_time
        sub_pad = [([], padtime)]

        sub_evo_noMW = [([], mwd)]

        seqlet_noMW = sub_init + sub_evo_noMW + sub_read

        seq_exp += sub_pad + seqlet_MW + sub_pad + seqlet_noMW

    sub_read = [([], read_wait), (["sdtrig"], read_laser)]
    padtime = seqlet_time_max - seqtime(sub_read)
    seqlet_bias = [([], padtime)]

    seq_rabiexp = seqlet_bias + seq_exp
    return seq_rabiexp, mw_dur


class Rabi_VDI(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            laser_current=80.0,  # percentage
            mw_freq=398.550,  # GHz
            mw_powervolt=5.0,  # voltage 0.0 to 5.0
            mw_phasevolt=0.0,  # voltage 0.0 to 5.0
            amp_input=1000,  # input amplitude for digitizer
            # -------------------
            init_nslaser=50,  # [ns]
            init_isc=150,
            init_repeat=40,
            init_wait=1000.0,
            read_wait=300.0,
            read_laser=900.0,
            mw_dur_begin=10.0,
            mw_dur_end=3500,
            mw_dur_step=50.0,
            # -------------------
            rate_refresh=10.0,
            moving_aveg=False,  # do moving average on data
            k_order=100,  # from int 1 to  inf
        )
        num_steps = int(
            (__paraset["mw_dur_end"] - __paraset["mw_dur_begin"])
            / __paraset["mw_dur_step"]
        )
        __dataset = dict(
            num_repeat=0,
            mw_freq=0.0,
            mw_dur=np.zeros(num_steps),
            sig_mw=np.zeros(num_steps),
            sig_nomw=np.zeros(num_steps),
        )

        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        # set the mw frequency --------------------------------------------------
        freq = self.paraset["mw_freq"] / 24.0
        try:
            hw.mwsyn.open()
        except Exception as ee:
            logger.exception(ee)
        _errorbyte, freq_actual = hw.mwsyn.cw_frequency(freq)
        # -----------------------------------------------------------------------

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # # -----------------------------------------------------------------------

        # set the mw power and phase ------------------------------------------------------
        mwpower_vlevel = self.paraset["mw_powervolt"]  # 5V equals to max power
        task_uca = nidaqmx.Task("UCA")  # user controlled attenuation
        task_uca.ao_channels.add_ao_voltage_chan(hcf.NI_ch_UCA, min_val=0, max_val=10)

        task_uca.start()
        task_uca.write([mwpower_vlevel], auto_start=False)

        mwphase_vlevel = self.paraset["mw_phasevolt"]  # voltage to phase shifter
        task_mwbp = nidaqmx.Task("MW B Phase")  # user controlled attenuation
        task_mwbp.ao_channels.add_ao_voltage_chan(hcf.NI_ch_MWBP, min_val=0, max_val=10)

        task_mwbp.start()
        task_mwbp.write([mwphase_vlevel], auto_start=False)
        # -----------------------------------------------------------------------

        # set the pulse sequence-------------------------------------------
        init_nslaser = self.paraset["init_nslaser"]
        init_isc = self.paraset["init_isc"]
        init_wait = self.paraset["init_wait"]
        init_repeat = self.paraset["init_repeat"]
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        mw_dur_begin = self.paraset["mw_dur_begin"]
        mw_dur_end = self.paraset["mw_dur_end"]
        mw_dur_step = self.paraset["mw_dur_step"]

        seq_rabiexp, mw_dur = sequence_Rabi(
            init_nslaser,
            init_isc,
            init_wait,
            init_repeat,
            read_wait,
            read_laser,
            mw_dur_begin,
            mw_dur_end,
            mw_dur_step,
        )

        tt_seq = hw.pg.setSequence(
            seq_rabiexp
        )  # WARNING only works well with small seq
        hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        hw.pg.setClock10MHzExt()
        hw.pg.stream(n_runs=REPEAT_INFINITELY)
        # -----------------------------------------------------------------------

        # set up the digitizer-------------------------------------------
        self.mw_dur_num = len(mw_dur)
        self.databufferlen = 2 * self.mw_dur_num

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming
        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            int(self.databufferlen / (tt_seq * rate_refresh / 1e9)) // 32 * 32
        )  # number of "reads" every data refresh

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
        self.bgextend_size = 256
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
        self.mw_dur = mw_dur
        # self.freq_actual = freq_actual
        self.freq_actual = self.paraset["mw_freq"]
        self.task_uca = task_uca
        self.task_mwbp = task_mwbp
        self.data_store = np.zeros(
            (self.databufferlen, pretrig_size + posttrig_size),
            dtype=np.float64,
            order="C",
        )
        self.idx_pointer = 0
        if self.paraset["moving_aveg"]:
            self.data_store_ma = np.zeros(
                (
                    self.paraset["k_order"],
                    self.databufferlen,
                    pretrig_size + posttrig_size,
                ),
                dtype=np.float64,
                order="C",
            )
            self.segments_ma = np.zeros((self.paraset["k_order"], self.databufferlen))
        else:
            self.data_store_ma = None
            self.segments_ma = None

        self.dataset["sig_mw"] = np.zeros(self.mw_dur_num)
        self.dataset["sig_nomw"] = np.zeros(self.mw_dur_num)
        # -----------------------------------------------------------------------
        self.segments = np.zeros(self.databufferlen)

        # start the laser and DAQ then wait for trigger from the  pulse streamer--------------
        hw.laser.laser_on()  # turn on laser
        # logger.debug("Start the trigger from the pulse streamer")
        hw.dig.start_buffer()
        hw.pg.startNow()

    def _run_exp(self):
        self.rawraw = hw.dig.stream()
        if self.rawraw is not None:
            # # Check if self.rawraw is a numpy array
            # if not isinstance(self.rawraw, np.ndarray):
            #     raise ValueError("self.rawraw is not a numpy array")
            # Get the number of segments
            # print(self.rawraw.shape)
            num_segs = self.rawraw.shape[0]
            idx_ptr_overflow = self.idx_pointer + num_segs
            count_fill, idx_pointer_new = divmod(idx_ptr_overflow, self.databufferlen)
            # print(
            #     f"idx_pointer: {self.idx_pointer}, num_segs: {num_segs}, count_fill: {count_fill}, idx_pointer_new: {idx_pointer_new}, databufferlen: {self.databufferlen}"
            # )
            if self.paraset["moving_aveg"]:
                # TODO: !! this is a dummy way to do moving average that would throw out some data
                # shift the MA data store buffer
                self.data_store -= self.data_store_ma[0]
                self.segments -= self.segments_ma[0]
                self.data_store_ma[0:-1] = self.data_store_ma[1:]
                self.segments_ma[0:-1] = self.segments_ma[1:]

                # assign the new data to the last slot in the MA data store
                if count_fill > 1:
                    num_tailslot = self.databufferlen - self.idx_pointer
                    to_add_unstructured = np.reshape(
                        self.rawraw[
                            num_tailslot : num_tailslot
                            + (count_fill - 1) * self.databufferlen
                        ],
                        (count_fill - 1, self.databufferlen, -1),
                    )

                    self.data_store_ma[-1] = np.sum(to_add_unstructured, axis=0)
                    self.segments_ma[-1] = count_fill - 1
                self.data_store += self.data_store_ma[-1]
                self.segments += self.segments_ma[-1]
            else:
                if count_fill < 1:
                    # underfill================================
                    # if the segment number is small to the remaining slot numbers in the buffer
                    idx_i = self.idx_pointer
                    idx_f = self.idx_pointer + num_segs
                    self.data_store[idx_i:idx_f, :] += np.reshape(
                        self.rawraw[:num_segs], (num_segs, -1)
                    )
                    self.segments[idx_i:idx_f] += 1
                else:
                    # exactly fill or overfill===============================

                    # fill the tail of the data_store buffer ----------------
                    num_tailslot = self.databufferlen - self.idx_pointer
                    idx_i = self.idx_pointer
                    idx_f = self.databufferlen
                    self.data_store[idx_i:idx_f, :] += np.reshape(
                        self.rawraw[:num_tailslot], (num_tailslot, -1)
                    )

                    self.segments[idx_i:idx_f] += 1

                    # fill the entire data_store buffer multiple times ----------------
                    if count_fill > 1:
                        to_add_unstructured = np.reshape(
                            self.rawraw[
                                num_tailslot : num_tailslot
                                + (count_fill - 1) * self.databufferlen
                            ],
                            (count_fill - 1, self.databufferlen, -1),
                        )
                        self.data_store += np.sum(to_add_unstructured, axis=0)
                        self.segments += count_fill - 1

                    # fill the head of the data_store buffer for the remaining segments --------------
                    self.data_store[:idx_pointer_new, :] += (
                        np.reshape(
                            self.rawraw[-idx_pointer_new:], (idx_pointer_new, -1)
                        )
                        if idx_pointer_new
                        else self.data_store[:idx_pointer_new, :]
                    )  # the if condition is needed to handle the case that the idx_pointer_new is 0
                    self.segments[:idx_pointer_new] += 1
            self.idx_pointer = idx_pointer_new

        # self.data_store_push = np.copy(self.data_store)
        # self.segments_push = np.copy(self.segments)
        self.data_store_push = self.data_store
        self.segments_push = self.segments
        self.idx_run = self.segments_push[-1]
        # -----------------------------------------------------------------------
        return None

    def average_repeated_data(self, arr, start, stop, segments):
        averaged_norm = np.mean(arr[:, start:stop], axis=1) / segments
        averaged_bg = (
            np.mean(arr[:, self.bgextend_size - 156 : self.bgextend_size - 56], axis=1)
            / segments
        )  # TODO: use parameters instead of fixed number to select background
        with_mw = averaged_norm[0::2] - averaged_bg[0::2]
        no_mw = averaged_norm[1::2] - averaged_bg[1::2]
        return no_mw, with_mw

    # TODO: Generalize the start stop, maybe add the SNR opt
    def _organize_data(self):
        self.no_mw, self.mw = self.average_repeated_data(
            self.data_store_push,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            self.segments_push,
        )  # TODO: use parameters instead of fixed number to select integration window

        self.dataset["sig_mw"] = self.mw
        self.dataset["sig_nomw"] = self.no_mw
        self.dataset["mw_dur"] = self.mw_dur
        self.dataset["mw_freq"] = self.freq_actual
        self.dataset["num_repeat"] = self.idx_run

        return super()._organize_data()

    def _handle_exp_error(self):
        try:
            hw.laser.laser_off()  # turn off laser
            hw.laser.set_diode_current(0.00, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            hw.laser.open()

            hw.mwsyn.reboot()
            hw.mwsyn.close()
            hw.mwsyn.open()

            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            hw.pg.reboot()

            self.task_uca.stop()
            self.task_uca.close()
            self.task_mwbp.stop()
            self.task_mwbp.close()
            hw.dig.stop_card()
            hw.dig.reset()

        except Exception as ee:
            print("I tried T^T")
            print(ee)

    def _shutdown_exp(self):
        # turn off laser and set diode current to zero
        hw.laser.laser_off()
        hw.laser.set_diode_current(0.00, save_memory=False)
        # hw.laser.close()
        # reset pulse generator
        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())
        # hw.pg.reset()
        self.task_uca.stop()
        self.task_uca.close()
        self.task_mwbp.stop()
        self.task_mwbp.close()
        _ = hw.dig.stream()
        hw.dig.stop_card()
        # hw.dig.reset()
        # reboot(optional) and close the MW synthesizer
        # mwsyn.reboot()
        # hw.mwsyn.close()
        # hw.mwsyn.close()


class Rabi_WDF(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            laser_current=80.0,  # percentage
            mw_freq=398.550,  # GHz
            mw_powervolt=5.0,  # voltage 0.0 to 5.0
            mw_phasevolt=0.0,  # voltage 0.0 to 5.0
            amp_input=1000,  # input amplitude for digitizer
            # -------------------
            init_nslaser=50,  # [ns]
            init_isc=150,
            init_repeat=40,
            init_wait=1000.0,
            read_wait=300.0,
            read_laser=900.0,
            mw_dur_begin=10.0,
            mw_dur_end=3500,
            mw_dur_step=50.0,
            # -------------------
            rate_refresh=10.0,
            moving_aveg=False,  # do moving average on data
            k_order=100,  # from int 1 to  inf
        )
        num_steps = int(
            (__paraset["mw_dur_end"] - __paraset["mw_dur_begin"])
            / __paraset["mw_dur_step"]
        )
        __dataset = dict(
            num_repeat=0,
            mw_freq=0.0,
            mw_dur=np.zeros(num_steps),
            sig_mw=np.zeros(num_steps),
            sig_nomw=np.zeros(num_steps),
        )

        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        # set the mw frequency --------------------------------------------------
        freq = self.paraset["mw_freq"] / 24.0
        hw.windfreak.set_output(
            freq=freq * (1e9), power=self.paraset["mw_powervolt"]
        )  # 16.6056 GHz
        time.sleep(0.1)
        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # # -----------------------------------------------------------------------

        # # set the mw power and phase ------------------------------------------------------
        # mwpower_vlevel = self.paraset["mw_powervolt"]  # 5V equals to max power
        # task_uca = nidaqmx.Task("UCA")  # user controlled attenuation
        # task_uca.ao_channels.add_ao_voltage_chan(hcf.NI_ch_UCA, min_val=0, max_val=10)

        # task_uca.start()
        # task_uca.write([mwpower_vlevel], auto_start=False)

        # mwphase_vlevel = self.paraset["mw_phasevolt"]  # voltage to phase shifter
        # task_mwbp = nidaqmx.Task("MW B Phase")  # user controlled attenuation
        # task_mwbp.ao_channels.add_ao_voltage_chan(hcf.NI_ch_MWBP, min_val=0, max_val=10)

        # task_mwbp.start()
        # task_mwbp.write([mwphase_vlevel], auto_start=False)
        # -----------------------------------------------------------------------

        # set the pulse sequence-------------------------------------------
        init_nslaser = self.paraset["init_nslaser"]
        init_isc = self.paraset["init_isc"]
        init_wait = self.paraset["init_wait"]
        init_repeat = self.paraset["init_repeat"]
        read_wait = self.paraset["read_wait"]
        read_laser = self.paraset["read_laser"]
        mw_dur_begin = self.paraset["mw_dur_begin"]
        mw_dur_end = self.paraset["mw_dur_end"]
        mw_dur_step = self.paraset["mw_dur_step"]

        seq_rabiexp, mw_dur = sequence_Rabi_WDF(
            init_nslaser,
            init_isc,
            init_wait,
            init_repeat,
            read_wait,
            read_laser,
            mw_dur_begin,
            mw_dur_end,
            mw_dur_step,
        )

        tt_seq = hw.pg.setSequence(
            seq_rabiexp
        )  # WARNING only works well with small seq
        hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        hw.pg.stream(n_runs=REPEAT_INFINITELY)
        # -----------------------------------------------------------------------

        # set up the digitizer-------------------------------------------
        self.mw_dur_num = len(mw_dur)
        self.databufferlen = 2 * self.mw_dur_num

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming
        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            int(self.databufferlen / (tt_seq * rate_refresh / 1e9)) // 32 * 32
        )  # number of "reads" every data refresh

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
        self.bgextend_size = 256
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
        hw.dig.set_config()
        # -----------------------------------------------------------------------

        # put some necessary variables in self-------------------------------------
        self.mw_dur = mw_dur
        # self.freq_actual = freq_actual
        self.freq_actual = self.paraset["mw_freq"]
        # self.task_uca = task_uca
        # self.task_mwbp = task_mwbp
        self.data_store = np.zeros(
            (self.databufferlen, pretrig_size + posttrig_size),
            dtype=np.float64,
            order="C",
        )
        self.idx_pointer = 0
        if self.paraset["moving_aveg"]:
            self.data_store_ma = np.zeros(
                (
                    self.paraset["k_order"],
                    self.databufferlen,
                    pretrig_size + posttrig_size,
                ),
                dtype=np.float64,
                order="C",
            )
            self.segments_ma = np.zeros((self.paraset["k_order"], self.databufferlen))
        else:
            self.data_store_ma = None
            self.segments_ma = None

        self.dataset["sig_mw"] = np.zeros(self.mw_dur_num)
        self.dataset["sig_nomw"] = np.zeros(self.mw_dur_num)
        # -----------------------------------------------------------------------
        self.segments = np.zeros(self.databufferlen)

        # start the laser and DAQ then wait for trigger from the  pulse streamer--------------
        hw.laser.laser_on()  # turn on laser
        # logger.debug("Start the trigger from the pulse streamer")
        hw.dig.start_buffer()
        hw.pg.startNow()

    def _run_exp(self):
        self.rawraw = hw.dig.stream()
        if self.rawraw is not None:
            # # Check if self.rawraw is a numpy array
            # if not isinstance(self.rawraw, np.ndarray):
            #     raise ValueError("self.rawraw is not a numpy array")
            # Get the number of segments
            # print(self.rawraw.shape)
            num_segs = self.rawraw.shape[0]
            idx_ptr_overflow = self.idx_pointer + num_segs
            count_fill, idx_pointer_new = divmod(idx_ptr_overflow, self.databufferlen)
            # print(
            #     f"idx_pointer: {self.idx_pointer}, num_segs: {num_segs}, count_fill: {count_fill}, idx_pointer_new: {idx_pointer_new}, databufferlen: {self.databufferlen}"
            # )
            if self.paraset["moving_aveg"]:
                # TODO: !! this is a dummy way to do moving average that would throw out some data
                # shift the MA data store buffer
                self.data_store -= self.data_store_ma[0]
                self.segments -= self.segments_ma[0]
                self.data_store_ma[0:-1] = self.data_store_ma[1:]
                self.segments_ma[0:-1] = self.segments_ma[1:]

                # assign the new data to the last slot in the MA data store
                if count_fill > 1:
                    num_tailslot = self.databufferlen - self.idx_pointer
                    to_add_unstructured = np.reshape(
                        self.rawraw[
                            num_tailslot : num_tailslot
                            + (count_fill - 1) * self.databufferlen
                        ],
                        (count_fill - 1, self.databufferlen, -1),
                    )

                    self.data_store_ma[-1] = np.sum(to_add_unstructured, axis=0)
                    self.segments_ma[-1] = count_fill - 1
                self.data_store += self.data_store_ma[-1]
                self.segments += self.segments_ma[-1]
            else:
                if count_fill < 1:
                    # underfill================================
                    # if the segment number is small to the remaining slot numbers in the buffer
                    idx_i = self.idx_pointer
                    idx_f = self.idx_pointer + num_segs
                    self.data_store[idx_i:idx_f, :] += np.reshape(
                        self.rawraw[:num_segs], (num_segs, -1)
                    )
                    self.segments[idx_i:idx_f] += 1
                else:
                    # exactly fill or overfill===============================

                    # fill the tail of the data_store buffer ----------------
                    num_tailslot = self.databufferlen - self.idx_pointer
                    idx_i = self.idx_pointer
                    idx_f = self.databufferlen
                    self.data_store[idx_i:idx_f, :] += np.reshape(
                        self.rawraw[:num_tailslot], (num_tailslot, -1)
                    )

                    self.segments[idx_i:idx_f] += 1

                    # fill the entire data_store buffer multiple times ----------------
                    if count_fill > 1:
                        to_add_unstructured = np.reshape(
                            self.rawraw[
                                num_tailslot : num_tailslot
                                + (count_fill - 1) * self.databufferlen
                            ],
                            (count_fill - 1, self.databufferlen, -1),
                        )
                        self.data_store += np.sum(to_add_unstructured, axis=0)
                        self.segments += count_fill - 1

                    # fill the head of the data_store buffer for the remaining segments --------------
                    self.data_store[:idx_pointer_new, :] += (
                        np.reshape(
                            self.rawraw[-idx_pointer_new:], (idx_pointer_new, -1)
                        )
                        if idx_pointer_new
                        else self.data_store[:idx_pointer_new, :]
                    )  # the if condition is needed to handle the case that the idx_pointer_new is 0
                    self.segments[:idx_pointer_new] += 1
            self.idx_pointer = idx_pointer_new

        # self.data_store_push = np.copy(self.data_store)
        # self.segments_push = np.copy(self.segments)
        self.data_store_push = self.data_store
        self.segments_push = self.segments
        self.idx_run = self.segments_push[-1]
        # -----------------------------------------------------------------------
        return None

    def average_repeated_data(self, arr, start, stop, segments):
        averaged_norm = np.mean(arr[:, start:stop], axis=1) / segments
        averaged_bg = (
            np.mean(arr[:, self.bgextend_size - 156 : self.bgextend_size - 56], axis=1)
            / segments
        )  # TODO: use parameters instead of fixed number to select background
        with_mw = averaged_norm[0::2] - averaged_bg[0::2]
        no_mw = averaged_norm[1::2] - averaged_bg[1::2]
        return no_mw, with_mw

    # TODO: Generalize the start stop, maybe add the SNR opt
    def _organize_data(self):
        self.no_mw, self.mw = self.average_repeated_data(
            self.data_store_push,
            self.bgextend_size + 160,
            self.bgextend_size + 400,
            self.segments_push,
        )  # TODO: use parameters instead of fixed number to select integration window

        self.dataset["sig_mw"] = self.mw
        self.dataset["sig_nomw"] = self.no_mw
        self.dataset["mw_dur"] = self.mw_dur
        self.dataset["mw_freq"] = self.freq_actual
        self.dataset["num_repeat"] = self.idx_run

        return super()._organize_data()

    def _handle_exp_error(self):
        try:
            hw.laser.laser_off()  # turn off laser
            hw.laser.set_diode_current(0.00, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            hw.laser.open()

            hw.windfreak.disable()
            hw.windfreak.disconnect()
            hw.windfreak.connect()
            # hw.mwsyn.reboot()
            # hw.mwsyn.close()
            # hw.mwsyn.open()

            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            hw.pg.reboot()

            # self.task_uca.stop()
            # self.task_uca.close()
            # self.task_mwbp.stop()
            # self.task_mwbp.close()
            hw.dig.stop_card()
            hw.dig.reset()

        except Exception as ee:
            print("I tried T^T")
            print(ee)

    def _shutdown_exp(self):
        # turn off laser and set diode current to zero
        hw.laser.laser_off()
        hw.laser.set_diode_current(0.00, save_memory=False)
        hw.windfreak.disable()

        # hw.laser.close()
        # reset pulse generator
        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())
        hw.pg.reset()
        # self.task_uca.stop()
        # self.task_uca.close()
        # self.task_mwbp.stop()
        # self.task_mwbp.close()
        hw.dig.stop_card()
        # hw.dig.reset()
        # reboot(optional) and close the MW synthesizer
        # mwsyn.reboot()
        # hw.mwsyn.close()
        # hw.mwsyn.close()


# import logging

# from hardware.hardwaremanager import HardwareManager
# from measurement.task_base import Measurement

# logger = logging.getLogger(__name__)
# hw = HardwareManager()

# import logging

# from hardware.hardwaremanager import HardwareManager
# from measurement.task_base import Measurement

# logger = logging.getLogger(__name__)
# hw = HardwareManager()

# import logging

# from hardware.hardwaremanager import HardwareManager
# from measurement.task_base import Measurement

# logger = logging.getLogger(__name__)
# hw = HardwareManager()


class PL_trace(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            laser_current=80.0,
            num_segment=64,
            pre_trig_size=16,
            segment_size=256 * 16 * 2,
            sampling_rate=10e6,
            amp_input=1000,
            readout_ch=hcf.SIDIG_chmap["apd"],
            terminate_input=TERMIN_INPUT_1MOHM,
            DCCOUPLE=0,
            wait_time=1e7,
            window_size=20.0,
            scale_window=5.0,
            run_time=3600.0,  # Total run time in seconds
        )
        # TODO move these calculations to the _setup_exp
        __paraset["post_trig_size"] = (
            __paraset["segment_size"] - __paraset["pre_trig_size"]
        )
        __paraset["memsize"] = __paraset["num_segment"] * __paraset["segment_size"]
        __paraset["notify_size"] = int(__paraset["memsize"] // 4)

        __dataset = dict(
            x_data=[],
            y_data=[],
            run_time=0,
            num_repeat=0,
        )

        super().__init__(name, __paraset, __dataset)
        # self.start_time = None

    def _setup_exp(self):
        logger.debug("Setting up PL_trace experiment")
        # Clean up instruments
        hw.laser.laser_off()
        hw.dig.stop_card()
        hw.pg.forceFinal()
        hw.pg.reset()

        # Set up the laser
        hw.laser.open()
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(self.paraset["laser_current"], save_memory=False)

        # Set up the pulse generator
        time_on = self.paraset["segment_size"] * (
            1 / self.paraset["sampling_rate"] * 1e9
        )
        wait = self.paraset["wait_time"]
        seq_laser = [
            (time_on / 3, HIGH),
            (time_on / 3, LOW),
            (time_on / 3, HIGH),
            (wait, LOW),
        ]
        seq_dig = [(time_on, HIGH), (wait, LOW)]

        hw.pg.setDigital("sdtrig", seq_dig)
        hw.pg.setDigital("laser", seq_laser)
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

        # Set up the digitizer
        hw.dig.reset_param()
        hw.dig.assign_param(
            dict(
                readout_ch=self.paraset["readout_ch"],
                amp_input=self.paraset["amp_input"],
                num_segment=self.paraset["num_segment"],
                pretrig_size=self.paraset["pre_trig_size"],
                posttrig_size=self.paraset["post_trig_size"],
                segment_size=self.paraset["segment_size"],
                terminate_input=self.paraset["terminate_input"],
                DCCOUPLE=self.paraset["DCCOUPLE"],
                sampling_rate=self.paraset["sampling_rate"],
                notify_size=self.paraset["notify_size"],
                mem_size=self.paraset["memsize"],
            )
        )
        hw.dig.set_config()

        # Start hardware
        hw.pg.stream(n_runs=INF)
        hw.dig.start_buffer()
        hw.pg.startNow()
        hw.laser.laser_on()

        # Reset the pl start time
        if not self.tokeep:
            # # Reset dataset and prepare for new start time
            # self.dataset["x_data"] = []
            # self.dataset["y_data"] = []
            # # self.dataset["run_time"] = self.paraset["run_time"]
            # self.dataset["num_repeat"] = 0
            self.pl_start_time = time.time()
            # self.start_time = None  # Set to None to trigger reset in _run_exp
            logger.debug(
                "Dataset reset: x_data, y_data, num_repeat cleared;"
                # "Dataset reset: x_data, y_data, num_repeat cleared; start_time set to None"
            )

        _new_y = hw.dig.stream()  # to acquire and throw out the first data

    def _run_exp(self):
        # logger.debug("Running PL_trace experiment")
        # # Reset start_time at the beginning of each new run
        # if self.start_time is None:
        #     self.start_time = time.time()
        #     logger.debug("Reset start_time to %f", self.start_time)

        # current_time = time.time() - self.start_time
        # logger.debug("Current time: %f, start_time: %f", current_time, self.start_time)

        # if current_time >= self.paraset["run_time"]:
        #     logger.debug("Run time exceeded, stopping")
        #     self.state = "done"
        #     return

        self.new_y = hw.dig.stream()
        if self.new_y is None or len(self.new_y) == 0:
            logger.debug("No data from digitizer")
            return
        self.timestamp = time.time() - self.pl_start_time

        # self.stateset["time_run"] = current_time
        # self.stateset["time_stop"] = self.paraset["run_time"]

    def _organize_data(self):
        # logger.debug("Organizing PL_trace data")
        # avg = np.mean(self.new_y)
        # current_time = time.time() - self.start_time

        # self.dataset["x_data"].append(current_time)
        # self.dataset["y_data"].append(avg)

        # # Keep only the last window_size seconds of data
        # while (
        #     len(self.dataset["x_data"]) > 0
        #     and (current_time - self.dataset["x_data"][0]) > self.paraset["window_size"]
        # ):
        #     self.dataset["x_data"].pop(0)
        #     self.dataset["y_data"].pop(0)
        # current_time = time.time() - self.pl_start_time

        self.dataset["x_data"].append(self.timestamp)
        self.dataset["y_data"].append(np.mean(self.new_y) * 1e3)  # in mV
        # Keep only the last window_size seconds of data
        while (
            len(self.dataset["x_data"]) > 0
            and (self.timestamp - self.dataset["x_data"][0])
            > self.paraset["window_size"]
        ):
            self.dataset["x_data"].pop(0)
            self.dataset["y_data"].pop(0)
        self.dataset["num_repeat"] += 1
        super()._organize_data()  # update the default set

    def _shutdown_exp(self):
        logger.debug("Shutting down PL_trace experiment")
        try:
            hw.laser.laser_off()
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.dig.stop_card()
            # hw.dig.reset()
            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            logger.info("PL_trace shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            self.state = "error"

    def _handle_exp_error(self):
        logger.debug("Handling PL_trace experiment error")
        try:
            hw.laser.laser_off()
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            hw.dig.stop_card()
            hw.dig.reset()
            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            hw.pg.reboot()
            logger.info("PL_trace error handling complete")
        except Exception as e:
            logger.error(f"Error during error handling: {e}")
            print(f"Error handling failed: {e}")


# class PL_trace(Measurement):
#     def __init__(self, name="default"):
#         _paraset = dict(
#             laser_current=80.0,
#             num_segment=64,
#             pre_trig_size=16,
#             segment_size=256 * 16 * 2,
#             sampling_rate=10e6,
#             amp_input=1000,
#             readout_ch=hcf.SIDIG_chmap["apd"],
#             terminate_input=TERMIN_INPUT_1MOHM,
#             DCCOUPLE=0,
#             wait_time=1e7,
#             window_size=20.0,
#             scale_window=5.0,
#             run_time=3600.0,  # Total run time in seconds
#         )
#         _paraset["post_trig_size"] = (
#             _paraset["segment_size"] - _paraset["pre_trig_size"]
#         )
#         _paraset["memsize"] = _paraset["num_segment"] * _paraset["segment_size"]
#         _paraset["notify_size"] = int(_paraset["memsize"] // 4)

#         _dataset = dict(
#             x_data=[],
#             y_data=[],
#             run_time=0,
#             num_repeat=0,
#         )

#         super().__init__(name, _paraset, _dataset)
#         self.start_time = None

#     def _setup_exp(self):
#         logger.debug("Setting up PL_trace experiment")
#         # Clean up instruments
#         hw.laser.laser_off()
#         hw.dig.stop_card()
#         hw.pg.forceFinal()
#         hw.pg.reset()

#         # Set up the laser
#         hw.laser.open()
#         hw.laser.laser_off()
#         hw.laser.set_analog_control_mode("current")
#         hw.laser.set_modulation_state("Pulsed")
#         hw.laser.set_diode_current(self.paraset["laser_current"], save_memory=False)

#         # Set up the pulse generator
#         time_on = self.paraset["segment_size"] * (
#             1 / self.paraset["sampling_rate"] * 1e9
#         )
#         wait = self.paraset["wait_time"]
#         seq_laser = [
#             (time_on / 3, HIGH),
#             (time_on / 3, LOW),
#             (time_on / 3, HIGH),
#             (wait, LOW),
#         ]
#         seq_dig = [(time_on, HIGH), (wait, LOW)]

#         hw.pg.setDigital("sdtrig", seq_dig)
#         hw.pg.setDigital("laser", seq_laser)
#         hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

#         # Set up the digitizer
#         hw.dig.reset_param()
#         hw.dig.assign_param(
#             dict(
#                 readout_ch=self.paraset["readout_ch"],
#                 amp_input=self.paraset["amp_input"],
#                 num_segment=self.paraset["num_segment"],
#                 pretrig_size=self.paraset["pre_trig_size"],
#                 posttrig_size=self.paraset["post_trig_size"],
#                 segment_size=self.paraset["segment_size"],
#                 terminate_input=self.paraset["terminate_input"],
#                 DCCOUPLE=self.paraset["DCCOUPLE"],
#                 sampling_rate=self.paraset["sampling_rate"],
#                 notify_size=self.paraset["notify_size"],
#                 mem_size=self.paraset["memsize"],
#             )
#         )
#         hw.dig.set_config()

#         # Initialize data
#         self.current_time = time.time()
#         self.dataset["x_data"] = []
#         self.dataset["y_data"] = []
#         self.dataset["run_time"] = self.paraset["run_time"]
#         self.dataset["num_repeat"] = 0
#         self.start_time = time.time()

#         # Start hardware
#         hw.pg.stream(n_runs=INF)
#         hw.dig.start_buffer()
#         hw.pg.startNow()
#         hw.laser.laser_on()

#     def _run_exp(self):
#         logger.debug("Running PL_trace experiment")
#         if self.start_time is None:
#             self.start_time = time.time()

#         self.current_time = time.time() - self.start_time
#         if self.current_time >= self.paraset["run_time"]:
#             logger.debug("Run time exceeded, stopping")
#             self.state = "done"
#             return

#         self.new_y = hw.dig.stream()
#         if self.new_y is None or len(self.new_y) == 0:
#             logger.debug("No data from digitizer")
#             return

#         self._organize_data()
#         self.dataset["num_repeat"] += 1
#         self.stateset["time_run"] = self.current_time
#         self.stateset["time_stop"] = self.paraset["run_time"]

#     def _organize_data(self):
#         logger.debug("Organizing PL_trace data")
#         avg = np.mean(self.new_y)
#         current_time = time.time() - self.start_time

#         self.dataset["x_data"].append(current_time)
#         self.dataset["y_data"].append(avg)

#         # Keep only the last window_size seconds of data
#         while (
#             len(self.dataset["x_data"]) > 0
#             and (current_time - self.dataset["x_data"][0]) > self.paraset["window_size"]
#         ):
#             self.dataset["x_data"].pop(0)
#             self.dataset["y_data"].pop(0)

#     def _shutdown_exp(self):
#         logger.debug("Shutting down PL_trace experiment")
#         try:
#             hw.laser.laser_off()
#             hw.laser.set_diode_current(0.0, save_memory=False)
#             hw.dig.stop_card()
#             hw.dig.reset()
#             hw.pg.forceFinal()
#             hw.pg.constant(OutputState.ZERO())
#             hw.pg.reset()
#             logger.info("PL_trace shutdown complete")
#             self.dataset["x_data"] = []
#             self.dataset["y_data"] = []
#             self.dataset["run_time"] = self.paraset["run_time"]
#         except Exception as e:
#             logger.error(f"Error during shutdown: {e}")
#             self.state = "error"

#     def _handle_exp_error(self):
#         logger.debug("Handling PL_trace experiment error")
#         try:
#             hw.laser.laser_off()
#             hw.laser.set_diode_current(0.0, save_memory=False)
#             hw.laser.reset_alarm()
#             hw.laser.close()
#             hw.dig.stop_card()
#             hw.dig.reset()
#             hw.pg.forceFinal()
#             hw.pg.constant(0)
#             hw.pg.reset()
#             hw.pg.reboot()
#             logger.info("PL_trace error handling complete")
#         except Exception as e:
#             logger.error(f"Error during error handling: {e}")
#             print(f"Error handling failed: {e}")


# class PL_trace(Measurement):  # Inherit from Measurement
#     def __init__(self, name="default"):
#         _paraset = dict(            # Single underscore instead of double
#             laser_current=80.0,
#             num_segment=64,
#             pre_trig_size=16,
#             post_trig_size=None,
#             segment_size=256*16*2,
#             sampling_rate=10e6, #hcf.SIDIG_maxsr,
#             memsize=None,
#             notify_size=None,
#             amp_input=1000,
#             readout_ch=hcf.SIDIG_chmap["apd"],
#             terminate_input=TERMIN_INPUT_1MOHM,
#             DCCOUPLE=0,
#             wait_time=1e7,
#             window_size=20,    # Add this
#             scale_window=5     # Add this
#         )
#         _paraset["post_trig_size"] = _paraset["segment_size"] - _paraset["pre_trig_size"]
#         _paraset['memsize'] = _paraset["num_segment"] * _paraset["segment_size"]
#         _paraset['notify_size'] = int(_paraset["memsize"] // 4)

#         # Add empty dataset like Rabi example
#         _dataset = dict(
#             x_data=[],
#             y_data=[],
#             run_time=0,
#         )

#         super().__init__(name, _paraset, _dataset)

#     def _setup_exp(self):
#         # clean up instruments
#         hw.laser.laser_off()
#         hw.dig.stop_card()
#         hw.pg.forceFinal()
#         hw.pg.reset()

#         # set up the laser
#         hw.laser.open()
#         hw.laser.laser_off()
#         hw.laser.set_analog_control_mode("current")
#         hw.laser.set_modulation_state("Pulsed")
#         hw.laser.set_diode_current(self.paraset["laser_current"], save_memory=False)

#         # setup the pulse generator
#         time_on = self.paraset["segment_size"] * int(1/self.paraset['sampling_rate']*1e9)
#         wait = self.paraset["wait_time"]
#         seq_laser=[(time_on/3, HIGH),(time_on/3,LOW),(time_on/3,HIGH),(wait,LOW)]
#         seq_dig=[(time_on,HIGH),(wait,LOW)]

#         seq_laserB=seq_laser+[(wait,LOW)]
#         hw.pg.setDigital('sdtrig',seq_dig)
#         hw.pg.setDigital('laser',seq_laser)
#         hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

#         # setup the digitizer
#         hw.dig.reset_param()
#         hw.dig.assign_param(dict(
#             readout_ch=self.paraset['readout_ch'],
#             amp_input=self.paraset['amp_input'],
#             num_segment=self.paraset['num_segment'],
#             pretrig_size=self.paraset['pre_trig_size'],
#             posttrig_size=self.paraset['post_trig_size'],
#             segment_size=self.paraset['segment_size'],
#             terminate_input=self.paraset['terminate_input'],
#             DCCOUPLE=self.paraset['DCCOUPLE'],
#             sampling_rate=self.paraset['sampling_rate'],  # Fixed typo
#             notify_size=self.paraset['notify_size'],
#             mem_size=self.paraset['memsize']  # Fixed name
#         ))
#         hw.dig.set_config()

#     def _organize_data(self):
#         avg = np.mean(self.new_y)
#         current_time = time.time() - self.start_time

#         self.dataset["x_data"].append(current_time)
#         self.dataset["y_data"].append(avg)

#         # Keep only the last 20 seconds of data
#         while (len(self.dataset["x_data"]) > 0 and
#                (current_time - self.dataset["x_data"][0]) > self.window_size):
#             self.dataset["x_data"].pop(0)
#             self.dataset["y_data"].pop(0)

#     def _run_exp(self):
#         self.start_time = time.time()
#         self.run_time = 60 * 60  # Total script run time
#         self.window_size = 20    # Show 20 seconds of data
#         self.scale_window = 5    # Scale Y-axis to the last 5 seconds

#         # Initialize dataset
#         self.dataset["x_data"] = []
#         self.dataset["y_data"] = []
#         self.dataset["run_time"] = self.run_time

#         # Hardware setup
#         hw.pg.stream(n_runs=INF)
#         hw.dig.start_buffer()
#         hw.pg.startNow()
#         hw.laser.laser_on()

#         while time.time() - self.start_time < self.run_time:
#             self.new_y = hw.dig.stream()
#             if self.new_y is None or len(self.new_y) == 0:
#                 continue  # Skip empty data

#             self._organize_data()  # Call directly instead of super()
#             time.sleep(0.01)

#     def _shutdown_exp(self):  # Single underscore
#         print("Streaming Ended!")
#         hw.laser.laser_off()
#         hw.dig.stream()
#         hw.dig.stop_card()
#         hw.pg.forceFinal()

# class PL_trace(Measurement):
#     def __init__(self,name="default"):
#         __paraset = dict(
#             laser_current= 80.0,
#             num_segment=64,
#             pre_trig_size=16,
#             post_trig_size=None,
#             segment_size=256*16*2,
#             sampling_rate=10e6, #hcf.SIDIG_maxsr,
#             memsize=None,
#             notify_size=None,
#             amp_input=1000,
#             readout_ch=hcf.SIDIG_chmap["apd"],
#             terminate_input=TERMIN_INPUT_1MOHM,
#             DCCOUPLE=0,
#             wait_time=1e7
#             , )
#         __paraset["post_trig_size"] = __paraset["segment_size"] - __paraset["pre_trig_size"]
#         __paraset['memsize'] = __paraset["num_segment"] *__paraset["segment_size"]
#         __paraset['notify_size'] = int(__paraset["memsize"] //4)

#         super().__init__(name, __paraset) #, __dataset)

#         pass
#     def _setup_exp(self):
#         # clean up instrumements
#         hw.laser.laser_off()
#         hw.dig.stop_card()
#         hw.pg.forceFinal()
#         hw.pg.rest()

#         # set up the laser
#         hw.laser.open()
#         hw.laser.laser_off()
#         hw.laser.set_analog_control_mode("current")
#         hw.laser.set_modulation_state("Pulsed")
#         hw.laser.set_diode_current(self.paraset["laser_current"], save_memory=False)

#         # setup the pulse generator
#         time_on = self.paraset["segment_size"] * int(1/self.paraset['sampling_rate']*1e9)
#         wait = self.paraset["wait_time"]
#         seq_laser=[(time_on/3, HIGH),(time_on/3,LOW),(time_on/3,HIGH),(wait,LOW)]
#         seq_dig=[(time_on,HIGH),(wait,LOW)]

#         seq_laserB=seq_laser+[(wait,LOW)]
#         hw.pg.setDigital('sdtrig',seq_dig)
#         hw.pg.setDigital('laser',seq_laser)
#         hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

#         # setup the digitizer
#         # To set the configuration, make a dictionary with the key and value
#         hw.dig.reset_param()
#         hw.dig.assign_param(dict(
#                     readout_ch=self.paraset['readout_ch'],
#                     amp_input=self.paraset['amp_input'],
#                     num_segment=self.paraset['num_segment'],
#                     pretrig_size=self.paraset['pre_trig_size'],
#                     posttrig_size=self.paraset['post_trig_size'],
#                     segment_size=self.paraset['segment_size'],
#                     terminate_input=self.paraset['terminate_input'],
#                     DCCOUPLE = self.paraset['DCCOUPLE'],
#                     sampling_rate=self.paraset['sampling_rate'],
#                     notify_size=self.paraset['notify_size'],
#                     mem_size= self.paraset['mem_size'] #int(256* num_samples_in_segment * 64)*units.Sa
#                     #  terminate_input=TERMIN_INPUT_50OHM,
#                     ))
#         hw.dig.set_config()
#     def _organize_data(self):
#         avg = np.mean(self.new_y)
#         current_time = time.time() - self.start_time

#         self.x_data.append(current_time)
#         self.y_data.append(avg)

#         # Keep only the last 20 seconds of data
#         while self.x_data and (current_time - self.x_data[0]) > self.window_size:
#             self.x_data.pop(0)
#             self.y_data.pop(0)

#         # Extract the last 5 seconds for scaling
#         scale_indices = [i for i, t in enumerate(self.x_data) if current_time - t <= self.scale_window]
#         if scale_indices:
#             recent_y = [self.y_data[i] for i in scale_indices]
#             y_min, y_max = min(recent_y), max(recent_y)
#             margin = (y_max - y_min) * 0.1 if y_max > y_min else 1  # Add some margin
#         else:
#             y_min, y_max = 0, 1
#             margin = 1


#     def _run_exp(self):
#         self.start_time = time.time()
#         self.run_time = 60 * 60  # Total script run time
#         self.window_size = 20    # Show 20 seconds of data
#         self.scale_window = 5    # Scale Y-axis to the last 5 seconds

#         self.x_data, self.y_data = [], []

#         # Hardware setup

#         hw.pg.stream(n_runs=INF)
#         hw.dig.start_buffer()
#         hw.pg.startNow()
#         hw.laser.laser_on()

#         while time.time() - self.start_time < self.run_time:
#             self.new_y = hw.dig.stream()
#             if self.new_y is None or len(self.new_y) == 0:
#                 continue  # Skip empty data


#             return super()._organize_data()

#             # # Update the figure dynamically
#             # fig.update_traces(y=y_data, x=x_data)
#             # fig.update_layout(
#             #     yaxis=dict(range=[y_min - margin, y_max + margin]),
#             #     xaxis=dict(range=[x_data[0], x_data[-1]]),
#             #     title="Streaming Data (Last 20s visible, Y-scale from last 5s)"
#             # )

#             # clear_output(wait=True)
#             # display(fig)

#             time.sleep(0.01)

#     def __shutdown_exp(self):
#         print("Streaming Ended!")
#         hw.laser.laser_off()
#         hw.dig.stream()
#         hw.dig.stop_card()
#         hw.pg.forceFinal()
