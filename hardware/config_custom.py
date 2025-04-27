"""
the parameters here will overwrite the default hardware config
"""

from hardware.config import *

PS_choffs = {
    "laser": 0,
    "dclk": 0.0,  # was 1000
    "dtrig": 900.0,  # was 1000
    # "sdtrig": 900,  # Emmeline modified 4/25
    "sdtrig": 0,  # Tung modified 4/26
    "mwA": 0,
    "mwB": 0,
    "rftrig": 0,
    "Bz": 0,  # AO 0
    "Bx": 0,  # AO 1
    "WDF": 0,
}
