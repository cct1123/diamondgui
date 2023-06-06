from pyftdi import ftdi
# help(pyftdi)


# ftdidll.list_devices()
# ftdidll.show_devices()
# ftdidll.get_device("0")
# dd =  ftdidll.open(0, 0)
# ftdidll.is_connected()

# The instrument calculates the Exclusive OR of 
# all the bytes and compares with the last byte sent. If the results are the same, the instrument 
# sends 0x55, otherwise it sends 0xAB.
ERROR_BYTE = b'\x55'
MATCH_BYTE = b'\xAB'

INT32BIT = int(4294967296) # int(2**32)
FLOAT32BIT = 4294967296.0

def print_bytestring(bytestring):
    bs = ""
    for bbb in bytestring:
        bs += "0x{:02X} ".format(bbb)
    print(bs)

def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + int(b)
    return result

def int_to_bytes(value, length):
    result = []
    for i in range(0, length):
        result.append(value >> (i * 8) & 0xff)
    result.reverse()
    return result

def freq_to_bytes(freq):
    
    """
    convert frequency in GHz to 5-byte string
    freq: <256 GHz
    BYTE1: Integer portion of the output frequency in GHz. 
    BYTE2: Most significant byte of the 32 bit binary fraction of the output frequency in GHz 
    BYTE3: Next significant byte of the 32 bit binary fraction. 
    BYTE4: Next significant byte of the 32 bit binary fraction. 
    BYTE5: Least significant byte of the 32 bit binary fraction. 
    """
    freq_integer = freq // 1
    freq_fraction = freq % 1
    byte1 = int(freq_integer).to_bytes(1, "big")
    freq_fraction_int = min(int(freq_fraction * INT32BIT+0.5), INT32BIT-1)
    byte2345 = freq_fraction_int.to_bytes(4, "big")
    byte12345 = byte1+byte2345 # only for python3
    print(f"Input Freq: {freq} GHz, Output Bytes: {' '.join([hex(bb) for bb in byte12345])}")
    return byte12345

def bytes_to_freq(bytestring):
    
    """
    convert bytestring to frequency in GHz
    """
    freq_integer = int(bytestring[0])
    # freq_integer = int.from_bytes(bytestring[0], byteorder='big')

    # freq_fraction = int(bytestring[1:])/float(INT32BIT)
    freq_fraction = bytes_to_int(bytestring[1:])/FLOAT32BIT
    # freq_fraction = int.from_bytes(bytestring[1:], byteorder='big')/float(INT32BIT)
    return (freq_integer+freq_fraction)

def dwell_to_bytes(dewlltime):
    """
    convert step dwell time [ns] to 2-byte strings, 
    The dwell time is given by the binary number represented by the 2 bytes multiplied by 4ns,
    for example, 8ns dwell time is output as b"\x00\x02" 
    The minimum step dwell time is 4nS and would be represented by 2 bytes: 0x00, and 0x01. 
    The maximum step dwell time is 262.14uS, and is set by sending 2 bytes, 0xFF, 0xFF.
    """
    return int(dewlltime/4+0.5).to_bytes(2, "big")

def xor_bytes(bytestring):
    """
    calculate the XOR of all the bytes in a byte-string, 
    for example, this method returns b"\x06^\x46^\x09" 
    for b"\x06\x46\x09' where ^ is XOR operation
    """
    xor_all = bytestring[0]
    for bb in bytestring[1:len(bytestring)]:
        xor_all = xor_all ^ bb
    xorall_out = xor_all.to_bytes(1, 'big')
    print(f"XORall of {bytestring} is {xorall_out}")
    return xorall_out

