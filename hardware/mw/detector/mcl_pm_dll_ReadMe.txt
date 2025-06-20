mcl_pm.dll - ActiveX COM Object for programmers

This DLL file can be used by programmers of Visual Basic,VC++,Delphi,C#,
LabView or any other program that recognize ActiveX DLL file.

mcl_pm.dll file should be located on system folder eg: "c:\windows\system32"
the file should be registered using regsvr32 windows program.

The DLL file include the following Functions:

1. Long Open_Sensor(Optional *string SN)  :

SN parameter is needed in case of using more than 1 Power Sensor.
SN is the Serial Number of the Power Sensor.

A replacement function "Open_AnySensor()" can be used In case of using only one Power Sensor.

The function return a Value
             0=Fail to open Sensor
             1=Success
             2=Object is already open 
             3=SN is not Available

2. float ReadPower()   - Return the power Value
3. int GetStatus()     - Return  1=Connect or  0=disconnect
4. void Close_Sensor()
5. string GetSensorSN() - Return the Sensor Serial Number
6. float GetDeviceTemperature(Optional TemperatureFormat As String) 
   TemperatureFormat - optional parameter : "F" for Fahrenheit "C" (Default) for Celsius
7. long Get_Available_SN_List(*string SN_List)
	SN_List return with List of all available Serial Numbers: [SN1] [SN2] ...

8. short SetOffsetValues(short NoOfPoints , double  FreqArray[] , float  LossArray[]) 
9. short GetOffsetValues(short NoOfPoints , double  FreqArray[] , float  LossArray[]) 

10.string GetSensorModelName() - Returns the part number of the connected power sensor
11.void SetFasterMode(*Short S_A) - sets the measurement mode of the power sensor between "low noise" and "fast sampling" modes
12.void SetRange(*Short Range) -  optimizes the power sensor measurement for the expected input power range
13.float ReadImmediatePower() - This function returns the sensor power measurement with a faster response but reduced accuracy compared to ReadPower 
14.float ReadVoltage() -Returns the raw voltage detected at the power sensor head
15.short Get_Status() -Checks whether the USB connection to the power sensor is still active
			Returns 0 - No connection,1 -USB connection to power sensor is active 
16.string GetUSBDeviceName() -This function is for advanced users to identify the USB device name of the power sensor for direct communication
17.string GetUSBDeviceHandle() -This function is for advanced users to identify the handle to USB of the power sensor for direct communication
18.short GetFirmwareInfo(short FirmwareID, string FirmwareRev,short FirmwareNo) -Returns the internal firmware version of the power sensor
19.short GetFirmwareVer(short FirmwareVer) -Returns the internal firmware version of the power sensor (This function is antiquated, GetFirmwareInfo should be used instead)
20.short Open_AnySensor() -Method to connect to a power sensor
21.void Init_PM() -Method to connect to a power sensor (compatible with early models)
22.void Close_Connection() - Method to disconnect from a power sensor (compatible with early models)


Functions related only to PWR-SEN-8P-RC Model ( peak power sensor ):

23.  short PeakPS_SetSampleTime( long ST )  Set the Sample Time in usec
       return 1 on success
24.  short PeakPS_SetTriggerMode(int TM )   Set the Trigger Mode
       set TM=0 for Free mode
       set TM=1 for Internal mode
       set TM=2 for External mode
      return 1 on success     
25.    long PeakPS_GetSampleTime() - get the Sample time in usec
26.    short PeakPS_GetTriggerMode() - get the trigger mode
           return 0 for free mode, 1 for internal and 2 for external
27.   float PeakPS_GetPeakPower()  - get the peak power of the sample time trace    
28.   float PeakPS_GetAvgPower() - get the AVG power of the sample time trace
29.   short PeakPS_GetPower( int NoOfPoints , float PowerArray() , float PeakPower , long ST , long DelayAfterTrigger ) - read the power array of the sample time trace
      ST = Sample Time in micro seconds
      DelayAfterTrigger = Delay After trigger in micro seconds 
      the function return the reading Number of points - NoOfPoints ( Array size )
      the Array of power - PowerArray()
      the PeakPower - the peak power of the array()
      return 1 if success
30.  short  Send_SCPI( *string SndSTR , *string RetSTR )  - Send SCPI command
      Send and recieve SCPI command/Query
      SndSTR - SCPI command or query to send
      RetSTR - the result return from the device
        

Functions related only to FCPM-6000RC Model:

31. short FC_SetAutoFreq( short AutoFreq )  Set the Frequency of the the CAL factor. 
     if AutoFreq=1  the cal factor frequency is set acording the Frequency reading.
     if AutoFreq=0 then the Frequency for the CAL factor is set by user defined ( property .Freq ).
