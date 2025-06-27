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

    sub_evo_MW = [(["rfA"], mw_dur)]

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
            freq_start=(398.55 - 0.025),  # GHz
            freq_stop=(398.55 + 0.025),  # GHz
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
        _freq_actual = hw.mwsyn.cw_frequency(freq)
        hw.mwsyn.purge()
        # set the MW power----------------------------------------------
        mwpower_vlevel = self.paraset["mw_powervolt"]
        hw.mwmod.set_amp_volt(mwpower_vlevel)

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
        hw.pg.setSequence(seq_exp, reset=True)
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
        # freq_actual = hw.mwsyn.cw_frequency(freq)
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
        hw.mwmod.set_amp_volt(0)

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
            freq_start=0.4,  # GHz
            freq_stop=1.0,  # GHz
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
            mw_power=0.0,  # dBm
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
        hw.pg.setSequence(seq_exp, reset=True)
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

        # set RF -------------------------------------------------------------
        hw.windfreak.set_power(self.paraset["mw_power"], channel="rfA")
        hw.windfreak.enable_output(channel="rfA")
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
        freq = self.freq_actual[jj]
        try:
            hw.windfreak.set_freq(freq * 1e9, channel="rfA")
        except Exception as ee:
            logger.warning(f"Failed to set frequency to {freq} GHz on Windfreak: {ee}")
            return
        time.sleep(1 / self.paraset["rate_refresh"])

        hw.pg.startNow()
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

    sub_evo_MW = [(["rfA"], mw_dur[0])]

    sub_read = [([], read_wait), (["laser", "sdtrig"], read_laser)]

    seq_exp += sub_init + sub_evo_MW + sub_read

    seqlet_time_max = seqtime(seq_exp)

    sub_evo_noMW = [([], mw_dur[0])]

    seq_exp += sub_init + sub_evo_noMW + sub_read

    for mwd in mw_dur[1:]:
        sub_evo_MW = [(["rfA"], mwd)]

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


class Rabi(Measurement):
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
        freq_actual = hw.mwsyn.cw_frequency(freq)
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
        mwphase_vlevel = self.paraset["mw_phasevolt"]  # voltage to phase shifter
        hw.mwmod.set_amp_volt(mwpower_vlevel)
        hw.mwmod.set_phase_volt(mwphase_vlevel)
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
            seq_rabiexp, reset=True
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

    def _shutdown_exp(self):
        # turn off laser and set diode current to zero
        hw.laser.laser_off()
        hw.laser.set_diode_current(0.00, save_memory=False)
        # hw.laser.close()
        # reset pulse generator
        # set mw amp and phase to zero
        hw.mwmod.set_amp_volt(0)
        hw.mwmod.set_phase_volt(0)

        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())
        # hw.pg.reset()

        _ = hw.dig.stream()
        hw.dig.stop_card()
        # hw.dig.reset()
        # reboot(optional) and close the MW synthesizer
        # mwsyn.reboot()
        # hw.mwsyn.close()
        # hw.mwsyn.close()

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

            hw.mwmod.set_amp_volt(0)
            hw.mwmod.set_phase_volt(0)
            hw.mwmod.close()
            hw.mwmod.restart()

            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            hw.pg.reboot()

            hw.dig.stop_card()
            hw.dig.reset()

        except Exception as ee:
            print("I tried T^T")
            print(ee)


class Rabi_WDF(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            laser_current=80.0,  # percentage
            mw_freq=398.550,  # GHz
            mw_power=0.0,  # dBm
            mw_phase=0.0,  # deg
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
        freq = self.paraset["mw_freq"]
        hw.windfreak.set_output(
            freq=freq * (1e9), power=self.paraset["mw_power"]
        )  # 16.6056 GHz
        time.sleep(0.1)
        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # # -----------------------------------------------------------------------

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
            seq_rabiexp, reset=True
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