class Synthesizer():
    "provide python control class for VDI MW Synthesizer"
    def __init__(self, url):
        # self.ftdidll = ftdi.Ftdi(url)
        pass
    def send_command(self, command):
        byte_num_written = self.ftdidll.write_data(command)

        if byte_num_written == len(command):
            print(f"Command '{print_bytestring(command)}' sent without loss!")
            # self.receive_cw_frequency_command()
            return True
        else:
            print(f"Command '{print_bytestring(command)}' sent with loss!")
            # print("Try to send the command again")
            # self.send_cw_frequency_command(freq)
            return False  

    def receive_command(self):
        data_receive = self.ftdidll.read_data()
        error_byte = data_receive[0]
        if error_byte == ERROR_BYTE:
            print("Error(s) occured")
            raise " "
        elif error_byte == MATCH_BYTE:
            print("Command Sent without error.")
            print(f"Data Received : '{print(data_receive)}'")
            data_receive.pop(0)
            return data_receive
        return None

    def send_cw_frequency_command(self, freq):
        """
        Send: 
        BYTE1: The number of bytes to follow excluding the last byte. 
        BYTE2: CW frequency command, 0x46. 
        BYTE3: Integer portion of the output frequency in GHz. 
        BYTE4: Most significant byte of the 32 bit binary fraction of the output frequency in GHz 
        BYTE5: Next significant byte of the 32 bit binary fraction. 
        BYTE6: Next significant byte of the 32 bit binary fraction. 
        BYTE7: Least significant byte of the 32 bit binary fraction. 
        BYTE8: Exclusive OR result of all the previous bytes. 

        """
        data_send = b"\x06\x46"+freq_to_bytes(freq)
        data_send += xor_bytes(data_send)
        return self.send_command(data_send)    

    def receive_cw_frequency_command(self):
        """
        Receive: 
        BYTE1: Error byte. 
        BYTE2: Integer portion of the actual output frequency in GHz. 
        BYTE3: Most significant byte of the 32 bit binary fraction of the actual output frequency in GHz 
        BYTE4: Next significant byte of the 32 bit binary fraction. 
        BYTE5: Next significant byte of the 32 bit binary fraction. 
        BYTE6: Least significant byte of the 32 bit binary fraction. 
        """
        data_receive = self.ftdidll.read_data()
        error_byte = data_receive[0]
        if error_byte == ERROR_BYTE:
            print("Error(s) occured")
            raise " "
        elif error_byte == MATCH_BYTE:
            print("Command Sent without error.")
            freq_return = bytes_to_freq(data_receive[1:])
            return error_byte, freq_return
        return None, None

    def send_simple_sweep_command(self,
        freq_start:float, 
        freq_stop:float, 
        step_rise:int, 
        step_fall:int, 
        stepdwell_rise:float, 
        stepdwell_fall:float, 
        dwell_low:int,
        dwell_high:int
        ):
        '''
        Send: 
        BYTE1: The number of bytes to follow excluding the last byte. 
        BYTE2: Simple sweep frequency command, 0x73. 
        BYTE3: Designator of which settings will follow. 
        BYTE4: Integer portion of the output start frequency in GHz. 
        BYTE5: Most significant byte of the 32 bit binary fraction of the output start frequency in GHz 
        BYTE6: Next significant byte of the 32 bit binary fraction 
        BYTE7: Next significant byte of the 32 bit binary fraction. 
        BYTE8: Least significant byte of the 32 bit binary fraction. 
        BYTE9: Integer portion of the output stop frequency in GHz. 
        BYTE10: Most significant byte of the 32 bit binary fraction of the output stop frequency in GHz 
        BYTE11: Next significant byte of the 32 bit binary fraction. 
        BYTE12: Next significant byte of the 32 bit binary fraction. 
        BYTE13: Least significant byte of the 32 bit binary fraction. 
        BYTE14: Integer portion of the rising step size in GHz. 
        BYTE15: Most significant byte of the 32 bit binary fraction of the rising step size in GHz 
        BYTE16: Next significant byte of the 32 bit binary fraction. 
        BYTE17: Next significant byte of the 32 bit binary fraction. 
        BYTE18: Least significant byte of the 32 bit binary fraction. 
        BYTE19: Integer portion of the falling step size in GHz. 
        BYTE20: Most significant byte of the 32 bit binary fraction of the falling step size in GHz 
        BYTE21: Next significant byte of the 32 bit binary fraction. 
        BYTE22: Next significant byte of the 32 bit binary fraction. 
        BYTE23: Least significant byte of the 32 bit binary fraction. 
        BYTE24: Most significant byte of the 16 bit rising step dwell time. 
        BYTE25: Least significant byte of the 16 bit rising step dwell time. 
        BYTE26: Most significant byte of the 16 bit falling step dwell time. 
        BYTE27: Least significant byte of the 16 bit falling step dwell time. 
        BYTE28: Dwell low setting. 
        BYTE29: Dwell high setting. 
        BYTE30: Exclusive OR result of all the previous bytes.
        '''
        data_send = b"\x1C\x73\xFF"
        # data_send = b"\x1C\x73\x0A"
        data_send += freq_to_bytes(freq_start)
        data_send += freq_to_bytes(freq_stop)
        # min step size is 12.10719347 Hz
        data_send += freq_to_bytes(step_rise)
        data_send += freq_to_bytes(step_fall)
        data_send += dwell_to_bytes(stepdwell_rise)
        data_send += dwell_to_bytes(stepdwell_fall)
        data_send += int(dwell_low).to_bytes(1, 'big')
        data_send += int(dwell_high).to_bytes(1, 'big')
        # print(type(data_send))
        # print(type(xor_bytes(data_send)))
        data_send += xor_bytes(data_send)
        return self.send_command(data_send)

    def receive_simple_sweep_command(self):
        """
        Receive: 
        BYTE1: Error byte. 
        BYTE2: Integer portion of the actual output start frequency in GHz. 
        BYTE3: Most significant byte of the 32 bit binary fraction of the actual output start frequency in GHz 
        BYTE4: Next significant byte of the 32 bit binary fraction 
        BYTE5: Next significant byte of the 32 bit binary fraction. 
        BYTE6: Least significant byte of the 32 bit binary fraction. 

        BYTE7: Integer portion of the actual output stop frequency in GHz. 
        BYTE8: Most significant byte of the 32 bit binary fraction of the actual output stop frequency in GHz 
        BYTE9: Next significant byte of the 32 bit binary fraction. 
        BYTE10: Next significant byte of the 32 bit binary fraction. 
        BYTE11: Least significant byte of the 32 bit binary fraction. 
        BYTE12: Integer portion of the actual rising step size in GHz. 

        BYTE13: Most significant byte of the 32 bit binary fraction of the actual rising step size in GHz 
        BYTE14: Next significant byte of the 32 bit binary fraction. 
        BYTE15: Next significant byte of the 32 bit binary fraction. 
        BYTE16: Least significant byte of the 32 bit binary fraction. 
        BYTE17: Integer portion of the actual falling step size in GHz. 

        BYTE18: Most significant byte of the 32 bit binary fraction of the actual falling step size in GHz 
        BYTE19: Next significant byte of the 32 bit binary fraction. 
        BYTE20: Next significant byte of the 32 bit binary fraction. 
        BYTE21: Least significant byte of the 32 bit binary fraction. 
        """
        data_rec = self.receive_command() # the BYTE 1 is handled here
        freq_start = bytes_to_freq(data_rec[:5]) # in GHz
        freq_stoop = bytes_to_freq(data_rec[5:10])
        step_rise = bytes_to_freq(data_rec[10:15])
        step_fall = bytes_to_freq(data_rec[15:])
        return freq_start, freq_stoop, step_rise, step_fall

    def send_sweep_command(self, 
        freq_start:float, 
        freq_stop:float, 
        step_rise:int, 
        step_fall:int, 
        stepdwell_rise:float, 
        stepdwell_fall:float, 
        dwell_low:int,
        dwell_high:int
        ):
        '''
        same as simple sweep command, but 
        t the minimum step size changes based on the output frequency,
        '''
        data_send = b"\x1C\x53\xFF"
        # data_send = b"\x1C\x73\x0A"
        data_send += freq_to_bytes(freq_start)
        data_send += freq_to_bytes(freq_stop)
        # min step size is 12.10719347 Hz
        data_send += freq_to_bytes(step_rise)
        data_send += freq_to_bytes(step_fall)
        data_send += dwell_to_bytes(stepdwell_rise)
        data_send += dwell_to_bytes(stepdwell_fall)
        data_send += int(dwell_low).to_bytes(1, 'big')
        data_send += int(dwell_high).to_bytes(1, 'big')
        data_send += xor_bytes(data_send)
        return self.send_command(data_send)

    def receive_sweep_command(self):
        return self.receive_simple_sweep_command()

    def _send_get_min_step_size_command(self, freq_start_list, freq_stop_list):
        '''
        get the minimum step size if 'sweep' command is used
        Send: 
        BYTE1: The number of bytes to be returned over the USB by this command. 
        BYTE2: Get Minimum Step Size command, 0x6d. 

        BYTE3: Integer portion of the output start frequency in GHz. 
        BYTE4: Most significant byte of the 32 bit binary fraction of the output start frequency in GHz 
        BYTE5: Next significant byte of the 32 bit binary fraction 
        BYTE6: Next significant byte of the 32 bit binary fraction. 
        BYTE7: Least significant byte of the 32 bit binary fraction. 

        BYTE8: Integer portion of the output stop frequency in GHz. 
        BYTE9: Most significant byte of the 32 bit binary fraction of the output stop frequency in GHz 
        BYTE10: Next significant byte of the 32 bit binary fraction. 
        BYTE11: Next significant byte of the 32 bit binary fraction. 
        BYTE12: Least significant byte of the 32 bit binary fraction. 

        BYTE13...: Start and stop frequencies in groups of 10 bytes for other return minimum step sizes.. 
        LASTBYTE: Exclusive OR result of all the previous bytes. 
        '''
        num_returnbytes = len(freq_start_list)
        data_send = num_returnbytes.to_bytes(1, 'big') + b'\x6D'
        for fstart, fstop, in zip(freq_start_list, freq_stop_list):
            data_send += freq_to_bytes(fstart)
            data_send += freq_to_bytes(fstop)
        data_send += xor_bytes(data_send)
        # print_bytestring(data_send)
        return self.send_command(data_send)

    def _receive_get_min_step_size_command(self):
        '''
        Receive: 
        BYTE1: Error byte. 
        BYTE2..: Least significant byte of the 32 bit binary fraction of the minimum step size in GHz for each 
        group of 10 bytes sent. 
        '''     
        data_return = self.receive_command()
        out = []
        for fb in data_return:
            out.append(fb/FLOAT32BIT * 1E9)
        return out


    def reset_trigger(self):
        self.send_command(b"\x01\x52\x53")
        return self.receive_command()
    
    def sweep_direction(self, updown):
        '''
        change the sweep direction, up=1, down=0
        '''
        if updown == 1:
            # change the sweep direction to up
            self.send_command(b"\x03\xA6\x34\x01\x6E")
        elif updown == 0:
            # change the sweep direction to down
            self.send_command(b"\x03\xA6\x34\x00\x91")
        return self.receive_command()
    
    def sweep_pause(self, pause):
        '''
        to pause the sweep, 
        pause: True/False
        '''
        if pause:
            # the sweep will be paused
            self.send_command(b"\x03\xA6\x5F\x01\x05")
        elif not pause:
            # the sweep will be continued
            self.send_command(b"\x03\xA6\x5F\x00\xFA")
        return self.receive_command()

    def get_min_step_size(self, freq_start_list, freq_stop_list):
        self._send_get_min_step_size_command(freq_start_list, freq_stop_list)
        return self._receive_get_min_step_size_command()

    def boot_up_sequence(self, boot_up_commands):
        '''
        The initial settings when the synthesizer is turned on can be changed with this command. Any 
        sequence of other commands can be applied to the boot up sequence by preceding those 
        commands with this command. There are a limited number of lifetime cycles to the flash 
        memory of 1,000,000 cycles, so it is not recommended to use this command in program loops. 
        The first byte is the most significant byte of the number of bytes to be used in the boot up 
        sequence. The next byte is the command, 0x42, and the third byte is the least significant byte of 
        the number of bytes used in the boot up sequence. 
        Send: 
        BYTE1: Most significant byte of the 16 bit number used to represent the number of bytes to be used 
        during the boot up sequence. 
        BYTE2: Boot up Sequence command, 0x42. 
        BYTE3: Least significant byte of the 16 bit number used to represent the number of bytes to be used 
        during the boot up sequence. 
        BYTE4…: Boot up commands for the next bytes. 
        LASTBYTE: Exclusive OR result of all the previous bytes. 
        Receive: 
        BYTE1: Error byte. 

        input:
            boot_up_commands: list of boot up commands
                              for example, to set synthesizer to 8GHz automatically after power up.
                              boot_up_commands = [b"\x06\x46\x08\x00\x00\x00\x00\x48"]
        return: 
            whether the commands are sent without loss
        '''
        
        commands =b""
        for buc in boot_up_commands:
            commands += buc
        num_bytes_send = len(commands)
        nbsb = num_bytes_send.to_bytes(2, "big")
        data_send = nbsb[0] + b"\x42" + nbsb[1]
        data_send += commands
        data_send += xor_bytes(data_send)
        return self.receive_command()

    def reboot(self):
        '''
        The synthesizer will return an error byte if there is an error, but otherwise will not return a byte. 
        It may be worthwhile to use FT_purge to clear the transmit buffer after a reboot.
        '''
        self.send_command(b'\x01\x88\x89')
        data_receive = self.ftdidll.read_data()
        if len(data_receive) > 0:
            print("Error ocurred when trying to reboot!")
        else:
            print("MW Synthesizer Rebooted!")
        self.ftdidll.purge_buffers() # clear both the tx and rx buffers


if __name__ == "__main__":
    mwsyn = Synthesizer(url="fdsfdsf")
    # mwsyn.send_cw_frequency_command(8.9999999999)
    # print(mwsyn.send_simple_sweep_command(8, 20, 1e-6, 10e-6, 1.99e3, 4, 0, 0))
    mwsyn.send_get_min_step_size_command([8, 9], [20, 10])