"""
This script provides a short example version of a class SyncPulseStreamer, which allows to most widely treat two synchronized 
Pulse Streamer 8/2 as one Pulse Streamer object without any modifications to the internal hardware. 
Therefore one Pulse Streamer master generates the clock signal and trigger for one Pulse Streamer slave.

The features of the resulting Pulse Streamer object can be described as follows:
- 14 digital channels (6 of the master, 8 of the slave)
- 4 analog channels (2 in each case master/slave)  

Prearrangement:
The only necessary preparation is that digital channel 6 of the master must be connected to the external clock input of the slave 
as well as digital channel 7 of the master must be connected to the trigger input of the slave. 
To avoid race conditions between the trigger and trigger-sampling clock-edge, we recommend using cables of equal length.

Usage:
The Pulse Streamer synchronization wrapper offers the same API-structure as the original Pulse Streamer client if possible. When it comes 
to sequence generation, unlike the original method createSequence(), the equivalent method of the sync-wrapper returns two sequence objects, 
one for the Pulse Streamer master and one for the Pulse Streamer slave. You can set the digital and analog channels of both sequences independently. 
Setting Channel 6 (clock signal) of the master will be ignored, and channel 7 (trigger) of the master will be overwritten by the stream method).
If you want to use a parameter n_runs>1 with the stream function, you should ensure that the two sequences are of equal duration.

Limitations:
1) The slave is delayed by a constant time offset of ~70ns (internal + cable). To compensate for the delay of the Pulse Streamer slave, you can add 
an empty pulse as a first pulse to each channel of the master sequence. This slightly limits the potentialities of our tool for sequence generation. For more details, please have a look at 
the full documentation of the PUlse Streamer 8/2 https://www.swabianinstruments.com/static/documentation/PulseStreamer/index.html

2) If you use the synchronized Pulse Streamer with a fast external trigger, it is possible that the Pulse Streamer master is ready for retriggering and 
the slave is not and vice versa. Therefore, you should always poll the method hasFinished() before retriggering the Pulse Streamer with the external trigger.

3) If you stream a second pulse pattern into an already running sequence, you previously should set the Pulse Streamer to a constant state by using the methods 
constant(...) or reset(). Otherwise, the new sequence of the Pulse Streamer slave might already be triggered by the still running stream of the Pulse Streamer master.

You can either communicate with the hardware via JSON-RPC (recommended) or Google-RPC. Before you run this more sophisticated example, we recommend trying the 
previous examples <2_SimplePulses.py> and <3_Tutorial.py> as well as to have an extensive look at the full documentation of the Pulse Streamer 8/2 
https://www.swabianinstruments.com/static/documentation/PulseStreamer/index.html

Before you can run this example, you need to install "pulsestreamer" client package

  > pip install pulsestreamer

"""

# imports used by SyncPulseStreamer class
from pulsestreamer import *


