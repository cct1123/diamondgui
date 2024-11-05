import time
import numpy as np
import logging
from measurement.task_base import Measurement

def lorentzian(x, x0, gamma):
    """
    Lorentzian function.

    Parameters:
        x: array-like, the independent variable
        x0: float, the center of the Lorentzian
        gamma: float, the half-width at half-maximum (HWHM)
    """
    return gamma / np.pi / ((x - x0)**2 + gamma**2)

def fake_nv_spectrum(freq, mw_power, bfield, freq_zfs=2.8705, linewidth=0.0005, hyperfine=2.2E-3, splitting=[-1,0,1]):
    hfsplitting = hyperfine*np.array(splitting) # hyperfine splitting
    zeeman = bfield*2.8E-3
    peakpos = []
    for hf in hfsplitting:
        peakpos += [freq_zfs+hf-0.5*zeeman, freq_zfs+hf+0.5*zeeman]
    spectra = np.array([lorentzian(freq, pp, (1+mw_power)*linewidth) for pp in peakpos])
    spectrum = -np.average(spectra, axis=0)
    return spectrum-np.min(spectrum)

class DummyODMR(Measurement):  

    def __init__(self, name="dummy-default"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict(freq_begin=2.0, 
                         freq_end=4.0, 
                         freq_step=0.5, 
                         mw_power=0.5, # percentage of linewidth
                         bfield=0.0, #[G]
                         )
        # !!< has to be specific by users>
        __dataset = dict(freq=np.zeros(10), signal=np.zeros(10))
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        logging.debug(f"Parameters are: {self.paraset}")
        if not self.tokeep:
            self.freq_array = np.arange(self.paraset["freq_begin"],  self.paraset["freq_end"], self.paraset["freq_step"])
            self.paraset["freq_end"] = self.freq_array[-1]
            length = len(self.freq_array)
            self.buffer_rawdata = np.zeros(length)
            self.signalsum = np.zeros(length)

    def _run_exp(self):
        logging.debug(f"hey fake experiment-'{self._name}' no.{self.idx_run}")
        logging.debug(f"I'm cooking some fake data")
        time.sleep(0.1)
        length = len(self.freq_array)
        fakespec = fake_nv_spectrum(self.freq_array, self.paraset["mw_power"], self.paraset["bfield"])
        self.buffer_rawdata = fakespec + (np.max(fakespec)-np.min(fakespec))*np.random.rand(length)*4
        

    def _upload_dataserv(self):
        logging.debug(f"Moving data to a data server")
        self.signalsum += np.copy(self.buffer_rawdata)
        self.dataset["freq"] = self.freq_array
        self.dataset["signal"] = self.signalsum/self.idx_run
        super()._upload_dataserv()  

    def _handle_exp_error(self):
        super()._handle_exp_error()
        logging.debug(f"dumdum measurement has troubles!")


    def _shutdown_exp(self):
        super()._shutdown_exp()
        logging.debug(f"goodbye dumdum measurement")