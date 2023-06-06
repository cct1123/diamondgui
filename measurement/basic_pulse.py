
import numpy as np

from nspyre import DataSource
from nspyre import InstrumentGateway

gw = InstrumentGateway()
class Rabi:
    buffer_size = 4123432434
    data_pipe = DataSource
    buffer = np.array([], dtype=np.float64, order='C')
    num_pts = 100000
    def __init__(self):
        self.buffer_size = 65266346234
        self.data_pipe = DataSource(self.__class__.__name__)
    def run(self):
        gw.connect()
        buffer = np.ones((1, self.buffer_size), dtype=np.float64, order='C')
        
        gw.daq.open_task(True, self.num_pts)
        gw.disconnect()



    def setup(self):
        pass
    def shutdown(self):
        pass

if __name__ == "__main__":
    rr = Rabi()
    print(rr.buffer)