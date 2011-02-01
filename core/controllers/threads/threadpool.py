"""Easy to use object-oriented thread pool framework.

A thread pool is a class that maintains a pool of worker threads to perform
time consuming operations in parallel. It assigns jobs to the threads
by putting them in a work request queue, where they are picked up by the
next available thread. This then performs the requested operation in the
background and puts the results in a another queue.

The thread pool class can then collect the results from all threads from
this queue as soon as they become available or after all threads have
finished their work. It's also possible, to define callbacks to handle
each result as it comes in.

The basic concept and some code was taken from the book "Python in a Nutshell"
by Alex Martelli, copyright 2003, ISBN 0-596-00188-6, from section 14.5
"Threaded Program Architecture". I wrapped the main program logic in the
ThreadPool class, added the WorkRequest class and the callback system and
tweaked the code here and there.

Basic usage:

    <<< main = TreadPool(poolsize)
    <<< requests = makeRequests(some_callable, list_of_args, callback)
    <<< [main.putRequests(req) for req in requests]
    <<< main.wait()

See the end of the module code for a brief, annotated usage example.
"""

__all__ = ['makeRequests', 'NoResultsPending', 'NoWorkersAvailable',
  'ThreadPool', 'WorkRequest', 'WorkerThread']

__author__ = "Christopher Arndt"
__version__ = "1.1"
__date__ = "2005-07-19"

import threading, Queue
import core.controllers.outputManager as om
import traceback
import time

DEBUG = False

class NoResultsPending(Exception):
    """All work requests have been processed."""
    pass
class NoWorkersAvailable(Exception):
    """No worker threads available to process remaining requests."""
    pass

class WorkerThread(threading.Thread):
    """Background thread connected to the requests/results queues.

    A worker thread sits in the background and picks up work requests from
    one queue and puts the results in another until it is dismissed.
    """

    def __init__(self, requestsQueue, resultsQueue, **kwds):
        """Set up thread in damonic mode and start it immediatedly.

        requestsQueue and resultQueue are instances of Queue.Queue passed
        by the ThreadPool class when it creates a new worker thread.
        """
        threading.Thread.__init__(self, **kwds)
        self.setDaemon(1)
        self.workRequestQueue = requestsQueue
        if DEBUG:
            print '[worker] Init with queue',  id(self.workRequestQueue)
        self.resultQueue = resultsQueue
        self._dismissed = threading.Event()
        self.start()

    def run(self):
        """Repeatedly process the job queue until told to exit.
        """
        while not self._dismissed.isSet():
            
            if DEBUG:
                msg = '[worker] Blocking at Queue.get().'
                om.out.debug( msg )
                
            try:
                # thread blocks here for 1 second, if queue empty
                request = self.workRequestQueue.get(timeout=1)
            except:
                if DEBUG:
                    msg = '[worker] Is blocked at Queue.get() because the queue is empty (size='
                    msg += str(self.workRequestQueue.qsize()) +').'
                    om.out.debug( msg )
                continue

            
            if DEBUG:
                msg = '[worker] Unblocking after Queue.get().'
                om.out.debug( msg )
                msg = '[worker] workRequestQueue length for thread with id ' + str(id(self)) + ' is '
                msg += str(self.workRequestQueue.qsize())
                om.out.debug( msg )
            
            if self._dismissed.isSet():
                # return the work request we just picked up
                self.workRequestQueue.put(request)
                break # and exit
            
            try:
                self.resultQueue.put( (request, request.callable(*request.args, **request.kwds)) )
            except Exception, e:
                om.out.debug('The thread: ' + str(self) + ' raised an exception while running the request: ' + str(request.callable) )
                om.out.debug('Exception: ' + str( e ) )
                om.out.debug( 'Traceback: ' + str( traceback.format_exc() ) )
                self.resultQueue.put( (request, e) )
        
        if DEBUG:
            om.out.debug('[worker] Ending!')
                
            

    def dismiss(self):
        """Sets a flag to tell the thread to exit when done with current job.
        """
        self._dismissed.set()


