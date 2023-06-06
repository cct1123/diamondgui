"""
This file shows how to run the Pulse Streamer 8/2 without making use of the high-level Python-wrappers.
You will communicate with and access the device by directly making use of the JSON-RPC library.
For advanced application and convenient use, we recommend to have a look at the files
<2_SimplePulses.py> and <3_Tutorial.py> as well as the full documentation of the Pulse Streamer 8/2
https://www.swabianinstruments.com/static/documentation/PulseStreamer/index.html

Before you can run this example, you need to install "pulsestreamer" client package

  > pip install pulsestreamer

"""
import sys
# we use the tinyrpc package to connect to the JSON-RPC server

try:
    import pulsestreamer
except ImportError:
    # Package was not installed.
    # Here we add path to "pulsestreamer" folder manually
    import sys
    import os.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from tinyrpc import RPCClient
    from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
    from tinyrpc.transports.http import HttpPostClientTransport        
except Exception as e:
    print(str(e))
    print (
"""
Failed to import JSON-RPC library. Ensure that you have it installed by typing
> pip install tinyrpc or pip install tinyrpc --upgrade (latest version supports Python3)
> pip install gevent-websocket
in your terminal.
""")
    sys.exit(1)

# binary and base64 conversion
import struct
import base64

import numpy as np

from pulsestreamer.enums import TriggerStart, TriggerRearm


def get_random_seq(min_len=0, max_len=1024, n_pulses=1000):
    """
    Generate a sequence of random sequence steps on the digital
    channels 1-7 and the two analog channels.
    Sequence steps are represented as tuples in the form (time, [1,3], analog0, analog1),
    where time is an integer in ns (clock ticks), [1,3] is a list numbering the channels
    which should be high the last two numbers specify the analog outputs in 16bit DAC-integer values.
    
    Digital channel 0 is used as a trigger.    
    """
    t = np.random.uniform(min_len, max_len, n_pulses).astype(int)
    seq = [ (8, 1, 0, 0) ] # 8 ns trigger pulse on channel 0
    for i, ti in enumerate(t):
        state = i%2
        seq += [ (ti, 0xfe*state, 0x7fff*state, -0x7fff*state) ]
    return seq

def enc(seq):
    """
    Convert a human readable python sequence to a base64 encoded string
    """
    s = b''
    for pulse in seq:
        s+=struct.pack('>IBhh', *pulse)
    return base64.b64encode(s)
  
if __name__ == '__main__':

    #create Pulsestreamer
    """To set the IP-Address of the Pulsestreamer see
    https://www.swabianinstruments.com/static/documentation/PulseStreamer/sections/network.html
    """
    ip_hostname ='pulsestreamer' # edit this line to use a specific Pulse Streamer IP address
    url = 'http://'+ip_hostname+':8050/json-rpc'
    client = RPCClient(JSONRPCProtocol(), HttpPostClientTransport(url, timeout=20))

    pulser = client.get_proxy()

    #reset Pulsestreamer
    pulser.reset()
    print('Reset Pulsestreamer')

    #get random sequence
    seq = get_random_seq(n_pulses=1000)

    # example how to set values
    n_runs = -1 #run infinite pulse
    final = (0,0x00,0x7fff,0x7fff) #set final state

    #set trigger mode
    start = TriggerStart.IMMEDIATE.value
    rearm = TriggerRearm.MANUAL.value
    pulser.setTrigger(start=start, rearm=rearm)
    print('Set Triggermode')

    #stream pulse
    pulser.stream(enc(seq).decode("utf-8"), n_runs, final)
    print('Load sequence')
    print('Pulse Streamer is streaming: '+str(pulser.isStreaming()))