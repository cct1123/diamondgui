"""
Digitizer control class to configure, read, stream a single task

ref:
    [1] qdSpectro

Author: Emmeline Riendeau & ChunTung Cheung
Email: emmelineriendeau@gmail & ctcheung1123@gmail.com
Created:  2024-12-20
Modified: 2024-12-20
"""

import logging
import time as time

import numpy as np
import spcm
from spcm import units

logger = logging.getLogger(__name__)


class FIFO_DataAcquisition(object):
    def __init__(self, ip_address):
        # initialize the default configuration
        self._init_config = dict(
            ACCOUPLE=1,
            AMP=1000,  # in mV
            card_timeout=20 * units.s,
            DCCOUPLE=1,
            HF_INPUT_50OHM=1,  # 1 = 50 ohm, 0 = 1 Mohm
            num_pts_in_exp=None,
            num_iters=None,
            mem_size=None,
            num_segment=None,
            pretrig_size=32 * units.Sa,
            posttrig_size=None,
            readout_ch=None,
            ip_address=ip_address,
            runs=None,
            sampling_frequency=0.5 * units.GHz,
            segment_size=512 * units.Sa,
            TERMINATE50OHM=1,
            conversion_offset=0.1340332,
            conversion_amp=0.8819033287026647,
        )

        # assign the configuration to self
        for key, value in self._init_config.items():
            setattr(self, key, value)

        # # open the connection with the digitizer
        self.connect()

    def connect(self):
        self.card = spcm.Card(self.ip_address)
        self.card.__enter__()

        if self.card._closed == False:
            print("Successfully connected to the digitizer")
            if self.card._closed == True:
                assert print("Connection unsuccessful")

    def disconnect(self):
        self.card.__exit__()
        if self.card._closed == True:
            print("Card disconnection successful")
            # reset the configuraiton
            for key, value in self._init_config.items():
                setattr(self, key, value)
        if self.card._closed == False:
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
                if key == "segment_size" or "pretrig_size":
                    setattr(self, key, value * units.Sa)
                else:
                    setattr(self, key, value)

    def config(self):
        # handling memory assignment

        print("SETTINGS: card timeout = ", self.card_timeout)
        print("SETTINGS: # segments = ", self.segment_size)
        print("SETTINGS: sampling freq = ", self.sampling_frequency)
        print("SETTINGS: pretrig size = ", self.pretrig_size)
        print("SETTINGS: termination = ", int(self.HF_INPUT_50OHM / units.Sa))

        self.posttrig_size = self.segment_size - self.pretrig_size

        self.num_segment = self.runs * self.num_pts_in_exp  # *self.num_iters
        self.mem_size = self.num_segment * self.segment_size

        clock = spcm.Clock(self.card)
        clock.mode(spcm.SPC_CM_INTPLL)
        clock.sample_rate(self.sampling_frequency)

        CH_mapping = {0: spcm.CHANNEL0, 1: spcm.CHANNEL1}

        ACDC_mapping = {0: spcm.SPC_ACDC0, 1: spcm.SPC_ACDC1}
        self.ACDC = ACDC_mapping.get(self.readout_ch)

        PATH_mapping = {0: spcm.SPC_PATH0, 1: spcm.SPC_PATH1}
        self.PATH = PATH_mapping.get(self.readout_ch)

        AMP_mapping = {0: spcm.SPC_AMP0, 1: spcm.SPC_AMP1}
        self.AMP_ch = AMP_mapping.get(self.readout_ch)

        # setup card mode
        self.card.card_mode(spcm.SPC_REC_FIFO_MULTI)  # SPC_REC_FIFO_MULTI
        self.card.timeout(self.card_timeout)

        # set Analog input parameters
        print(f"50 ohm impedance? {int(self.HF_INPUT_50OHM/units.Sa)}")
        self.card.set_i(self.PATH, int(self.HF_INPUT_50OHM / units.Sa))
        self.card.set_i(self.AMP_ch, int(self.AMP))
        self.card.set_i(self.ACDC, int(self.ACCOUPLE / units.Sa))

        # setup trigger engine
        trigger = spcm.Trigger(self.card)
        trigger.ext0_mode(spcm.SPC_TM_POS)  # set trigger mode
        trigger.or_mask(spcm.SPC_TMASK_EXT0)  # trigger set to external
        trigger.termination(self.TERMINATE50OHM)
        trigger.ext0_coupling(spcm.COUPLING_DC)  # trigger coupling

        self.multiple_recording = spcm.Multi(self.card)
        self.multiple_recording.memory_size(self.mem_size)
        self.multiple_recording.allocate_buffer(
            self.segment_size, num_segments=self.num_segment
        )
        self.multiple_recording.post_trigger(self.posttrig_size)

        # record forever
        self.multiple_recording.to_transfer_samples(0)  # 2*self.mem_size)
        self.multiple_recording.notify_samples(self.mem_size // 4)

        self.multiple_recording.start_buffer_transfer(spcm.M2CMD_DATA_STARTDMA)

    def check_connection(self):
        if self.card._closed == False:
            pass
        elif self.card._closed == True:
            assert print("Digitizer is not connected")

    def start_buffer(self):
        self.card.start(spcm.M2CMD_CARD_ENABLETRIGGER)

    def convert_data(self):
        return self.raw_data * ((self.AMP / 1000) / np.abs(self.max_value)) + 0.1

    def acquire(self):
        try:
            data_block = next(self.multiple_recording)
            print(np.shape(data_block))

            print(f"termination setting: {self.HF_INPUT_50OHM/units.Sa}")

            self.raw_data = np.copy(data_block)
            self.max_value = self.card.max_sample_value()

        except spcm.SpcmTimeout:
            self.card.stop(spcm.M2CMD_DATA_STOPDMA)
            self.card.__exit__()
            self.card.__enter__()

        finally:
            self.card.reset()
            pass

        return self.raw_data * ((self.AMP / 1000) / np.abs(self.max_value)) + 0.1