class SyncPulseStreamer():

    def __init__(self, ip_master='', ip_slave=''):

        self.ps_master=PulseStreamer(ip_master)
        self.ps_slave=PulseStreamer(ip_slave)
        assert self.ps_master.getFirmwareVersion() == self.ps_slave.getFirmwareVersion(), "The firmware version number of PulseStreamer master differs from the firmware version number of PulseStreamer slave. We recommend using the latest firmware version on both devices."
        assert self.reset()==0

    def reset(self):
        ret=0
        ret=ret or self.ps_slave.reset()
        ret=ret or self.ps_master.reset()
        #configure Pulse Streamer master
        ret=ret or self.ps_master.setSquareWave125MHz([6])
        #configure Pulse Streamer slave
        ret=ret or self.ps_slave.selectClock(ClockSource.EXT_125MHZ)
        ret=ret or self.ps_slave.setTrigger(start=TriggerStart.HARDWARE_RISING, rearm=TriggerRearm.MANUAL)
        return ret

    def constant(self, state_master=OutputState.ZERO(), state_slave=OutputState.ZERO()):
        self.ps_slave.constant(state_slave)
        self.ps_master.constant(state_master)

    def createOutputState(self, digi, A0=0.0, A1=0.0, A2=0.0, A3=0.0):
        chan_master=[]
        chan_slave=[]
        for chan in digi:
            if chan >5:
                chan.slave.append(chan-6)
            else:
                chan_master.append(chan)
        output_master=self.ps_master.createOutputState(digi=chan_master,A0=A0, A1=A1)
        output_slave=self.ps_slave.createOutputState(digi=chan_master,A0=A2, A1=A3)
        return output_master, output_slave

    def createSequence(self): #ToDo parameter for safe communication/sequence creation
        seq_master = self.ps_master.createSequence()
        seq_slave = self.ps_slave.createSequence()
        return seq_master, seq_slave

    def stream(self, seq_master, seq_slave, n_runs, final_master=OutputState.ZERO(), final_slave=OutputState.ZERO()):
        #if you use sequence object, duration is checked and trigger for Pulse Streamer slave is set automaticlly
        if (isinstance(seq_master, Sequence) and isinstance(seq_slave, Sequence)): 
            # shift trigger pulse by two nanoseconds to make sure there is no race condition between trigger and trigger-sampling clock-edge
            # adjusted for cables of equal length for clock and trigger
            seq_master.setDigital(7, [(2,0),(4,1),(2,0)]) 
            duration_master=seq_master.getDuration()
            duration_slave=seq_slave.getDuration()
            if (duration_master != duration_slave):
                print("WARNING: Sequence duration of PulseStreamer slave (" +str(duration_slave) +"ns) differs from PulseStreamer master (" +str(duration_master) +"ns)")
        self.ps_slave.stream(seq_slave, n_runs, final_slave)
        self.ps_master.stream(seq_master, n_runs, final_master)

    def isStreaming(self):
        return (self.ps_master.isStreaming() or self.ps_slave.isStreaming())

    def hasFinished(self):
        return (self.ps_master.hasFinished() and self.ps_slave.hasFinished())
    
    def hasSequence(self):
        return (self.ps_master.hasSequence() or self.ps_slave.hasSequence())

    def startNow(self):
        #To use the software retrigger the Pulse Streamer slave has to be rearmed (manual rearm mode)
        self.ps_slave.rearm()
        return self.ps_master.startNow()

    def forceFinal(self):
        ret=0
        ret=ret or self.ps_slave.forceFinal()
        ret=ret or self.ps_master.forceFinal()
        return ret 

    def selectClock(self, source):
        return self.ps_master.selectClock(source)

    def getClock(self):
        return self.ps_master.getClock()

    def getFirmwareVersion(self):
        return self.ps_master.getFirmwareVersion()

    def getSerial(self):
        return {'serial_master':self.ps_master.getSerial(), 'serial_slave':self.ps_slave.getSerial()} 

    def getFPGAID(self):
        return {'fpgaid_master':self.ps_master.getFPGAID(), 'fpgaid_slave':self.ps_slave.getFPGAID()} 

    def setTrigger(self, start, rearm=TriggerRearm.AUTO):
        #If you use the external trigger, the Pulse Streamer slave is set to automatic rearm mode
        if (start != TriggerStart.IMMEDIATE and start != TriggerStart.SOFTWARE):
            self.ps_slave.setTrigger(start=TriggerStart.HARDWARE_RISING, rearm=TriggerRearm.AUTO)
        return self.ps_master.setTrigger(start, rearm)

    def getTriggerStart(self):
        return self.ps_master.getTriggerStart()
    
    def getTriggerRearm(self):
        return self.ps_master.getTriggerRearm()

    def rearm(self):
        return self.ps_master.rearm()

    def getUnderflow(self):
        return (self.ps_master.getUnderflow() or self.ps_slave.getUnderflow())


