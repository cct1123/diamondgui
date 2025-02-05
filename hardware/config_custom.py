"""
the parameters here will overwrite the default hardware config
"""

from hardware.config import *

PS_choffs = {
    "laser": 0,
    "dclk": 1000.0,
    "dtrig": 1000.0,
    "sdtrig":0,
    "mwA": 0,
    "mwB": 0,
    "rftrig": 0,
    "Bz": 0,  # AO 0
    "Bx": 0,  # AO 1
}
