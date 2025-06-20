# Control Mini-Circuits' PWR series power meters via USB
# Requirements:
#   1: Python.Net (pip install pythonnet)
#   2: Mini-Circuits' DLL API file (mcl_pm_NET45.dll)
#      https://www.minicircuits.com/softwaredownload/mcl_pm64_dll.zip
#      Note: - Windows may block the DLL file after download as a precaution
#            - Right-click on the file, select properties, click "Unblock" (if shown)

import clr # pythonnet
clr.AddReference('mcl_pm_NET45')    # Reference the DLL

from mcl_pm_NET45 import usb_pm
pwr = usb_pm()                      # Create an instance of the control class

Status = pwr.Open_Sensor()          # Connect the system (pass the serial number as an argument if required)

if Status[0] > 0:                   # The connection was successful

    ModelName = pwr.GetSensorModelName()
    SerialNo = pwr.GetSensorSN()
    print (ModelName, SerialNo)

    pwr.Freq = 1000                 # Set measurement frequency

    pwr.AvgCount = 16               # Set averaging count to 16
    pwr.AVG = 1                     # Enable averaging

    Power = pwr.ReadPower()         # Read power
    print (Power, "dBm")

    pwr.CloseSensor()               # Disconnect at the end of the program

else:
    print ("Could not connect.")
