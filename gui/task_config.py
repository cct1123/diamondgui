# measurement components------------------------------------------------
from calibration.pl_trace import PL_trace
from calibration.thzreflection_trace import THzReflectionTrace
from measurement.magneticresonance import Rabi, Rabi_WDF, pODMR, pODMR_WDF
from measurement.task_base import JobManager

JM = JobManager()
# JM.start()
TASK_ODMR = pODMR(name="default")

TASK_ODMR_WDF = pODMR_WDF(name="default")
# TASK_ODMR_ID = TASK_ODMR.get_uiid()
TASK_RABI = Rabi(name="default")
TASK_RABI_WDF = Rabi_WDF(name="default")
# TASK_RABI_ID = TASK_RABI.get_uiid()
TASK_THZRTRACE = THzReflectionTrace(name="default")
# TASK_THZRTRACE_ID = TASK_THZRTRACE.get_uiid()
# ------------------------------------------------------------------
TASK_PL_TRACE = PL_trace(name="default")
