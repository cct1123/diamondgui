import importlib
import logging

# import the neccessary hardware controller
import hardware.config as hcf
from measurement.task_base import Singleton

logger = logging.getLogger(__name__)


class HardwareManager(metaclass=Singleton):
    _hardware_instances = dict()

    def __init__(self):
        pass

    def add_default_hardware(self):
        # ========== !! Please REVIEW and EDIT before using this method !! ======

        # # add VDI 400GHz system ------------------------
        # from hardware.mw.mwsource import VDISource
        # addflag = VDISource.__name__ not in self._hardware_instances
        # if addflag:
        #     self.vdi = VDISource(
        #         hcf.NI_ch_UCA,
        #         hcf.NI_ch_MWBP,
        #         hcf.VDISYN_SN,
        #         vidpid=hcf.VDISYN_VIDPID,
        #         baudrate=hcf.VDISYN_BAUD,
        #     )
        #     self._hardware_instances[VDISource.__name__] = self.vdi
        #     logger.info(f"Added Hardware 'vdi' for VDI Source with address {self.vdi}")
        #     self.mwsyn = self.vdi.mwsyn  # for downward compatibility
        #     self.mwmod = self.vdi.mwmod  # for downward compatibility
        # else:
        #     logger.info(
        #         f"Hardware {VDISource.__name__} is added already with name {self._hardware_instances[VDISource.__name__]}"
        #     )

        # # add VDI MW synthesizer ------------------------
        # addflag = Synthesizer.__name__ not in self._hardware_instances
        # if addflag:
        #     self.mwsyn = Synthesizer(
        #         hcf.VDISYN_SN,
        #         vidpid=hcf.VDISYN_VIDPID,
        #         baudrate=hcf.VDISYN_BAUD,
        #         # timeout=5,
        #         # write_timeout=5,
        #     )
        #     self._hardware_instances[Synthesizer.__name__] = self.mwsyn
        #     logger.info(
        #         f"Added Hardware 'mwsyn' for VDI Synthesizer with address {self.mwsyn}"
        #     )
        # else:
        #     logger.info(
        #         f"Hardware {Synthesizer.__name__} is added already with name {self._hardware_instances[Synthesizer.__name__]}"
        #     )
        # # -----------------------------------------------

        # # add MW modulator ---------------------------
        # from hardware.mw.mwmodulation import Modulator

        # addflag = Modulator.__name__ not in self._hardware_instances
        # if addflag:
        #     self.mwmod = Modulator(ch_amp=hcf.NI_ch_UCA, ch_phase=hcf.NI_ch_MWBP)
        #     self._hardware_instances[Modulator.__name__] = self.mwmod
        #     logger.info(
        #         f"Added Hardware 'mwmod' for MW Modulator with address {self.mwmod}"
        #     )
        # else:
        #     logger.info(
        #         f"Hardware {Modulator.__name__} is added already with name {self._hardware_instances[Modulator.__name__]}"
        #     )

        # add laser control -----------------------------
        from hardware.laser.laser import LaserControl

        addflag = LaserControl.__name__ not in self._hardware_instances
        if addflag:
            self.laser = LaserControl(hcf.LASER_SN)
            self._hardware_instances[LaserControl.__name__] = self.laser
            logger.info(f"Added Hardware 'laser' for Laser with address {self.laser}")
        else:
            logger.info(
                f"Hardware {LaserControl.__name__} is added already with name {self._hardware_instances[LaserControl.__name__]}"
            )
        # -----------------------------------------------

        # add pulse generator---------------------------
        from hardware.pulser.pulser import PulseGenerator

        addflag = PulseGenerator.__name__ not in self._hardware_instances
        if addflag:
            self.pg = PulseGenerator(
                ip=hcf.PS_IP, chmap=hcf.PS_chmap, choffs=hcf.PS_choffs
            )
            self._hardware_instances[PulseGenerator.__name__] = self.pg
            logger.info(
                f"Added Hardware 'pg' for Pulse Streamer with address {self.pg}"
            )
        else:
            logger.info(
                f"Hardware {PulseGenerator.__name__} is added already with name {self._hardware_instances[PulseGenerator.__name__]}"
            )
        # ----------------------------------------------

        # add SI digitizer ---------------------------
        from hardware.daq.sidig import FIFO_DataAcquisition

        addflag = FIFO_DataAcquisition.__name__ not in self._hardware_instances
        if addflag:
            self.dig = FIFO_DataAcquisition(sn_address=hcf.SIDIG_ADDRESS)
            self._hardware_instances[FIFO_DataAcquisition.__name__] = (
                self.dig
            )  # TODO this is not correct
            logger.info(
                f"Added Hardware 'dig' for Pulse Streamer with address {self.dig}"
            )
        else:
            logger.info(
                f"Hardware {FIFO_DataAcquisition.__name__} is added already with name {self._hardware_instances[FIFO_DataAcquisition.__name__]}"
            )
        # #----------------------------------------------

        # # add Attocube controller ------------------------
        # from hardware.positioner.positioner import XYZPositioner

        # addflag = XYZPositioner.__class__ not in self._hardware_instances
        # if addflag:
        #     self.xyz = XYZPositioner(hcf.AMC_IP)
        #     self._hardware_instances[XYZPositioner.__class__] = self.xyz
        #     logger.info(
        #         f"Added Hardware 'xyz' for Attocube Positioner with address {self.xyz}"
        #     )
        # else:
        #     logger.info(
        #         f"Hardware {XYZPositioner.__class__} is added already with instane name {self._hardware_instances[XYZPositioner.__class__]}"
        #     )
        # # # -----------------------------------------------

        # add Windfreak -----------------------------
        from hardware.mw.windfreakcontrol import WindfreakSynth

        addflag = WindfreakSynth.__name__ not in self._hardware_instances
        if addflag:
            self.windfreak = WindfreakSynth()
            self._hardware_instances[WindfreakSynth.__name__] = self.windfreak
            logger.info(
                f"Added Hardware 'windfreak' for Laser with address {self.windfreak}"
            )
        else:
            logger.info(
                f"Hardware {WindfreakSynth.__name__} is added already with name {self._hardware_instances[WindfreakSynth.__name__]}"
            )
        # -----------------------------------------------

        # Inside add_default_hardware
        from hardware.camera.thorlabs import CameraController

        addflag = CameraController.__name__ not in self._hardware_instances
        if addflag:
            self.camera = CameraController()
            self._hardware_instances[CameraController.__name__] = self.camera
            logger.info("Added Hardware 'camera' for Thorlabs Camera")
        else:
            logger.info(
                f"Hardware {CameraController.__name__} is added already with name {self._hardware_instances[CameraController.__name__]}"
            )
        # -----------------------------------------------

        # add white light control -----------------------
        from hardware.camera.light import WhiteLight

        addflag = WhiteLight.__name__ not in self._hardware_instances
        if addflag:
            self.whitelight = WhiteLight(hcf.NI_ch_WL)
            self._hardware_instances[WhiteLight.__name__] = self.whitelight
            logger.info(
                f"Added Hardware 'whitelight' for WhiteLight on channel {hcf.NI_ch_WL}"
            )
        else:
            logger.info(
                f"Hardware {WhiteLight.__name__} is added already with name {self._hardware_instances[WhiteLight.__name__]}"
            )
        # -----------------------------------------------

    def add(self, name, path_controller, class_controller, args=[], kwargs={}):
        spec = importlib.util.spec_from_file_location(class_controller, path_controller)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ClassController = getattr(module, class_controller)

        class_controller_name = ClassController.__name__
        if class_controller_name in self._hardware_instances:
            raise ValueError(
                f"Hardware Controller '{class_controller_name}' already exists"
            )

        setattr(self, name, ClassController(*args, **kwargs))
        self._hardware_instances[class_controller_name] = getattr(self, name)

    def has(self, name):
        if name in self._hardware_instances:
            return True
        else:
            return False
