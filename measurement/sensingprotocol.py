import logging
import time

import numpy as np

import hardware.config as hcf
from hardware.hardwaremanager import HardwareManager
from hardware.pulser.pulser import OutputState, TriggerRearm, TriggerStart
from measurement.task_base import Measurement

hw = HardwareManager()
logger = logging.getLogger(__name__)


def slice_average(data: np.ndarray, signal_range: tuple[int, int]) -> np.ndarray:
    """
    Computes the mean over a specified signal range for each row.

    Parameters:
        data (np.ndarray): 2D array (rows = segments, columns = samples).
        signal_range (tuple[int, int]): (start, end) index range (exclusive end).

    Returns:
        np.ndarray: 1D array of row-wise means over the signal range.
    """
    start, end = signal_range
    return np.mean(data[:, start:end], axis=1)


def slice_average_offset(
    data: np.ndarray, signal_range: tuple[int, int], background_range: tuple[int, int]
) -> np.ndarray:
    """
    Computes the mean over a signal range minus the mean over a background range.

    Parameters:
        data (np.ndarray): 2D array (rows = segments, columns = samples).
        signal_range (tuple[int, int]): (start, end) index range for the signal.
        background_range (tuple[int, int]): (start, end) index range for the background.

    Returns:
        np.ndarray: 1D array of background-subtracted signal means.
    """
    signal = slice_average(data, signal_range)
    background = slice_average(data, background_range)
    return signal - background


def weighted_average(data: np.ndarray, weight_fn: callable) -> np.ndarray:
    """
    Computes the weighted average over all columns using a custom weight function.

    Parameters:
        data (np.ndarray): 2D array (rows = segments, columns = samples).
        weight_fn (callable): Function that maps indices (np.arange) to weights.

    Returns:
        np.ndarray: 1D array of weighted averages per row.
    """
    indices = np.arange(data.shape[1])
    weights = weight_fn(indices)
    weights = weights / np.sum(weights)
    return np.average(data, axis=1, weights=weights)


def weighted_average_offset(
    data: np.ndarray, signal_weight_fn: callable, background_range: tuple[int, int]
) -> np.ndarray:
    """
    Computes the weighted average of a signal region minus the mean over a background slice.

    Parameters:
        data (np.ndarray): 2D array (rows = segments, columns = samples).
        signal_weight_fn (callable): Weight function over all columns for the signal.
        background_range (tuple[int, int]): (start, end) index range for background.

    Returns:
        np.ndarray: 1D array of background-subtracted weighted averages.
    """
    signal = weighted_average(data, signal_weight_fn)
    background = slice_average(data, background_range)
    return signal - background


class Qdyne(Measurement):
    def __init__(self, name="default"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict()
        # !!< has to be specific by users>
        __dataset = dict()
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)


bgextend_size = 0  # TODO: why 0? is it a fixed number?

T_PREUNBLK_MIN = 1000  #  1us mini pre-unblanking time
T_UNBLK_MAX = 300e6  # max unblanking time for the amplifier is 300ms
T_PREUNBLK = T_PREUNBLK_MIN + 500  #  we use 1.5us pre-unblanking time