class WorkRequest(object):
    """A request to execute a callable for putting in the request queue later.

    See the module function makeRequests() for the common case
    where you want to build several work requests for the same callable
    but different arguments for each call.
    """

    def __init__(self, callable, args=None, kwds=None, requestID=None, callback=None, ownerObj=None):
        """A work request consists of the a callable to be executed by a
        worker thread, a list of positional arguments, a dictionary
        of keyword arguments.

        A callback function can be specified, that is called when the results
        of the request are picked up from the result queue. It must accept
        two arguments, the request object and it's results in that order.
        If you want to pass additional information to the callback, just stick
        it on the request object.

        requestID, if given, must be hashable as it is used by the ThreadPool
        class to store the results of that work request in a dictionary.
        It defaults to the return value of id(self).
        """
        if requestID is None:
            self.requestID = id(self)
        else:
            self.requestID = requestID
        self.callback = callback
        self.callable = callable
        self.args = args or []
        self.kwds = kwds or {}
        self.ownerObj = ownerObj


class ThreadPoolImplementation(object):
    """A thread pool, distributing work requests and collecting results.

    See the module doctring for more information.
    """

    def __init__(self, num_workers, q_size=0):
        """Set up the thread pool and start num_workers worker threads.

        num_workers is the number of worker threads to start initialy.
        If q_size > 0 the size of the work request is limited and the
        thread pool blocks when queue is full and it tries to put more
        work requests in it.
        """
        # There are some problems with the q_size. Lets analyze it:
        #
        #   - qsize == 10
        #   - We have 10 queued work requests
        #   - One of the work requests says "Hey, lets create a new thread"
        #   - That startFunction() will lock until its able to input the work request in the queue
        #   - The queue is full, no new requests can come in.
        #   - Dead-locks occur.
        #
        #   In most cases, having a q_size of 150 is enough to avoid this situation, and at the same
        #   time save some memory. The q_size is set in threadManager.py.
        self.requestsQueue = Queue.Queue()
        self.resultsQueue = Queue.Queue()
        if DEBUG:
            print '[ThreadPool][',id(self),'] Init with queue',  id(self.requestsQueue)
        self.workers = []
        self.workRequests = {}
        self.createWorkers(num_workers)

    def createWorkers(self, num_workers):
        """Add num_workers worker threads to the pool."""

        for i in xrange(num_workers):
            self.workers.append(WorkerThread(self.requestsQueue, self.resultsQueue))

    def dismissWorkers(self, num_workers):
        """Tell num_workers worker threads to to quit when they're done."""

        for i in xrange(min(num_workers, len(self.workers))):
            worker = self.workers.pop()
            worker.dismiss()

    def putRequest(self, request):
        """Put work request into work queue and save for later."""

        self.requestsQueue.put(request)
        self.workRequests[request.requestID] = request

    def poll(self, block=False, ownerObj=None, joinAll=False):
        """Process any new results in the queue."""
        while 1:
            try:
                # still results pending?
                if not joinAll:
                    owned_work_reqs_len = \
                            len([wr for wr in self.workRequests.values() \
                                 if id(wr.ownerObj) == id(ownerObj)])
                else:
                    owned_work_reqs_len = len(self.workRequests)

                if not owned_work_reqs_len:
                    raise NoResultsPending
                
                if DEBUG:
                    msg = 'The object calling poll("%s") still owns %s work' \
                    ' requests.' % (ownerObj, owned_work_reqs_len)
                    om.out.debug(msg)
                
                # Are there still workers to process remaining requests?
                elif block and not self.workers:
                    raise NoWorkersAvailable
                                
                # Get back a new result from the queue where the workers put
                # their result.
                request, result = self.resultsQueue.get(block=block, timeout=1)

                if id(request.ownerObj) == id(ownerObj) or joinAll:
                    # and hand them to the callback, if any
                    if request.callback:
                        request.callback(request, result)
                    del self.workRequests[request.requestID]

                    # Raised here so I can handle it in the main thread...
                    # TODO: Remove this. No part of the code handles errors 
                    # from tm.join()
                    if isinstance(result, Exception):
                        raise result
                    
                else:
                    self.resultsQueue.put( (request,result) )
                
            except Queue.Empty:
                if DEBUG:
                    msg = 'The results Queue is empty, breaking.'
                    om.out.debug( msg )
                break

    def wait(self, ownerObj=None, joinAll=False ):
        """Wait for results, blocking until all have arrived."""
        while 1:
            try:
                self.poll(block=True, ownerObj=ownerObj, joinAll=joinAll)
            except NoResultsPending:
                break

