"""
Digitizer control class to configure, read, stream a single task
Tested specifically with Spectrum M4i.44xx series digitizers

ref:
    [1] https://spectrum-instrumentation.com/dl/m4i_m4x_44xx_manual_english.pdf

Author: Emmeline Riendeau & ChunTung Cheung
Email: emmelineriendeau@gmail & ctcheung1123@gmail.com
Created:  2024-12-20
Modified: 2025-04-20
"""

import logging
import time as time

import numpy as np
import spcm
from spcm import units

logger = logging.getLogger(__name__)

TERMINATE50OHM = 1

# amplitude settings (buffered 1Mohm)
AMP_200MIV = 200  # 200 ± 200 mV calibrated input range for the appropriate channel.
AMP_500MIV = 500  # 500 ± 500 mV calibrated input range for the appropriate channel.
AMP_1V = 1000  # 1000 ± 1 V calibrated input range for the appropriate channel.
AMP_2V = 2000  # 2000 ± 2 V calibrated input range for the appropriate channel.
AMP_5V = 5000  # 5000 ± 5 V calibrated input range for the appropriate channel.
AMP_10V = 10000  # 10000 ± 10 V calibrated input range for the appropriate channel.

# amplitude settings (HF, 50ohm)
AMP_HF_500MIV = 500  # 500 ± 500 mV calibrated input range for the appropriate channel.
AMP_HF_1V = 1000  # 1000 ± 1 V calibrated input range for the appropriate channel.
AMP_HF_2_5V = 2500  # 2500 ± 2.5 V calibrated input range for the appropriate channel.
AMP_HF_5V = 5000  # 5000 ± 5 V calibrated input range for the appropriate channel.

DCCOUPLE = 0
ACCOUPLE = 1
TERMIN_INPUT_50OHM = 1
TERMIN_INPUT_1MOHM = 0
CONTINUOUS_STREAMING = 0


MEMSIZE_MAX = 2 * units.GiS  # read from manual of M4i.4450-x8, 2 GiS = 1073741824
EXTEND_AUTOMEM = 16  # a factor for automatically determining the memory size
CH_mapping = {0: spcm.CHANNEL0, 1: spcm.CHANNEL1}
ACDC_mapping = {0: spcm.SPC_ACDC0, 1: spcm.SPC_ACDC1}
PATH_mapping = {0: spcm.SPC_PATH0, 1: spcm.SPC_PATH1}
AMP_mapping = {0: spcm.SPC_AMP0, 1: spcm.SPC_AMP1}


DEFAULT_CONFIG = dict(
    couple_input=ACCOUPLE,
    amp_input=AMP_5V,
    terminate_input=TERMIN_INPUT_1MOHM,
    terminate_trigger=TERMINATE50OHM,
    card_timeout=5 * units.s,
    # ------------------------------------
    segment_size=None,
    pretrig_size=None,
    posttrig_size=None,
    num_segment=1,
    mem_size="auto",  # defined automatically?
    readout_ch=None,  # int or list of int
    sampling_frequency=0.5 * units.GHz,
    verbose=False,
    # ------------------------------------
    # for compatibility with NSYPRE------
    num_pts_in_exp=None,  # Set some values that work instead of None
    num_iters=None,
    runs=None,
    notify_size=None,
    # ------------------------------------
    # ------------------------------------
)


