"""
classes and functions to handle tasks with multi-threads and queue

copied directly from pi3diamond in Sen Yang's group

"""

import time
import threading
import logging


logger = logging.getLogger(__name__)

class StoppableThread( threading.Thread ):
    """
    A thread that can be stopped.
    
    Parameters:
        target:    callable that will be execute by the thread
        name:      string that will be used as a name for the thread
    
    Methods:
        stop():    stop the thread
        
    Use threading.currentThread().stop_request.isSet()
    or threading.currentThread().stop_request.wait([timeout])
    in your target callable to react to a stop request.
    """
    
    def __init__(self, group=None, target=None, name=None):
        super().__init__(group=group, target=target, name=name)
        # super().__init__(self, group, target, name)
        self.stop_request = threading.Event()
        
    def stop(self, timeout=10.):
        name = str(self)
        logger.debug('attempt to stop thread '+name)
        if threading.currentThread() is self:
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
    Singleton using metaclass.
    
    Usage:
    
    class Myclass( MyBaseClass )
        __metaclass__ = Singleton
    
    Taken from stackoverflow.com.
    http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class JobManager(metaclass=Singleton): # ToDo: In principle this need not be a singleton. Then there could be different job managers handling different sets of resources. However currently we need singleton since the JobManager is called explicitly on ManagedJob class.    
    """Provides a queue for starting and stopping jobs according to their priority."""
    def __init__(self):
        self.thread = StoppableThread() # the thread the manager loop is running in
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
        queue.sort(cmp=lambda x,y: cmp(x.priority,y.priority), reverse=True) # ToDo: Job sorting not thoroughly tested
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
        if self.thread.is_alive():
            return
        logging.getLogger().info('Starting Job Manager.')
        self.thread = StoppableThread(target = self._process, name=self.__class__.__name__ + timestamp())
        self.thread.start()
    
    def stop(self, timeout=None):
        """Stop the process loop."""
        self.thread.stop_request.set()
        self.lock.acquire()
        self.lock.notify()
        self.lock.release()        
        self.thread.stop(timeout=timeout)
    
    def _process(self):
        
        """
        The process loop.
        
        Use .start() and .stop() methods to start and stop processing of the queue.
        """
        
        while True:
            
            self.thread.stop_request.wait(self.refresh_interval)
            if self.thread.stop_request.isSet():
                break
            
            # ToDo: jobs can be in queue before process loop is started
            # what happens when manager is stopped while jobs are running?
            
            self.lock.acquire()
            if self.running is None:
                if self.queue == []:
                    logging.debug('No job running. No job in queue. Waiting for notification.')
                    self.lock.wait()
                    logging.debug('Caught notification.')
                    if self.thread.stop_request.isSet():
                        self.lock.release()        
                        break
                logging.debug('Attempt to fetch first job in queue.')
                self.running = self.queue.pop(0)
                logging.debug('Found job '+str(self.running)+'. Starting.')
                self.running.start()
            elif not self.running.thread.is_alive():
                logging.debug('Job '+str(self.running)+' stopped.')
                self.running=None
                if self.queue != []:
                    logging.debug('Attempt to fetch first job in queue.')
                    self.running = self.queue.pop(0)
                    logging.debug('Found job '+str(self.running)+'. Starting.')
                    self.running.start()
            elif self.queue != [] and self.queue[0].priority > self.running.priority:
                logging.debug('Found job '+str(self.queue[0])+' in queue with higher priority than running job. Attempt to stop running job.')            
                self.running.stop()
                if self.running.state != 'done':
                    logging.debug('Reinserting job '+str(self.running)+' in queue.')
                    self.queue.insert(0,self.running)
                    self.queue.sort(cmp=lambda x,y: cmp(x.priority,y.priority), reverse=True) # ToDo: Job sorting not thoroughly tested
                    self.running.state='wait'
                self.running = self.queue.pop(0)
                logging.debug('Found job '+str(self.running)+'. Starting.')
                self.running.start()                
            self.lock.release() 

if __name__ == "__main__":
    class DummyJob():

        name = "Dummy_task"

        priority = 1 # from 1 to 10
        state = "idle" # 'idle', 'run', 'wait', 'done', 'error'
        thread = StoppableThread()

        keep_data = True # whether to the data when the measurement is paused (idx_iter<num_iter)
        time_mea = 0.0 # readonly, accumulated measurement time
        num_iter = 100 # number of iteration, readonly
        idx_iter = 0 # indicating which iteration we are at, 1-based
        to_keep = False

        params = dict()
        dataset = dict(raw=[[]]) # store the raw data of each iteration

    def __init__(self, 
        name="Dummy_task"
        ):
        self.name = name

    def set_expname(self, name):
        self.name = name

    def set_priority(self, order):
        self.priority = order
    
    def set_iternum(self, num):
        self.num_iter = num

    def set_keepdata(self, to_keep):
        self.keep_data = to_keep

    def set_params(self, para_dict):
            # set parametes
        for kk, vv in para_dict.items():
            self.params[kk] = vv

    def _setup_exp(self):

        if not self.keep_data:
            self.idx_iter = 0
            # reset the dataset
            self.dataset = dict()

        # setup the hardwares
        # gw.set_something(self.params["var1"])

    def _run_exp(self):
        # exp_name: label of the measurement for dataset
        # run the experiment
        self.data["raw"] = []
        self.to_dataserv["data"] = self.data

        
    def _upload_dataserv(self):
        status = dict(
            priority=self.priority,
            state=self.state,
            run_time=self.run_time,
            idx_iter=self.idx_iter, 
            num_iter=self.num_iter
        )
        
        to_dataserv = dict(
            # name=__name__,
            status = status,
            params = self.params, 
            datasets = self.dataset
        )
        # push the data to the data server
        with self.ds as pipe:
            pipe.push(self.to_dataserv)

    def _shutdown_exp(self):
        pass

    def _run(self):
        """Method that is run in a thread."""
        try:
            self.state='run'
            start_time = time.time()
            self._setup_exp()
            for iii in range(self.num_iter):
                self.thread.stop_request.wait(1.0) # little trick to have a long (1 s) refresh interval but still react immediately to a stop request
                if self.thread.stop_request.isSet():
                    logger.debug('Received stop signal. Returning from thread.')
                    break
                
                self._run_exp()

                self.num_iter += 1 
                curr_time = time.time()
                self.run_time = curr_time - start_time
                self.idx_iter += 1
                self._upload_dataserv()
            else:
                if self.num_iter == 0:
                    self.state = "idle"
                else:
                    self.state='done'
        except:
            logger.exception('Error in job.')
            self.state='error'
        finally:
            logger.debug('Turning off all instruments.')  
            self._shutdown_exp()