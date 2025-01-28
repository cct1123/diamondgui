import importlib
import logging

# import the neccessary hardware controller
import hardware.config_custom as hcf
from hardware.laser.laser import LaserControl
from hardware.mw.mwsynthesizer import Synthesizer
from hardware.pulser.pulser import PulseGenerator
from measurement.task_base import Singleton

logger = logging.getLogger(__name__)


class HardwareManager(metaclass=Singleton):
    _hardware_instances = dict()

    def __init__(self):
        pass

    def add_default_hardware(self):
        # ========== !! Please REVIEW and EDIT before using this method !! ======

        # add VDI MW synthesizer ------------------------
        addflag = Synthesizer.__name__ not in self._hardware_instances
        if addflag:
            self.mwsyn = Synthesizer(
                hcf.VDISYN_SN,
                vidpid=hcf.VDISYN_VIDPID,
                baudrate=hcf.VDISYN_BAUD,
                # timeout=5,
                # write_timeout=5,
            )
            self._hardware_instances[Synthesizer.__name__] = self.mwsyn
            logger.info(
                f"Added Hardware 'mwsyn' for VDI Synthesizer with address {self.mwsyn}"
            )
        else:
            logger.info(
                f"Hardware {Synthesizer.__name__} is added already with instane name {self._hardware_instances[Synthesizer.__name__]}"
            )
        # -----------------------------------------------

        # add laser control -----------------------------
        addflag = LaserControl.__name__ not in self._hardware_instances
        if addflag:
            self.laser = LaserControl(hcf.LASER_SN)
            self._hardware_instances[LaserControl.__name__] = self.laser
            logger.info(f"Added Hardware 'laser' for Laser with address {self.laser}")
        else:
            logger.info(
                f"Hardware {LaserControl.__name__} is added already with instane name {self._hardware_instances[LaserControl.__name__]}"
            )
        # -----------------------------------------------

        # add pulse generator---------------------------
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
                f"Hardware {PulseGenerator.__name__} is added already with instane name {self._hardware_instances[PulseGenerator.__name__]}"
            )
        # ----------------------------------------------

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
        # # -----------------------------------------------

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
