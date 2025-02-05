"""
default hardware config
"""
# ------------------------------------------------------------------------------------------------
# Pulse Streamer Settings ------------------------------------------------------------------------

# communication
# PS_IP = "169.254.8.2"
PS_IP = "192.168.1.26"

# channels
PS_chmap = {
    "laser": 0, # excitation laser trigger
    "dclk": 1, # NIIO sample clock
    "dtrig": 2, # NIIO trigger
    "sdtrig":3, # spectrum instrumentation digitizer trigger
    "mwA": 4, # MW switch A
    "mwB": 5, # MW switch B
    "rftrig": 6, # Redstone RF console trigger
    "Bz": 8,  # AO 0
    "Bx": 9,  # AO 1
}

PS_choffs = {
    "laser": 0,
    "dclk": 0,
    "dtrig": 0,
    "sdtrig":0,
    "mwA": 0,
    "mwB": 0,
    "rftrig": 0,
    "Bz": 0,  # AO 0
    "Bx": 0,  # AO 1
}
PS_timebase = 1  # ns

# AO Channels
# please refer to the following for AO calibration
# https://www.swabianinstruments.com/static/documentation/PulseStreamer/sections/api-doc.html#calibrating-the-analog-outputs

# ------------------------------------------------------------------------------------------------
# NI DAQ Settings --------------------------------------------------------------------------------
NI_ch_APD = "/Dev1/ai16"
NI_ch_Clock = "/Dev1/PFI11"  # clock source
NI_ch_Trig = "/Dev1/PFI12"  # trigger source
NI_ch_VDISynTrigOut = "/Dev1/port0/line7"
NI_ch_ZBD = "/Dev1/ai7"
NI_ch_UCA = "/Dev1/ao1"
NI_ch_MWBP = "/Dev1/ao2"
NI_ch_WL = "/Dev1/ao0"  # white light modulation

# # for positioner I/O
# NI_ch_Ax1_InAp = "Dev1/port/line8"
# NI_ch_Ax1_InBp = "Dev1/port/line9"
# NI_ch_Ax2_InAp = "Dev1/port/line10"
# NI_ch_Ax2_InBp = "Dev1/port/line11"
# NI_ch_Ax3_InAp = "Dev1/port/line12"
# NI_ch_Ax3_InBp = "Dev1/port/line13"

# NI_ch_Ax1_OutAp = "Dev1/port/line14"
# NI_ch_Ax1_OutBp = "Dev1/port/line15"
# NI_ch_Ax2_OutBp = "Dev1/port/line16"
# NI_ch_Ax2_OutAp = "Dev1/port/line17"
# NI_ch_Ax3_OutAp = "Dev1/port/line18"
# NI_ch_Ax3_OutBp = "Dev1/port/line19"
NI_ch_Ax123_InABp = "/Dev1/port/line8:13"
NI_ch_Ax123_OutABp = "/Dev1/port/line14:19"

NI_chmap = dict(
    apd=NI_ch_APD,
    clock=NI_ch_Clock,
    trig=NI_ch_Trig,
    pax123_in=NI_ch_Ax123_InABp,
    pax123_out=NI_ch_Ax123_OutABp,
)

NI_ratebase = 100.0e6  # Hz
NI_timebase = int(1.0 / NI_ratebase * 1e9)  # ns
NI_sampling_max = 500e3  # Hz
# #

# ------------------------------------------------------------------------------------------------
# Positioners -------------------------------------------------------------------------------------
AMC_IP = "169.254.16.155"  # AMC300's static IP
XRANGE = [58.5, 3113.8]  # in um
YRANGE = [30.5, 3168.3]  # in um
ZRANGE = [26.4, 2657.4]  # in um
SERIAL_X = "ANPx51-03971"
SERIAL_Y = "ANPx51-03967"
SERIAL_Z = "ANPz51-05545"

# ------------------------------------------------------------------------------------------------
# Oxxius Laser -------------------------------------------------------------------------------------
LASER_SN = "LAS-09434"  # default ip


# ------------------------------------------------------------------------------------------------
# VDI synthesizer -------------------------------------------------------------------------------------
VDISYN_SN = "VDIS200A"  # VDI synthesizer serial number
VDISYN_VIDPID = "0403:6001"  # the USB VID:PID
VDISYN_BAUD = 921600  # USB baud rate between PC and VDI sythesizer
VDISYN_timebase = int(4)  # ns
VDISYN_multiplier = 24.0  # multiplication factor of the amplifier-multiplier chain


# # ------------------------------------------------------------------------------------------------
# Spectrum Instruments Digitizer -------------------------------------------------------------------------------------
SIDIG_ADDRESS = "dev/spcm0" # M4i.4450-x8	sn 22817  /dev/spcm0
SIDIG_maxsr = 500e6  # Hz
SIDIG_timebase = int(1 / SIDIG_maxsr * 1e9)  # ns
SIDIG_chmap = {
    "apd": 0,
    "aux": 1,
}

# # ------------------------------------------------------------------------------------------------
# Tecmag Redstone RF console -------------------------------------------------------------------------------------
RSRF_client = "NTNMR.Application"
RSRF_timebase = 20  # ns
