import time

from pymodbus.client import ModbusTcpClient

# a default valve map
valve_map = {
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
    BASE_COIL_ADDR = 0x200

    def __init__(
        self,
        host: str = "192.168.1.3",
        port: int = 502,
        valve_map: dict = valve_map,
        **kwargs,
    ):
        self.vmap = valve_map
        # half the entries (each valve has two keys)
        self.vnum = len(valve_map) // 2
        super().__init__(host=host, port=port, **kwargs)

    def depressurize(self, valve):
        """Open (depressurize) a single valve."""
        coil = self.vmap[valve]
        self.write_coil(self.BASE_COIL_ADDR + coil, True)

    def depressurize_list(self, valve_list):
        """Open (depressurize) multiple valves at once."""
        state_all = self.read_coils(self.BASE_COIL_ADDR, count=self.vnum).bits
        for v in valve_list:
            state_all[self.vmap[v]] = True
        self.write_coils(self.BASE_COIL_ADDR, state_all)

    def depressurize_all(self):
        """Open all valves."""
        self.write_coils(self.BASE_COIL_ADDR, [True] * self.vnum)

    def pressurize(self, valve):
        """Close (pressurize) a single valve."""
        coil = self.vmap[valve]
        self.write_coil(self.BASE_COIL_ADDR + coil, False)

    def pressurize_list(self, valve_list):
        """Close (pressurize) multiple valves at once."""
        state_all = self.read_coils(self.BASE_COIL_ADDR, count=self.vnum).bits
        for v in valve_list:
            state_all[self.vmap[v]] = False
        self.write_coils(self.BASE_COIL_ADDR, state_all)

    def pressurize_all(self):
        """Close all valves."""
        self.write_coils(self.BASE_COIL_ADDR, [False] * self.vnum)

    def valve_state(self, valve):
        """Get the state (True=open/depressurized, False=closed/pressurized) of one valve."""
        coil = self.vmap[valve]
        return self.read_coils(self.BASE_COIL_ADDR + coil, count=1).bits[0]

    def valve_state_all(self):
        """Return a dict of all valve states."""
        bits = self.read_coils(self.BASE_COIL_ADDR, count=self.vnum).bits
        return {key: bits[idx] for key, idx in self.vmap.items()}


if __name__ == "__main__":
    # for test only
    ip_address = "192.168.1.3"
    mac_address = "00:30:DE:5F:31:43"
    item_nubmer = "750-891"

    pneu = PneumaticControl(host=ip_address)

    def rain_drop(interv, vnum):
        for i in range(0, vnum, 2):
            pneu.depressurize(i)
            time.sleep(interv)
        for i in range(0, vnum, 2):
            pneu.pressurize(i)
            time.sleep(interv)
        for i in range(0, vnum, 2):
            pneu.depressurize(vnum - (i + 1))
            time.sleep(interv)
        for i in range(0, vnum, 2):
            pneu.pressurize(vnum - (i + 1))
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

    def rhythm(interv):
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
        rain_drop(interv, pneu.vnum)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv, pneu.vnum)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv, pneu.vnum)
        rain_drop(interv * 2, pneu.vnum)
        rain_drop(interv, pneu.vnum)
        thunder(interv * 2)
        thunder(interv)

    # start with all valves closed
    pneu.pressurize_all()
    rhythm(0.02)
    # close everything at end
    pneu.pressurize_all()