class NuclearQuasiStaticTrack(Measurement):
    """
    A measurement protocol for the nuclear quasi-static track
    This protocol is designed to perform a sequence of operations on a sensor and the nuclear spin target.
    It includes preparation & probing phases on the sensor with a sequence of laser and microwave pulses; and
    the target is interlaced with free evolution and spin locking phases with RF pulses.
    The sequence time for a track equals to
        t_track = 4*(t_prep + t_prob), where t_prep is the preparation time for the sensor and t_prob is the probing time for the sensor, and
        t_track = 4*(t_prlo + t_lock), where t_prlo is the free evolution time and t_lock is the spin locking time for the target.
    The free evolution phase consists of a free evolution time for the target;
    The locking phase consists of two RF pulses with 180 degrees phase difference to flip the nuclear spins forth and back with equal extent.
    The preparation phase consists of a laser pulse sequence to prepare the sensor in a polarized state;
    The probing phase consists of a repeated Ramsey sequence on the sensor to extract the slow nutating nuclear spin signals (ie. the amplitude-encoded radio signals).
    A track consists of four probing signals:
        no RF
        RF A + RF B
        no RF
        RF B + RF A
    """

    # repeated ramsey sequence on sensors to extract the slow-dressing nuclear spin signals
    def __init__(self, name="default"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict(
            rate_refresh=10.0,
            # --------------------
            laser_current=30.0,  # percentage
            mw_freq=392.8488,  # GHz
            mw_powervolt=5.0,  # voltage 0.0 to 5.0
            mw_phasevolt=0.0,  # voltage 0.0 to 5.0
            rf_set=False,  # set the RF manually before running the measurement
            # rf_a_amp=0.5,  # amplitude for rf A
            # rf_b_amp=0.5,  # amplitude for rf B
            # rf_a_freq=600.8,  # MHz
            # rf_b_freq=600.8,  # MHz
            # rf_a_phase=0.0,  # phase for rf A
            # rf_b_phase=0.0,  # phase for rf B
            amp_input=200,  # input amplitude for digitizer
            # -------------------
            n_track=1000,  # number of tracks
            # -------------------
            t_prep_laser=250.0,  # laser time in the preparation phase in a track
            t_prep_isc=250.0,  # wait time for ISC in the preparation phase in a track
            n_prep_lpul=100,  # number of laser pulses in the preparation phase in a track
            # -------------------
            t_prob_init_wait=300.0,
            t_prob_mw_a_pio2=28.0,
            t_prob_phacc=0.0,
            t_prob_read_wait=300.0,
            t_prob_laser=600.0,
            n_dbloc_fwd=8,  # number of a probe
            n_dbloc_bwd=8,  # number of b probe
            # -------------------
            t_rf_pio2=16666,
            t_prlo=90000,  # pre-lock time
            t_lock_fwd=17000,
            t_lock_bwd=17000,
            # -------------------
            emulate=True,
            emulate_acfreq=122.0,  # Hz
        )
        # !!< has to be specific by users>
        __dataset = dict(
            num_repeat=0,
            tau_AB=np.zeros(2, dtype=np.float64),  # time of free evolution
            tau_BA=np.zeros(2, dtype=np.float64),  # time of free evolution
            sig_AB=np.zeros(2, dtype=np.float64),  # signal for AB
            sig_AB_bg=np.zeros(2, dtype=np.float64),  # background signal for AB
            sig_BA=np.zeros(2, dtype=np.float64),  # signal for BA
            sig_BA_bg=np.zeros(2, dtype=np.float64),  # background signal for BA
        )
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _parameter_check(self):
        t_prob_init_wait = self.paraset["t_prob_init_wait"]
        t_prob_mw_a_pio2 = self.paraset["t_prob_mw_a_pio2"]
        t_prob_phacc = self.paraset["t_prob_phacc"]
        t_prob_read_wait = self.paraset["t_prob_read_wait"]
        t_prob_laser = self.paraset["t_prob_laser"]
        n_dbloc_fwd = self.paraset["n_dbloc_fwd"]
        n_dbloc_bwd = self.paraset["n_dbloc_bwd"]
        t_lock_fwd = self.paraset["t_lock_fwd"]
        t_lock_bwd = self.paraset["t_lock_bwd"]
        t_prlo = self.paraset["t_prlo"]
        n_track = self.paraset["n_track"]
        assert n_track % 2 == 0, (
            "Number of tracks must be even for the protocol to work properly."
        )
        t_prep_laser = self.paraset["t_prep_laser"]
        t_prep_isc = self.paraset["t_prep_isc"]
        n_prep_lpul = self.paraset["n_prep_lpul"]
        t_lock = t_lock_fwd + t_lock_bwd  # total time for a nuclerar spin lock
        t_fevo = t_prlo + t_lock + t_prlo
        assert T_PREUNBLK * 2 + t_lock < T_UNBLK_MAX
        assert (
            t_fevo >= 5 * t_lock + T_PREUNBLK * 2
        )  # the duty cycle for RF must be <20%

        t_dbloc = (
            t_prob_init_wait
            + t_prob_mw_a_pio2
            + t_prob_phacc
            + t_prob_mw_a_pio2
            + t_prob_read_wait
            + t_prob_laser
        )  # the detection block depends on the sensing sequence on the sensor
        assert t_lock_fwd >= n_dbloc_fwd * t_dbloc, (
            "Lock time (pos) is not enough for the sequence."
        )
        assert t_lock_bwd >= n_dbloc_bwd * t_dbloc, (
            "Lock time (neg) is not enough for the sequence."
        )
        n_dbloc = n_dbloc_fwd + n_dbloc_bwd
        t_prob_dbloc = t_dbloc * n_dbloc
        t_prob_empt_fwd = t_lock_fwd - n_dbloc_fwd * t_dbloc
        t_prob_empt_bwd = t_lock_bwd - n_dbloc_bwd * t_dbloc
        t_prob = t_prob_empt_fwd + t_prob_dbloc + t_prob_empt_bwd
        t_prep = (t_prlo + t_lock) - t_prob
        t_prep_init = (t_prep_laser + t_prep_isc) * n_prep_lpul
        t_prep_empt = t_prep - t_prep_init
        assert t_prep_empt >= 0, "Preparation time is not enough for the sequence."

        assert (t_prlo + t_lock) == (t_prep + t_prob)
        self.paraset["t_lock"] = t_lock  # store it in the parameter set
        self.paraset["t_fevo"] = t_fevo  # store it in the parameter set
        self.paraset["t_prob"] = t_prob  # store it in the parameter set
        self.paraset["t_prob_dbloc"] = t_prob_dbloc  # store it in the parameter set
        self.paraset["t_prob_empt_fwd"] = (
            t_prob_empt_fwd  # store it in the parameter set
        )
        self.paraset["t_prob_empt_bwd"] = (
            t_prob_empt_bwd  # store it in the parameter set
        )
        self.paraset["t_dbloc"] = t_dbloc  # store it in the parameter set
        self.paraset["t_prep"] = t_prep  # store it in the parameter set
        self.paraset["t_prep_empt"] = t_prep_empt  # store it in the parameter set
        self.paraset["t_prep_init"] = t_prep_init  # store it in the parameter set
        self.paraset["n_dbloc"] = n_dbloc  # store it in the parameter set
        # n_seg = n_dbloc * 4  # number of readout segments per track
        # paraset["n_seg"] = n_seg  # store it in the parameter set

    def _sequence_sensor(self):
        t_prob_init_wait = self.paraset["t_prob_init_wait"]
        t_prob_mw_a_pio2 = self.paraset["t_prob_mw_a_pio2"]
        t_prob_phacc = self.paraset["t_prob_phacc"]
        t_prob_read_wait = self.paraset["t_prob_read_wait"]
        t_prob_empt_fwd = self.paraset["t_prob_empt_fwd"]
        t_prob_empt_bwd = self.paraset["t_prob_empt_bwd"]
        t_prob_laser = self.paraset["t_prob_laser"]
        n_dbloc_fwd = self.paraset["n_dbloc_fwd"]
        n_dbloc_bwd = self.paraset["n_dbloc_bwd"]
        # t_lock_fwd = self.paraset["t_lock_fwd"]
        # t_lock_bwd = self.paraset["t_lock_bwd"]
        t_prep_laser = self.paraset["t_prep_laser"]
        t_prep_isc = self.paraset["t_prep_isc"]
        n_prep_lpul = self.paraset["n_prep_lpul"]
        n_track = self.paraset["n_track"]
        t_prep_empt = self.paraset["t_prep_empt"]
        # t_dbloc = self.paraset["t_dbloc"]

        t_rf_pio2 = self.paraset["t_rf_pio2"]
        seq_pretrack = [([], t_rf_pio2)]
        seq_prep = [([], t_prep_empt)] + [
            (["laser"], t_prep_laser),
            ([], t_prep_isc),
        ] * n_prep_lpul

        seq_prob_no = (
            [([], t_prob_empt_fwd)]
            + [
                ([], t_prob_init_wait),
                # (["mwA"], t_prob_mw_a_pio2),
                ([], t_prob_mw_a_pio2),
                ([], t_prob_phacc),
                # (["mwA"], t_prob_mw_a_pio2),
                ([], t_prob_mw_a_pio2),
                ([], t_prob_read_wait),
                (["laser", "sdtrig"], t_prob_laser),
            ]
            * (n_dbloc_fwd + n_dbloc_bwd)
            + [([], t_prob_empt_bwd)]
        )
        seq_prob = (
            [([], t_prob_empt_fwd)]
            + [
                ([], t_prob_init_wait),
                (["mwA"], t_prob_mw_a_pio2),
                # ([], t_prob_mw_a_pio2),
                ([], t_prob_phacc),
                (["mwA"], t_prob_mw_a_pio2),
                # ([], t_prob_mw_a_pio2),
                ([], t_prob_read_wait),
                (["laser", "sdtrig"], t_prob_laser),
            ]
            * (n_dbloc_fwd + n_dbloc_bwd)
            + [([], t_prob_empt_bwd)]
        )
        if self.paraset["emulate"]:
            seq = seq_prep + seq_prob_no + seq_prep + seq_prob
        else:
            seq = seq_prep + seq_prob + seq_prep + seq_prob
        # return seq * n_track
        return seq_pretrack + seq * 2 * n_track, None

    def _sequence_target(self):
        t_rf_pio2 = self.paraset["t_rf_pio2"]
        t_prlo = self.paraset["t_prlo"]
        t_lock_fwd = self.paraset["t_lock_fwd"]
        t_lock_bwd = self.paraset["t_lock_bwd"]
        n_track = self.paraset["n_track"]
        # prime the amplifier by putting the BLK in advance
        # seq_prlo = [([], t_prlo)]
        seq_prlo_blk_fall = [(["BLK"], T_PREUNBLK), ([], t_prlo - T_PREUNBLK)]
        seq_prlo_blk_rise = [([], t_prlo - T_PREUNBLK), (["BLK"], T_PREUNBLK)]
        seq_nolock = [([], t_lock_fwd)] + [([], t_lock_bwd)]
        seq_lockAB = [(["rfA", "BLK"], t_lock_fwd)] + [(["rfB", "BLK"], t_lock_bwd)]
        seq_lockBA = [(["rfB", "BLK"], t_lock_fwd)] + [(["rfA", "BLK"], t_lock_bwd)]
        seq = (
            seq_prlo_blk_fall
            + seq_nolock
            + seq_prlo_blk_rise
            + seq_lockAB
            + seq_prlo_blk_fall
            + seq_nolock
            + seq_prlo_blk_rise
            + seq_lockBA
        )
        seq_pretrack = [(["rfB"], t_rf_pio2)]
        return seq_pretrack + seq * n_track, None

    def _sequence_target_emulation(self):
        t_rf_pio2 = self.paraset["t_rf_pio2"]
        t_prlo = self.paraset["t_prlo"]
        t_lock_fwd = self.paraset["t_lock_fwd"]
        t_lock_bwd = self.paraset["t_lock_bwd"]
        t_fevo = self.paraset["t_fevo"]
        n_track = self.paraset["n_track"]

        # prime the amplifier by putting the BLK in advance
        # seq_prlo = [([], t_prlo)]
        seq_prlo_blk_fall = [(["BLK"], T_PREUNBLK), ([], t_prlo - T_PREUNBLK)]
        seq_prlo_blk_rise = [([], t_prlo - T_PREUNBLK), (["BLK"], T_PREUNBLK)]
        seq_nolock = [([], t_lock_fwd)] + [([], t_lock_bwd)]
        seq_lockAB = [(["rfA", "BLK"], t_lock_fwd)] + [(["rfB", "BLK"], t_lock_bwd)]
        seq_lockBA = [(["rfB", "BLK"], t_lock_fwd)] + [(["rfA", "BLK"], t_lock_bwd)]
        seq = (
            seq_prlo_blk_fall
            + seq_nolock
            + seq_prlo_blk_rise
            + seq_lockAB
            + seq_prlo_blk_fall
            + seq_nolock
            + seq_prlo_blk_rise
            + seq_lockBA
        )
        seq_pretrack = [(["rfA", "BLK"], t_rf_pio2)]
        seq_digi = seq_pretrack + seq * n_track
        # some analog seq --------------------------
        Hz = 1e-9
        amp = 1.0
        omega = 2 * np.pi * self.paraset["emulate_acfreq"] * Hz
        # wmf_fevo = [(t_fevo, 0)]
        wmf_prlo = [(t_prlo, 0)]
        wfm_anlg = [(t_rf_pio2, 0)]
        for ii_track in range(n_track):
            t_i_AB = ii_track * t_fevo * 2 + 1 * t_fevo
            t_i_BA = ii_track * t_fevo * 2 + 2 * t_fevo
            amp_mod_AB = amp * np.cos(omega * t_i_AB)
            # amp_mod_AB = 0
            amp_mod_BA = amp * np.cos(omega * t_i_BA)
            # mz analog pattern in a spin lock
            rabi_nuclear = 1.0 / t_rf_pio2 / 4.0
            ac_samplerate = rabi_nuclear * 20.0  # 20 pt per period
            dt = int(1 / ac_samplerate)
            # n_dt = int(t_rf_pio2 * ac_samplerate)
            # dt = int(t_rf_pio2 / n_dt)
            ttt_fwd = np.arange(0.0, t_lock_fwd // dt * dt, dt)
            ttt_bwd = np.arange(0.0, t_lock_bwd // dt * dt, dt)
            ttt_fwd_end_compen = t_lock_fwd - len(ttt_fwd) * dt
            ttt_bwd_end_compen = t_lock_bwd - len(ttt_bwd) * dt
            # print(f" t pi/2 rf : {t_rf_pio2}")
            # print(f"dt sampling time: {dt}")
            # print(f" dt time total : {len(ttt_fwd)*dt}")
            # print(f"forward ttt time end: {ttt_fwd[-1]}")
            # print(f" forward lock time : {t_lock_fwd}")
            # ttt_fwd = np.linspace(0.0, t_rf_pio2, n_dt, endpoint=True)
            # ttt_bwd = np.linspace(0.0, t_rf_pio2, n_dt, endpoint=True)

            mz_wave_fwd = np.sin(2 * np.pi * rabi_nuclear * ttt_fwd)
            mz_wave_fwd_end = np.sin(2 * np.pi * rabi_nuclear * len(ttt_fwd) * dt)
            mz_wave_bwd = np.sin(2 * np.pi * rabi_nuclear * (-ttt_bwd + t_lock_fwd))
            mz_wave_bwd_end = np.sin(
                2 * np.pi * rabi_nuclear * (-len(ttt_bwd) * dt + t_lock_fwd)
            )

            wfm_lock_AB = (
                [(dt, amp_mod_AB * val) for val in mz_wave_fwd]
                + [(ttt_fwd_end_compen, amp_mod_AB * mz_wave_fwd_end)]
                + [(dt, amp_mod_AB * val) for val in mz_wave_bwd]
                + [(ttt_bwd_end_compen, amp_mod_AB * mz_wave_bwd_end)]
            )

            wfm_lock_BA = (
                [(dt, amp_mod_BA * val) for val in mz_wave_fwd]
                + [(ttt_fwd_end_compen, amp_mod_BA * mz_wave_fwd_end)]
                + [(dt, amp_mod_BA * val) for val in mz_wave_bwd]
                + [(ttt_bwd_end_compen, amp_mod_BA * mz_wave_bwd_end)]
            )
            wfm_anlg += (
                wmf_prlo
                + wfm_lock_AB
                + wmf_prlo
                + wfm_lock_AB
                + wmf_prlo
                + wfm_lock_BA
                + wmf_prlo
                + wfm_lock_BA
            )
        return seq_digi, wfm_anlg

    def _setup_exp(self):
        # check the parameters -----------------------------------------------------------------------
        self._parameter_check()
        # set the rf frequency, power and phase ------------------------------------------------------
        # make the rf setting before the measurement
        if self.paraset["rf_set"]:
            ref = hw.windfreak.get_reference()
            status_a = hw.windfreak.get_output_status("rfA")
            status_b = hw.windfreak.get_output_status("rfB")
            freq_a = hw.windfreak.get_freq("rfA")
            freq_b = hw.windfreak.get_freq("rfB")
            power_a = hw.windfreak.get_power("rfA")
            power_b = hw.windfreak.get_power("rfB")
            phase_a = hw.windfreak.get_phase("rfA")
            phase_b = hw.windfreak.get_phase("rfB")

            logger.info(
                f"Reference: mode = {ref['mode']}, frequency = {ref['frequency'] / 1e6:.6f} MHz"
            )
            logger.info(
                f"rfA: {'ENABLED' if status_a else 'DISABLED'}, freq = {freq_a / 1e6:.3f} MHz, "
                f"power = {power_a:.1f} dBm, phase = {phase_a:.1f}°"
            )
            logger.info(
                f"rfB: {'ENABLED' if status_b else 'DISABLED'}, freq = {freq_b / 1e6:.3f} MHz, "
                f"power = {power_b:.1f} dBm, phase = {phase_b:.1f}°"
            )
        else:
            # self.stop()
            logger.warning("Please set the RF manually before running the measurement")
        # -----------------------------------------------------------------------

        # set the mw frequency, power and phase ------------------------------------------------------
        freq = self.paraset["mw_freq"]
        freq_actual = hw.vdi.set_freq(freq)
        self.paraset["mw_freq"] = freq_actual
        hw.vdi.set_amp_volt(self.paraset["mw_powervolt"])
        hw.vdi.set_phase_volt(self.paraset["mw_phasevolt"])
        # -----------------------------------------------------------------------

        # set the laser power -------------------------------------------------
        current_percent = self.paraset["laser_current"]
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(current_percent, save_memory=False)
        # # -----------------------------------------------------------------------

        # set the pulse sequence-------------------------------------------
        hw.pg.setClock10MHzExt()
        hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        if self.paraset["emulate"]:
            logger.info("Emulating the sequence")
            seq_sensor, _ = self._sequence_sensor()
            seq_target, wfm_emul = self._sequence_target_emulation()
            hw.pg.resetSeq()
            hw.pg.setAnalog("Bz", wfm_emul, offset=True)
            tt_seqs = hw.pg.setSequence(seq_sensor, reset=False)
            tt_seqt = hw.pg.setSequence(seq_target, reset=False)
            logger.info(f"tt_seqs = {tt_seqs}, tt_seqt = {tt_seqt}")
            assert tt_seqs == tt_seqt
            hw.pg.stream(n_runs=-1)
        else:
            seq_sensor, _ = self._sequence_sensor()
            tt_seqs = hw.pg.setSequence(seq_sensor, reset=True)
            seq_target, _ = self._sequence_target()
            tt_seqt = hw.pg.setSequence(seq_target, reset=False)
            logger.info(f"tt_seqs = {tt_seqs}, tt_seqt = {tt_seqt}")
            assert tt_seqs == tt_seqt

            hw.pg.stream(n_runs=1)
        tt_seq = tt_seqs
        # -----------------------------------------------------------------------

        # set up the digitizer-------------------------------------------
        read_wait = self.paraset["t_prob_read_wait"]
        read_laser = self.paraset["t_prob_laser"]
        n_dbloc = self.paraset["n_dbloc"]
        n_track = self.paraset["n_track"]
        self.databufferlen = int(4 * n_dbloc * n_track)

        rate_refresh = self.paraset[
            "rate_refresh"
        ]  # Hz rate of refreshing the data streaming
        amp_input = self.paraset["amp_input"]
        readout_ch = hcf.SIDIG_chmap["apd"]
        num_segment = (
            int(self.databufferlen / (tt_seq * rate_refresh / 1e9)) // 32 * 32
        )  # number of "reads" every data refresh
        logger.info(f"num_segment = {num_segment}")
        # num_segment = (
        #     int(self.databufferlen / 10.0) // 32 * 32
        # )  # number of "reads" every data refresh

        # num_segment = (
        #     int(n_dbloc * 4 * max(n_track / 10, 1) * 8) // 32 * 32
        # )  # number of "reads" every data refresh

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
        # TODO: the integration windows is to be determined
        self.idx_av_0 = int(pretrig_size + 120)
        self.idx_av_1 = int(pretrig_size + 300)
        self.idx_bg_0 = int(pretrig_size * 0.1)
        self.idx_bg_1 = int(pretrig_size * 0.75)
        # To set the configuration, make a dictionary with the key and value
        hw.dig.reset_param()
        hw.dig.set_ext_clock()
        hw.dig.assign_param(
            dict(
                readout_ch=readout_ch,
                amp_input=amp_input,
                num_segment=num_segment,
                pretrig_size=pretrig_size + bgextend_size,  # TODO: why ?
                posttrig_size=posttrig_size - bgextend_size,
                segment_size=segment_size,
            )
        )
        logger.debug(
            f"readout_ch = {readout_ch}, amp_input = {amp_input}, num_segment = {num_segment}, pretrig_size = {pretrig_size}, posttrig_size = {posttrig_size}, segment_size = {segment_size}"
        )
        hw.dig.set_config()
        # -----------------------------------------------------------------------

        # put some necessary variables in self-------------------------------------
        if not self.tokeep:
            self.idx_pointer = 0
            self.seg_count = np.zeros(
                self.databufferlen,
                dtype=np.float64,
                order="C",
            )
            self.seg_store = np.zeros(
                (self.databufferlen),
                dtype=np.float64,
                order="C",
            )
            self.rawraw = np.zeros(
                (self.databufferlen, segment_size, 1),
                dtype=np.float64,
                order="C",
            )
        # -----------------------------------------------------------------------
        # start the laser and digitizer then wait for trigger from the  pulse streamer--------------
        hw.laser.laser_on()  # turn on laser
        hw.dig.start_buffer()
        # logger.debug("Start the trigger from the pulse streamer")
        # hw.pg.rearm()
        hw.pg.startNow()
        logger.info("Start the trigger from the pulse streamer")

    def _run_exp(self):
        # # logger.debug(
        # #     f"hey experiment-'{self._name}' no.{self.idx_run} sequence rearm{hw.pg.rearm()}"
        # # )
        # if not self.paraset["emulate"]:
        #     if hw.pg.rearm():
        #         logger.debug(
        #             "Pulse generator has finished, restart the measurement sequence."
        #         )
        #         time.sleep(0.1)  # wait for the nuclear spin to relax
        #         # hw.uf.depressurize(1)
        #         # time.sleep(1.0)  # wait for the liquid sample to settle down
        #         # hw.uf.pressurize(1)
        #         hw.pg.startNow()
        #         # else:
        #         #     logger.debug("Pulse sequence not finished")

        self.rawraw = hw.dig.stream()
        # logger.info(f"raw stream: {self.rawraw}")
        if self.rawraw is not None:
            num_segs = self.rawraw.shape[0]
            idx_ptr_overflow = self.idx_pointer + num_segs
            count_fill, idx_pointer_new = divmod(idx_ptr_overflow, self.databufferlen)
            if count_fill < 1:
                # underfill================================
                # if the segment number is small to the remaining slot numbers in the buffer
                idx_i = self.idx_pointer
                idx_f = self.idx_pointer + num_segs
                rawreshaped = np.reshape(self.rawraw[:num_segs], (num_segs, -1))
                self.seg_store[idx_i:idx_f] += slice_average_offset(
                    rawreshaped,
                    (self.idx_av_0, self.idx_av_1),
                    (self.idx_bg_0, self.idx_bg_1),
                )
                self.seg_count[idx_i:idx_f] += 1
            else:
                # exactly fill or overfill===============================

                # fill the tail of the data_store buffer ----------------
                num_tailslot = self.databufferlen - self.idx_pointer
                idx_i = self.idx_pointer
                idx_f = self.databufferlen
                rawreshaped = np.reshape(self.rawraw[:num_tailslot], (num_tailslot, -1))
                self.seg_store[idx_i:idx_f] += slice_average_offset(
                    rawreshaped,
                    (self.idx_av_0, self.idx_av_1),
                    (self.idx_bg_0, self.idx_bg_1),
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
                    repeatedsegments = np.sum(to_add_unstructured, axis=0)
                    self.seg_store += slice_average_offset(
                        repeatedsegments,
                        (self.idx_av_0, self.idx_av_1),
                        (self.idx_bg_0, self.idx_bg_1),
                    )
                    self.seg_count += count_fill - 1

                # fill the head of the data_store buffer for the remaining segments --------------
                if idx_pointer_new:
                    # the if condition is needed to handle the case that the idx_pointer_new is 0
                    rawreshaped = np.reshape(
                        self.rawraw[-idx_pointer_new:], (idx_pointer_new, -1)
                    )
                    self.seg_store[:idx_pointer_new] += slice_average_offset(
                        rawreshaped,
                        (self.idx_av_0, self.idx_av_1),
                        (self.idx_bg_0, self.idx_bg_1),
                    )
                self.seg_count[:idx_pointer_new] += 1
            self.idx_pointer = idx_pointer_new

        self.idx_run = self.seg_count[-1]
        # -----------------------------------------------------------------------
        return None

    # TODO: Generalize the start stop, maybe add the SNR opt
    def _organize_data(self):
        t_fevo = self.paraset["t_fevo"]
        n_track = self.paraset["n_track"]
        tau_AB = 2 * t_fevo * np.arange(0.0, n_track, 1.0) + 1 * t_fevo
        tau_BA = 2 * t_fevo * np.arange(0.0, n_track, 1.0) + 2 * t_fevo
        self.dataset["tau_AB"] = tau_AB
        self.dataset["tau_BA"] = tau_BA
        seg_store_av = self.seg_store / self.seg_count
        seg_store_av_rs = np.reshape(seg_store_av, (-1, self.paraset["n_dbloc"]))
        seg_store_av_av = np.mean(seg_store_av_rs, axis=1)

        self.dataset["num_repeat"] = np.max(self.seg_count)
        self.dataset["sig_AB_bg"] = seg_store_av_av[0::4]
        self.dataset["sig_AB"] = seg_store_av_av[1::4]
        self.dataset["sig_BA_bg"] = seg_store_av_av[2::4]
        self.dataset["sig_BA"] = seg_store_av_av[3::4]

        return super()._organize_data()

    def _shutdown_exp(self):
        # # turn off laser and set diode current to zero
        hw.laser.laser_off()
        hw.laser.set_diode_current(0.00, save_memory=False)

        # set mw amp and phase to zero
        hw.vdi.set_amp_volt(0)
        hw.vdi.set_phase_volt(0)

        # dump remaining data & stop digitizer
        _ = hw.dig.stream()
        hw.dig.stop_card()

        # set pulse generator to zero
        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())

    def _handle_exp_error(self):
        # Laser hardware reset
        try:
            hw.laser.laser_off()  # turn off laser
            hw.laser.set_diode_current(0.00, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            hw.laser.open()
        except Exception as e:
            logger.warning(f"Laser hardware reset failed: {e}")

        # Pulse generator reset
        try:
            hw.pg.forceFinal()
            hw.pg.reset()
            # hw.pg.reboot()
        except Exception as e:
            logger.warning(f"Pulse generator reset failed: {e}")

        # VDI system reset
        try:
            hw.vdi.reset()
        except Exception as e:
            logger.warning(f"VDI system reset failed: {e}")

        # Digitizer reset
        try:
            hw.dig.stop_card()
            hw.dig.reset()
        except Exception as e:
            logger.warning(f"Digitizer reset failed: {e}")


class EmulatorAERIS(Measurement):
    def __init__(self, name="dumdefault"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict(epicpara1=0, epicpara2="", volt_amp=1, freq=20.0, length=100)
        # !!< has to be specific by users>
        __dataset = dict(signal=np.zeros(1), timestamp=np.zeros(1))
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        super()._setup_exp()
        logger.debug(f"Parameters are: {self.paraset}")
        logger.debug(f"this class name: {self.__class__.__name__}")
        logger.debug("Hello it's set up!")
        logger.debug(f"total number of runs: {self.num_run}")
        self.buffer_rawdata = np.zeros(self.paraset["length"])
        self.buffer_timetime = np.zeros(self.paraset["length"])

    def _run_exp(self):
        logger.debug(f"hey fake experiment-'{self._name}' no.{self.idx_run}")
        logger.debug("I'm cooking some fake data")
        time.sleep(0.1)
        self.buffer_timetime = (np.arange(self.paraset["length"]) + self.time_run) / 1e3
        self.buffer_rawdata = (
            (1 + 0.3 * np.random.rand(self.paraset["length"]))
            * self.paraset["volt_amp"]
            * np.sin(2 * np.pi * self.paraset["freq"] * self.buffer_timetime)
        )

    def _organize_data(self):
        logger.debug("Moving data to a data server if you have one")
        self.dataset["signal"] = np.copy(self.buffer_rawdata)
        self.dataset["timestamp"] = np.copy(self.buffer_timetime) + self.buffer_timetime
        super()._organize_data()

    def _handle_exp_error(self):
        super()._handle_exp_error()
        logger.debug("dumdum measurement has troubles!")

    def _shutdown_exp(self):
        super()._shutdown_exp()
        logger.debug("goodbye dumdum measurement")


class DummyNQST(Measurement):
    def __init__(self, name="NQST_DUMMY"):
        paraset_initial = dict(
            rate_refresh=10.0,
            laser_current=30.0,
            mw_freq=398.550,
            mw_powervolt=5.0,
            mw_phasevolt=0.0,
            rf_set=True,
            amp_input=1000,
            n_track=100,
            t_prep_laser=300.0,
            t_prep_isc=200.0,
            n_prep_lpul=30,
            t_prob_init_wait=300.0,
            t_prob_mw_a_pio2=30.0,
            t_prob_phacc=600.0,
            t_prob_read_wait=300.0,
            t_prob_laser=600.0,
            n_dbloc_fwd=6,
            n_dbloc_bwd=6,
            t_rf_pio2=16666,
            t_prlo=20000,
            t_lock_fwd=17000,
            t_lock_bwd=17000,
        )
        dataset_initial = dict(
            num_repeat=0,
            tau_AB=np.array([]),
            tau_BA=np.array([]),
            sig_AB=np.array([]),
            sig_AB_bg=np.array([]),
            sig_BA=np.array([]),
            sig_BA_bg=np.array([]),
        )
        super().__init__(name, paraset_initial, dataset_initial)

    def _setup_exp(self):
        print("DummyNQST._setup_exp")
        pass
        # self.set_runnum(self.paraset.get("n_track", 100))
        # self.stateset["num_run"] = self.num_run
        # self._refresh_interval = 1.0 / self.paraset.get("rate_refresh", 10.0)

    def _run_exp(self):
        time.sleep(1 / self.paraset.get("rate_refresh"))
        # This simulates one step of data acquisition
        t_lock = self.paraset["t_lock_fwd"] + self.paraset["t_lock_bwd"]
        t_fevo = self.paraset["t_prlo"] * 2 + t_lock

        current_idx = self.idx_run // 2

        # Calculate new data point
        tau_ab_point = 2 * t_fevo * current_idx
        tau_ba_point = 2 * t_fevo * current_idx + t_fevo

        t_ab_sec = tau_ab_point * 1e-9
        t_ba_sec = tau_ba_point * 1e-9
        noise = (np.random.rand() - 0.5) * 0.1

        # Create oscillating fake signals
        frequency = 3.54968e6  # 10MHz frequency for oscillation
        amplitude = 0.5  # Amplitude of the oscillation signal

        sig_ab_point = (
            1.0
            + amplitude
            * np.cos(2 * np.pi * frequency * t_ab_sec)
            * np.exp(-t_ab_sec / 1e-2)
            + noise
        )
        sig_ba_point = (
            1.0
            - amplitude
            * np.cos(2 * np.pi * frequency * t_ba_sec)
            * np.exp(-t_ba_sec / 1e-2)
            + noise
        )

        # Append to existing data
        self.dataset["tau_AB"] = np.append(self.dataset["tau_AB"], tau_ab_point)
        self.dataset["sig_AB"] = np.append(self.dataset["sig_AB"], sig_ab_point)
        self.dataset["sig_AB_bg"] = np.append(self.dataset["sig_AB_bg"], 1.0 + noise)

        self.dataset["tau_BA"] = np.append(self.dataset["tau_BA"], tau_ba_point)
        self.dataset["sig_BA"] = np.append(self.dataset["sig_BA"], sig_ba_point)
        self.dataset["sig_BA_bg"] = np.append(self.dataset["sig_BA_bg"], 1.0 + noise)
        self.dataset["sig_BA"] = np.append(self.dataset["sig_BA"], sig_ba_point)
        self.dataset["sig_BA_bg"] = np.append(self.dataset["sig_BA_bg"], 1.0 + noise)

    def _organize_data(self):
        self.dataset["num_repeat"] = self.idx_run
        super()._organize_data()
