"""
This is example script demonstrates most of the basic functionality of nspyre.

Copyright (c) 2021, Jacob Feder
All rights reserved.

This work is licensed under the terms of the 3-Clause BSD license.
For a copy, see <https://opensource.org/licenses/BSD-3-Clause>.
"""
import time
import queue

import numpy as np
from nspyre import DataSource
from nspyre import InstrumentGateway

class SpinMeasurements:
    """Perform spin measurements."""

    def odmr_sweep(self, dataset: str, start_freq: float, stop_freq: float, num_points: int, iterations: int, msg_queue=None):
        """Run a fake ODMR (optically detected magnetic resonance) PL (photoluminescence) sweep over a set of microwave frequencies.

        Args:
            dataset: name of the dataset to push data to
            start_freq (float): start frequency
            stop_freq (float): stop frequency
            num_points (int): number of points between start-stop (inclusive)
            iterations: number of times to repeat the experiment
            msg_queue: an optional multiprocessing message Queue object used for interprocess communication
        """

        # connect to the instrument server
        # connect to the data server and create a data set, or connect to an
        # existing one with the same name if it was created earlier.
        with InstrumentGateway() as gw, DataSource(dataset) as odmr_data:
            # set the signal generator amplitude for the scan (dBm).
            gw.drv.set_amplitude(6.5)
            gw.drv.set_output_en(True)

            # frequencies that will be swept over in the ODMR measurement
            frequencies = np.linspace(start_freq, stop_freq, num_points)

            # for storing the experiment data
            # python list of numpy arrays of shape (2, num_points)
            data = {'mydata' : []}
            for i in range(iterations):
                if i == 0:
                    # photon counts corresponding to each frequency
                    # initialize to 0 for the first run
                    counts = np.zeros(num_points)
                    data['mydata'].append(np.stack([frequencies/1e9, counts]))
                else:
                    # duplicate the last data entry which will be filled during the sweep
                    last_entry = np.copy(data['mydata'][-1])
                    data['mydata'].append(last_entry)

                # sweep counts vs. frequency.
                for f, freq in enumerate(frequencies):
                    # access the signal generator driver on the instrument server and set its frequency.
                    gw.drv.set_frequency(freq)
                    # retrive the last counts entry
                    counts = data['mydata'][-1][1]
                    # read the number of photon counts received by the photon counter.
                    counts[f] = gw.drv.cnts(0.002)
                    # check for messages from the GUI
                    if msg_queue is not None:
                        try:
                            # try to get a message from the queue
                            o = msg_queue.get_nowait()
                        except queue.Empty:
                            # no message was available so we can continue
                            pass
                        else:
                            if o == 'stop':
                                # the GUI has asked us nicely to exit
                                return
                            else:
                                raise ValueError(f'Unrecognized command: [{o}]')
                    # save the current data to the data server.
                    odmr_data.push({'params': {'start': start_freq, 'stop': stop_freq, 'num_points': num_points, 'iterations': iterations},
                                    'title': 'Optically Detected Magnetic Resonance',
                                    'xlabel': 'Frequency (GHz)',
                                    'ylabel': 'Counts',
                                    'datasets': data
                    })

if __name__ == '__main__':
    exp = SpinMeasurements()
    exp.odmr_sweep('odmr', 3e9, 4e9, 100, 2)
