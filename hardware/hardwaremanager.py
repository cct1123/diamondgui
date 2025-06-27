import concurrent.futures
import importlib
import logging
import time
from typing import Optional

# Import all hardware configuration constants
import hardware.config as hcf
from hardware.camera.light import WhiteLight
from hardware.camera.thorlabs import CameraController
from hardware.daq.sidig import FIFO_DataAcquisition
from hardware.laser.laser import LaserControl
from hardware.mw.detector.pwrcontrol import MWPowerMeter
from hardware.mw.mwmodulation import Modulator

# Import all potential hardware controller classes
from hardware.mw.mwsource import VDISource
from hardware.mw.mwsynthesizer import Synthesizer
from hardware.mw.windfreakcontrol import WindfreakSynth
from hardware.pulser.pulser import PulseGenerator

# 1. DEPENDENCIES
# =================
# Import standard library and measurement framework base classes
from measurement.task_base import Singleton

# from hardware.positioner.positioner import XYZPositioner # Uncomment if used

# 2. SETUP
# ==========
logger = logging.getLogger(__name__)


# 3. HARDWARE MANAGER IMPLEMENTATION
# ==================================
class HardwareManager(metaclass=Singleton):
    """
    Manages the initialization and access of all hardware controllers.

    This class uses a singleton pattern to ensure only one instance exists.
    It initializes hardware in parallel for fast startup and provides type hints
    for full static analysis support in modern IDEs.
    """

    _hardware_instances = dict()

    # --- Static Analysis Blueprint ---
    # Pre-declare all potential hardware attributes with their types. This gives
    # static analyzers (e.g., VS Code's Pylance) the info they need for
    # autocompletion and "Go to Definition", even though attributes are
    # populated dynamically.
    vdi: Optional[VDISource]
    mwsyn: Optional[Synthesizer]  # Type can be more specific if known
    mwmod: Optional[Modulator]  # Type can be more specific if known
    windfreak: Optional[WindfreakSynth]
    pwr: Optional[MWPowerMeter]
    laser: Optional[LaserControl]
    pg: Optional[PulseGenerator]
    dig: Optional[FIFO_DataAcquisition]
    camera: Optional[CameraController]
    whitelight: Optional[WhiteLight]
    # xyz: Optional[XYZPositioner] # Uncomment if used

    def __init__(self):
        """Initializes the manager, setting all hardware attributes to None initially."""
        # Set all hinted attributes to None to ensure they exist on the instance
        for attr in self.__annotations__:
            setattr(self, attr, None)
        self.initialization_complete = False

    def add_default_hardware(self):
        """Initializes all default hardware controllers in parallel using a thread pool."""
        # --- Hardware Configuration List ---
        # Defines all hardware to be loaded. Easy to add, remove, or configure.
        hardware_to_load = [
            {
                "name": "vdi",
                "class": VDISource,
                "info": "VDI Source",
                "args": (hcf.NI_ch_UCA, hcf.NI_ch_MWBP, hcf.VDISYN_SN),
                "kwargs": {"vidpid": hcf.VDISYN_VIDPID, "baudrate": hcf.VDISYN_BAUD},
                "post_init": lambda s, inst: (
                    setattr(s, "mwsyn", inst.mwsyn),
                    setattr(s, "mwmod", inst.mwmod),
                ),
            },
            {
                "name": "windfreak",
                "class": WindfreakSynth,
                "info": "Windfreak Synth",
                "args": (),
                "kwargs": {},
            },
            {
                "name": "pwr",
                "class": MWPowerMeter,
                "info": "Mini-Circuits Power Meter",
                "args": (),
                "kwargs": {},
            },
            {
                "name": "laser",
                "class": LaserControl,
                "info": "Laser Control",
                "args": (hcf.LASER_SN,),
                "kwargs": {},
            },
            {
                "name": "pg",
                "class": PulseGenerator,
                "info": "Pulse Streamer",
                "args": (hcf.PS_IP,),
                "kwargs": {"chmap": hcf.PS_chmap, "choffs": hcf.PS_choffs},
            },
            {
                "name": "dig",
                "class": FIFO_DataAcquisition,
                "info": "SI Digitizer",
                "args": (),
                "kwargs": {"sn_address": hcf.SIDIG_ADDRESS},
            },
            {
                "name": "camera",
                "class": CameraController,
                "info": "Thorlabs Camera",
                "args": (),
                "kwargs": {},
            },
            {
                "name": "whitelight",
                "class": WhiteLight,
                "info": f"WhiteLight on channel {hcf.NI_ch_WL}",
                "args": (hcf.NI_ch_WL,),
                "kwargs": {},
            },
        ]

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(hardware_to_load)
        ) as executor:
            future_to_hardware = {}
            for hw_config in hardware_to_load:
                class_name = hw_config["class"].__name__
                if class_name in self._hardware_instances:
                    logger.info(f"Hardware {class_name} is already loaded.")
                    continue

                future = executor.submit(
                    hw_config["class"], *hw_config["args"], **hw_config["kwargs"]
                )
                future_to_hardware[future] = hw_config

            for future in concurrent.futures.as_completed(future_to_hardware):
                hw_config = future_to_hardware[future]
                name, class_name = hw_config["name"], hw_config["class"].__name__
                try:
                    instance = future.result()
                    setattr(self, name, instance)
                    self._hardware_instances[class_name] = instance
                    logger.info(
                        f"Added '{name}' for {hw_config['info']} with address {instance}"
                    )

                    if "post_init" in hw_config:
                        hw_config["post_init"](self, instance)

                except Exception as e:
                    logger.error(
                        f"Failed to initialize '{name}' ({class_name}): {e}",
                        exc_info=True,
                    )
        logger.info("Hardware initialization process has finished.")
        # Optional: Add a small delay to ensure all logs are flushed if needed
        time.sleep(0.1)
        self.initialization_complete = True

    def add(
        self,
        name: str,
        path_controller: str,
        class_controller: str,
        args: list = [],
        kwargs: dict = {},
    ):
        """Dynamically loads and adds a hardware controller from a file path."""
        spec = importlib.util.spec_from_file_location(class_controller, path_controller)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        ControllerClass = getattr(module, class_controller)

        class_name = ControllerClass.__name__
        if class_name in self._hardware_instances:
            raise ValueError(f"Hardware Controller '{class_name}' already exists.")

        instance = ControllerClass(*args, **kwargs)
        setattr(self, name, instance)
        self._hardware_instances[class_name] = instance
        logger.info(
            f"Dynamically added '{name}' for {class_name} with address {instance}"
        )

    def has(self, instance_name: str) -> bool:
        """
        Checks if hardware with the given instance name (e.g., 'laser')
        has been successfully initialized.
        """
        instance = getattr(self, instance_name, None)
        return instance is not None and instance in self._hardware_instances.values()

    def shutdown(self):
        """
        Iterates through all initialized hardware instances and calls their
        close() method if it exists, ensuring a graceful shutdown.
        """
        logger.info("HardwareManager is shutting down all connections...")
        for name, instance in self._hardware_instances.items():
            # Check if the instance has a 'close' method
            if hasattr(instance, "close") and callable(getattr(instance, "close")):
                try:
                    logger.info(f"Closing connection for: {name}")
                    instance.close()
                except Exception as e:
                    # Log any errors but continue trying to close other devices
                    logger.error(f"Error closing {name}: {e}")
        print("All hardware connections have been instructed to close.")
