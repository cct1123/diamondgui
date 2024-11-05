"""
This script includes classes and functions to handle tasks with multi-threads and queue.
It is improved from the pi3diamond softwares developped in Jorg Wrachtrup group and Sen Yang group.

The Singleton pattern is used to ensure that only one instance of the JobManager and Measurement class is created.
The JobManager uses a thread to execute the run() method of the Job objects one by one according to their priority. The JobManager also provides a queue to store the Job objects, and a lock to protect the queue.
The Job class is an abstract class that has a run() method which is the main method to be executed by the JobManager. The run() method is supposed to be overridden in the subclass.
The Measurement class is a subclass of Job and provides a template for a measurement task. 
It has a run() method that is NOT supposed to be overridden in the subclass
But users should define the setup_exp(), run_exp(), upload_dataserv() and shutdown_exp() and handle_exp_error() methods 

Reference: 
    [1] https://github.com/HelmutFedder/pi3diamond/tree/master/tools
    [2] http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python


Author: ChunTung Cheung 
Email: ctcheung1123@gmail.com
Created:  2023-03-03
Modified: 2024-10-03
"""
import numpy as np
import time
import threading
import logging
logger = logging.getLogger(__name__)
from pathlib import Path
import os


INT_INF = np.iinfo(np.int32).max
FLOAT_INF = np.finfo(np.float32).max

def timestamp():
    """Returns the current time as a human readable string."""
    return time.strftime('%y-%m-%d_%Hh%Mm%S', time.localtime())

class StoppableThread(threading.Thread):
    """
    A thread that can be stopped.
    
    Parameters:
        target:    callable that will be execute by the thread
        name:      string that will be used as a name for the thread
    
    Methods:
        stop():    stop the thread
        
    Use threading.current_thread().stop_request.is_set()
    or threading.current_thread().stop_request.wait([timeout])
    in your target callable to react to a stop request.
    """
    
    def __init__(self, group=None, target=None, name=None):
        super().__init__(group=group, target=target, name=name)
        # super().__init__(self, group, target, name)
        self.stop_request = threading.Event()
        
    def stop(self, timeout=10.):
        name = str(self)
        logger.debug('attempt to stop thread '+name)
        if threading.current_thread() is self:
            logger.debug('Thread '+name+' attempted to stop itself. Ignoring stop request...')
            return
        elif not self.is_alive():
            logger.debug('Thread '+name+' is not running. Continuing...')
            return
        self.stop_request.set()
        self.join(timeout)
        if self.is_alive():
            logger.warning('Thread '+name+' failed to join after '+str(timeout)+' s. Continuing anyway...')

