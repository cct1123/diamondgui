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


# import JSON-RPC Pulse Streamer wrapper class, to use Google-RPC import from pulsestreamer.grpc
from pulsestreamer import PulseStreamer

# import enum types
from pulsestreamer import TriggerStart, TriggerRearm

# import class Sequence and OutputState for advanced sequence building
from pulsestreamer import Sequence, OutputState

# for python2 compatibility
import six   

# python module for scientific computing only used for creating the random pulse and merging signals
import numpy as np

ip_hostname='pulsestreamer' # edit this line to use a specific Pulse Streamer IP address
HIGH = 1
LOW = 0

"""------------------functions to set pulsestreamer outputs ----------------------------"""

def all_zero(pulser):
    """setting Pulsestreamer constant (LOW)"""
    pulser.constant(OutputState.ZERO())

def all_constant(pulser):
    """setting Pulsestreamer constant (digital channel 0,1,4 HIGH and analog channel 1 1V)"""
    output = OutputState([0,1,4],0.0, 1.0)
    pulser.constant(output)

def rectangular_pulse(pulser):
    """streaming an endless rectangular pulse on all channels"""
    #values for creating the Pulsestreamer sequence
    n_periods = 10
    period = 256

    #values for setting the Pulsestreamer data-stream
    n_runs = PulseStreamer.REPEAT_INFINITELY # -1 for endless streaming
    final = OutputState.ZERO()

    #setting the trigger mode
    start = TriggerStart.IMMEDIATE
    rearm =TriggerRearm.MANUAL
    pulser.setTrigger(start=start, rearm=rearm)

    
    #pulse-sequence on all channels using class sequence
    seq=Sequence()
    #Set digital channels at one setting
    seq.setDigital([0,1,2,3,4,5,6,7], n_periods*[(period//2, HIGH), (period//2, LOW)])
    #Set analog channels at one setting
    seq.setAnalog([0,1],n_periods*[(period//2, 1.0), (period//2, -1.0)])

    pulser.stream(seq, n_runs, final)

    print('Pulse Streamer is streaming: '+str(pulser.isStreaming())+'\n')
    
def random_sequence(pulser):
    """streaming random pulse pattern on all channels (channel 0 is used as a trigger"""
    #values for setting the Pulsestreamer data-stream
    n_runs = 1
    final = OutputState([1,2,3,4,5,6,7],0,0)

    #setting the trigger mode
    start = TriggerStart.IMMEDIATE
    rearm =TriggerRearm.MANUAL
    pulser.setTrigger(start=start, rearm=rearm)
           
    #creating random sequence by directly creating the sequence steps as tuples of ticks, digital channel list and analog values
    t = np.random.uniform(16, 128, 1000).astype(int)
    sequence=[]
    for i, ti in enumerate(t):
        #digital channel list
        ch=[0]
        for j in range(1,8):
            state=np.random.randint(0,2)
            if (state==1):
                ch.append(j)
        #analog values
        a0 = np.random.uniform(-1.0, 1.0)
        a1 = np.random.uniform(-1.0, 1.0)
        #appending tuples of ticks, digital channel list and analog values
        sequence += [ (ti, ch, a0, a1)  ]

    pulser.stream(sequence, n_runs, final)

    print('Pulse Streamer has finished the sequence: '+str(pulser.hasFinished())+'\n')

def random_sequence_software(pulser):
    """streaming random pulse pattern with software_start on all channels (channel 0 is used as a trigger)"""
    #values for setting the Pulsestreamer data-stream
    n_runs = 1
    final = OutputState.ZERO()

    #setting the trigger mode
    start = TriggerStart.SOFTWARE
    rearm = TriggerRearm.AUTO #retrigger enable
    pulser.setTrigger(start=start, rearm=rearm)
    
           
    #creating random sequence using class Sequence with its the methods setDigital() and setAnalog()
    seq = Sequence()
    t = np.random.uniform(20, 256, 1000).astype(int)
    #creating pulse pattern for each digital channel
    seq.setDigital(0, [(8, HIGH),(8, LOW)]) # Trigger on channel 0
    for ch_digi in range(1,8):
        channel_seq = []
        for i, ti in enumerate(t):
            state = i%2
            channel_seq.append((ti, state))
        seq.setDigital(ch_digi, channel_seq)

    #creating pulse pattern for each analog channel  
    for ch_ana in range(2):
        channel_seq = []
        for i, ti in enumerate(t):
            a = np.random.uniform(-1.0, 1.0)
            channel_seq.append((ti, a))
        seq.setAnalog(ch_ana, channel_seq)

    pulser.stream(seq, n_runs, final)
    print('Pulse Streamer holds sequence in memory: '+ str(pulser.hasSequence())+'\n')

    six.moves.input("To start stream press <ENTER>")
    pulser.startNow()
    print('Pulse Streamer has finished the sequence: '+str(pulser.hasFinished())+'\n')
    six.moves.input("To retrigger sequence press <ENTER>")
    pulser.startNow()
    print('Pulse Streamer has finished the sequence: '+str(pulser.hasFinished())+'\n')

def stream_merged_pulse_pattern(pulser):
    """
    Merge example for a Rabi Sequence accounting for AOM delay.
    
        channel 0: laser
        channel 1: microwaves
        channel 2-8: square waves
    """
    
    delay = 10

    t_laser = 300
    t_wait = 100
    t_mw = np.arange(10, 100, 10) # values are generated (start, stop, step)

    #pulse pattern to merge
    laser_seq = []
    mw_seq = []
    square_1_seq = []
    square_2_seq = []
    square_3_seq = []
    square_4_seq = []
    square_5_seq = []
    square_6_seq = []
    for ti in t_mw:
        laser_seq += [ (t_laser, HIGH), (t_wait+ti, LOW) ] 
        mw_seq += [ (t_laser+t_wait, HIGH), (ti, LOW) ] 
        square_1_seq += [(t_wait, HIGH), (t_wait, LOW)]
        square_2_seq += [(t_wait//2, HIGH), (t_wait//2, LOW)]
        square_3_seq += [(t_wait//3, HIGH), (t_wait//3, LOW)]
        square_4_seq += [(t_wait//4, HIGH), (t_wait//4, LOW)]
        square_5_seq += [(t_wait//5, HIGH), (t_wait//5, LOW)]
        square_6_seq += [(t_wait//6, HIGH), (t_wait//6, LOW)]

    # delay microwave sequence
    mw_seq = [(delay, 0)] + mw_seq

    #sequence list
    union_list = [laser_seq, mw_seq, square_1_seq, square_2_seq, square_3_seq, square_4_seq, square_5_seq, square_6_seq]    

    #set channels using class Sequence
    seq=Sequence()
    for ch_number in range(len(union_list)):
        seq.setDigital(ch_number, union_list[ch_number])

    n_runs = 1
    final = OutputState.ZERO()
    
    #setting the trigger mode
    start = TriggerStart.IMMEDIATE
    rearm =TriggerRearm.MANUAL
    pulser.setTrigger(start=start, rearm=rearm)

    pulser.stream(seq, n_runs, final)

    print('Pulse Streamer has finished the sequence: '+str(pulser.hasFinished()))

if __name__=='__main__':
    

    #create Pulsestreamer
    """To set the IP-Address of the Pulsestreamer see
    https://www.swabianinstruments.com/static/documentation/PulseStreamer/sections/network.html
    """
    pulser = PulseStreamer(ip_hostname)
    
    print ("*********************************")
    print ("****** Set all outputs low ******")
    print ("*********************************")
    print ("")
    print ("Switch digital channel 0-7 to LOW and analog outputs to 0V")
    print ("")
    all_zero(pulser)

    six.moves.input("For next example press <ENTER>")

    print ("***********************************")
    print ("*** Streaming a rectangle pulse ***")
    print ("***********************************")
    print ("")
    print ("Endless rectangle pulse with 10 peridos of 256ns on all channels")
    print ("")
    pulser.reset()
    rectangular_pulse(pulser)
 
    six.moves.input("For next example press <ENTER>")

    print ("**************************************")
    print ("****** Set all outputs constant ******")
    print ("**************************************")
    print ("")
    print ("Switch digital channel 0,1 and 4 to HIGH and analog output 1 to 1.0V")
    print ("")
    pulser.reset()
    all_constant(pulser)

    six.moves.input("For next example press <ENTER>")

    print ("********************************************************")
    print ("*** Streaming a random pulse pattern on all channels ***")
    print ("********************************************************")
    print ("")
    print ("Random pulse pattern on digital channel 1-7 and analog channel 0-1")
    print ("")
    pulser.reset()
    random_sequence(pulser)

    six.moves.input("For next example press <ENTER>")

    print ("*************************************************************************")
    print ("*** Streaming random sequence and demonstrate user start-command ***")
    print ("*************************************************************************")
    print ("")
    print ("Random sequence - user starts streaming with <ENTER>")
    print ("")
    pulser.reset()
    random_sequence_software(pulser)

    six.moves.input("For next example press <ENTER>")

    print ("********************************************")
    print ("*** Streaming a merged digital sequence  ***")
    print ("********************************************")
    print ("")
    print ("Merging pulse pattern to one sequence on channel 0 to 7")
    print ("")
    pulser.reset()
    stream_merged_pulse_pattern(pulser)