def makeRequests(callable, args_list, callback=None):
    """Convenience function for building several work requests for the same
    callable with different arguments for each call.

    args_list contains the parameters for each invocation of callable.
    Each item in 'argslist' should be either a 2-item tuple of the list of
    positional arguments and a dictionary of keyword arguments or a single,
    non-tuple argument.

    callback is called when the results arrive in the result queue.
    """

    requests = []
    for item in args_list:
        if item == isinstance(item, tuple):
            requests.append(
              WorkRequest(callable, item[0], item[1], callback=callback))
        else:
            requests.append(
              WorkRequest(callable, [item], None, callback=callback))
    return requests

class ThreadPool(object):
    '''
    This is a Singleton class that I had to add here as a kludge, in order to avoid the
    creation of two ThreadPool instances. If two ThreadPools are created, the whole
    threading system is crazy...
    '''
    ## Stores the unique Singleton instance-
    _iInstance = None
 
    ## Class used with this Python singleton design pattern
    #  @todo Add all variables, and methods needed for the Singleton class below
    Singleton = ThreadPoolImplementation
 
    ## The constructor
    #  @param self The object pointer.
    def __init__( self, num_workers, q_size=0):
        # Check whether we already have an instance
        if ThreadPool._iInstance is None:
            # Create and remember instanc
            ThreadPool._iInstance = ThreadPool.Singleton(num_workers,  q_size)
 
        # Store instance reference as the only member in the handle
        self._EventHandler_instance = ThreadPool._iInstance
 
 
    ## Delegate access to implementation.
    #  @param self The object pointer.
    #  @param attr Attribute wanted.
    #  @return Attribute
    def __getattr__(self, aAttr):
        return getattr(self._iInstance, aAttr)
 
 
    ## Delegate access to implementation.
    #  @param self The object pointer.
    #  @param attr Attribute wanted.
    #  @param value Vaule to be set.
    #  @return Result of operation.
    def __setattr__(self, aAttr, aValue):
        return setattr(self._iInstance, aAttr, aValue)
        

if __name__ == '__main__':
    import random
    import time

    # the work the threads will have to do (rather trivial in our example)
    def do_something(data):
        time.sleep(random.randint(1,5))
        return round(random.random() * data, 5)

    # this will be called each time a result is available
    def print_result(request, result):
        print "Result: %s from request #%s" % (result, request.requestID)

    # assemble the arguments for each job to a list...
    data = [random.randint(1,10) for i in range(20)]
    # ... and build a WorkRequest object for each item in data
    requests = makeRequests(do_something, data, print_result)

    
    # This is a crash test!
    '''
    f00 = []
    for i in xrange(1000):
        print i
        f00.append( ThreadPool(1) )
    '''
    
    # we create a pool of 10 worker threads
    main = ThreadPool(10)
    
    # then we put the work requests in the queue...
    for req in requests:
        main.putRequest(req)
        print "Work request #%s added." % req.requestID
    # or shorter:
    # [main.putRequest(req) for req in requests]

    # ...and wait for the results to arrive in the result queue
    # wait() will return when results for all work requests have arrived
    # main.wait()

    # alternatively poll for results while doing something else:
    i = 0
    while 1:
        try:
            main.poll()
            print "Main thread working..."
            time.sleep(0.5)
            if i == 10:
                print "Adding 3 more worker threads..."
                main.createWorkers(3)
            i += 1
        except (KeyboardInterrupt, NoResultsPending):
            break