class Singleton(type):
    """
    Singleton Metaclass.
    Usage:
    
        #Python2
        class MyClass(BaseClass):
            __metaclass__ = Singleton

        #Python3
        class MyClass(BaseClass, metaclass=Singleton):
            pass
    
    Modified from stackoverflow.com.
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        """
        if there is a key-word argument called "name", then use that name to make class instance, 
        so users can create multiple class instances with different names, it's a "Multiton"

        otherwise just always assigen "default" to the name, so this is a real "Singleton"
        """
        clsname = kwargs["name"] if "name" in kwargs else "default" 
        if cls not in cls._instances:
            # a particular class not existed
            # then create this class 
            # then create an instance of this class with a specific name
            cls._instances[cls] = dict()
            cls._instances[cls][clsname] = super(Singleton, cls).__call__(*args, **kwargs)
        elif clsname not in cls._instances[cls]:
            # a particular class existed
            # but an instance with the specified name not existed
            # then create a new instance of class with the specified name
            cls._instances[cls][clsname] = super(Singleton, cls).__call__(*args, **kwargs)
        #else just call that particular instance of that class with the specified name
        return cls._instances[cls][clsname]

class JobManager(metaclass=Singleton): 
    """
    Provides a queue for starting and stopping jobs according to their priority.
    
    ToDo: In principle this need not be a singleton. Then there could be different job managers handling different sets of resources. 
          However currently we need singleton since the JobManager is called explicitly on ManagedJob class.    
    """
    def __init__(self):
        self._thread = StoppableThread() # the thread the manager loop is running in
        self.lock = threading.Condition() # lock to control access to 'queue' and 'running'
        self.queue = []
        self.running = None
        self.refresh_interval = 0.1 # seconds
    
    def submit(self, job):

        """
        Submit a job.
        
        If there is no job running, the job is appended to the queue.

        If the job is the running job or the job is already in the queue, do nothing.
        
        If job.priority =< priority of the running job,
            the job is appended to the queue and the queue sorted according to priority.
        
        If job.priority > priority of the running job,
            the job is inserted at the first position of the queue, the running job is stopped
            and inserted again at the first position of the queue.
        """

        logger.debug('Attempt to submit job '+str(job))
        self.lock.acquire()
        
        running = self.running
        queue = self.queue

        if job is running or job in queue:
            logger.info('The job '+str(job)+' is already running or in the queue.')
            self.lock.release()
            return

        queue.append(job)
        queue.sort(key=lambda job: job.priority, reverse=True) # ToDo: Job sorting not thoroughly tested
        job.state='wait'
                    
        logger.debug('Notifying process thread.')
        self.lock.notify()
            
        self.lock.release()
        logger.debug('Job '+str(job)+' submitted.')
 
    def remove(self, job):
        
        """
        Remove a job.
        
        If the job is running, stop it.
        
        If the job is in the queue, remove it.
        
        If the job is not found, this will result in an exception.
        """
 
        logger.debug('Attempt to remove job '+str(job))
        self.lock.acquire()

        try:
            if job is self.running:
                logger.debug('Job '+str(job)+' is running. Attempt stop.')
                job.stop()
                logger.debug('Job '+str(job)+' removed.')
            else:
                if not job in self.queue:
                    logger.debug('Job '+str(job)+' neither running nor in queue. Returning.')
                else:
                    logger.debug('Job '+str(job)+' is in queue. Attempt remove.')
                    self.queue.remove(job)
                    logger.debug('Job '+str(job)+' removed.')
                    job.state='idle' # ToDo: improve handling of state. Move handling to Job?
        finally:
            self.lock.release()
        
    def start(self):
        """Start the process loop in a thread."""
        if self._thread.is_alive():
            return
        logger.info('Starting Job Manager.')
        self._thread = StoppableThread(target = self._process, name=self.__class__.__name__ + timestamp())
        self._thread.start()
    
    def stop(self, timeout=None):
        """Stop the process loop."""
        self._thread.stop_request.set()
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()        
        self._thread.stop(timeout=timeout)
    
    def _process(self):
        
        """
        The process loop.
        
        Use .start() and .stop() methods to start and stop processing of the queue.
        """
        
        while True:
            
            self._thread.stop_request.wait(self.refresh_interval)
            if self._thread.stop_request.is_set():
                break
            
            # ToDo: jobs can be in queue before process loop is started
            # what happens when manager is stopped while jobs are running?
            
            self.lock.acquire()
            if self.running is None:
                if self.queue == []:
                    logger.debug('No job running. No job in queue. Waiting for notification.')
                    self.lock.wait()
                    logger.debug('Caught notification.')
                    if self._thread.stop_request.is_set():
                        self.lock.release()        
                        break
                logger.debug('Attempt to fetch first job in queue.')
                self.running = self.queue.pop(0)
                logger.debug('Found job '+str(self.running)+'. Starting.')
                self.running.start()
            elif not self.running._thread.is_alive():
                logger.debug('Job '+str(self.running)+' stopped.')
                self.running=None
                if self.queue != []:
                    logger.debug('Attempt to fetch first job in queue.')
                    self.running = self.queue.pop(0)
                    logger.debug('Found job '+str(self.running)+'. Starting.')
                    self.running.start()
            elif self.queue != [] and self.queue[0].priority > self.running.priority:
                logger.debug('Found job '+str(self.queue[0])+' in queue with higher priority than running job. Attempt to stop running job.')            
                self.running.pause()
                if self.running.state != 'done':
                    logger.debug('Reinserting job '+str(self.running)+' in queue.')
                    self.queue.insert(0,self.running)
                    self.queue.sort(key=lambda job: job.priority, reverse=True) # ToDo: Job sorting not thoroughly tested
                    self.running.state='wait'
                self.running = self.queue.pop(0)
                logger.debug('Found job '+str(self.running)+'. Starting.')
                self.running.start()                
            self.lock.release() 

class Job(metaclass=Singleton):
    _refresh_interval = 0.01
    _name = "dummyjob"
    _thread = StoppableThread()

    priority = 1 # from 1 to 10
    state = "idle" # 'idle', 'run', 'wait', 'done', 'error'
    tokeep = False  # whether to keep the data when the thread is stopped (idx_run<=num_run)

    
    time_stop = FLOAT_INF# time the job is stopped
    time_run = 0.0 # readonly, accumulated measurement time
    num_run = INT_INF # number of repetition, 
    idx_run = 0 # indicating which iteration we are at, 1-based

    def __init__(self, name="default"):
        self._name =  self.__class__.__name__+"-"+name
        self._uiid = self._name + "-" + "ui"

    def set_name(self, name):
        self._name =  self.__class__.__name__+"-"+name
        self._uiid = self._name + "-" + "ui"

    def get_uiid(self):
        return self._uiid

    def get_classname(self):
        return self.__class__.__name__

    def get_name(self):
        return self._name

    def set_priority(self, order):
        self.priority = order

    def set_runnum(self, num):
        # set either num_run or time_stop but not both of them!!
        self.num_run = num
        self.time_stop = FLOAT_INF

    def set_stoptime(self, time):
        # set either num_run or time_stop but not both of them!!
        self.time_stop = time
        self.num_run = INT_INF

    def set_tokeep(self, keepdata):
        # keepdata? (bool)
        self.tokeep = keepdata

    # methods for handling the run thread====================================
    def start(self):
        self._thread = StoppableThread(target = self._run, name=self.__class__.__name__ + str(time.time()))
        self._thread.start()

    def pause(self, timeout=None):
        """Stop the process loop."""
        self._thread.stop_request.set()  
        self._thread.stop(timeout=timeout)
        self.tokeep = True
    
    def stop(self, timeout=None):
        self.pause(timeout)
        self.tokeep = False # this must be placed after pause()
        self.state = 'idle'
    # ======================================================================

    def _run(self):
        """
        Method that is running in a thread.
        It should NOT be modified or called in other script
        """
        try:
            self.time_run = 0
            self.idx_run = 0
            self.state='run'
            time_start = time.time()
            # self._setup_exp()
            for _ in range(self.num_run):
                self._thread.stop_request.wait(self._refresh_interval)
                stopflag = (self.time_run>self.time_stop) or \
                           (self._thread.stop_request.is_set()) or \
                           (self.idx_run==self.num_run)
                if stopflag:
                    logger.debug('Received stop signal. Returning from thread.')
                    break
                # self._run_exp()

                # update the run idex and run time
                self.idx_run += 1
                time_now = time.time()
                self.time_run = time_now - time_start

                # self._upload_dataserv()

            # after the for-loop passed or completed
        except:
            logger.exception('Error in job.')
            self.state='error'
            # self._handle_exp_error()
        finally:
            # put state indicator
            if self.idx_run == 0:
                self.state = "idle"
            elif self.idx_run < self.num_run and self.time_run < self.time_stop:
                self.state = 'wait'
            elif self.idx_run == self.num_run or self.time_run >= self.time_stop:
                self.state = 'done'
            else:
                self.state = 'error'
            logger.debug('Reseting the job.')  
            # self._shutdown_exp()

class Measurement(Job):
    # buffer = np.array([], dtype=np.float64, order='C')
    # buffer should be handled in the hardware class object
    
    # ==some dictionaries stored with some default values--------------------------
    __stateset = dict(
                priority=Job.priority,
                state=Job.state,
                time_run=Job.time_run,
                time_stop=Job.time_stop,
                idx_run=Job.idx_run, 
                num_run=Job.num_run
            )
    # !!< has to be specific by users>
    __paraset = dict() # store all parameters for experiments
    # !!< has to be specific by users>
    __dataset = dict() # store all signals from measurements 
    # ==--------------------------------------------------------------------------

    def __init__(self, name="default", paraset_initial=__paraset, dataset_initial=__dataset, stateset_initial=__stateset):
        self.set_name(name)
        self.__stateset = stateset_initial
        self.__paraset = paraset_initial
        self.__dataset = dataset_initial
        self.reset_paraaset()
        self.reset_dataset()
        self.reset_stateset()

    def reset_paraaset(self):
        # initialize the dataset structure
        self.paraset = self.__paraset.copy()
        self.tokeep = False

    def set_paraset(self, **para_dict):
        # set parametes
        for kk, vv in para_dict.items():
            self.paraset[kk] = vv
        self.tokeep = False

    def reset_dataset(self):
        # initialize the dataset structure
        self.dataset = self.__dataset.copy()
        self.tokeep = False

    def set_dataset(self, **data_dict):
        # set datat
        for kk, vv in data_dict.items():
            self.dataset[kk] = vv


    def reset_stateset(self):
        self.stateset = self.__stateset.copy()

    def _setup_exp(self):
        """
        Setup the experiment. This is called at the beginning of each measurement.

        If self.tokeep is False, do something, like initializing the dataset.

        !! Put super()._setup_exp() at the end of your _setup_exp()
        """
        # check the parameters if needed -------------------------------------
        
        # setup the hardwares here--------------------------------------------

        # setup the data structure here---------------------------------------

        pass

        

    def _run_exp(self):
        """
        Run the experiment. This is called in each iteration of the measurement.
        
        Overwrite this method to define the experiment.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        pass

    def _upload_dataserv(self):
        """
        Upload the current state and data to the data server.
        
        This method is called by the measurement framework after each
        iteration of the measurement. It is used to send the current
        state and data to the data server.
        
        !! Put super()._upload_dataserv() at the end of your _upload_dataserv()
        """
        
        self.stateset = dict(
            priority=self.priority,
            state=self.state,
            time_run=self.time_run,
            time_stop=self.time_stop,
            idx_run=self.idx_run, 
            num_run=self.num_run
        )
        
        to_dataserv = dict(
            # name=__name__,
            stateset= self.stateset,
            paraset = self.paraset, 
            dataset = self.dataset
        )

        # push the data to the data server-------
        pass #TODO save the data to a temporary file but itwill slow down the measurement event loop
        # ---------------------------------------


    def _handle_exp_error(self):
        """
        Handle experiment errors
        
        This method is called by the measurement framework if an error
        occurs during the measurement. It is used to handle the error and
        take appropriate actions.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        pass


    def _shutdown_exp(self):
        """
        Shutdown the experiment
        
        This method is called by the measurement framework when the measurement
        is stopped. It is used to shutdown the experiment and disconnect the
        instrument gateway.
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """
        pass

    def _run(self):
        """
        Method that is running in a thread.
        It should NOT be modified or called in any classes of the lower hierachy
        This method is used to run the experiment in a separate thread managed by the singelton job manager 

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        try:
            print(f"in task base measurement, state is {self.state}")
            self._setup_exp() # !! <defined by users>
            # --------------------------------------------------------------------
            # whether to keep the parameters and data when the thread is stopped
            if not self.tokeep:
                self.idx_run = 0
                self.time_run = 0
                # reset the dataset
                self.reset_dataset()
                self.idx_run = 0

            self.state='run'
            time_start = time.time()-self.time_run
            for _ in range(self.num_run):
                self._thread.stop_request.wait(self._refresh_interval)
                stopflag = (self.time_run>=self.time_stop) or \
                (self._thread.stop_request.is_set()) or \
                (self.idx_run==self.num_run)
                if stopflag:
                    logger.debug('Received stop signal. Returning from thread.')
                    break
                
                self._run_exp() # !! <defined by users>

                # update the run idex and run time
                self.idx_run += 1
                time_now = time.time()
                self.time_run = time_now - time_start

                self._upload_dataserv() # !! <defined by users>

        except Exception as ee:
            logger.exception(f'Error in job: {ee}')
            self.state='error'
            self._handle_exp_error() # !! <defined by users>
        finally:
            # put state indicator
            if self.idx_run == 0:
                self.state = "idle"
            elif self.idx_run < self.num_run and self.time_run < self.time_stop:
                self.state = 'wait'
                self.tokeep = True
            elif self.idx_run == self.num_run or self.time_run >= self.time_stop:
                self.state = 'done'
                self.tokeep = False
            else:
                self.state = 'error'
                self.tokeep = False
            self._upload_dataserv() # !! <defined by users>
            logger.debug('Reseting all instruments.')  
            self._shutdown_exp() # !! <defined by users>

