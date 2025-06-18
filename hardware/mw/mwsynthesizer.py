"""
THIS WRAPPER IS NOT FINISHED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
This is a python wrapper to control the VDI microwave(MW) sythesizers
Here we use the package 'pyftdi' to communicate with the FTDI chips in synthesizers
Please refer to the VDI programming manual for more details about the commands.

Reference:
    [1] VDI Synthesizer Programming Manual (Version 4 Revised March 2014 ), https://vadiodes.com/en/resources/downloads

Author: ChunTung Cheung
Email: ctcheung1123@gmail.com
Created:  2022-12-06
Modified: 2025-01-17
"""

import time

# from pyftdi import ftdi
import serial  # import the pyserial package
import serial.tools.list_ports

INT32BIT = int(4294967296)  # int(2**32)
FLOAT32BIT = 4294967296.0
READSIZE_MAX = 256

# The instrument calculates the Exclusive OR of
# all the bytes and compares with the last byte sent. If the results are the same, the instrument
# sends 0x55, otherwise it sends 0xAB.
ERROR_BYTE = b"\xab"
MATCH_BYTE = b"\x55"

# some default commands of the MW synthesizer
REBOOT = b"\x01\x88\x89"
SWEEP_PAUSE = b"\x03\xa6\x5f\x01\x05"
SWEEP_CONTIN = b"\x03\xa6\x5f\x00\xfa"
SWEEP_UP = b"\x03\xa6\x34\x01\x6e"
SWEEP_DOWN = b"\x03\xa6\x34\x00\x91"
RESET_TRIGGER = b"\x01\x52\x53"


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
        result.append(value >> (i * 8) & 0xFF)
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
    freq_fraction_int = min(int(freq_fraction * INT32BIT + 0.5), INT32BIT - 1)
    byte2345 = freq_fraction_int.to_bytes(4, "big")
    byte12345 = byte1 + byte2345  # only for python3
    # print(f"Input Freq: {freq} GHz, Output Bytes: {' '.join([hex(bb) for bb in byte12345])}")
    return byte12345


def bytes_to_freq(bytestring):
    """
    convert bytestring to frequency in GHz
    """
    freq_integer = int(bytestring[0])
    # freq_integer = int.from_bytes(bytestring[0], byteorder='big')

    # freq_fraction = int(bytestring[1:])/float(INT32BIT)
    freq_fraction = bytes_to_int(bytestring[1:]) / FLOAT32BIT
    # freq_fraction = int.from_bytes(bytestring[1:], byteorder='big')/float(INT32BIT)
    return freq_integer + freq_fraction


def dwell_to_bytes(dewlltime):
    """
    convert step dwell time [ns] to 2-byte strings,
    The dwell time is given by the binary number represented by the 2 bytes multiplied by 4ns,
    for example, 8ns dwell time is output as b"\x00\x02"
    The minimum step dwell time is 4nS and would be represented by 2 bytes: 0x00, and 0x01.
    The maximum step dwell time is 262.14uS, and is set by sending 2 bytes, 0xFF, 0xFF.
    """
    return int(dewlltime / 4 + 0.5).to_bytes(2, "big")


def xor_bytes(bytestring):
    """
    calculate the XOR of all the bytes in a byte-string,
    for example, this method returns b"\x06^\x46^\x09"
    for b"\x06\x46\x09' where ^ is XOR operation
    """
    xor_all = bytestring[0]
    for bb in bytestring[1 : len(bytestring)]:
        xor_all = xor_all ^ bb
    xorall_out = xor_all.to_bytes(1, "big")
    # print(f"XORall of {bytestring} is {xorall_out}")
    return xorall_out


