"""
This file shows how to use the Pulse Streamer 8/2.
The PulseStreamer 8/2 describes sequences made up of sequence steps. The sequence step is 
the smallest element of a sequence that contains information on the state of every output 
of the Pulse Streamer and the duration to hold this state. It is represented by a tuple 
in the form (time, [1,3], 0.8, -0.4), where time is an integer in ns (clock ticks), 
[1,3] is a list numbering the channels which should be high the last two numbers specify 
the analog outputs in volt.
To create sophisticated sequences, you can make use of the classes Sequence and OutputState. 
Class Sequence enables you to independently set pulse patterns on each of the eight digital 
and the two analog channels. A pulse pattern is represented by a tuple in the form (duration, level).
The duration is always specified in nanoseconds and the level is either 0 or 1 for digital output 
a real number between -1 and +1 in Volt for analog outputs.

You can either communicate with the hardware via JSON-RPC (recommended) or Google-RPC. As an example, how
to detetct your Pulse Streamer in the network and discover its IP-address, we recommend to have a look at
the file <1_TestConnection.py> as well as the full documentation of the Pulse Streamer 8/2
https://www.swabianinstruments.com/static/documentation/PulseStreamer/index.html

Before you can run this example, you need to install "pulsestreamer" client package

  > pip install pulsestreamer

"""


#import JSON-RPC Pulse Streamer wrapper class, to use Google-RPC import from pulsestreamer.grpc
from pulsestreamer import PulseStreamer

#import enum types 
from pulsestreamer import TriggerStart, TriggerRearm

#import class Sequence and OutputState for advanced sequence building
from pulsestreamer import Sequence, OutputState

#python module for scientific computing only used for creating the random pulse and merging signals
import numpy as np

#create Pulsestreamer
"""To set the IP-Address of the Pulsestreamer see
https://www.swabianinstruments.com/static/documentation/PulseStreamer/sections/network.html
"""

ip_hostname='pulsestreamer' # edit this line to use a specific Pulse Streamer IP address

pulser = PulseStreamer(ip_hostname)

#define channel names 
ch_pockels   = 0 # output channel 0
ch_camera1   = 1 # output channel 1
ch_camera2   = 2 # output channel 2
ch_ref       = 3 # output channel 3
ch_ref2      = 4 # output channel 4
trigger_high_time = 10 #ns
delay_pockels = 5 #ns
delay_camera1 = 100 #ns
delay_camera2 = 150 #ns
refPeriod     = 20 #ns
refPeriod2    = 40 #ns

#define digital levels
HIGH=1
LOW=0

#define pulse patterns for each channels
# simply add more pulses with ', (time, HIGH/LOW)'
seq_pockels = [(delay_pockels, LOW), (trigger_high_time, HIGH)]
seq_camera1 = [(delay_camera1, LOW), (trigger_high_time, HIGH)]
seq_camera2 = [(delay_camera2, LOW), (trigger_high_time, HIGH)]

# 10 pulses with a period of refPeriod and refPeriod2
seq_ref     = [(int(refPeriod - (refPeriod / 2))  , HIGH), (int(refPeriod / 2), LOW)] * 10
seq_ref2    = [(int(refPeriod2 - (refPeriod2 / 2)), HIGH), (int(refPeriod2 / 2), LOW)] * 10

#create the sequence
seq = Sequence()

#set digital channels
seq.setDigital(ch_pockels, seq_pockels)
seq.setDigital(ch_camera1, seq_camera1)
seq.setDigital(ch_camera2, seq_camera2)
seq.setDigital(ch_ref, seq_ref)
seq.setDigital(ch_ref2 , seq_ref2)

#run the sequence only once 
n_runs = 1
#n_runs = 'INFIITE' # repeat the sequence all the time

#reset the device - all outputs 0V
pulser.reset()

#set constant state of the device
pulser.constant(OutputState.ZERO()) #all outputs 0V

# define the final state of the Pulsestreamer - the device will enter this state when the sequence is finished
final = OutputState.ZERO()

#Start via the trigger input and enable the retrigger-function
#start = Start.HARDWARE_RISING
#mode = Mode.NORMAL

#Start the sequence after the upload and disable the retrigger-function
start = TriggerStart.IMMEDIATE
rearm = TriggerRearm.MANUAL

pulser.setTrigger(start=start, rearm=rearm)

print ("\nGenerated sequence pulse list:")
print ("Data format: Sequence as a list of sequence steps (duration [ns], digital bit pattern, analog 0, analog 1)")
print(seq.getData())
print("\nThe channel pulse pattern are shown in a Pop-Up window. To proceed with streaming the sequence, please close the sequence plot.")
seq.plot()
#upload the sequence and arm the device
pulser.stream(seq, n_runs, final)
print ("\nOutput running on Pulse Streamer")