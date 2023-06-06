"""
This script uses the device detection to test connctions to devices in the network
and connects connects to the first discovered Pulse Streamer 8/2. 
During connection and with some rpc called afterwards it prints the following hardware/software information about the Pulse Streamer:
 - Firmware version (printed by default when connection isestablished)
 - Version of the client software (printed by default when connection isestablished)
 - MAC address of the ethernet interface 
 - Serial number of the Pulse Streamer

Before you can run this example, you need to install "pulsestreamer" client package

  > pip install pulsestreamer

"""

#import JSON-RPC Pulse Streamer wrapper class, to use Google-RPC import from pulsestreamer.grpc
from pulsestreamer import PulseStreamer

#import the device detection
from pulsestreamer import findPulseStreamers

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
    ip = 'pulsestreamer';

#connect to the pulse streamer
pulser = PulseStreamer(ip)

# Print serial number and FPGA-ID
print('Serial: ' + pulser.getSerial())
print('FPGA ID: ' + pulser.getFPGAID())