"""
classes and functions to handle tasks with multi-threads and queue.

copied and modified from the pi3diamond in Sen Yang's group.

Reference: 
    [1] https://github.com/HelmutFedder/pi3diamond
    [2] http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python


Author: ChunTung Cheung 
Email: ctcheung1123@gmail.com
Created:  2023-03-03
Modified: 2023-07-21

"""
import numpy as np
import time
import threading
import logging
from pathlib import Path
import os

settings_folder = Path(__file__).parent
logging_file = os.path.join(settings_folder, "temp.log")
logging.basicConfig(
 filename = logging_file,
 filemode = 'a',
 format = '%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
 datefmt = '%H:%M:%S',
 level = logging.DEBUG
)
logging.getLogger(logging_file)

if not os.path.isdir(settings_folder):
    os.mkdir(settings_folder)

# add logging to console and log file
logging.basicConfig(filename=logging_file, format='%(asctime)s (%(levelname)s) %(message)s', level=logging.DEBUG,
                    datefmt='%d.%m.%Y %H:%M:%S')
logging.getLogger().addHandler(logging.StreamHandler())

def timestamp():
    """Returns the current time as a human readable string."""
    return time.strftime('%y-%m-%d_%Hh%Mm%S', time.localtime())

class StoppableThread( threading.Thread ):
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
        logging.debug('attempt to stop thread '+name)
        if threading.current_thread() is self:
            logging.debug('Thread '+name+' attempted to stop itself. Ignoring stop request...')
            return
        elif not self.is_alive():
            logging.debug('Thread '+name+' is not running. Continuing...')
            return
        self.stop_request.set()
        self.join(timeout)
        if self.is_alive():
            logging.warning('Thread '+name+' failed to join after '+str(timeout)+' s. Continuing anyway...')