if __name__=='__main__':
    def get_answer(question, options):
        choice=int(input(question + " Choose one out of "+str(options)))
        while choice not in options:
            print(question)
            choice = int(input("Choose one out of "+str(options)))
        return choice

    #choose devices and connect to Pulse Streamer
    pulser_list=findPulseStreamers()
    if (pulser_list==[]):
        assert False, "No Pulse Streamer 8/2 found"
    for i, ps in enumerate(pulser_list):
        print("Device " +str(i) +"\nProperties: " + str(ps))
        print("----------------------------------------------------")

    options=list(range(len(pulser_list)))
    choice_master = get_answer("Which device do you want to set to Pulse Streamer master?", options)
    ip_master=pulser_list[choice_master][0]
    choice_slave=get_answer("Which device do you want to set to Pulse Streamer slave?", options)
    ip_slave=pulser_list[choice_slave][0]


    #create synchronized Pulse Streamer object
    pulser=SyncPulseStreamer(ip_master, ip_slave)

    #create Sequence
    seq_master, seq_slave = pulser.createSequence()
    seq_master.setDigital(0, [(8,1)]) # Trigger, HIGH during whole sequence
    seq_master.setDigital(1, [(320,1),(320,0)]) # Square wave
    seq_master.setDigital(2, [(80,1),(560,0)]) # short pulse of 80ns
    seq_master.setDigital(3, [(80,0),(80,1),(480,0)]) # short pulse shifted right by 80 ns
    seq_master.setDigital(4, [(160,0),(80,1),(400,0)]) # short pulse shifted right by 160 ns
    seq_master.setDigital(5, [(240,0),(80,1),(320,0)]) # short pulse shifted right by 240 ns

    print ("\nGenerated sequence pulse list for Pulse Streamer master:")
    print(seq_master.getData())
    print("\nThe channel pulse pattern are shown in a Pop-Up window. To proceed with creating the sequence for Pulse Streamer slave, please close the sequence plot.")
    seq_master.plot()

    seq_slave.setDigital(0, [(320,1),(320,0)]) # Square wave
    seq_slave.setDigital(1, [(80,1),(560,0)]) # short pulse of 80ns
    seq_slave.setDigital(2, [(80,0),(80,1),(480,0)]) # short pulse shifted right by 80 ns
    seq_slave.setDigital(3, [(160,0),(80,1),(400,0)]) # short pulse shifted right by 160 ns
    seq_slave.setDigital(4, [(240,0),(80,1),(320,0)]) # short pulse shifted right by 240 ns

    print ("\nGenerated sequence pulse list for Pulse Streamer slave:")
    print(seq_slave.getData())
    print("\nThe channel pulse pattern are shown in a Pop-Up window. To proceed with streaming the sequence, please close the sequence plot.")
    seq_slave.plot()
    
    #stream sequence
    pulser.stream(seq_master, seq_slave,-1)
    print ("\nOutput running with n_runs=INFINITE on synchornized Pulse Streamer (master/slave): " + str(pulser.isStreaming()))

    #reset system and start next sequence
    input("\nPress ENTER to reset system and start delay-compensated sequence")
    pulser.reset()

    #create sequence with delay compensation
    delay_compensation=70 #the exact value is device-dependent
    seq_master, seq_slave = pulser.createSequence()
    seq_master.setDigital(0, [(delay_compensation ,0),(8,1)]) # Trigger, HIGH during whole sequence
    seq_master.setDigital(1, [(delay_compensation ,0),(320,1),(320-delay_compensation,0)]) # Square wave
    seq_master.setDigital(2, [(delay_compensation ,0),(80,1),(560-delay_compensation,0)]) # short pulse of 80ns
    seq_master.setDigital(3, [(delay_compensation ,0),(80,0),(80,1),(480-delay_compensation,0)]) # short pulse shifted right by 80 ns
    seq_master.setDigital(4, [(delay_compensation ,0),(160,0),(80,1),(400-delay_compensation,0)]) # short pulse shifted right by 160 ns
    seq_master.setDigital(5, [(delay_compensation ,0),(240,0),(80,1),(320-delay_compensation,0)]) # short pulse shifted right by 240 ns

    print ("\nGenerated sequence pulse list for Pulse Streamer master:")
    print(seq_master.getData())
    print("\nThe channel pulse pattern are shown in a Pop-Up window. To proceed with creating the sequence for Pulse Streamer slave, please close the sequence plot.")
    seq_master.plot()

    seq_slave.setDigital(0, [(320,1),(320,0)]) # Square wave
    seq_slave.setDigital(1, [(80,1),(560,0)]) # short pulse of 80ns
    seq_slave.setDigital(2, [(80,0),(80,1),(480,0)]) # short pulse shifted right by 80 ns
    seq_slave.setDigital(3, [(160,0),(80,1),(400,0)]) # short pulse shifted right by 160 ns
    seq_slave.setDigital(4, [(240,0),(80,1),(320,0)]) # short pulse shifted right by 240 ns

    print ("\nGenerated sequence pulse list for Pulse Streamer slave:")
    print(seq_slave.getData())
    print("\nThe channel pulse pattern are shown in a Pop-Up window. To proceed with streaming the sequence, please close the sequence plot.")
    seq_slave.plot()
    
    #stream sequence
    pulser.stream(seq_master, seq_slave,-1)
    print ("\nOutput running with n_runs=INFINITE on synchornized Pulse Streamer (master/slave): " + str(pulser.isStreaming()))
    