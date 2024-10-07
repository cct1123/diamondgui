from measurement.task_base import Measurement


class cwODMR(Measurement):
    # unsynchronized cw OMDR
    def __init__(self, name="default"):
        super().__init__(name)

        # default parameters
        self.paraset = dict(


        )

        self.dataset = dict(

            
        )

    def _setup_exp(self):
        super()._setup_exp()

        # current_percent = self.paraset["laser_current"]
        # self.ds.laser.laser_off()
        # self.ds.laser.set_analog_control_mode("current")
        # self.ds.laser.set_modulation_state("Pulsed")
        # self.ds.laser.set_diode_current(current_percent, save_memory=False)
        # self.ds.laser.laser_on()

        laserpower = self.paraset["laser_power"]
        self.ds.laser.laser_off()
        self.ds.laser.set_analog_control_mode("power")
        self.ds.laser.set_modulation_state("CW")
        self.ds.laser.set_laser_power(laserpower, save_memory=False)
        self.ds.laser.laser_on()

        self.ds.mwgen.
        self.ds.laser
        self.ds.laser
    
    def _run_exp(self):
        return super()._run_exp()

