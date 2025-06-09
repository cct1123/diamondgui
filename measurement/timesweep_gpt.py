import logging

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


def average_repeated_data(
    seg_store: np.ndarray,
    seg_count: np.ndarray,
    start: int,
    stop: int,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """
    Compute weighted, background‑subtracted signals from repeated data segments.

    Parameters
    ----------
    seg_store : np.ndarray
        Accumulated raw segment data, shape (n_segments, segment_length).
    seg_count : np.ndarray
        Count of fills per segment index, shape (n_segments,).
    start : int
        Index to start integration window.
    stop : int
        Index to end integration window.

    Returns
    -------
    dark : float
        Offset-corrected dark reference signal.
    bright : float
        Offset-corrected bright reference signal.
    sig_p_int : np.ndarray
        Weighted positive-phase signal integration per repetition.
    sig_n_int : np.ndarray
        Weighted negative-phase signal integration per repetition.
    """
    # Normalize by repetition counts
    averaged_norm = np.mean(seg_store[:, start:stop], axis=1) / seg_count

    # Estimate electronic background using a fixed window before data window
    averaged_bg = (
        np.mean(
            seg_store[:, max(0, start - 100) : start],
            axis=1,
        )
        / seg_count
    )

    # First two entries are dark and bright references
    dark = averaged_norm[0] - averaged_bg[0]
    bright = averaged_norm[1] - averaged_bg[1]

    # Compute weights based on reference contrast
    weight = np.abs(bright - dark)
    weight = weight / np.sum(weight)

    # Extract alternating positive and negative signals
    idx_start = 2
    sig_p = averaged_norm[idx_start::2] - averaged_bg[idx_start::2]
    sig_n = averaged_norm[idx_start + 1 :: 2] - averaged_bg[idx_start + 1 :: 2]

    # Weighted integration
    sig_p_int = sig_p * weight
    sig_n_int = sig_n * weight
    return dark, bright, sig_p_int, sig_n_int


def seq_init(
    init_nslaser: int,
    init_isc: int,
    init_wait: float,
    init_repeat: int,
) -> list[tuple[list[str], float]]:
    """
    Build the initialization subsequence: alternating laser and idle states.

    Parameters
    ----------
    init_nslaser : int
        Laser pulse duration in nanoseconds.
    init_isc : int
        Inter-pulse spacing in clock cycles.
    init_wait : float
        Wait time in nanoseconds between repeats.
    init_repeat : int
        Number of repeats of laser/idling.

    Returns
    -------
    sequence : list of (channels, duration) tuples
    """
    single = [(["laser"], init_nslaser), ([], init_isc)]
    # Repeat the basic unit, then idle
    return single * init_repeat + [([], init_wait)]


def seq_read(
    read_wait: float,
    read_laser: float,
) -> list[tuple[list[str], float]]:
    """
    Build the readout subsequence: idle then laser+trigger.

    Parameters
    ----------
    read_wait : float
        Wait time before readout in nanoseconds.
    read_laser : float
        Laser pulse duration during readout in nanoseconds.

    Returns
    -------
    sequence : list of (channels, duration) tuples
    """
    return [([], read_wait), (["laser", "sdtrig"], read_laser)]


class TimeSweep(Measurement):
    """
    Base class for time-domain pulsed measurements (e.g., T1, Ramsey, Echo).

    Defines parameter and dataset structures, sequence builder, and data handling.
    """

    _para_seq: dict = {}  # Override for specific sequence timings

    def __init__(self, name: str = "TimeSweep"):
        """
        Initialize parameter set and dataset placeholders.
        """
        # Default parameters
        base_paraset = dict(
            rate_refresh=10.0,
            laser_current=80.0,
            mw_freq=398.550,  # GHz
            mw_powervolt=5.0,
            mw_phasevolt=0.0,
            amp_input=1000,
            bgextend_size=256,
            init_nslaser=50,
            init_isc=150,
            init_repeat=40,
            init_wait=1000.0,
            t_pi_mwa=100.0,
            read_wait=300.0,
            read_laser=900.0,
            tau_begin=0.0,
            tau_end=100.0,
            tau_step=10.0,
        )
        # Merge in subclass-specific timing overrides
        base_paraset.update(self._para_seq)

        # Prepare storage for results
        base_dataset = dict(
            num_repeat=0,
            tau=np.zeros(
                int(
                    (base_paraset["tau_end"] - base_paraset["tau_begin"])
                    / base_paraset["tau_step"]
                )
                + 1
            ),
            sig_p=np.zeros_like(np.zeros(0)),
            sig_n=np.zeros_like(np.zeros(0)),
            bright=0.0,
            dark=0.0,
        )

        super().__init__(name, base_paraset, base_dataset)

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        """
        Generate the variable-delay subsequence. To be overridden by subclasses.

        Parameters
        ----------
        tau : float
            Free-evolution time in nanoseconds.

        Returns
        -------
        seq : list of (channel, duration) tuples
        tau_ext : float
            Additional overhead time to account for finite pulse durations.
        """
        return [([], 0.0)], 0.0

    def _sequence(self) -> tuple[list[tuple[list[str], float]], np.ndarray]:
        """
        Build the full pulse sequence: dark/bright references + tau sweep.

        Returns
        -------
        sq_exp : list of (channels, duration) tuples
        tau_array : np.ndarray
            Effective delay times including overhead.
        """
        # Initial dark and bright reference blocks
        sq_init = seq_init(
            self.paraset["init_nslaser"],
            self.paraset["init_isc"],
            self.paraset["init_wait"],
            self.paraset["init_repeat"],
        )
        sq_read = seq_read(
            self.paraset["read_wait"],
            self.paraset["read_laser"],
        )

        # Build reference segments
        sq_exp: list[tuple[list[str], float]] = []
        for ref in ("dark", "bright"):
            sq_exp += sq_init + [([], self.paraset["t_pi_mwa"])] + sq_read

        # Build tau-sweep portion
        tau_vals = np.arange(
            self.paraset["tau_begin"],
            self.paraset["tau_end"] + self.paraset["tau_step"],
            self.paraset["tau_step"],
        )
        tau_eff = np.zeros_like(tau_vals)
        for i, tau in enumerate(tau_vals):
            sub_seq, ext = self._sequence_ts(tau)
            tau_eff[i] = tau + ext
            # Two measurement shots per tau: with and without MW pulse
            sq_exp += sq_init + sub_seq + [([], self.paraset["t_pi_mwa"])] + sq_read
            sq_exp += (
                sq_init + sub_seq + [(["mwA"], self.paraset["t_pi_mwa"])] + sq_read
            )

        return sq_exp, tau_eff

    def _setup_exp(self) -> None:
        """
        Configure hardware and start streaming data for the experiment.
        """
        # --- Configure microwave synthesizer frequency ---
        freq_setting = self.paraset["mw_freq"] / hcf.VDISYN_multiplier
        try:
            hw.mwsyn.open()
        except Exception as e:
            logger.exception("Error opening mwsyn: %s", e)
        _, actual_freq = hw.mwsyn.cw_frequency(freq_setting)
        logger.debug(
            "Set MW frequency: requested=%.3f GHz, actual=%.3f GHz",
            self.paraset["mw_freq"],
            actual_freq,
        )

        # --- Configure laser driver ---
        hw.laser.laser_off()
        hw.laser.set_analog_control_mode("current")
        hw.laser.set_modulation_state("Pulsed")
        hw.laser.set_diode_current(self.paraset["laser_current"], save_memory=False)

        # --- Configure MW amplitude and phase ---
        hw.mwmod.set_amp_volt(self.paraset["mw_powervolt"])
        hw.mwmod.set_phase_volt(self.paraset["mw_phasevolt"])

        # --- Load and start pulse sequence ---
        seq_exp, tau_arr = self._sequence()
        tt_seq = hw.pg.setSequence(seq_exp)
        hw.pg.setTrigger(TriggerStart.SOFTWARE, rearm=TriggerRearm.AUTO)
        hw.pg.setClock10MHzExt()
        hw.pg.stream(n_runs=REPEAT_INFINITELY)

        # --- Configure digitizer parameters ---
        self.tau_arr = tau_arr
        n_points = 2 * len(tau_arr) + 2
        self.databufferlen = n_points

        # Derive segment sizes based on acquisition timing
        rate = self.paraset["rate_refresh"]
        num_segment = (
            int(self.databufferlen / (tt_seq * rate / 1e9)) // 32 * 32
        )  # number of "reads" every data refresh
        pretrig = (
            int((self.paraset["read_wait"] / 2) * hcf.SIDIG_maxsr / 1e9) // 64 * 64
        )
        posttrig = int(self.paraset["read_laser"] * hcf.SIDIG_maxsr / 1e9) // 64 * 64
        seg_size = 1 << (int(np.log2(pretrig + posttrig)) + 1)
        pretrig_ext = pretrig + self.paraset["bgextend_size"]
        posttrig_ext = seg_size - pretrig_ext

        hw.dig.reset_param()
        hw.dig.assign_param(
            {
                "readout_ch": hcf.SIDIG_chmap["apd"],
                "amp_input": self.paraset["amp_input"],
                "num_segment": num_segment,
                "pretrig_size": pretrig_ext,
                "posttrig_size": posttrig_ext,
                "segment_size": seg_size,
            }
        )
        hw.dig.set_ext_clock()
        hw.dig.set_config()
        logger.debug(
            "Digitizer config: segments=%d, pretrig=%d, posttrig=%d, seg_size=%d",
            num_segment,
            pretrig_ext,
            posttrig_ext,
            seg_size,
        )

        # Initialize data buffers
        if not self.tokeep:
            self.idx_pointer = 0
            self.dataset["tau"] = tau_arr
            self.dataset["sig_p"] = np.zeros(len(tau_arr))
            self.dataset["sig_n"] = np.zeros(len(tau_arr))
            self.seg_count = np.zeros(self.databufferlen, dtype=float)
            self.seg_store = np.zeros((self.databufferlen, seg_size), dtype=float)

        # Start acquisition
        hw.laser.laser_on()
        hw.dig.start_buffer()
        hw.pg.startNow()

    def _run_exp(self) -> None:
        """
        Pull streamed data from digitizer and accumulate into buffers.
        """
        raw = hw.dig.stream()
        if raw is None:
            return
        n_segs = raw.shape[0]
        end_idx = self.idx_pointer + n_segs
        wraps, new_ptr = divmod(end_idx, self.databufferlen)

        # Handle no wrap case
        if wraps == 0:
            self.seg_store[self.idx_pointer : end_idx] += raw
            self.seg_count[self.idx_pointer : end_idx] += 1
        else:
            # Fill tail to buffer end
            tail = self.databufferlen - self.idx_pointer
            self.seg_store[self.idx_pointer :] += raw[:tail]
            self.seg_count[self.idx_pointer :] += 1
            # Full-buffer wraps
            if wraps > 1:
                mid = raw[tail : tail + (wraps - 1) * self.databufferlen]
                self.seg_store += mid.reshape(wraps - 1, self.databufferlen).sum(axis=0)
                self.seg_count += wraps - 1
            # Head portion
            head = raw[-new_ptr:] if new_ptr else np.empty((0, raw.shape[1]))
            if new_ptr:
                self.seg_store[:new_ptr] += head
                self.seg_count[:new_ptr] += 1
        self.idx_pointer = new_ptr
        self.idx_run = self.seg_count[-1]

    def _organize_data(self) -> dict:
        """
        Process accumulated data to extract dark, bright, and tau-dependent signals.
        """
        start = self.paraset["bgextend_size"] + 160
        stop = self.paraset["bgextend_size"] + 400
        dark, bright, sig_p, sig_n = average_repeated_data(
            self.seg_store,
            self.seg_count,
            start,
            stop,
        )
        self.dataset.update(
            {
                "dark": dark,
                "bright": bright,
                "sig_p": sig_p,
                "sig_n": sig_n,
                "num_repeat": self.idx_run,
            }
        )
        return super()._organize_data()

    def _shutdown_exp(self) -> None:
        """
        Safely power down hardware and clear resources after experiment.
        """
        # Laser off
        hw.laser.laser_off()
        hw.laser.set_diode_current(0.0, save_memory=False)
        # Stop pulse generator
        hw.pg.forceFinal()
        hw.pg.constant(OutputState.ZERO())
        # Reset MW
        hw.mwmod.set_amp_volt(0)
        hw.mwmod.set_phase_volt(0)
        # Drain digitizer
        _ = hw.dig.stream()
        hw.dig.stop_card()

    def _handle_exp_error(self) -> None:
        """
        Attempt to recover from hardware errors by resetting subsystems.
        """
        try:
            # Reset laser
            hw.laser.laser_off()
            hw.laser.set_diode_current(0.0, save_memory=False)
            hw.laser.reset_alarm()
            hw.laser.close()
            hw.laser.open()
            # Reset MW synth
            hw.mwsyn.reboot()
            hw.mwsyn.close()
            hw.mwsyn.open()
            # Reset pulse generator
            hw.pg.forceFinal()
            hw.pg.constant(OutputState.ZERO())
            hw.pg.reset()
            hw.pg.reboot()
            # Reset MW modulator
            hw.mwmod.set_amp_volt(0)
            hw.mwmod.set_phase_volt(0)
            hw.mwmod.close()
            hw.mwmod.restart()
            # Reset digitizer
            _ = hw.dig.stream()
            hw.dig.stop_card()
            hw.dig.reset()
        except Exception as e:
            logger.error("Error during cleanup: %s", e)


# Subclasses for common pulse sequences
class Relaxation(TimeSweep):
    """
    T1 Relaxation measurement: single wait period then pi-pulse.
    """

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        return [([], tau)], 0.0


class Ramsey(TimeSweep):
    """
    Ramsey interferometry: pi/2 - tau - pi/2 pulses.
    """

    _para_seq = dict(t_pio2_mwa=50.0)

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        t = self.paraset["t_pio2_mwa"]
        seq = [(["mwA"], t), ([], tau), (["mwA"], t)]
        return seq, t


class HahnEcho(TimeSweep):
    """
    Hahn echo: pi/2 - tau/2 - pi - tau/2 - pi/2.
    """

    _para_seq = dict(t_pio2_mwa=50.0, t_pi_mwa=100.0)

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        t_half = tau / 2.0
        seq = [
            (["mwA"], self.paraset["t_pio2_mwa"]),
            ([], t_half),
            (["mwA"], self.paraset["t_pi_mwa"]),
            ([], t_half),
            (["mwA"], self.paraset["t_pio2_mwa"]),
        ]
        ext = self.paraset["t_pi_mwa"] + self.paraset["t_pio2_mwa"]
        return seq, ext


class CPMG(TimeSweep):
    """
    CPMG sequence with n pi-pulses between pi/2 pulses.
    """

    _para_seq = dict(t_pio2_mwa=50.0, t_pi_mwa=100.0, n_pi=10)

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        t2 = tau / 2.0
        # Build XY blocks
        blocks = []
        for _ in range(self.paraset["n_pi"] - 1):
            blocks += [(["mwA"], self.paraset["t_pi_mwa"]), ([], tau)]
        seq = (
            [(["mwA"], self.paraset["t_pio2_mwa"]), ([], t2)]
            + blocks
            + [
                (["mwA"], self.paraset["t_pi_mwa"]),
                ([], t2),
                (["mwA"], self.paraset["t_pio2_mwa"]),
            ]
        )
        ext = (
            self.paraset["n_pi"] * self.paraset["t_pi_mwa"] + self.paraset["t_pio2_mwa"]
        ) / self.paraset["n_pi"]
        return seq, ext


class XY4(TimeSweep):
    """
    Placeholder for XY4 dynamical decoupling (not yet implemented).
    """

    _para_seq = dict(t_pi_mwa=100.0, t_pi_mwb=100.0, n_pi=10)

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        raise NotImplementedError("XY4 sequence not implemented yet.")


class XY8(TimeSweep):
    """
    Placeholder for XY8 dynamical decoupling (not yet implemented).
    """

    _para_seq = dict(t_pi_mwa=100.0, t_pi_mwb=100.0, n_pi=10)

    def _sequence_ts(self, tau: float) -> tuple[list[tuple[str, float]], float]:
        raise NotImplementedError("XY8 sequence not implemented yet.")
