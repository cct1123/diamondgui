import time

from pymodbus.client import ModbusTcpClient

# a default valve map
vavle_map = {
    0: 0b0000,
    "DI": 0b0000,
    1: 0b0010,
    "oil": 0b0010,
    2: 0b0001,
    "noname1": 0b0001,
    3: 0b0011,
    "noname2": 0b0011,
    4: 0b0100,
    "blue": 0b0100,
    5: 0b0110,
    "green": 0b0110,
    6: 0b0101,
    "yellow": 0b0101,
    7: 0b0111,
    "red": 0b0111,
}


class PneumaticControl(ModbusTcpClient):
    def __init__(
        self,
        host: str = "192.168.1.3",
        port: int = 502,
        vavle_map: dict = vavle_map,
        **kwargs,
    ):
        self.vmap = vavle_map
        self.vnum = len(vavle_map) // 2
        super().__init__(
            host=host,
            port=port,
            **kwargs,
        )

    def depressurize(self, valve):
        self.write_coil(self.vmap[valve], True)

    def depressurize_list(self, valve_list):
        state_all = self.read_coils(0x200 + 0b00, self.vnum).bits
        for kk in valve_list:
            state_all[self.vmap[kk]] = True
        self.write_coils(0b00, state_all)

    def depressurize_all(self):
        self.write_coils(0b00, [True] * self.vnum)

    def pressurize(self, valve):
        self.write_coil(self.vmap[valve], False)

    def pressurize_list(self, valve_list):
        state_all = self.read_coils(0x200 + 0b00, self.vnum).bits
        for kk in valve_list:
            state_all[self.vmap[kk]] = False
        self.write_coils(0b00, state_all)

    def pressurize_all(self):
        self.write_coils(0b00, [False] * self.vnum)

    def valve_state(self, valve):
        # Offset the register number
        register_number = 0x200 + self.vmap[valve]
        return self.read_coils(register_number, 1).bits[0]

    def valve_state_all(self):
        # Offset the register number
        state_all = self.read_coils(0x200 + 0b00, self.vnum).bits
        return dict((kk, state_all[ii]) for kk, ii in self.vmap.items())


if __name__ == "__main__":
    # for test only
    ip_address = "192.168.1.3"
    pneu = PneumaticControl(host=ip_address)

    def rain_drop(interv, vnum):
        for ii in range(0, vnum, 2):
            pneu.depressurize(ii)
            time.sleep(interv)

        for ii in range(0, vnum, 2):
            pneu.pressurize(ii)
            time.sleep(interv)

        for ii in range(0, vnum, 2):
            pneu.depressurize(vnum - (ii + 1))
            time.sleep(interv)

        for ii in range(0, vnum, 2):
            pneu.pressurize(vnum - (ii + 1))
            time.sleep(interv)

    def thunder(interv):
        pneu.depressurize_all()
        time.sleep(interv)
        pneu.pressurize_all()
        time.sleep(interv)
        pneu.depressurize_list([0, 2, 4, 6])
        time.sleep(interv)
        pneu.pressurize_list([0, 2, 4, 6])
        time.sleep(interv)
        pneu.depressurize_list([1, 3, 5, 7])
        time.sleep(interv)
        pneu.pressurize_list([1, 3, 5, 7])
        time.sleep(interv)

    def rythum(interv):
        rain_drop(interv * 10, pneu.vnum)
        rain_drop(interv * 5, pneu.vnum)
        rain_drop(interv, pneu.vnum)
        thunder(interv)
        rain_drop(interv * 2, pneu.vnum)
        thunder(interv * 5)
        rain_drop(interv * 2, pneu.vnum)
        thunder(interv * 2)
        thunder(interv)
        thunder(interv * 2)
        thunder(interv)
        thunder(interv * 2)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv * 1, pneu.vnum)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv * 1, pneu.vnum)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv * 1, pneu.vnum)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv * 1, pneu.vnum)
        thunder(interv * 2)
        thunder(interv)

    pneu.pressurize_all()
    rythum(0.02)
    pneu.pressurize_all()
