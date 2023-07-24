# import ACS
# from about import About
# from access import Access
# from amcids import Amcids
# from control import Control
# from description import Description
# from diagnostic import Diagnostic
# from functions import Functions
# from move import Move
# from network import Network
# from res import Res
# from rotcomp import Rotcomp
# from rtin import Rtin
# from rtout import Rtout
# from status import Status
# from system_service import System_service
# from update import Update

# import attocube.ACS
# from attocube.about import About
# from attocube.access import Access
# from attocube.amcids import Amcids
# from attocube.control import Control
# from attocube.description import Description
# from attocube.diagnostic import Diagnostic
# from attocube.functions import Functions
# from attocube.move import Move
# from attocube.network import Network
# from attocube.res import Res
# from attocube.rotcomp import Rotcomp
# from attocube.rtin import Rtin
# from attocube.rtout import Rtout
# from attocube.status import Status
# from attocube.system_service import System_service
# from attocube.update import Update

import hardware.positioner.attocube.ACS
from hardware.positioner.attocube.about import About
from hardware.positioner.attocube.access import Access
from hardware.positioner.attocube.amcids import Amcids
from hardware.positioner.attocube.control import Control
from hardware.positioner.attocube.description import Description
from hardware.positioner.attocube.diagnostic import Diagnostic
from hardware.positioner.attocube.functions import Functions
from hardware.positioner.attocube.move import Move
from hardware.positioner.attocube.network import Network
from hardware.positioner.attocube.res import Res
from hardware.positioner.attocube.rotcomp import Rotcomp
from hardware.positioner.attocube.rtin import Rtin
from hardware.positioner.attocube.rtout import Rtout
from hardware.positioner.attocube.status import Status
from hardware.positioner.attocube.system_service import System_service
from hardware.positioner.attocube.update import Update

class Device(hardware.positioner.attocube.ACS.Device):

    def __init__ (self, address):
    
        super().__init__(address)
        
        self.about = About(self)
        self.access = Access(self)
        self.amcids = Amcids(self)
        self.control = Control(self)
        self.description = Description(self)
        self.diagnostic = Diagnostic(self)
        self.functions = Functions(self)
        self.move = Move(self)
        self.network = Network(self)
        self.res = Res(self)
        self.rotcomp = Rotcomp(self)
        self.rtin = Rtin(self)
        self.rtout = Rtout(self)
        self.status = Status(self)
        self.system_service = System_service(self)
        self.update = Update(self)

def discover():
    return Device.discover("amc")