class Singleton(type):
    """
    Singleton using metaclass.
    
    Usage:
    
    class Myclass( MyBaseClass )
        __metaclass__ = Singleton
    
    Modified from stackoverflow.com.
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        clsname = kwargs["name"] if "name" in kwargs else "default"
        if cls not in cls._instances:
            # no class object is created
            cls._instances[cls] = dict()
            cls._instances[cls][clsname] = super(Singleton, cls).__call__(*args, **kwargs)
        elif clsname not in cls._instances[cls]:
            # some class objects are created but not with the new name
            cls._instances[cls][clsname] = super(Singleton, cls).__call__(*args, **kwargs)
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

        logging.debug('Attempt to submit job '+str(job))
        self.lock.acquire()
        
        running = self.running
        queue = self.queue

        if job is running or job in queue:
            logging.info('The job '+str(job)+' is already running or in the queue.')
            self.lock.release()
            return

        queue.append(job)
        # queue.sort(key=lambda job: job.priority, reverse=True) # ToDo: Job sorting not thoroughly tested
        job.state='wait'
                    
        logging.debug('Notifying process thread.')
        self.lock.notify()
            
        self.lock.release()
        logging.debug('Job '+str(job)+' submitted.')
 
    def remove(self, job):
        
        """
        Remove a job.
        
        If the job is running, stop it.
        
        If the job is in the queue, remove it.
        
        If the job is not found, this will result in an exception.
        """
 
        logging.debug('Attempt to remove job '+str(job))
        self.lock.acquire()

        try:
            if job is self.running:
                logging.debug('Job '+str(job)+' is running. Attempt stop.')
                job.stop()
                logging.debug('Job '+str(job)+' removed.')
            else:
                if not job in self.queue:
                    logging.debug('Job '+str(job)+' neither running nor in queue. Returning.')
                else:
                    logging.debug('Job '+str(job)+' is in queue. Attempt remove.')
                    self.queue.remove(job)
                    logging.debug('Job '+str(job)+' removed.')
                    job.state='idle' # ToDo: improve handling of state. Move handling to Job?
        finally:
            self.lock.release()
        
    def start(self):
        """Start the process loop in a thread."""
        if self._thread.is_alive():
            return
        logging.getLogger().info('Starting Job Manager.')
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
                    logging.debug('No job running. No job in queue. Waiting for notification.')
                    self.lock.wait()
                    logging.debug('Caught notification.')
                    if self._thread.stop_request.is_set():
                        self.lock.release()        
                        break
                logging.debug('Attempt to fetch first job in queue.')
                self.running = self.queue.pop(0)
                logging.debug('Found job '+str(self.running)+'. Starting.')
                self.running.start()
            elif not self.running._thread.is_alive():
                logging.debug('Job '+str(self.running)+' stopped.')
                self.running=None
                if self.queue != []:
                    logging.debug('Attempt to fetch first job in queue.')
                    self.running = self.queue.pop(0)
                    logging.debug('Found job '+str(self.running)+'. Starting.')
                    self.running.start()
            elif self.queue != [] and self.queue[0].priority > self.running.priority:
                logging.debug('Found job '+str(self.queue[0])+' in queue with higher priority than running job. Attempt to stop running job.')            
                self.running.pause()
                if self.running.state != 'done':
                    logging.debug('Reinserting job '+str(self.running)+' in queue.')
                    self.queue.insert(0,self.running)
                    self.queue.sort(key=lambda job: job.priority, reverse=True) # ToDo: Job sorting not thoroughly tested
                    self.running.state='wait'
                self.running = self.queue.pop(0)
                logging.debug('Found job '+str(self.running)+'. Starting.')
                self.running.start()                
            self.lock.release() 

class Job(metaclass=Singleton):
    _refresh_interval = 0.001
    _name = "dummyjob"
    _thread = StoppableThread()

    priority = 1 # from 1 to 10
    state = "idle" # 'idle', 'run', 'wait', 'done', 'error'
    tokeep = False  # whether to keep the data when the thread is stopped (idx_run<=num_run)

    time_run = 0.0 # readonly, accumulated measurement time
    num_run = 2 # number of repetition, 
    idx_run = 0 # indicating which iteration we are at, 1-based

    def __init__(self, name="default"):
        self._name =  self.__class__.__name__+"-"+name

    def set_name(self, name):
        self._name =  self.__class__.__name__+"-"+name

    def set_priority(self, order):
        self.priority = order

    def set_runnum(self, num):
        self.num_run = num

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
    # ======================================================================

    def _run(self):
        """
        Method that is running in a thread.
        It should NOT be modified or called in other script
        """
        try:
            self.state='run'
            time_start = time.time()
            self.time_run = 0
            # self._setup_exp()
            for _ in range(self.num_run):
                self._thread.stop_request.wait(self._refresh_interval)
                if self._thread.stop_request.is_set() or self.idx_run==self.num_run:
                    logging.debug('Received stop signal. Returning from thread.')
                    break
                
                # self._run_exp()
                
                time_now = time.time()
                self.time_run = time_now - time_start
                self.idx_run += 1
                # self._upload_dataserv()
            else:
                if self.num_run == 0:
                    self.state = "idle"
                else:
                    self.state='done'
        except:
            logging.exception('Error in job.')
            self.state='error'
            # self._handle_exp_error()
        finally:
            logging.debug('Reseting the job.')  
            # self._shutdown_exp()

from nspyre import InstrumentGateway
from nspyre import DataSource
# from rpyc.utils.classic import obtain
class Measurement(Job):
    # buffer = np.array([], dtype=np.float64, order='C')
    # buffer should be handled in the hardware class object
    paraset = dict() # store all parameters for experiments
    dataset = dict() # store all signals from measurements 

    def __init__(self, name="default"):
        self._name = self.__class__.__name__+"-"+name

    def reset_paraaset(self):
        # initialize the dataset structure
        self.paraset = dict()

    def set_paraset(self, **para_dict):
        # set parametes
        for kk, vv in para_dict.items():
            self.paraset[kk] = vv

    def reset_dataset(self):
        # initialize the dataset structure
        self.dataset = dict()

    def set_dataset(self, **data_dict):
        # set datat
        for kk, vv in data_dict.items():
            self.dataset[kk] = vv

    def _setup_exp(self):
        # check the parameters if needed -------------------------------------
        if not self.tokeep:
            self.idx_run = 0
            self.time_run = 0
            self.state = "idle"
            # reset the dataset
            self.reset_dataset()
            self.idx_run = 0

        self.gw = InstrumentGateway(addr='127.0.0.1')
        self.ds = DataSource(self._name, addr='127.0.0.1')

        self.ds.start()
        # --------------------------------------------------------------------
        self.gw.connect()
        # setup the hardwares here--------------------------------------------
        # # gw.aninstrument.set_something(self.paraset["var1"])
        # --------------------------------------------------------------------


    def _run_exp(self):
        # run the experiment
        # self.dataset = self.gw.nidaq.read_data()
        pass

    def _upload_dataserv(self):
        stateset = dict(
            priority=self.priority,
            state=self.state,
            time_run=self.time_run,
            idx_run=self.idx_run, 
            num_run=self.num_run
        )
        
        to_dataserv = dict(
            # name=__name__,
            stateset= stateset,
            paraset = self.paraset, 
            dataset = self.dataset
        )
        # push the data to the data server
        self.ds.push(to_dataserv)

    def _handle_exp_error(self):
        pass

    def _shutdown_exp(self):
        self.ds.stop()

        # set the hardwares here ------------------------------------
        # # gw.aninstrument.set_something(self.paraset["var1"])
        self.gw.disconnect()
        # -----------------------------------------------------------

    def _run(self):
        """
        Method that is running in a thread.
        It should NOT be modified or called in any classes of the lower hierachy
        """
        try:
            self.state='run'
            time_start = time.time()
            self.time_run = 0
            self._setup_exp()
            for _ in range(self.num_run):
                self._thread.stop_request.wait(self._refresh_interval)
                if self._thread.stop_request.is_set() or self.idx_run==self.num_run:
                    logging.debug('Received stop signal. Returning from thread.')
                    break
                self.idx_run += 1
                time_now = time.time()
                self.time_run = time_now - time_start

                self._run_exp()
                self._upload_dataserv()
            else:
                if self.num_run == 0:
                    self.state = "idle"
                else:
                    self.state='done'
        except:
            logging.exception('Error in job.')
            self.state='error'
            self._handle_exp_error()
        finally:
            logging.debug('Reseting all instruments.')  
            self._shutdown_exp()

if __name__ == "__main__":
    '''
    for test only
    '''
    class DummyMeasurement(Measurement):
        dumvariable = 500

        paraset = dict(epicpara1=0, 
                       epicpara2="",
                       abc=1, 
                       bbb=555)
        
        def __init__(self, name="dumdefault"):
            super().__init__(name=name)
            # self._name = name

        def reset_dataset(self):
            
            self.dataset = dict(signal=np.zeros(self.num_run), ref=[])

        def _setup_exp(self):
            super()._setup_exp()
            logging.debug(f"Parameters are: {self.paraset}")
            logging.debug(f"this class name: {self.__class__.__name__}")
            logging.debug("Hello it's set up!")
            logging.debug(f"total number of runs: {self.num_run}")


        def _run_exp(self):
            logging.debug(f"hey fake experiment-'{self._name}' no.{self.idx_run}")
            self.dataset["signal"][self.idx_run-1] = self.paraset["epicpara1"]+self.idx_run
        def _shutdown_exp(self):
            super()._shutdown_exp()
            logging.debug(f"goodbye dumdum measurement")
               
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