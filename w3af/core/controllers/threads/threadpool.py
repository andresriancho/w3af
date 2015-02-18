"""
threadpool.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import threading
import Queue
import time

from functools import partial

from multiprocessing.pool import ThreadPool, RUN
from multiprocessing.dummy import Process
from multiprocessing.util import Finalize
from multiprocessing import cpu_count


__all__ = ['Pool']


class one_to_many(object):
    """
    This is a simple wrapper that translates one argument to many in a function
    call. Useful for passing to the threadpool map function.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, args):
        return self.func(*args)


class return_args(object):
    """
    Utility function that returns the args in the result, useful when calling
    functions like imap_unordered().
    """
    def __init__(self, func, *args, **kwds):
        self.func = partial(func, *args, **kwds)

    def __call__(self, *args, **kwds):
        return args, self.func(*args, **kwds)


class DaemonProcess(Process):
    
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(DaemonProcess, self).__init__(group, target, name, args, kwargs)
        self.daemon = True


class Pool(ThreadPool):

    def __init__(self, processes=None, initializer=None, initargs=(),
                 worker_names=None, maxtasksperchild=None):
        """
        Overriding this method in order to:
            * Name the pool worker threads
            * Name the threads used for managing the Pool internals
        """
        self.Process = partial(DaemonProcess, name=worker_names)

        self._setup_queues()
        self._taskqueue = Queue.Queue()
        self._cache = {}
        self._state = RUN
        self._maxtasksperchild = maxtasksperchild
        self._initializer = initializer
        self._initargs = initargs

        if processes is None:
            try:
                processes = cpu_count()
            except NotImplementedError:
                processes = 1
        if processes < 1:
            raise ValueError("Number of processes must be at least 1")

        if initializer is not None and not hasattr(initializer, '__call__'):
            raise TypeError('initializer must be a callable')

        self._processes = processes
        self._pool = []
        self._repopulate_pool()

        self._worker_handler = threading.Thread(
            target=Pool._handle_workers,
            args=(self, ),
            name='PoolWorkerHandler')
        self._worker_handler.daemon = True
        self._worker_handler._state = RUN
        self._worker_handler.start()

        self._task_handler = threading.Thread(
            target=Pool._handle_tasks,
            args=(self._taskqueue, self._quick_put, self._outqueue,
                  self._pool, self._cache),
            name='PoolTaskHandler')
        self._task_handler.daemon = True
        self._task_handler._state = RUN
        self._task_handler.start()

        self._result_handler = threading.Thread(
            target=Pool._handle_results,
            args=(self._outqueue, self._quick_get, self._cache),
            name='PoolResultHandler')
        self._result_handler.daemon = True
        self._result_handler._state = RUN
        self._result_handler.start()

        self._terminate = Finalize(
            self, self._terminate_pool,
            args=(self._taskqueue, self._inqueue, self._outqueue, self._pool,
                  self._worker_handler, self._task_handler,
                  self._result_handler, self._cache),
            exitpriority=15)
    
    def _setup_queues(self):
        self._inqueue = Queue.Queue()
        self._outqueue = Queue.Queue()
        self._quick_put = self._inqueue.put
        self._quick_get = self._outqueue.get
        
    def map_multi_args(self, func, iterable, chunksize=None):
        """
        Blocks until all results are done (please note the .get())
        """
        assert self._state == RUN
        return self.map_async(one_to_many(func), iterable, chunksize).get()

    def in_qsize(self):
        return self._taskqueue.qsize()

    def is_running(self):
        return self._state == RUN

    def terminate_join(self):
        self.terminate()
        self.join()

    def finish(self, timeout=120):
        """
        Wait until all tasks in the self._inqueue have been processed (the queue
        has size == 0) and then call terminate on the Pool.

        I know this is not the best way of doing it, but had some dead-lock
        issues with:

            self.close()
            self.join()

        :param timeout: Wait up to timeout seconds for the queues to be empty
        """
        delay = 0.1

        for _ in xrange(int(timeout / delay)):
            if (self._inqueue.qsize() == 0 and
                self._outqueue.qsize() == 0 and
                self._taskqueue.qsize() == 0):
                break
            else:
                time.sleep(delay)

        self.terminate()
        self.join()

