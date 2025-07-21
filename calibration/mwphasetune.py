import logging
import time

import numpy as np

from hardware import config as hcf
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import TriggerRearm, TriggerStart
from measurement.task_base import Measurement

logger = logging.getLogger(__name__)
hw = HardwareManager()


def seqtime(seq_tb):
    return np.sum([pulse[-1] for pulse in seq_tb])


def sequence_MWPhaseTune(
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

    sub_evo_MWA = [(["mwA"], mw_dur)]
    sub_evo_MWB = [(["mwB"], mw_dur)]

    sub_read = [([], read_wait), (["laser", "sdtrig"], read_laser)]

    seq_exp += sub_init + sub_evo_MWA + sub_evo_MWB + sub_read

    sub_evo_noMW = [([], mw_dur)]

    seq_exp += (
        sub_init + sub_evo_noMW + sub_evo_noMW + sub_read
    )  # add two elements of sub_evo_noMW to account for the 2 x mwdur in MWA and MAB

    _aux = None

    return seq_exp, _aux


class MWPhaseTune(Measurement):
    def __init__(self, name="default"):
        __paraset = dict(
            mw_phasevolt_start=0,  # Volts
            mw_phasevolt_stop=0.6,  # Volts
            mw_phasevolt_step=0.005,  # Volts
            # -------------------
            init_laser=1500.0,
            init_wait=401.0,
            init_nslaser=250,
            init_isc=250,
            init_repeat=50,
            mw_time=500.0,
            read_wait=500.0,
            read_laser=1201.0,
            # -------------------
            mw_powerlevel=5.0,
            laser_current=35,  # 0 to 100%
            amp_input=1000,  # input amplitude for digitizer
            repeat_daq=10,
            bz_bias_vol=1,  # -1V to 1V
            # -------------------
            rate_refresh=30.0,  # Hz rate of refreshing the entire spectrum, approx
            ODMR_freq=392.83,
        )

        # DEFINE THE DATASET
        __dataset = dict(
            num_repeat=0,
            phasevolt=np.zeros(
                len(
                    np.arange(
                        __paraset["mw_phasevolt_start"],
                        __paraset["mw_phasevolt_stop"],
                        __paraset["mw_phasevolt_step"],
                    )
                )
            ),
            signal=np.zeros(
                len(
                    np.arange(
                        __paraset["mw_phasevolt_start"],
                        __paraset["mw_phasevolt_stop"],
                        __paraset["mw_phasevolt_step"],
                    )
                )
            ),
            background=np.zeros(
                len(
                    np.arange(
                        __paraset["mw_phasevolt_start"],
                        __paraset["mw_phasevolt_stop"],
                        __paraset["mw_phasevolt_step"],
                    )
                )
            ),
        )
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        mw_phasevolt_start = self.paraset["mw_phasevolt_start"]
        mw_phasevolt_stop = self.paraset["mw_phasevolt_stop"]
        mw_phasevolt_step = self.paraset["mw_phasevolt_step"]
        ODMR_freq = self.paraset["ODMR_freq"]
        mw_phasevolt_array = np.arange(
            mw_phasevolt_start, mw_phasevolt_stop, mw_phasevolt_step
        )
        num_phase = len(mw_phasevolt_array)

        # set the resonant frequency ------------------------------------
        hw.vdi.set_freq(ODMR_freq)

        # set the MW power----------------------------------------------
        mwpower_level = self.paraset["mw_powerlevel"]
        hw.vdi.set_amp_volt(mwpower_level)

        # set the measurement sequence-------------------------------------------
        seq_exp, _ = sequence_MWPhaseTune(
            self.paraset["init_nslaser"],
            self.paraset["init_isc"],
            self.paraset["init_wait"],
            self.paraset["init_repeat"],
            self.paraset["read_wait"],
            self.paraset["read_laser"],
            self.paraset["mw_time"],
        )
        tt_seq = seqtime(seq_exp)

        hw.pg.setSequence(seq_exp, reset=True)
        hw.pg.setTrigger(start=TriggerStart.SOFTWARE, rearm=TriggerRearm.MANUAL)

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

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        hw.laser.laser_on()  # turn on laser

        # Allocate arrays and arguments for the experiment------------------------------------------------
        if not self.tokeep:
            self.num_seg_singlephase = num_segment
            self.num_phase = num_phase
            self.phase_actual = np.copy(mw_phasevolt_array)
            self.segment_list = np.zeros_like(self.phase_actual)
            self.sig_mwon_raw = np.zeros((len(self.phase_actual), segment_size))
            self.sig_mwoff_raw = np.zeros((len(self.phase_actual), segment_size))
            self.sig_mwon = np.zeros_like(self.phase_actual)
            self.sig_mwoff = np.zeros_like(self.phase_actual)
            self.num_repeat = 10
            self.phase_idx = 0

        # start the digitizer buffering------------------------------------
        hw.dig.set_config()
        hw.dig.start_buffer()

    def _run_exp(self):
        hw.pg.rearm()
        jj = self.phase_idx % self.num_phase
        ff = self.phase_actual[jj]
        hw.vdi.set_phase_volt(ff)

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
        self.phase_idx += 1

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
        self.dataset["phasevolt"] = self.phase_actual
        self.dataset["num_repeat"] = np.mean(self.segment_list)

        super()._organize_data()

    def _shutdown_exp(self):
        # reconnect the mw syn connection
        hw.vdi.set_amp_volt(0)
        hw.vdi.set_phase_volt(0)

        # turn off laser and set diode current to zero
        hw.laser.laser_off()  # turn off laser
        hw.laser.set_diode_current(0.0, save_memory=False)

        # pasue the mw pause then reboot
        # hw.mwsyn.sweep_pause()

        # mwsyn.reboot()

        # clear the pulse sequence
        hw.pg.forceFinal()
        # hw.pg.rearm()
        hw.pg.constant()  # default set to zero constant
        # hw.pg.reset()

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
            hw.pg.constant()
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