class Synthesizer:
    "provide python control class for VDI MW Synthesizer"

    # def __init__(self, ser="VDI200A", vidpid="0403:6001"):
    def __init__(self, ser, vidpid="auto", baudrate=9600, timeout=1, write_timeout=1):
        # TO DO (20221220): this initial function is not finished,  I have to waiting for the actual hardware to test the codes
        targetports = {}
        allports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(allports):
            if ser in hwid:
                targetports[hwid] = port
        if targetports == {}:
            print(
                f"No Serial Device with SN '{ser}' can be found. \nPlease Check the USB connection with the sythesizer!"
            )
        else:
            if vidpid == "auto":
                # if vidpid is not specified, always connect to the first device
                self.serialcom = serial.Serial(
                    list(targetports.values())[0],
                    baudrate=baudrate,
                    timeout=timeout,
                    write_timeout=write_timeout,
                )
            else:
                for kk in targetports.keys():
                    if vidpid in kk:
                        key = kk
                        break
                self.serialcom = serial.Serial(
                    targetports[key],
                    baudrate=baudrate,
                    timeout=timeout,
                    write_timeout=write_timeout,
                )

        if self.serialcom.is_open:
            print("VDI Sythesizer Serail Port Open")
        else:
            try:
                self.open()
            except Exception as excpt:
                print("Connection with the synthesizer's FTDI chip fails!")
                print(excpt)

    def open(self):
        if not self.serialcom.is_open:
            return self.serialcom.open()

    def close(self):
        if self.serialcom.is_open:
            return self.serialcom.close()

    def close_gracefully(self):
        try:
            self.purge()
        finally:
            # Close the serial connection properly
            if self.serialcom.is_open:
                self.serialcom.close()
                print("VDI Synthesizer Serial port closed.")

    def send_command(self, command):
        """
        To send bytes to the FTDI chip.
        Always read the return bytes before sending a new command,
        or purge the transmit buffer if the return bytes are not read
        """
        byte_num_written = self.serialcom.write(command)
        if byte_num_written == len(command):
            # print(type(command))
            # print(command)
            # print("Command sent without loss:")
            # print_bytestring(command)
            # self.receive_cw_frequency_command()
            return True
        else:
            # print("Command sent with loss:")
            # print_bytestring(command)
            self.serialcom.reset_input_buffer()  # clear the tx buffers
            self.serialcom.reset_output_buffer()  # clear the rx buffers
            # print("Please try to send the command again")
            return False

    def receive_command(self, size=READSIZE_MAX):
        data_receive = self.serialcom.read(size=size)
        error_byte = data_receive[0].to_bytes(1, "big")
        if error_byte == ERROR_BYTE:
            self.purge()  # clear the rx buffers
            raise Exception("Unknown Error(s) occured")
        elif error_byte == MATCH_BYTE:
            # print("Command Sent without error.")
            # print(f"Data Received : ")
            # print_bytestring(data_receive)
            return data_receive[1:]
        return None

    def cw_frequency(self, *args, **kargs):
        if self.send_command(self._cw_frequency_command(*args, **kargs)):
            return self._receive_cw_frequency_command()

    def simple_sweep(self, *args, **kargs):
        if self.send_command(self._simple_sweep_command(*args, **kargs)):
            return self._receive_simple_sweep_command()

    def sweep(self, *args, **kargs):
        if self.send_command(self._sweep_command(*args, **kargs)):
            return self._receive_sweep_command()

    def reset_trigger(self):
        # reset the frequency at the low limit of the sweep
        # reset the level to high
        if self.send_command(RESET_TRIGGER):
            return self.serialcom.read(size=1)

    def sweep_direction(self, updown):
        """
        change the sweep direction, up=1, down=0
        """
        if updown == 0:
            # change the sweep direction to up
            self.send_command(SWEEP_DOWN)
        elif updown == 1:
            # change the sweep direction to down
            self.send_command(SWEEP_UP)
        return self.serialcom.read(size=1)

    def sweep_up(self):
        return self.sweep_direction(1)

    def sweep_down(self):
        return self.sweep_direction(0)

    def sweep_continue(self):
        """
        to continue the sweep,
        pause: True/False
        """
        # the sweep will be continued
        self.send_command(SWEEP_CONTIN)
        return self.serialcom.read(size=1)

    def sweep_pause(self):
        """
        to pause the sweep,
        pause: True/False
        """
        # the sweep will be paused
        self.send_command(SWEEP_PAUSE)
        return self.serialcom.read(size=1)

    def get_min_step_size(self, freq_start_list, freq_stop_list):
        self.send_command(
            self._send_get_min_step_size_command(freq_start_list, freq_stop_list)
        )
        return self._receive_get_min_step_size_command(len(freq_start_list))

    def boot_up_sequence(self, boot_up_commands):
        """
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
        """

        commands = b""
        for buc in boot_up_commands:
            commands += buc
        num_bytes_send = len(commands)
        nbsb = num_bytes_send.to_bytes(2, "big")
        data_send = nbsb[0] + b"\x42" + nbsb[1]
        data_send += commands
        data_send += xor_bytes(data_send)
        return self.receive_command(size=1)

    def reboot(self):
        """
        The synthesizer will return an error byte if there is an error, but otherwise will not return a byte.
        It may be worthwhile to use FT_purge to clear the transmit buffer after a reboot.
        """
        self.serialcom.reset_input_buffer()  # clear the tx buffers
        self.serialcom.reset_output_buffer()  # clear the rx buffers
        self.send_command(REBOOT)
        data_receive = self.serialcom.read(size=1)
        if len(data_receive) > 0:
            print("Error ocurred when trying to reboot!")
        else:
            print("MW Synthesizer Rebooted!")
        time.sleep(1)
        if not self.serialcom.is_open:
            self.serialcom.open()
        self.serialcom.reset_input_buffer()  # clear the tx buffers
        self.serialcom.reset_output_buffer()  # clear the rx buffers

    def other_parameters(self):
        """
        Other functions are possible. Phase can be changed or swept. Waveforms for frequency or
        phase can be played with 1024 points. Contact VDI for more information.
        """
        data_send = b"\x44"
        # TO DO (20221220): ask VDI for other available parameters
        pass

    def purge(self):
        # Ensure all TX data has been sent and clean out the TX buffer
        self.serialcom.flush()
        self.serialcom.reset_input_buffer()
        # Clean up RX buffers
        if self.serialcom.in_waiting > 0:
            print("Cleaning up RX buffer. Remaining data:", self.serialcom.read_all())
            self.serialcom.reset_output_buffer()

    def _cw_frequency_command(self, freq):
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
        data_send = b"\x06\x46" + freq_to_bytes(freq)
        data_send += xor_bytes(data_send)
        return data_send

    def _receive_cw_frequency_command(self):
        """
        Receive:
        BYTE1: Error byte.
        BYTE2: Integer portion of the actual output frequency in GHz.
        BYTE3: Most significant byte of the 32 bit binary fraction of the actual output frequency in GHz
        BYTE4: Next significant byte of the 32 bit binary fraction.
        BYTE5: Next significant byte of the 32 bit binary fraction.
        BYTE6: Least significant byte of the 32 bit binary fraction.
        """
        data_returned = self.receive_command(size=6)
        if data_returned:
            return bytes_to_freq(data_returned)
        else:
            return None

    def _simple_sweep_command(
        self,
        freq_start: float,
        freq_stop: float,
        step_rise: int,
        step_fall: int,
        stepdwell_rise: float,
        stepdwell_fall: float,
        dwell_low: int,
        dwell_high: int,
    ):
        """
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
        """
        data_send = b"\x1c\x73\xff"
        # data_send = b"\x1C\x73\x0A"
        data_send += freq_to_bytes(freq_start)
        data_send += freq_to_bytes(freq_stop)
        # min step size is 12.10719347 Hz
        data_send += freq_to_bytes(step_rise)
        data_send += freq_to_bytes(step_fall)
        data_send += dwell_to_bytes(stepdwell_rise)
        data_send += dwell_to_bytes(stepdwell_fall)
        data_send += int(dwell_low).to_bytes(1, "big")
        data_send += int(dwell_high).to_bytes(1, "big")
        # print(type(data_send))
        # print(type(xor_bytes(data_send)))
        data_send += xor_bytes(data_send)
        return data_send

    def _receive_simple_sweep_command(self):
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
        data_rec = self.receive_command(size=21)  # the BYTE 1 is handled here
        freq_start = bytes_to_freq(data_rec[:5])  # in GHz
        freq_stoop = bytes_to_freq(data_rec[5:10])
        step_rise = bytes_to_freq(data_rec[10:15])
        step_fall = bytes_to_freq(data_rec[15:])
        return freq_start, freq_stoop, step_rise, step_fall

    def _sweep_command(
        self,
        freq_start: float,
        freq_stop: float,
        step_rise: int,
        step_fall: int,
        stepdwell_rise: float,
        stepdwell_fall: float,
        dwell_low: int,
        dwell_high: int,
    ):
        """
        same as simple sweep command, but
        t the minimum step size changes based on the output frequency,
        """
        data_send = b"\x1c\x53\xff"
        # data_send = b"\x1C\x73\x0A"
        data_send += freq_to_bytes(freq_start)
        data_send += freq_to_bytes(freq_stop)
        # min step size is 12.10719347 Hz
        data_send += freq_to_bytes(step_rise)
        data_send += freq_to_bytes(step_fall)
        data_send += dwell_to_bytes(stepdwell_rise)
        data_send += dwell_to_bytes(stepdwell_fall)
        data_send += int(dwell_low).to_bytes(1, "big")
        data_send += int(dwell_high).to_bytes(1, "big")
        data_send += xor_bytes(data_send)
        return data_send

    def _receive_sweep_command(self):
        return self._receive_simple_sweep_command()

    def _send_get_min_step_size_command(self, freq_start_list, freq_stop_list):
        """
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
        """
        num_returnbytes = len(freq_start_list)
        data_send = num_returnbytes.to_bytes(1, "big") + b"\x6d"
        for (
            fstart,
            fstop,
        ) in zip(freq_start_list, freq_stop_list):
            data_send += freq_to_bytes(fstart)
            data_send += freq_to_bytes(fstop)
        data_send += xor_bytes(data_send)
        # print_bytestring(data_send)
        return data_send

    def _receive_get_min_step_size_command(self, num_freqgroup):
        """
        Receive:
        BYTE1: Error byte.
        BYTE2..: Least significant byte of the 32 bit binary fraction of the minimum step size in GHz for each
        group of 10 bytes sent.
        """
        data_return = self.receive_command(size=1 + num_freqgroup)
        out = []
        for fb in data_return:
            out.append(fb / FLOAT32BIT * 1e9)
        return out


if __name__ == "__main__":
    mwsyn = Synthesizer("VDIS200A")
    # mwsyn.send_cw_frequency_command(8.9999999999)
    # print(mwsyn.send_simple_sweep_command(8, 20, 1e-6, 10e-6, 1.99e3, 4, 0, 0))
    # mwsyn.send_get_min_step_size_command([8, 9], [20, 10])
