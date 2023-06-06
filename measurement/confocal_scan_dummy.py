# perform 2D confocal scan with attocube XYZ positioners


from nspyre import InstrumentGateway
from nspyre import DataSource
from rpyc.utils.classic import obtain

gw = InstrumentGateway()

class ConfocalScan():

    name = "dffgsdfgdsf"
    state = "idle"
    to_keep = False

    para = dict(
        h0=0.0,
        h1=1.0,
        h_step=10,
        v0=0.0,
        v1=1.0,
        v_step=10, 
        depth=0.5, 
        fix_axis="z", 
        
    )
    data = dict(
        raw=[[]] # store the raw data of each iteration
    )
    to_dataserv = dict(
        # name=__name__,
        params = para, 
        datasets = data
    )
    def __init__(self, name=__name__):
        # name: name of the dataset in the dataserver
        self.ds = DataSource(name)
    def set_params(self, para_dict):
            # set parametes
        for kk, vv in para_dict.items():
            self.para[kk] = vv
    def _setup_exp(self):
        if not self.to_keep:
            # reset the dataset
            self.data = dict()
        
        self.to_dataserv["params"] = self.para

    def _run_exp(self):
        # exp_name: label of the measurement for dataset


        # run the experiment

        gw.connect()

        self.data["raw"] = []
        
        
        gw.disconnect()
        self.to_dataserv["data"] = self.data

        
    def _upload_dataserv(self):
        # push the data to the data server
        with self.ds as pipe:
            pipe.push(self.to_dataserv)

    def _shutdown_exp(self):
        pass

    def new_dataset(self, name):
        self.ds = DataSource(name)
