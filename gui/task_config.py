# measurement components------------------------------------------------
import logging

from calibration.mwphasetune import MWPhaseTune
from calibration.pl_trace import PL_trace
from calibration.rfphasetune import RFPhaseTune
from calibration.thzreflection_trace import THzReflectionTrace
from measurement.magneticresonance import Rabi, Rabi_WDF, pODMR, pODMR_WDF
from measurement.task_base import JobManager

JM = JobManager()
JM.start()
TASK_ODMR = pODMR(name="default")

TASK_ODMR_WDF = pODMR_WDF(name="default")
# TASK_ODMR_ID = TASK_ODMR.get_uiid()
TASK_RABI = Rabi(name="default")
TASK_RABI_WDF = Rabi_WDF(name="default")
TASK_MW_PHASE_CALIBRATION = MWPhaseTune(name="default")

# TASK_RABI_ID = TASK_RABI.get_uiid()
TASK_THZRTRACE = THzReflectionTrace(name="default")
# TASK_THZRTRACE_ID = TASK_THZRTRACE.get_uiid()
# ------------------------------------------------------------------
TASK_PL_TRACE = PL_trace(name="default")
TASK_PHASETUNE = RFPhaseTune(name="default")

# from measurement.timesweep import DummyTimeSweep
# TASK_TSWEEP = DummyTimeSweep()

# from measurement.sensingprotocol import DummyNQST
# TASK_NQST = DummyNQST()


# from measurement.timesweep import TimeSweep

# TASK_TSWEEP = TimeSweep(name="default")

from measurement.sensingprotocol import NuclearQuasiStaticTrack

TASK_NQST = NuclearQuasiStaticTrack(name="default")
# TASK_NQST11 = NuclearQuasiStaticTrack()
# assert TASK_NQST11 is TASK_NQST


logger = logging.getLogger(__name__)
from measurement.task_base import Singleton
from measurement.timesweep import CPMG, XY4, XY8, CorrSpec, HahnEcho, Ramsey, Relaxation


class TimeSweepCollection(metaclass=Singleton):
    """
    Manages a collection of TimeSweep measurement objects and proxies
    calls to the currently active one.
    """

    measurements = {
        "Relaxation": Relaxation(),
        "Ramsey": Ramsey(),
        "HahnEcho": HahnEcho(),
        "CPMG": CPMG(),
        "XY4": XY4(),
        "XY8": XY8(),
        "CorrSpec": CorrSpec(),
    }

    def __init__(self, name="default"):
        self._name = self.__class__.__name__ + "-" + name
        self._uiid = self._name + "-" + "ui"
        self._active_measurement_name = "Relaxation"

    @property
    def active_measurement(self):
        return self.measurements[self._active_measurement_name]

    def set_name(self, name):
        self._name = self.__class__.__name__ + "-" + name
        self._uiid = self._name + "-" + "ui"

    def get_uiid(self):
        return self._uiid

    def get_classname(self):
        return self.__class__.__name__

    def get_name(self):
        return self._name

    def select(self, name):
        """Selects the active measurement task."""
        if name in self.measurements:
            self._active_measurement_name = name
        else:
            logging.error(f"Attempted to select unknown measurement: {name}")


TASK_TSWEEPCOLL = TimeSweepCollection()