32. short FC_GetAutoFreq() - return if AutoFreq is 1 (auto mode) or 0 (user defined).
33. short FC_SetRange( short Range )  Set the Frequency Range for the Frequency Counter module.
     Range=0 for Auto Range or any range from 1 to 4.
34. short FC_GetRequstedRange() - return the range requested.
35. short FC_GetRange() - return the Actual current frequency counter range.
36. short FC_SetSampleTime( short SampleTime )  Set the Sample Time for the Frequency Counter module.
     SampleTime in milli seconds can be from 100 to 3000. default is 1000 msec.
37. short FC_GetSampleTime() - return the Frequency counter -  SampleTime in milli seconds.
38.  double FC_ReadFreq () - return the last reqding of Frequency value in MHz.
39. short FC_GetRef() - return 1 for external ref detected or 0 for internal ref.



40.Ethernet Functions can be called while the devices are connected via the USB interface & only for PM model has Ethernet support
		
	a. short GetEthernet_CurrentConfig(short IP1, short IP2, short IP3, short IP4, short Mask1, short Mask2,
									_ short Mask3, short Mask4, short Gateway1, short Gateway2, short Gateway3, short Gateway4)
			returns the current static IP address, subnet mask and network gateway
		
        b. short GetEthernet_IPAddress (short b1, short b2, short b3, short b4)
			returns the current IP address of the connected power meter in a series of user defined variables (one per octet).
			
        c. short GetEthernet_MACAddress (short MAC1, short MAC2, short MAC3, short MAC4,short MAC5, short MAC6)
			returns the MAC (media access control) address, the physical address, of the connected power meter as a series of decimal values
					
        d. short GetEthernet_NetworkGateway(short b1, short b2, short b3, short b4)
			returns the IP address of the network gateway to which the power meter is currently connected
			
        e. short GetEthernet_PWD(String Pwd)
			returns the current password used by the power meter for HTTP/Telnet communication
			
        f. short GetEthernet_SubNetMask(short b1, short b2, short b3, short b4)
			This function returns the subnet mask used by the network gateway to which the power meter is currently connected
		
        g. short GetEthernet_TCPIPPort(short port)
			returns the TCP/IP port used by the power meter for HTTP communication.
		
        h. short GetEthernet_UseDHCP()
			return 0 - DHCP not in use 
			return 1 - DHCP in use
			
        i1. short GetEthernet_UsePWD()
			return 0 - Password not required
			return 1 - require a password for HTTP/Telnet communication

        i2. short GetEthernet_EnableEthernet()    // for supported models only
			return 0 - Ethernet is Disabled
			return 1 - Ethernet is Enabled
			
        j. short SaveEthernet_IPAddress(short b1, short b2, short b3, short b4)
			sets a static IP address to be used by the connected power meter
			
        k. short SaveEthernet_NetworkGateway(short b1, short b2, short b3, short b4)
			sets the IP address of the network gateway to which the power meter should connect
			
        l. short SaveEthernet_PWD(String Pwd)
			sets the password used by the power meter for HTTP/Telnet communication
			
        m. short SaveEthernet_SubnetMask(short b1, short b2, short b3, short b4)
			This function sets the subnet mask of the network to which the power meter should connect
			
        n. short SaveEthernet_TCPIPPort(short port)
			sets the TCP/IP port used by the power meter for HTTP communication
			
        o. short SaveEthernet_UseDHCP(short UseDHCP) 
			enables or disables DHCP (dynamic host control protocol)
			
        p. short SaveEthernet_UsePWD (short UsePwd)
			enables or disables the password requirement for HTTP/Telnet communication with the power meter
        
        Q. short SaveEthernet_EnableEthernet (short EnEthernet)  // for supported models only
			enables or disables Ethernet
			
41. short ResetDevice() - Reset and initialize the device without reset the CPU
42. short ResetCPU() - Rest the device CPU

The DLL file object has the following Properties:

Freq : the CAl Freq in MHz
AVG  : 1=ON 0=OFF
AvgCount: the No of Avg Count
Format_mW: if true the ReadPower result will be in mW
OffsetValue_Enable : 0= Disable ; 1=Enable Single Offset Value ;  2= Enable Offset Array values 
OffsetValue - Offset Single Value 

program Example in VB:

public pm1 As New MCL_PM.USB_PM  'this line recommended to be in a global module

pm1.Open_Sensor
pm1.Freq=1500
r=pm1.ReadPower
pm1.Close_Sensor     ' Recommended to close connection in the END of the program

Note: The Open_Sensor takes several sec,
      so, it is better to "Close_Sensor" only when the program is 
      closed.
 

program Example in Visual C++:

mcl_pm::USB_PM ^pm1 = gcnew mcl_pm::USB_PM();
short Status = 0;
System::String ^SN = "";
float ReadResult = 0;
Status = pm1->Open_Sensor(SN);
pm1->Freq = 3000;
ReadResult = pm1->ReadPower();
pm1->Close_Sensor();

      