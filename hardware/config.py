'''
default hardware config
'''
# ------------------------------------------------------------------------------------------------
# Pulse Streamer Settings ------------------------------------------------------------------------

# communication
PS_IP = "169.254.8.2"

# channels
PSch_Laser = 0 # trigger the laser
PSch_DAQClock = 1 # as the clock for DAQ
PSch_DAQstart = 3 # trigger pulse to start the DAQ
PSch_MW_A = 4 # control switch of MW line with 0 phase shift  
PSch_MW_B = 5 # control switch of MW line with certain phase shift  

PS_chmap = {"laser":PSch_Laser, 
            "clock":PSch_DAQClock, 
            "daqtrig":PSch_DAQstart,
            "mw_A":PSch_MW_A, 
            "mw_B":PSch_MW_B
            }

PSch_RFconsole = 5 # to trigger the red stone RF console

# AO Channels
# please refer to the following for AO calibration
# https://www.swabianinstruments.com/static/documentation/PulseStreamer/sections/api-doc.html#calibrating-the-analog-outputs 
PS_aoSlope = 1.0
PS_aoOffset = 0.0 # [V]
PSaoch_PhaseShifter = 0 # AO channel for MW phase shifter which controls the phase of the MW line
PSaoch_Attenuator = 1 # AO channel for the MW attenuator which controls the MW power

# ------------------------------------------------------------------------------------------------
# NI DAQ Settings --------------------------------------------------------------------------------
DAQch_APD = "/Dev1/ai16"
DAQch_Clock = "/Dev1/PFI8" # clock source
DAQch_Trig = "/Dev1/PFI9" # trigger source
DAQch_VDISynTrigOut = "/Dev1/port0/line7"

# # for positioner I/O
# DAQch_Ax1_InAp = "Dev1/port/line8"
# DAQch_Ax1_InBp = "Dev1/port/line9"
# DAQch_Ax2_InAp = "Dev1/port/line10"
# DAQch_Ax2_InBp = "Dev1/port/line11"
# DAQch_Ax3_InAp = "Dev1/port/line12"
# DAQch_Ax3_InBp = "Dev1/port/line13"

# DAQch_Ax1_OutAp = "Dev1/port/line14"
# DAQch_Ax1_OutBp = "Dev1/port/line15"
# DAQch_Ax2_OutBp = "Dev1/port/line16"
# DAQch_Ax2_OutAp = "Dev1/port/line17"
# DAQch_Ax3_OutAp = "Dev1/port/line18"
# DAQch_Ax3_OutBp = "Dev1/port/line19"
DAQch_Ax123_InABp = "/Dev1/port/line8:13"
DAQch_Ax123_OutABp = "/Dev1/port/line14:19"

DAQchmap = dict(apd = DAQch_APD, 
                clock = DAQch_Clock, 
                trig = DAQch_Trig, 
                pax123_in = DAQch_Ax123_InABp, 
                pax123_out = DAQch_Ax123_OutABp)
# # 

# ------------------------------------------------------------------------------------------------
# Positioners -------------------------------------------------------------------------------------
AMC_IP = "169.254.16.155" # AMC300's static IP




# ------------------------------------------------------------------------------------------------
# Oxxius Laser -------------------------------------------------------------------------------------
LASER_SN = "LAS-09434" # default ip


# ------------------------------------------------------------------------------------------------
# VDI synthesizer -------------------------------------------------------------------------------------
VDISYN_SN = "VDIS200A" # VDI synthesizer serial number
VDISYN_VIDPID = "0403:6001" # the USB VID:PID
VDISYN_BAUD = 921600 # USB baud rate between PC and VDI sythesizer