# TODO: add docstring to the class and class methods
class FIFO_DataAcquisition(object):
    def __init__(self, sn_address):
        self.sn_address = sn_address
        # initialize the default configuration
        self.__init_config = DEFAULT_CONFIG
        # assign the configuration to self
        self.reset_param()  # MUST BE CALLED in __init__ to set the default values

        # # open the connection with the digitizer
        self.connect()
        # self.set_ext_clock() # 20250519 Tung: Set it manually in the measurement, not at the beginning

    def set_ext_clock(self):
        self.card.set_i(spcm.SPC_CLOCKMODE, spcm.SPC_CM_EXTREFCLOCK)
        self.card.set_i(spcm.SPC_REFERENCECLOCK, 10000000)  # 10 MHz reference clock
        logger.info("Clock mode set to:", self.card.get_i(spcm.SPC_CLOCKMODE))
        logger.info("1: Internal, 2: Quartz, 3: External, 32: Direct External Sampling")

    def connect(self):
        self.card = spcm.Card(self.sn_address)
        self.card.__enter__()

        if not self.card._closed:
            logger.info("Successfully connected to the digitizer")
        else:
            logger.warning("Connection unsuccessful")

    def disconnect(self):
        self.card.__exit__()
        if self.card._closed:
            print("Card disconnection successful")
            # reset the configuraiton
            self.reset_param()
        else:
            print("Card disconnection unsuccessful")

    def stop_card(self):
        self.card.stop(spcm.M2CMD_DATA_STOPDMA)
        print("Card stopped")

    def reset(self):
        self.card.reset()

    def assign_param(self, settings_dict):
        # assign the configuration to self
        for key, value in settings_dict.items():
            if hasattr(self, key):
                # TODO: check if other parameters also need to be converted to units
                # TODO: or if we can skip the units for all parameters
                flag_unitSa = (
                    (key == "segment_size")
                    or (key == "pretrig_size")
                    or (key == "posttrig_size")
                )
                if flag_unitSa:
                    setattr(self, key, value * units.Sa)
                else:
                    setattr(self, key, value)

    def reset_param(self):
        for key, value in self.__init_config.items():
            setattr(self, key, value)

    def check_config(self):
        # segment settings ------------------------------------
        # for compatibility with NSYPRE------
        if self.num_pts_in_exp or self.num_iters or self.runs:
            self.posttrig_size = self.segment_size - self.pretrig_size
            self.num_segment = self.runs * self.num_pts_in_exp  # *self.num_iters
        # ------------------------------------

        # parameter checks for segment settings---
        if self.pretrig_size and self.posttrig_size and self.segment_size:
            flag_validsegment = self.segment_size == (
                self.pretrig_size + self.posttrig_size
            )
            if not flag_validsegment:
                logger.warning(
                    "Invalid 'segment_size', 'pretrig_size' or 'posttrig_size'"
                )
                logger.warning(
                    "Please make sure Segment Size = Pre-trigger + Post-trigger"
                )
        elif (not self.pretrig_size) and self.posttrig_size and self.segment_size:
            self.pretrig_size = self.segment_size - self.posttrig_size
        elif self.pretrig_size and (not self.posttrig_size) and self.segment_size:
            self.posttrig_size = self.segment_size - self.pretrig_size
        elif self.pretrig_size and self.posttrig_size and (not self.segment_size):
            self.segment_size = self.posttrig_size + self.pretrig_size
        else:
            logger.warning(
                "Please specify either two of the segment settings: 'segment_size', 'pretrig_size', 'posttrig_size'"
            )
        logger.info(
            f"Pre-trigger: {self.pretrig_size}, Post-trigger: {self.posttrig_size}, Segment Size: {self.segment_size}"
        )
        # ------------------------------------
        #  ----------------------------------------------------

        if self.mem_size == "auto" or self.mem_size is None:
            self.mem_size = self.num_segment * self.segment_size * EXTEND_AUTOMEM
        # TODO: review and put the printouts to logging
        if self.verbose:
            print("SETTINGS: card timeout = ", self.card_timeout)
            print("SETTINGS: # of segments = ", self.segment_size)
            print("SETTINGS: sampling freq = ", self.sampling_frequency)
            print("SETTINGS: pretrig size = ", self.pretrig_size)
            print("SETTINGS: termination = ", self.terminate_input)

    def config(self):
        # check the config parameters users have set
        self.check_config()

        # setup card mode
        self.card.card_mode(spcm.SPC_REC_FIFO_MULTI)  # SPC_REC_FIFO_MULTI
        self.card.timeout(self.card_timeout)
        clock = spcm.Clock(self.card)
        clock.mode(spcm.SPC_CM_INTPLL)
        clock.sample_rate(self.sampling_frequency)

        # set Analog input parameters
        if type(self.readout_ch) is int:
            ch_ch = CH_mapping.get(self.readout_ch)
        elif type(self.readout_ch) is list:
            ch_ch = 0
            for ch in self.readout_ch:
                ch_ch |= CH_mapping.get(ch)

        channels = spcm.Channels(self.card, card_enable=ch_ch)
        channels.amp(self.amp_input)  # amplitude in [mV]
        channels.termination(self.terminate_input)
        channels.coupling(self.couple_input)
        self.channels = channels

        # ch_acdc = ACDC_mapping.get(self.readout_ch)
        # ch_path = PATH_mapping.get(self.readout_ch)
        # ch_amp = AMP_mapping.get(self.readout_ch)
        # self.card.set_i(ch_acdc, self.couple_input)
        # self.card.set_i(ch_path, self.terminate_input)
        # self.card.set_i(ch_amp, self.amp_input)

        # setup trigger engine
        trigger = spcm.Trigger(self.card)
        trigger.ext0_mode(spcm.SPC_TM_POS)  # set trigger mode
        trigger.or_mask(spcm.SPC_TMASK_EXT0)  # trigger set to external
        trigger.termination(self.terminate_trigger)
        trigger.ext0_coupling(spcm.COUPLING_DC)  # trigger coupling

        self.multiple_recording = spcm.Multi(self.card)
        self.multiple_recording.memory_size(
            self.mem_size
        )  # the size of the memory in Bytes
        self.multiple_recording.allocate_buffer(
            self.segment_size, num_segments=self.num_segment
        )
        self.multiple_recording.post_trigger(self.posttrig_size)

        self.multiple_recording.to_transfer_samples(
            CONTINUOUS_STREAMING
        )  # number of samples to transfer
        # self.notify_size = (
        #     2 ** int(np.log2(self.mem_size / 1024 / 4)) * 1024 * 8
        # )  # TODO:to be tested\
        if self.notify_size is None:
            self.notify_size = self.mem_size // EXTEND_AUTOMEM
        # self.notify_size = self.num_segment * self.num_segment * 8
        # print("notify size: ", self.notify_size)
        self.multiple_recording.notify_samples(self.notify_size)

        self.max_value = self.card.max_sample_value()

    def set_config(self):
        # alias function name to config
        return self.config()

    def check_connection(self):
        if self.card._closed:
            logger.info("Digitizer is not connected")

    def start_buffer(self):
        try:
            self.multiple_recording.start_buffer_transfer(spcm.M2CMD_DATA_STARTDMA)
            self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER)
        except spcm.SpcmTimeout:
            print("Timeout...")

    def convert_data(self):
        return self.raw_data * ((self.amp_input / 1000) / np.abs(self.max_value)) + 0.1

    def acquire(self):
        # for singe acuqisition-------
        try:
            data_block = next(self.multiple_recording)

            # print(f"termination setting: {self.terminate_input}")
            self.raw_data = np.copy(data_block)
        except Exception as e:
            print(e)
            self.card.stop(spcm.M2CMD_DATA_STOPDMA)
            self.card.reset()
            self.card.__exit__()
            self.card.__enter__()
        finally:
            self.card.stop(spcm.M2CMD_DATA_STOPDMA)
            # self.card.reset()
        # TODO: check the conversion factor
        return (self.raw_data) * ((self.amp_input) / np.abs(self.max_value)) / 1000

    def stream(self):
        # for continuous streaming, please stop the card manually after acquisition---------
        try:
            data_block = next(self.multiple_recording)
            self.raw_data = np.copy(data_block)
            # print(np.shape(data_block))
            # self.raw_data = self.channels[0].convert_data(self.raw_data, units.mV)
            return (self.raw_data) * ((self.amp_input) / self.max_value) / 1000
            # return np.copy(data_block)
        except Exception as e:
            print(e)
        # return self.raw_data
        return None