class DummyMeasurement(Measurement):

    def __init__(self, name="dumdefault"):
        # ==some dictionaries stored with some default values--------------------------
        # __stateset = super().__stateset.copy()
        # !!< has to be specific by users>
        __paraset = dict(epicpara1=0, 
                        epicpara2="",
                        volt_amp=1, 
                        freq=20.0, 
                        length=100)
        # !!< has to be specific by users>
        __dataset = dict(signal=np.zeros(1), timestamp=np.zeros(1))
        # ==--------------------------------------------------------------------------
        super().__init__(name, __paraset, __dataset)

    def _setup_exp(self):
        super()._setup_exp()
        logger.debug(f"Parameters are: {self.paraset}")
        logger.debug(f"this class name: {self.__class__.__name__}")
        logger.debug("Hello it's set up!")
        logger.debug(f"total number of runs: {self.num_run}")
        self.buffer_rawdata = np.zeros(self.paraset["length"])
        self.buffer_timetime = np.zeros(self.paraset["length"])

    def _run_exp(self):
        logger.debug(f"hey fake experiment-'{self._name}' no.{self.idx_run}")
        logger.debug(f"I'm cooking some fake data")
        time.sleep(0.1)
        self.buffer_timetime = (np.arange(self.paraset["length"])+self.time_run)/1E3
        self.buffer_rawdata = (1+0.3*np.random.rand(self.paraset["length"]))*self.paraset["volt_amp"]*np.sin(2*np.pi*self.paraset["freq"]*self.buffer_timetime)

    def _upload_dataserv(self):
        logger.debug(f"Moving data to a data server if you have one")
        self.dataset["signal"] = np.copy(self.buffer_rawdata)
        self.dataset["timestamp"] = np.copy(self.buffer_timetime) + self.buffer_timetime
        super()._upload_dataserv()  

    def _handle_exp_error(self):
        super()._handle_exp_error()
        logger.debug(f"dumdum measurement has troubles!")


    def _shutdown_exp(self):
        super()._shutdown_exp()
        logger.debug(f"goodbye dumdum measurement")

