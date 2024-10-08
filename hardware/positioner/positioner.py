import time
import logging
import numpy as np
from hardware.positioner.attocube import AMC

# from attocube.AMC import Device
OL = 1 # if open loop positioner is connected
RES = 3 # if 
IP = "192.168.1.1" # default ip

logger = logging.getLogger(__name__)

TTL = 0
LVDS = 1

RTOUT_OFF = 0
RTOUT_AQUADB = 1
RTOUT_TRIGGER = 2
CLOSED_LOOP = 1
OPEN_LOOP = 0

class XYZPositioner(AMC.Device):
    """
    Drivers for AMC controller + RES positioners
    """
    ip = IP
    xaxis = 0
    yaxis = 1
    zaxis = 2

    # position = np.array([0, 0, 0])

    def __init__(self, ip, xaxis=0, yaxis=1, zaxis=2):
        self.ip = ip
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.zaxis = zaxis
        super().__init__(self.ip)
        self.connect()
        self.check_3axis_connected()
        self.open_control()
        # self.close()
        
    def open_control(self):
        if not self.control.getControlOutput(self.xaxis):
            self.control.setControlOutput(self.xaxis, True)
        if not self.control.getControlOutput(self.yaxis):
            self.control.setControlOutput(self.yaxis, True)
        if not self.control.getControlOutput(self.zaxis):
            self.control.setControlOutput(self.zaxis, True)

    def close_control(self):
        if self.control.getControlOutput(self.xaxis):
            self.control.setControlOutput(self.xaxis, False)
        if self.control.getControlOutput(self.yaxis):
            self.control.setControlOutput(self.yaxis, False)
        if self.control.getControlOutput(self.zaxis):
            self.control.setControlOutput(self.zaxis, False)

    def check_3axis_connected(self):
        xres = self.status.getOlStatus(self.xaxis) == RES
        yres = self.status.getOlStatus(self.yaxis) == RES
        zres = self.status.getOlStatus(self.zaxis) == RES
        xcon = self.status.getStatusConnected(self.xaxis)
        ycon = self.status.getStatusConnected(self.yaxis)
        zcon = self.status.getStatusConnected(self.zaxis)
        if (xres and yres and zres and xcon and ycon and zcon):
            logger.info("All 3 axes are connected with RES positioners.")
        else:
            if not (xcon and xres):
                logger.warning("x-axis is not connected with a RES positioner.")
            if not (ycon and yres):
                logger.warning("y-axis is not connected with a RES positioner.")
            if not (zcon and zres):
                logger.warning("z-axis is not connected with a RES positioner.")
    
    def discover(self):
        return super().discover("amc")

    def connect(self):
        super().connect()
    
    def close(self):
        super().close()

    # simple move functions ---------------------------------------------------------------------------------------------
    def get_x(self):
        position = self.move.getPosition(self.xaxis)
        logger.info(f'Got X position: {position}')
        return position

    def get_y(self):
        position = self.move.getPosition(self.yaxis)
        logger.info(f'Got Y position: {position}')
        return position

    def get_z(self):
        position = self.move.getPosition(self.zaxis)
        logger.info(f'Got Z position: {position}')
        return position

    def get_positions(self):
        # get the current position
        return np.array([self.get_x(), self.get_y(), self.get_z()])

    def move_x(self, distance):
        # move along x axis by a distance
        # distance: [nm]
        position = self.move.getPosition(self.xaxis)
        self.move.setControlTargetPosition(self.xaxis, position + distance)
        self.control.setControlMove(self.xaxis, True)
        while not self.status.getStatusTargetRange(self.xaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.xaxis, False)
        logger.info(f'Move along X by {distance} nm')

    def move_y(self, distance):
        # move along y axis by a distance
        # distance: [nm]
        position = self.move.getPosition(self.yaxis)
        self.move.setControlTargetPosition(self.yaxis, position + distance)
        self.control.setControlMove(self.yaxis, True)
        while not self.status.getStatusTargetRange(self.yaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.yaxis, False)
        logger.info(f'Move along Y by {distance} nm')

    def move_z(self, distance):
        # move along x axis by a distance
        # distance: [nm]
        position = self.move.getPosition(self.zaxis)
        self.move.setControlTargetPosition(self.zaxis, position + distance)
        self.control.setControlMove(self.zaxis, True)
        while not self.status.getStatusTargetRange(self.zaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.zaxis, False)
        logger.info(f'Move along Z by {distance} nm')

    def set_x(self, position):
        self.move.setControlTargetPosition(self.xaxis, position)
        self.control.setControlMove(self.xaxis, True)
        while not self.status.getStatusTargetRange(self.xaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.xaxis, False)
        logger.info(f'Set X position to {position} nm')

    def set_y(self, position):
        self.move.setControlTargetPosition(self.yaxis, position)
        self.control.setControlMove(self.yaxis, True)
        logger.info(f'Set Y position to {position} nm')
        while not self.status.getStatusTargetRange(self.yaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.yaxis, False)
        logger.info(f'Set X position to {position} nm')

    def set_z(self, position):
        self.move.setControlTargetPosition(self.zaxis, position)
        self.control.setControlMove(self.zaxis, True)
        logger.info(f'Set Z position to {position} nm')
        while not self.status.getStatusTargetRange(self.zaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.zaxis, False)
        logger.info(f'Set X position to {position} nm')

    def set_pos(self, xyz):
        self.move.setControlTargetPosition(self.xaxis, xyz[0])
        self.control.setControlMove(self.xaxis, True)
        self.move.setControlTargetPosition(self.yaxis, xyz[1])
        self.control.setControlMove(self.yaxis, True)
        self.move.setControlTargetPosition(self.zaxis, xyz[2])
        self.control.setControlMove(self.zaxis, True)
        logger.info(f'Set X Y Z position to {xyz} nm')

        while not self.status.getStatusTargetRange(self.xaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.xaxis, False)
        while not self.status.getStatusTargetRange(self.yaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.yaxis, False)
        while not self.status.getStatusTargetRange(self.zaxis):
            time.sleep(0.2)
        else:
            self.control.setControlMove(self.zaxis, False)

        logger.info(f'Set X Y Z positions to {xyz} nm')

    # grounding would stable the positioner by reducing electric noises
    def ground_x(self):
        self.move.setGroundAxis(self.xaxis, True)
    def ground_y(self):
        self.move.setGroundAxis(self.yaxis, True)
    def ground_z(self):
        self.move.setGroundAxis(self.zaxis, True)
    def ground_allaxis(self):
        self.ground_x()
        self.ground_y()
        self.ground_z()

    def unground_x(self):
        self.move.setGroundAxis(self.xaxis, False)
    def unground_y(self):
        self.move.setGroundAxis(self.yaxis, False)
    def unground_z(self):
        self.move.setGroundAxis(self.zaxis, False)
    def unground_allaxis(self):
        self.unground_x()
        self.unground_y()
        self.unground_z()


    def set_positoin(self, position):
        self.set_x(position[0])
        self.set_y(position[1])
        self.set_z(position[2])

    def set_x_tol(self, tolerance):
        self.control.setControlTargetRange(self.xaxis, tolerance)
    def set_y_tol(self, tolerance):
        self.control.setControlTargetRange(self.yaxis, tolerance)
    def set_z_tol(self, tolerance):
        self.control.setControlTargetRange(self.zaxis, tolerance)

    # realtime input/output interface ---------------------------------------------------------------
    def set_closedloop_x(self):
        self.rtin.getRealTimeInFeedbackLoopMode(self.xaxis, CLOSED_LOOP)
    
    def set_openloop_x(self):
        self.rtin.getRealTimeInFeedbackLoopMode(self.xaxis, OPEN_LOOP)
    
    def set_realtime_mode_x(self, mode):
        # mode: AquadB, Trigger, Stepper, 
        # 0,1,8,9,10,11, 15
        if mode.lower() == "aquadb":
            self.rtin.setRealTimeInMode(self.xaxis, 0) # AquadB LVTTL
            self.rtout.setMode(self.xaxis, RTOUT_AQUADB)
            self.rtout.setSignalMode(TTL)
        elif mode.lower() == "trigger":
            self.rtin.setRealTimeInMode(self.xaxis, 10) # Trigger LVTTL
            self.rtout.setMode(self.xaxis, RTOUT_TRIGGER)
            self.rtout.setSignalMode(TTL)
        elif mode.lower() == "stepper":
            self.rtin.setRealTimeInMode(self.xaxis, 8) # Stepper LVTTL
            self.rtout.setMode(self.xaxis, RTOUT_TRIGGER)
        else:
            logger.debug(f"'{mode}' is recieved. Please enter a valid realtime interface mode: 'AquadB', 'Trigger', 'Stepper'.")
        self.rtin.apply()
        self.rtout.apply()

    def set_realtime_mode_y(self, mode):
        # mode: AquadB, Trigger, Stepper, 
        # 0, 1, 8, 9, 10, 11, 15
        if mode.lower() == "aquadb":
            self.rtin.setRealTimeInMode(self.yaxis, 0) # AquadB LVTTL
            self.rtout.setMode(self.yaxis, RTOUT_AQUADB)
            self.rtout.setSignalMode(TTL)
        elif mode.lower() == "trigger":
            self.rtin.setRealTimeInMode(self.xaxis, 10) # Trigger LVTTL
            self.rtout.setMode(self.yaxis, RTOUT_TRIGGER)
            self.rtout.setSignalMode(TTL)
        elif mode.lower() == "stepper":
            self.rtin.setRealTimeInMode(self.xaxis, 8) # Stepper LVTTL
            self.rtout.setMode(self.yaxis, RTOUT_TRIGGER)
        else:
            logger.debug(f"'{mode}' is recieved. Please enter a valid realtime interface mode: 'AquadB', 'Trigger', 'Stepper'.")
        self.rtin.apply()
        self.rtout.apply()

    def set_change_per_pulse_x(self, dx):
        # for closed-loop only
        # dx: increment size
        self.rtin.setRealTimeInChangePerPulse(self.xaxis, dx)

    def set_triggerout_config_x(self, higher, lower, epsilon, polarity):
        self.rtout.setTriggerConfig(self.xaxis, higher, lower, epsilon, polarity)
        self.rtout.apply()

    def set_triggerout_config_y(self, higher, lower, epsilon, polarity):
        self.rtout.setTriggerConfig(self.yaxis, higher, lower, epsilon, polarity)
        self.rtout.apply()

    def set_steps_per_pulse_x(self, steps):
        # when trigger and stepper mode is used, for open-loop only
        self.rtin.setRealTimeInStepsPerPulse(self.xaxis, steps)

    def set_steps_per_pulse_y(self, steps):
        self.rtin.setRealTimeInStepsPerPulse(self.yaxis, steps)
        
    def set_steps_per_pulse_z(self, steps):
        self.rtin.setRealTimeInStepsPerPulse(self.zaxis, steps)

    
