"""
Control class for pulse generation using Swabian pulse streamer

Reference: 
    [1] examples in 'pulsestreamer' python package
    [2] 'pi3diamond' control software in Sen Yang group
    [3] Evan Villafranca's 'pulses.py' script

Author: ChunTung Cheung 
Email: ctcheung1123@gmail.com
Created:  2023-01-11
Modified: 2023-04-02
"""



from pulsestreamer import findPulseStreamers
from pulsestreamer import PulseStreamer
#import enum types 
from pulsestreamer import TriggerStart, TriggerRearm
#import class Sequence and OutputState for advanced sequence building
from pulsestreamer import Sequence, OutputState

CHANNEL_MAP = {
    'ch0':0,'ch1':1,'ch2':2,'ch3':3,'ch4':4,'ch5':5,'ch6':6,'ch7':7,'ch8':8,
    '0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,
    0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:7,8:8,
}
import numpy as np
HIGH=1
LOW=0
INF = np.iinfo(np.int64).max

class PulseGenerator(PulseStreamer):

    def __init__(self, ip="", chmap=CHANNEL_MAP):
        if ip == "":
            devices = findPulseStreamers()
            # DHCP is activated in factory settings
            if devices !=[]:
                print("Detected Pulse Streamer 8/2: ")
                print(devices)
                print("------------------------------------------------------\n")
                #Connect to the first discovered Pulse Streamer
                ip = devices[0][0]
            else:
                # if discovery failed try to connect by the default hostname
                # IP address of the pulse streamer (default hostname is 'pulsestreamer')
                print("No Pulse Streamer found")
                ip = 'pulsestreamer'
        super().__init__(ip)
        self.chmap = chmap
        self.seq = Sequence()
        self.chmap.update(CHANNEL_MAP)

    def setTrigger(self, start=TriggerStart.IMMEDIATE, rearm=TriggerRearm.MANUAL):
        #Default: Start the sequence after the upload and disable the retrigger-function
        super().setTrigger(start=start, rearm=rearm)
        
    def stream(self, n_runs=1, state_i=OutputState.ZERO(), state_f=OutputState.ZERO()):
        #run the sequence 
        #n_runs = 'INFIITE' # repeat the sequence all the time

        # #reset the device - all outputs 0V
        # super().reset()

        #set constant state of the device
        super().constant(state_i) #all outputs 0V

        super().stream(self.seq, n_runs, state_f)

    def reset(self):
        #reset system and start next sequence
        input("\nPress ENTER to reset system and start delay-compensated sequence")
        super().reset()

    def setDigital(self, ch, pulse_patt):
        self.seq.setDigital(self.chmap[ch], pulse_patt)
        # super().setDigital(self.chmap[ch], pulse_patt)

    def setAnalog(self, ch, pulse_patt):
        self.seq.setAnalog(self.chmap[ch], pulse_patt)
        # super().setAnalog(self.chmap[ch], pulse_patt)
    
    def plotSeq(self):
        print(self.seq.getData())
        print("\nThe channel pulse pattern are shown in a Pop-Up window. To proceed with streaming the sequence, please close the sequence plot.")
        self.seq.plot()

    def seqTranslator(self, seq_tbased):
        '''
        translate time-based sequence to channel-based sequence
        for example we translate
            seq_tbased = [
                            (["laser"], 300), 
                            ([], 300),
                            ([], 300),
                            (["mw_A"], 300), 
                            (["mw_B", "laser"], 300), 
                            (["laser"], 300)
                         ]
        into
            seq_chbased = {
                        'laser': [(300, 1), (300, 0), (300, 0), (300, 0), (300, 1), (300, 1)],
                        'mw_B': [(300, 0), (300, 0), (300, 0), (300, 0), (300, 1), (300, 0)],
                        'mw_A': [(300, 0), (300, 0), (300, 0), (300, 1), (300, 0), (300, 0)]
                        } 
        '''
        total_time = 0
        ch_all = set()
        for (channels, duration) in seq_tbased:
            total_time += duration
            for ch in channels:
                ch_all.add(ch)
        assert total_time//1 == total_time, "Sequence Duration must be Int since base unit is 1ns"
        
        seq_chbased ={ch:[] for ch in ch_all}
        for (channels, duration) in seq_tbased:
            for ch in seq_chbased.keys():
                if ch in channels:
                    seq_chbased[ch] += [(duration, HIGH)]
                else: 
                    seq_chbased[ch] += [(duration, LOW)]

        for (ch, seq) in seq_chbased.items():
            self.setDigital(ch, seq)

        return total_time, seq_chbased
