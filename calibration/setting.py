import numpy as np

import hardware.config as hcf

# some parameters for PL integration ================================================
PRETRIG_TIME = 64  # [ns]
POSTRIG_TIME = 960  # [ns]
PRETRIG_SIZE = int((PRETRIG_TIME) * hcf.SIDIG_maxsr / 1e9) // 32 * 32
POSTRIG_SIZE = int((POSTRIG_TIME) * hcf.SIDIG_maxsr / 1e9)
SEGMENT_SIZE = PRETRIG_SIZE + POSTRIG_SIZE // 32 * 32
POSTRIG_SIZE = SEGMENT_SIZE - PRETRIG_SIZE

# 2025/08/12: calibrated  the fit parameters A, t0, tau_rise, tau_decay
PLINT_WEIGTHT_FITPARA = dict(A=1.28, t0=195.75, tau_rise=34.21, tau_decay=481.30)
T0_HEAVISIDE = PLINT_WEIGTHT_FITPARA["t0"]


def double_exponential(t, A, t0, tau_rise, tau_decay):
    """
    A function describing a pulse with an exponential rise and exponential decay.
    Ensures that tau_decay is greater than tau_rise to produce a positive pulse.
    """
    if tau_rise >= tau_decay:
        return (
            np.inf
        )  # Return infinity to guide the fitter away from this invalid parameter space

    # Calculate the function only for t > t0, otherwise it's zero
    result = np.zeros_like(t, dtype=float)
    mask = t > t0

    term1 = np.exp(-(t[mask] - t0) / tau_decay)
    term2 = np.exp(-(t[mask] - t0) / tau_rise)

    result[mask] = A * (term1 - term2)
    return result


def plint_weight(t):
    return double_exponential(t, **PLINT_WEIGTHT_FITPARA)


def WEIGHT_FUNC_DEFAULT(idx):
    return plint_weight(hcf.SIDIG_timebase * (np.array(idx) - PRETRIG_SIZE))


# =======================================================================================