if __name__ == "__main__":
    xyzpp = XYZPositioner(ip="192.168.1.78", xaxis=0, yaxis=1, zaxis=2)
    xyzpp.open_control()

    
    # # set the positioner to a target position
    # xyzpp.set_x(1500*1000)
    # xyzpp.set_y(1500*1000)
    # xyzpp.set_z(100*1000)

    # # move the positioner by some distance
    # xyzpp.move_x(2*1000)
    # xyzpp.move_y(2*1000)
    # xyzpp.move_z(2*1000)


    # # a fake scan ------------------------------
    # start_time = time.time()
    # x_range = 1000E3
    # y_range = 1000E3
    # z_range = 0
    # x_c = 1500E3
    # y_c = 1500E3
    # z_c = 1250E3
    # x_num = 100
    # y_num = 100
    # z_num = 1
    # x_d = x_range/x_num
    # y_d = y_range/y_num
    # if z_range == 0:
    #     z_d = min(x_d, y_d)
    # else:
    #     z_d = z_range/z_num

    # xlist = np.linspace(x_c-x_range/2, x_c+x_range/2, x_num)
    # ylist = np.linspace(y_c-y_range/2, y_c+y_range/2, y_num)
    # zlist = np.linspace(z_c-z_range/2, z_c+z_range/2, z_num)
    # xyzpp.set_x_tol(max(x_d/4.0, 100))
    # xyzpp.set_y_tol(max(y_d/4.0, 100))
    # xyzpp.set_z_tol(max(z_d/4.0, 100))

    # xyzpp.set_x(x_c)
    # xyzpp.set_y(y_c)
    # xyzpp.set_z(z_c)
    # for zz in zlist:
    #     xyzpp.set_z(zz)
    #     while not xyzpp.status.getStatusTargetRange(xyzpp.zaxis):
    #         time.sleep(0.1)
    #     else:
    #         print(f"z position: {xyzpp.get_z()/1000} um")
    #     for yy in ylist:
    #         xyzpp.set_y(yy)
    #         while not xyzpp.status.getStatusTargetRange(xyzpp.yaxis):
    #             time.sleep(0.1)
    #         else:
    #             print(f"y position: {xyzpp.get_y()/1000} um")
    #         for xx in list(xlist)+list(np.flip(xlist)):
    #             xyzpp.set_x(xx)
    #             while not xyzpp.status.getStatusTargetRange(xyzpp.xaxis):
    #                 time.sleep(0.1)
    #             else:
    #                 print(f"x position: {xyzpp.get_x()/1000} um")
    # end_time = time.time()
    # xyzpp.set_x(x_c)
    # xyzpp.set_y(y_c)
    # xyzpp.set_z(z_c)
    # print(f"Scanning of \n pts num {x_num*y_num*z_num}, \n range x{x_range/1000}um, y{y_range/1000}um, z{z_range/1000}um\n Takes Time {round(end_time-start_time)}s")
    # # fake scan done ------------------------------


    time.sleep(1)
    # some basic setting ---------------------------------------------------------------------
    mode = "trigger"
    # lower = 100
    # higher = 2000000
    # epsilon = 100
    # polarity = 1

    rate_slipstick = 4000E3 # [mHz],  from 1Hz to 5kHz
    num_steps = 100
    out_amp = 30E3 # [mV],  from 0 to 60V
    out_offset = 0.0 # [mV] from 0 to 60V
    target_range = 5.0*1000 # nm
    xyzpp.control.setControlAmplitude(xyzpp.xaxis, out_amp)
    xyzpp.control.setControlFixOutputVoltage(xyzpp.xaxis, out_offset)
    xyzpp.control.setControlFrequency(xyzpp.xaxis, rate_slipstick)
    xyzpp.control.setControlFixOutputVoltage(xyzpp.xaxis, out_offset)
    xyzpp.control.setControlTargetRange(xyzpp.xaxis, target_range)
    xyzpp.move.writeNSteps(xyzpp.xaxis, num_steps)

    xyzpp.control.setControlAmplitude(xyzpp.yaxis, out_amp)
    xyzpp.control.setControlFixOutputVoltage(xyzpp.yaxis, out_offset)
    xyzpp.control.setControlFrequency(xyzpp.yaxis, rate_slipstick)
    xyzpp.control.setControlFixOutputVoltage(xyzpp.yaxis, out_offset)
    xyzpp.control.setControlTargetRange(xyzpp.yaxis, target_range)
    xyzpp.move.writeNSteps(xyzpp.yaxis, num_steps)

    xyzpp.control.setControlAmplitude(xyzpp.zaxis, out_amp)
    xyzpp.control.setControlFixOutputVoltage(xyzpp.zaxis, out_offset)
    xyzpp.control.setControlFrequency(xyzpp.zaxis, rate_slipstick)
    xyzpp.control.setControlFixOutputVoltage(xyzpp.zaxis, out_offset)
    xyzpp.control.setControlTargetRange(xyzpp.zaxis, target_range)
    xyzpp.move.writeNSteps(xyzpp.zaxis, num_steps)

    steps_per_pulse_x = 10 # for open loop only
    steps_per_pulse_y = 10
    # nm_per_pulse_x = 100 # for close loop only
    # nm_per_pulse_y = 111

    xyzpp.rtin.setRealTimeInMode(xyzpp.xaxis, 10) # Trigger LVTTL
    xyzpp.rtin.setRealTimeInMode(xyzpp.yaxis, 10) # Trigger LVTTL
    xyzpp.rtin.setRealTimeInMode(xyzpp.zaxis, 15) # turn off input mode
    xyzpp.rtin.setRealTimeInFeedbackLoopMode(xyzpp.xaxis, 0) # 0:open loop, 1:close loop
    xyzpp.rtin.setRealTimeInFeedbackLoopMode(xyzpp.yaxis, 0)
    xyzpp.rtin.setRealTimeInStepsPerPulse(xyzpp.xaxis, steps_per_pulse_x)
    xyzpp.rtin.setRealTimeInStepsPerPulse(xyzpp.yaxis, steps_per_pulse_y)
    xyzpp.rtin.setRealTimeInFeedbackLoopMode(xyzpp.xaxis, 0) # 0:open loop, 1:close loop
    xyzpp.rtin.setRealTimeInFeedbackLoopMode(xyzpp.yaxis, 0)
    xyzpp.rtin.setRealTimeInStepsPerPulse(xyzpp.xaxis, steps_per_pulse_x)
    xyzpp.rtin.setRealTimeInStepsPerPulse(xyzpp.yaxis, steps_per_pulse_y)
    # xyzpp.rtin.setRealTimeInFeedbackLoopMode(xyzpp.xaxis, 1) # 0:open loop, 1:close loop
    # xyzpp.rtin.setRealTimeInFeedbackLoopMode(xyzpp.yaxis, 1)
    # xyzpp.rtin.setRealTimeInChangePerPulse(xyzpp.xaxis, nm_per_pulse_x)
    # xyzpp.rtin.setRealTimeInChangePerPulse(xyzpp.yaxis, nm_per_pulse_y)
    xyzpp.rtin.apply()

    xyzpp.rtout.setMode(xyzpp.xaxis, 0) # turn off output mode
    xyzpp.rtout.setMode(xyzpp.yaxis, 0) # turn off output mode
    xyzpp.rtout.setMode(xyzpp.zaxis, 0) # turn off output mode
    # xyzpp.rtout.setTriggerConfig(xyzpp.xaxis, higher, lower, epsilon, polarity)
    # xyzpp.rtout.setTriggerConfig(xyzpp.yaxis, higher, lower, epsilon, polarity)
    # xyzpp.rtout.setTriggerConfig(xyzpp.zaxis, higher, lower, epsilon, polarity)
    xyzpp.rtout.apply()

    # move to starting points ----------------------------------------------------------------------------------
    x_start = 1639.6570*1000 # nm
    y_start = 1639.6570*1000 # nm
    z_pos = 200*1000 # nm
    xyzpp.set_x(x_start)
    xyzpp.set_y(y_start)
    xyzpp.set_z(z_pos)

    


    # xyzpp.close_control()
    xyzpp.close()