'''
default hardware config
'''
# ------------------------------------------------------------------------------------------------
# Pulse Streamer Settings ------------------------------------------------------------------------

# communication
PS_ip = "169.254.8.2"

# channels
PSch_Laser = 0 # trigger the laser
PSch_DAQClock = 1 # as the clock for DAQ
PSch_DAQstart = 3 # trigger pulse to start the DAQ
PSch_MW0 = 1 # control switch of MW line with 0 phase shift  
PSch_MWps = 2 # control switch of MW line with certain phase shift  


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
DAQch_APD = "Dev1/ai16"
DAQch_Clock = "Dev1/PFI8" # clock source
DAQch_Trig = "Dev1/PFI9" # clock gate

# # for positioner I/O
DAQch_Ax1_InAp = "Dev1/P0.8"
DAQch_Ax1_InBp = "Dev1/P0.9"
DAQch_Ax1_OutBp = "Dev1/P0.10"

DAQch_Ax2_InAp = "Dev1/P0.12"
DAQch_Ax2_InBp = "Dev1/P0.13"
DAQch_Ax2_OutBp = "Dev1/P0.14"

DAQch_Ax3_InAp = "Dev1/P0.16"
DAQch_Ax3_InBp = "Dev1/P0.17"
DAQch_Ax3_OutBp = "Dev1/P0.18"

# # 

# ------------------------------------------------------------------------------------------------
# Positioners -------------------------------------------------------------------------------------
AMC_IP = "192.168.1.78" # default ip




# ------------------------------------------------------------------------------------------------
# Oxxius Laser -------------------------------------------------------------------------------------
LASER_SN = "LAS-09434" # default ip