if __name__ == "__main__":
    """
    FOR TEST ONLY
    """

    '''
    Test the Singleton Metaclass
    '''
    class epicfruit(metaclass=Singleton):
        def __init__(self, name="default"):
            # self._name = name
            pass

    class fakeepicfruit(metaclass=Singleton):
        def __init__(self, name="default"):
            # self._name = name
            pass

    class easyfruit():
        def __init__(self, name="default"):
            # self._name = name
            pass

    godfruit = easyfruit()
    godfruit_ex = easyfruit()
    print(f"When NOT using any Metaclass,")
    print(f"   Is godfruit and godfruit_ex the same? {godfruit is godfruit_ex}")
    godfruit = epicfruit()
    godfruit_ex = epicfruit()
    fakegodfruit = fakeepicfruit()
    print(f"When using Singleton,")
    print(f"   Is godfruit and godfruit_ex the same? {godfruit is godfruit_ex}")
    print(f"   Is godfruit and fakegodfruit the same? {godfruit is fakegodfruit}")
    myfruit = epicfruit(name="apple")
    myfruit_ex = epicfruit(name="banana")
    myfruit_ex_junior = epicfruit(name="banana")
    myfruit_ex_fake = fakeepicfruit(name="banana")
    print(f"When using Multiton,")
    print(f"   Is myfruit and myfruit_ex the same? {myfruit is myfruit_ex}")
    print(f"   Is myfruit_ex_junior and myfruit_ex the same? {myfruit_ex_junior is myfruit_ex}")
    print(f"   Is myfruit_ex_fake and myfruit_ex the same? {myfruit_ex_fake is myfruit_ex}")

    '''
    Test the Measurement class and job management
    '''

               
    jobmanager = JobManager()
    jobmanager.start()
    time.sleep(1)

    dmmm1 = DummyMeasurement()
    dmmm1.set_runnum(9)
    dmmm1.set_paraset(epicpara1=6565, epicpara2="I ate breakfast")
    jobmanager.submit(dmmm1) 


    jobs = [DummyMeasurement(name=f"rrrr{i}") for i in range(5)]
    
    jobs[0].priority = 4
    jobs[0].num_run = 5
    jobs[1].priority = 1
    jobs[2].priority = 0
    jobs[3].priority = 10
    jobs[4].priority = 0
    

    for job in jobs:
        JobManager().submit(job) 
    jobmanager.remove(jobs[4])

    time.sleep(0.1)
    q = JobManager().queue
    print([job for job in q])
    print([job.priority for job in q])
    print([q.index(job) if job in q else None for job in jobs])

    time.sleep(10)
    jobmanager.stop(1)